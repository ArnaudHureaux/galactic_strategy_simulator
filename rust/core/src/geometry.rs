//! Mirror of python/geometry.py.

use std::rc::Rc;

use crate::pymath;

pub type Position = [f64; 3];

/// geometry.dist: Python's `(a - b) ** 2` goes through C pow, kept here for parity.
#[inline]
pub fn dist(a: &Position, b: &Position) -> f64 {
    (pymath::pow(a[0] - b[0], 2.0) + pymath::pow(a[1] - b[1], 2.0) + pymath::pow(a[2] - b[2], 2.0)).sqrt()
}

/// Pairs (index, distance) within some radius of a point, sorted by index.
type Pairs = Rc<[(u32, f64)]>;

/// Civs never move: each point keeps the other points sorted by (distance, index), so a
/// radius query is a binary search instead of a scan over every civ.
#[derive(Default)]
pub struct NeighborIndex {
    positions: Vec<Position>,
    row_d: Vec<Vec<f64>>,
    row_i: Vec<Vec<u32>>,
    // Per point: (number of neighbours within the last radius, total points, pairs).
    cache: Vec<Option<(usize, usize, Pairs)>>,
}

impl NeighborIndex {
    pub fn add(&mut self, position: Position) -> usize {
        let new = self.positions.len();
        let mut pairs = Vec::with_capacity(new);
        for (j, other) in self.positions.iter().enumerate() {
            let d = dist(other, &position);
            let row_d = &mut self.row_d[j];
            let k = row_d.partition_point(|&x| x <= d);
            row_d.insert(k, d);
            self.row_i[j].insert(k, new as u32);
            pairs.push((d, j as u32));
        }
        // Indices are already increasing: a stable sort on distance sorts by (distance, index).
        pairs.sort_by(|a, b| a.0.partial_cmp(&b.0).expect("distances are not NaN"));
        self.positions.push(position);
        self.row_d.push(pairs.iter().map(|p| p.0).collect());
        self.row_i.push(pairs.iter().map(|p| p.1).collect());
        self.cache.push(None);
        new
    }

    /// (index, distance) of the other points at distance <= radius from point i, by index.
    pub fn within_pairs(&mut self, i: usize, radius: f64) -> Pairs {
        let row_d = &self.row_d[i];
        let k = row_d.partition_point(|&x| x <= radius);
        let n = self.positions.len();
        if let Some((ck, cn, pairs)) = &self.cache[i]
            && *ck == k
            && *cn == n
        {
            return Rc::clone(pairs);
        }
        let mut pairs: Vec<(u32, f64)> = self.row_i[i][..k].iter().copied().zip(row_d[..k].iter().copied()).collect();
        pairs.sort_unstable_by_key(|p| p.0);
        let pairs: Pairs = pairs.into();
        self.cache[i] = Some((k, n, Rc::clone(&pairs)));
        pairs
    }

    /// (distances, indices) of every other point, by increasing distance.
    pub fn row(&self, i: usize) -> (&[f64], &[u32]) {
        (&self.row_d[i], &self.row_i[i])
    }
}
