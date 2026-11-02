//! Mirror of python/state.py. Civs are referred to by their index in World::civs, which is
//! also their index in the neighbour index (both grow together).

use std::collections::{BTreeSet, HashMap, VecDeque};
use std::rc::Rc;

use crate::config::Config;
use crate::geometry::{NeighborIndex, Position};
use crate::pymath::{self, C_PC_PER_YEAR, pymax, pymin};

#[derive(Clone, Copy, Debug)]
pub struct Snapshot {
    pub t: f64,
    pub tech_level: f64,
    pub broadcast_radius: f64,
    pub probe_radius: f64,
    pub attacked_by: Option<usize>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Channel {
    Signal,
    Probe,
}

impl Channel {
    pub fn name(self) -> &'static str {
        match self {
            Channel::Signal => "signal",
            Channel::Probe => "probe",
        }
    }
}

#[derive(Clone, Debug)]
pub struct BeliefEntry {
    pub target: usize,
    pub estimated_tech_level: f64,
    pub tech_level_uncertainty: f64,
    pub is_competitor: bool,
    pub trust: f64,
    pub channel: Channel,
    pub attacked_me: bool,
    pub last_seen_at: f64,
    /// (rounded trust, attacked_me) as of the last stationarity check (see fast_forward).
    pub signature: Option<(f64, bool)>,
}

#[derive(Clone, Debug)]
pub struct Strategy {
    pub broadcast: bool,
    pub attack_gap_min: f64,
    pub attack_gap_max: f64,
    pub caution_k: f64,
    pub attack_when_trust_inferior_than: f64,
    pub trust_default_competitor: f64,
    pub trust_default_noncompetitor: f64,
    pub share_trust_threshold: f64,
    pub colonization_aggressiveness: f64,
}

impl Strategy {
    /// Values in config.STRATEGY_RANGES order.
    pub fn from_values(broadcast: bool, v: [f64; 8]) -> Strategy {
        Strategy {
            broadcast,
            attack_gap_min: v[0],
            attack_gap_max: v[1],
            caution_k: v[2],
            attack_when_trust_inferior_than: v[3],
            trust_default_competitor: v[4],
            trust_default_noncompetitor: v[5],
            share_trust_threshold: v[6],
            colonization_aggressiveness: v[7],
        }
    }

    /// (name, value) of the float parameters, in config.STRATEGY_RANGES order.
    pub fn values(&self) -> [(&'static str, f64); 8] {
        [
            ("strategy_attack_gap_min", self.attack_gap_min),
            ("strategy_attack_gap_max", self.attack_gap_max),
            ("strategy_caution_k", self.caution_k),
            ("strategy_attack_when_trust_inferior_than", self.attack_when_trust_inferior_than),
            ("strategy_trust_default_competitor", self.trust_default_competitor),
            ("strategy_trust_default_noncompetitor", self.trust_default_noncompetitor),
            ("strategy_share_trust_threshold", self.share_trust_threshold),
            ("strategy_colonization_aggressiveness", self.colonization_aggressiveness),
        ]
    }
}

#[derive(Clone, Debug)]
pub struct Civ {
    pub id: String,
    pub position: Position,
    pub birth_year: f64,
    pub alive: bool,
    pub biochem: usize,
    pub tech_level: f64,
    pub population_size: f64,
    pub nb_of_world: f64,
    pub natural_tech_progress: f64,
    pub natural_population_growth: f64,
    pub colonization_aggressiveness: f64,
    pub strategy: Strategy,
    pub broadcast_radius: f64,
    pub probe_speed: f64,
    pub probe_radius: f64,
    pub expansion_radius: f64,
    /// Beliefs in insertion order (an entry's index is its `order` in Python).
    pub belief: Vec<BeliefEntry>,
    /// Target civ -> index in `belief`.
    pub belief_of: HashMap<usize, usize>,
    /// Beliefs seen recently enough to still be actionable (indices in `belief`).
    pub recent: BTreeSet<usize>,
    pub attacked_by: Option<usize>,
    pub is_human: bool,
    pub extinct_at: Option<f64>,
    pub extinction_cause: Option<&'static str>,
    pub probe_arrived_at_human: Option<f64>,
    pub artefact_rolled: bool,
    pub history: VecDeque<Snapshot>,
}

impl Civ {
    /// Civilisation.recent_beliefs: indices of the beliefs that may still be actionable, in
    /// belief order. Callers apply their own exact test.
    pub fn recent_beliefs(&mut self, now: f64, memory: f64) -> Vec<usize> {
        let belief = &self.belief;
        self.recent.retain(|&b| {
            let seen = belief[b].last_seen_at;
            !(now - seen > memory && seen + memory < now)
        });
        self.recent.iter().copied().collect()
    }

