//! CPython's `random.Random` (MT19937 and the few methods rng.py uses), and the independent
//! streams of rng.make_streams.

use sha2::{Digest, Sha256};

use crate::pymath;

const N: usize = 624;
const M: usize = 397;
const MATRIX_A: u32 = 0x9908_b0df;
const UPPER_MASK: u32 = 0x8000_0000;
const LOWER_MASK: u32 = 0x7fff_ffff;

pub struct Rng {
    mt: [u32; N],
    mti: usize,
}

impl Rng {
    /// random.Random(seed) for a non-negative integer seed.
    pub fn new(seed: u64) -> Rng {
        // CPython splits abs(seed) into 32-bit words, least significant first (at least one).
        let key: Vec<u32> = if seed >> 32 == 0 { vec![seed as u32] } else { vec![seed as u32, (seed >> 32) as u32] };
        let mut rng = Rng { mt: [0; N], mti: N + 1 };
        rng.init_by_array(&key);
        rng
    }

    fn init_genrand(&mut self, s: u32) {
        self.mt[0] = s;
        for i in 1..N {
            let prev = self.mt[i - 1];
            self.mt[i] = 1_812_433_253u32.wrapping_mul(prev ^ (prev >> 30)).wrapping_add(i as u32);
        }
        self.mti = N;
    }

    fn init_by_array(&mut self, key: &[u32]) {
        self.init_genrand(19_650_218);
        let (mut i, mut j) = (1usize, 0usize);
        for _ in 0..N.max(key.len()) {
            let prev = self.mt[i - 1];
            self.mt[i] = (self.mt[i] ^ (prev ^ (prev >> 30)).wrapping_mul(1_664_525))
                .wrapping_add(key[j])
                .wrapping_add(j as u32);
            i += 1;
            j += 1;
            if i >= N {
                self.mt[0] = self.mt[N - 1];
                i = 1;
            }
            if j >= key.len() {
                j = 0;
            }
        }
        for _ in 0..N - 1 {
            let prev = self.mt[i - 1];
            self.mt[i] = (self.mt[i] ^ (prev ^ (prev >> 30)).wrapping_mul(1_566_083_941)).wrapping_sub(i as u32);
            i += 1;
            if i >= N {
                self.mt[0] = self.mt[N - 1];
                i = 1;
            }
        }
        self.mt[0] = 0x8000_0000;
    }

    fn genrand_u32(&mut self) -> u32 {
        let mag01 = |y: u32| if y & 1 == 0 { 0 } else { MATRIX_A };
        if self.mti >= N {
            let mt = &mut self.mt;
            for kk in 0..N - M {
                let y = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK);
                mt[kk] = mt[kk + M] ^ (y >> 1) ^ mag01(y);
            }
            for kk in N - M..N - 1 {
                let y = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK);
                mt[kk] = mt[kk + M - N] ^ (y >> 1) ^ mag01(y);
            }
            let y = (mt[N - 1] & UPPER_MASK) | (mt[0] & LOWER_MASK);
            mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ mag01(y);
            self.mti = 0;
        }
        let mut y = self.mt[self.mti];
        self.mti += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c_5680;
        y ^= (y << 15) & 0xefc6_0000;
        y ^= y >> 18;
        y
    }

    /// random.random(): 53 random bits in [0, 1).
    pub fn random(&mut self) -> f64 {
        let a = self.genrand_u32() >> 5;
        let b = self.genrand_u32() >> 6;
        (a as f64 * 67_108_864.0 + b as f64) * (1.0 / 9_007_199_254_740_992.0)
    }

    pub fn uniform(&mut self, low: f64, high: f64) -> f64 {
        low + (high - low) * self.random()
    }

    /// rng.Rng.exponential: random.expovariate(1.0 / scale).
    pub fn exponential(&mut self, scale: f64) -> f64 {
        let lambd = 1.0 / scale;
        -pymath::log(1.0 - self.random()) / lambd
    }

    fn getrandbits(&mut self, k: u32) -> u32 {
        debug_assert!((1..=32).contains(&k));
        self.genrand_u32() >> (32 - k)
    }

    /// random._randbelow_with_getrandbits: uniform integer in [0, n), n > 0.
    pub fn randbelow(&mut self, n: u32) -> u32 {
        let k = 32 - n.leading_zeros();
        let mut r = self.getrandbits(k);
        while r >= n {
            r = self.getrandbits(k);
        }
        r
    }

    /// Index drawn by random.choices(range(len(weights)), weights)[0].
    pub fn weighted_index(&mut self, weights: &[f64]) -> usize {
        let mut cum = Vec::with_capacity(weights.len());
        let mut total = 0.0;
        for (k, &w) in weights.iter().enumerate() {
            total = if k == 0 { w } else { total + w };
            cum.push(total);
        }
        let total = total + 0.0;
        let x = self.random() * total;
        // bisect_right(cum, x, 0, n - 1)
        let (mut lo, mut hi) = (0usize, weights.len() - 1);
        while lo < hi {
            let mid = (lo + hi) / 2;
            if x < cum[mid] {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        lo
    }

    /// rng.Rng.poisson (Knuth's multiplication method).
    pub fn poisson(&mut self, lam: f64) -> u64 {
        let target = pymath::exp(-lam);
        let mut k = 0u64;
        let mut p = 1.0;
        loop {
            k += 1;
            p *= self.random();
            if p <= target {
                return k - 1;
            }
        }
    }
}

/// rng.Streams: one independent stream per source of randomness.
pub struct Streams {
    pub world: Rng,
    pub humanity: Rng,
    pub birth: Rng,
    pub destruction: Rng,
    pub artefact: Rng,
}

impl Streams {
    pub fn new(seed: i64) -> Streams {
        let stream = |name: &str| Rng::new(derive_seed(seed, name));
        Streams {
            world: stream("world"),
            humanity: stream("humanity"),
            birth: stream("birth"),
            destruction: stream("destruction"),
            artefact: stream("artefact"),
        }
    }
}

fn derive_seed(seed: i64, name: &str) -> u64 {
    let digest = Sha256::digest(format!("{seed}/{name}").as_bytes());
    u64::from_be_bytes(digest[..8].try_into().expect("8 bytes"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn matches_cpython_random() {
        // Reference values printed by CPython.
        assert_eq!(Rng::new(42).random(), 0.6394267984578837);
        assert_eq!(Rng::new(0).random(), 0.8444218515250481);
        let mut r = Rng::new((1 << 40) + 7);
        assert_eq!(r.random(), 0.6137037779936511);
        // [r.choice([-1, 1]) for _ in range(8)], r.choices("abc", (0.7, 0.2, 0.1))[0], r.expovariate(1 / 300.0)
        let signs: Vec<i32> = (0..8).map(|_| if r.randbelow(2) == 0 { -1 } else { 1 }).collect();
        assert_eq!(signs, [1, 1, -1, 1, 1, 1, 1, 1]);
        assert_eq!(r.weighted_index(&[0.7, 0.2, 0.1]), 1);
        assert_eq!(r.exponential(300.0), 139.72862335577753);
    }
}
