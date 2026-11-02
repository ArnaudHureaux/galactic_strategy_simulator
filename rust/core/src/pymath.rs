//! Floating-point helpers that reproduce CPython's results bit for bit.
//!
//! CPython's `math` module and `float ** float` call the platform C library (ucrtbase on
//! Windows, libm elsewhere). Rust's own `f64::exp`, `ln`... may resolve to another
//! implementation (mingw on windows-gnu) that differs in the last bit, so the transcendental
//! functions are called through the same C library as CPython, by pointer so that LLVM does
//! not rewrite them (e.g. `pow(x, 2.0)` into `x * x`).

type F1 = unsafe extern "C" fn(f64) -> f64;
type F2 = unsafe extern "C" fn(f64, f64) -> f64;

struct Funcs {
    exp: F1,
    log: F1,
    log1p: F1,
    expm1: F1,
    sin: F1,
    cos: F1,
    pow: F2,
}

#[cfg(windows)]
mod platform {
    use super::{F1, F2, Funcs};
    use std::ffi::c_void;
    use std::sync::OnceLock;

    #[link(name = "kernel32")]
    unsafe extern "system" {
        fn LoadLibraryA(name: *const u8) -> *mut c_void;
        fn GetProcAddress(module: *mut c_void, name: *const u8) -> *mut c_void;
    }

    static FUNCS: OnceLock<Funcs> = OnceLock::new();

    fn load() -> Funcs {
        unsafe {
            let module = LoadLibraryA(c"ucrtbase.dll".as_ptr().cast());
            assert!(!module.is_null(), "ucrtbase.dll not found");
            let get = |name: &std::ffi::CStr| {
                let f = GetProcAddress(module, name.as_ptr().cast());
                assert!(!f.is_null(), "{name:?} not found in ucrtbase.dll");
                f
            };
            Funcs {
                exp: std::mem::transmute::<*mut c_void, F1>(get(c"exp")),
                log: std::mem::transmute::<*mut c_void, F1>(get(c"log")),
                log1p: std::mem::transmute::<*mut c_void, F1>(get(c"log1p")),
                expm1: std::mem::transmute::<*mut c_void, F1>(get(c"expm1")),
                sin: std::mem::transmute::<*mut c_void, F1>(get(c"sin")),
                cos: std::mem::transmute::<*mut c_void, F1>(get(c"cos")),
                pow: std::mem::transmute::<*mut c_void, F2>(get(c"pow")),
            }
        }
    }

    #[inline]
    pub(super) fn funcs() -> &'static Funcs {
        FUNCS.get_or_init(load)
    }
}

#[cfg(not(windows))]
mod platform {
    use super::Funcs;

    unsafe extern "C" {
        fn exp(x: f64) -> f64;
        fn log(x: f64) -> f64;
        fn log1p(x: f64) -> f64;
        fn expm1(x: f64) -> f64;
        fn sin(x: f64) -> f64;
        fn cos(x: f64) -> f64;
        fn pow(x: f64, y: f64) -> f64;
    }

    static FUNCS: Funcs = Funcs { exp, log, log1p, expm1, sin, cos, pow };

    #[inline]
    pub(super) fn funcs() -> &'static Funcs {
        std::hint::black_box(&FUNCS)
    }
}

use platform::funcs;

/// Parsecs travelled by light in one year (constants.C_PC_PER_YEAR).
pub const C_PC_PER_YEAR: f64 = 1.0 / 3.262;

#[inline]
pub fn exp(x: f64) -> f64 {
    unsafe { (funcs().exp)(x) }
}

#[inline]
pub fn log(x: f64) -> f64 {
    unsafe { (funcs().log)(x) }
}

/// math.log1p: CPython returns zeros unchanged before calling the C library.
#[inline]
pub fn log1p(x: f64) -> f64 {
    if x == 0.0 { x } else { unsafe { (funcs().log1p)(x) } }
}

#[inline]
pub fn expm1(x: f64) -> f64 {
    unsafe { (funcs().expm1)(x) }
}

#[inline]
pub fn sin(x: f64) -> f64 {
    unsafe { (funcs().sin)(x) }
}

#[inline]
pub fn cos(x: f64) -> f64 {
    unsafe { (funcs().cos)(x) }
}

/// Python's `iv ** iw` for floats (float_pow): special cases first, and a negative base
/// with an integer exponent is raised as |iv| then negated if the exponent is odd.
/// Cases where Python raises are not reached by the simulation.
pub fn pow(iv: f64, iw: f64) -> f64 {
    if iw == 0.0 {
        return 1.0;
    }
    if iv.is_nan() {
        return iv;
    }
    if iw.is_nan() {
        return if iv == 1.0 { 1.0 } else { iw };
    }
    let odd = |x: f64| (x.abs() % 2.0) == 1.0;
    if iv == 0.0 {
        return if odd(iw) { iv } else { 0.0 };
    }
    let mut base = iv;
    let mut negate = false;
    if base < 0.0 && iw.is_finite() {
        base = -base;
        negate = odd(iw);
    }
    if base == 1.0 {
        return if negate { -1.0 } else { 1.0 };
    }
    let result = unsafe { (funcs().pow)(base, iw) };
    if negate { -result } else { result }
}

/// Python's min(a, b): a unless b < a.
#[inline]
pub fn pymin(a: f64, b: f64) -> f64 {
    if b < a { b } else { a }
}

/// Python's max(a, b): a unless b > a.
#[inline]
pub fn pymax(a: f64, b: f64) -> f64 {
    if b > a { b } else { a }
}

/// Python's round(x, 9): exact decimal rounding (ties to even), then nearest double.
pub fn round9(x: f64) -> f64 {
    if !x.is_finite() {
        return x;
    }
    format!("{x:.9}").parse().expect("formatted float parses")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round9_matches_python() {
        // Values from CPython: round(x, 9).
        assert_eq!(round9(0.0009765625), 0.000976562); // exact tie, to even
        assert_eq!(round9(0.0029296875), 0.002929688); // exact tie, to even
        assert_eq!(round9(0.1234567891234), 0.123456789);
        assert_eq!(round9(-1e-12).to_bits(), (-0.0f64).to_bits());
        assert_eq!(round9(0.9999999999), 1.0);
    }

    #[test]
    fn pow_special_cases() {
        assert_eq!(pow(-3.0, 2.0), 9.0);
        assert_eq!(pow(0.0, 2.0), 0.0);
        assert_eq!(pow(1.0, 0.3), 1.0);
        assert_eq!(pow(4.0, 0.5), 2.0);
    }
}