    pub fn record(&mut self, now: f64, horizon: f64) {
        self.history.push_back(Snapshot {
            t: now,
            tech_level: self.tech_level,
            broadcast_radius: self.broadcast_radius,
            probe_radius: self.probe_radius,
            attacked_by: self.attacked_by,
        });
        // Keep the latest snapshot older than the horizon: it still describes the state at now - horizon.
        let cutoff = now - horizon;
        while self.history.len() >= 2 && self.history[1].t <= cutoff {
            self.history.pop_front();
        }
    }

    pub fn state_at(&self, t: f64) -> Option<Snapshot> {
        if self.extinct_at.is_some_and(|extinct_at| t >= extinct_at) {
            return None;
        }
        let i = self.history.partition_point(|s| s.t <= t);
        if i == 0 { None } else { Some(self.history[i - 1]) }
    }

    pub fn go_extinct(&mut self, t: f64, cause: &'static str) {
        if self.alive {
            self.alive = false;
            self.extinct_at = Some(t);
            self.extinction_cause = Some(cause);
        }
    }

    /// Probes are replenished while the creator lives, then survive it for a tech-dependent time.
    pub fn probes_end_at(&self, config: &Config) -> f64 {
        match self.extinct_at {
            None => f64::INFINITY,
            // A dead civ is never updated again: its last snapshot is final.
            Some(extinct_at) => {
                let tech_at_death = self.history.back().map_or(self.tech_level, |s| s.tech_level);
                extinct_at + config.probe_lifetime_per_tech * tech_at_death
            }
        }
    }

    pub fn belief_entry(&self, target: usize) -> Option<&BeliefEntry> {
        self.belief_of.get(&target).map(|&b| &self.belief[b])
    }
}

pub struct World {
    pub civs: Vec<Civ>,
    pub humanity: usize,
    pub n_initial: usize,
    pub rejected: bool,
    pub intractable: bool,
    pub rejection_reason: Option<String>,
    pub rejected_at: Option<f64>,
    neighbors: NeighborIndex,
    lo: [f64; 3],
    hi: [f64; 3],
    // Change tracking for the fast-forward belief signature (see note_* and beliefs_changed).
    tracking: bool,
    touched_beliefs: Vec<(usize, usize)>,
    detect_now: Option<f64>,
    prev_detect_now: Option<f64>,
    seen_count: usize,
    prev_seen_count: usize,
    seen_changed: bool,
}

impl World {
    /// The last civ is humanity.
    pub fn new(civs: Vec<Civ>, config: &Config) -> World {
        let first = civs.first().expect("humanity is in the world").position;
        let mut world = World {
            civs: Vec::with_capacity(civs.len()),
            humanity: civs.len() - 1,
            n_initial: civs.len(),
            rejected: false,
            intractable: false,
            rejection_reason: None,
            rejected_at: None,
            neighbors: NeighborIndex::default(),
            lo: first,
            hi: first,
            tracking: config.fast_forward,
            touched_beliefs: Vec::new(),
            detect_now: None,
            prev_detect_now: None,
            seen_count: 0,
            prev_seen_count: 0,
            seen_changed: false,
        };
        for civ in civs {
            world.add_civ(civ);
        }
        world
    }

    /// The run contradicts the observed silence: keep the first cause found.
    pub fn reject(&mut self, reason: String, t: f64) {
        if !self.rejected {
            self.rejected = true;
            self.rejection_reason = Some(reason);
            self.rejected_at = Some(t);
        }
    }

    pub fn add_civ(&mut self, civ: Civ) {
        let slot = self.neighbors.add(civ.position);
        debug_assert_eq!(slot, self.civs.len());
        for k in 0..3 {
            self.lo[k] = pymin(self.lo[k], civ.position[k]);
            self.hi[k] = pymax(self.hi[k], civ.position[k]);
        }
        self.civs.push(civ);
    }

    /// (other civ, distance) for every other civ at distance <= radius, in civs order.
    pub fn neighbor_pairs_within(&mut self, i: usize, radius: f64) -> Rc<[(u32, f64)]> {
        self.neighbors.within_pairs(i, radius)
    }

    /// (distances, civs) of every other civ, by increasing distance.
    pub fn neighbors_by_distance(&self, i: usize) -> (&[f64], &[u32]) {
        self.neighbors.row(i)
    }

    // The fast-forward compares, step after step, the rounded trust and attacked_me of every
    // belief and which beliefs were refreshed this step; the world records what may have
    // changed that signature since the previous step.
    pub fn note_detection_step(&mut self, now: f64) {
        self.prev_detect_now = self.detect_now;
        self.detect_now = Some(now);
        self.prev_seen_count = self.seen_count;
        self.seen_count = 0;
    }

    /// `previous_seen` is the entry's last_seen_at before this observation (None if created).
    pub fn note_seen(&mut self, civ: usize, belief: usize, previous_seen: Option<f64>) {
        if !self.tracking {
            return;
        }
        self.seen_count += 1;
        let created = previous_seen.is_none();
        if created || previous_seen != self.prev_detect_now {
            self.seen_changed = true;
        }
        if created {
            self.touched_beliefs.push((civ, belief));
        }
    }

    pub fn note_trust(&mut self, civ: usize, belief: usize) {
        if self.tracking {
            self.touched_beliefs.push((civ, belief));
        }
    }

    /// Whether the belief signature differs from the one at the previous call (one call per step).
    /// Trust is compared at 1e-9 (see state.World.beliefs_changed).
    pub fn beliefs_changed(&mut self) -> bool {
        let mut changed = self.seen_changed || self.seen_count != self.prev_seen_count;
        for &(c, b) in &self.touched_beliefs {
            let entry = &mut self.civs[c].belief[b];
            let signature = Some((pymath::round9(entry.trust), entry.attacked_me));
            if signature != entry.signature {
                entry.signature = signature;
                changed = true;
            }
        }
        self.touched_beliefs.clear();
        self.seen_changed = false;
        changed
    }

    pub fn light_crossing_years(&self) -> f64 {
        let squares = |k: usize| pymath::pow(self.hi[k] - self.lo[k], 2.0);
        let diagonal = pymath::pow(squares(0) + squares(1) + squares(2), 0.5);
        diagonal / C_PC_PER_YEAR
    }

    pub fn history_horizon(&self, config: &Config) -> f64 {
        self.light_crossing_years() + config.signal_window_years
    }

    pub fn alive_count(&self) -> usize {
        self.civs.iter().filter(|c| c.alive).count()
    }

    pub fn active(&self, now: f64) -> Vec<usize> {
        (0..self.civs.len()).filter(|&i| self.civs[i].alive && now >= self.civs[i].birth_year).collect()
    }

    pub fn orphan_probes(&self, now: f64, config: &Config) -> Vec<usize> {
        (0..self.civs.len())
            .filter(|&i| !self.civs[i].alive && now < self.civs[i].probes_end_at(config))
            .collect()
    }

    /// Extinct civs stay visible from afar until their last light has crossed the region.
    pub fn visible(&self, now: f64) -> Vec<bool> {
        let horizon = self.light_crossing_years();
        self.civs
            .iter()
            .map(|c| now >= c.birth_year && (c.alive || c.extinct_at.is_some_and(|e| now - e < horizon)))
            .collect()
    }
}
