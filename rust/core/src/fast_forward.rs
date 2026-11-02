//! Mirror of python/fast_forward.py (see its docstring for the method).

use crate::config::Config;
use crate::decisions::{max_number_of_attack, sort_scored};
use crate::events::{Event, Kind};
use crate::passive::{population_capacity, self_destruction_shape, tech_rate, time_to_reach};
use crate::pymath::{self, pymax, pymin};
use crate::rng::{Rng, Streams};
use crate::state::{Civ, World};

pub struct Jump {
    pub dt: f64,
    pub birth: bool,
    pub extinctions: Vec<bool>,
    // Civs whose tech/population is held periodic by events: they replay one regular
    // step of growth instead of drifting over the whole jump.
    pub frozen_tech: Vec<bool>,
    pub frozen_pop: Vec<bool>,
}

impl Jump {
    /// Membership in one of the civ sets (civs born after the jump was planned are not in it).
    #[inline]
    pub fn flag(set: &[bool], i: usize) -> bool {
        set.get(i).copied().unwrap_or(false)
    }
}

#[derive(PartialEq)]
enum CivSignature {
    Dead(usize),
    Alive { id: usize, attacked_by: Option<usize>, natural_tech_progress: f64, k: f64, tech: Option<f64>, pop: Option<f64> },
}

/// Python compares sorted tuples of ids: any fixed order of (kind, src, dst) gives the same equality.
#[derive(PartialEq)]
struct QuickSignature {
    applied: Vec<(Kind, usize, usize)>,
    emitted: Vec<(Kind, usize, usize)>,
    attacks: Vec<(Kind, usize, usize)>,
    civs: Vec<CivSignature>,
}

#[derive(Default)]
pub struct FastForward {
    quick: Option<QuickSignature>,
    beliefs_tracked: bool,
    stable_since: f64,
}

impl FastForward {
    pub fn step(
        &mut self,
        world: &mut World,
        applied: &[Event],
        emitted: &[Event],
        now: f64,
        streams: &mut Streams,
        config: &Config,
    ) -> Option<Jump> {
        let (tech_touched, pop_touched) = touched(world.civs.len(), applied, emitted);
        // Consumed at every step, so that it always compares with the previous step.
        let beliefs_changed = world.beliefs_changed();
        let quick = quick_signature(world, applied, emitted, &tech_touched, &pop_touched);
        if self.quick.as_ref() != Some(&quick) {
            self.quick = Some(quick);
            self.beliefs_tracked = false;
            self.stable_since = now;
            return None;
        }
        // The belief part only counts from the second step of an unchanged quick signature.
        if !self.beliefs_tracked || beliefs_changed {
            self.beliefs_tracked = true;
            self.stable_since = now;
            return None;
        }
        // Every event still in flight must have been emitted by the stationary cycle.
        if now - self.stable_since < world.history_horizon(config) {
            return None;
        }
        plan_jump(world, config, now, streams, tech_touched, pop_touched)
    }
}

fn touched(n: usize, applied: &[Event], emitted: &[Event]) -> (Vec<bool>, Vec<bool>) {
    let mut tech = vec![false; n];
    let mut pop = vec![false; n];
    for e in applied {
        tech[e.dst] = true;
        if e.kind == Kind::Attack {
            pop[e.dst] = true;
        }
    }
    for e in emitted {
        if e.kind == Kind::Attack {
            tech[e.src] = true;
        }
    }
    (tech, pop)
}

fn quick_signature(world: &World, applied: &[Event], emitted: &[Event], tech_touched: &[bool], pop_touched: &[bool]) -> QuickSignature {
    let key = |e: &Event| (e.kind, e.src, e.dst);
    let mut applied: Vec<_> = applied.iter().map(key).collect();
    applied.sort_unstable();
    let mut attacks: Vec<_> = emitted.iter().filter(|e| e.kind == Kind::Attack).map(key).collect();
    attacks.sort_unstable();
    let emitted = emitted.iter().filter(|e| e.kind != Kind::Attack).map(key).collect();
    let civs = world
        .civs
        .iter()
        .enumerate()
        .map(|(i, c)| {
            if !c.alive {
                return CivSignature::Dead(i);
            }
            CivSignature::Alive {
                id: i,
                attacked_by: c.attacked_by,
                natural_tech_progress: c.natural_tech_progress,
                k: (c.tech_level * c.population_size).trunc(),
                tech: tech_touched[i].then_some(c.tech_level),
                pop: pop_touched[i].then_some(c.population_size),
            }
        })
        .collect();
    QuickSignature { applied, emitted, attacks, civs }
}

fn plan_jump(world: &mut World, config: &Config, now: f64, streams: &mut Streams, tech_touched: Vec<bool>, pop_touched: Vec<bool>) -> Option<Jump> {
    let mut limit = config.max_jump_years;
    let milestones = [
        config.humanity_birth_date_years,
        config.present_date_years - config.artefact_window_years,
        config.present_date_years - config.signal_window_years,
        config.present_date_years,
    ];
    for milestone in milestones {
        if milestone > now {
            // Stop one regular step early so the milestone itself is crossed at normal resolution.
            limit = pymin(limit, milestone - now - config.dt);
        }
    }
    if limit < 2.0 * config.dt {
        return None;
    }

    let active = world.active(now);
    let rel = config.jump_max_relative_change;
    let n = world.civs.len();
    let mut tech_budget: Vec<Option<f64>> = vec![None; n];
    let mut pop_budget: Vec<Option<f64>> = vec![None; n];
    for &i in &active {
        tech_budget[i] = Some(rel * world.civs[i].tech_level);
        pop_budget[i] = Some(rel * world.civs[i].population_size);
    }

    limit = pymin(limit, belief_expiry_limit(world, &active, config, now));
    decision_budgets(world, &active, config, now, &mut tech_budget, &mut pop_budget);
    limit = pymin(limit, detection_limit(world, &active, config, now, &mut tech_budget));

    for &i in &active {
        let c = &world.civs[i];
        let (tb, pb) = (tech_budget[i].expect("active"), pop_budget[i].expect("active"));
        if !tech_touched[i] {
            limit = pymin(limit, time_to_spend_tech_budget(c, config, tb, pb));
        }
        if !pop_touched[i] {
            limit = pymin(limit, time_to_spend_pop_budget(c, config, pb));
        }
    }

    // Jumps last a whole number of regular steps so the time grid of the fixed-step run is kept.
    let mut n_steps = (limit / config.dt).floor();
    if n_steps.is_nan() || n_steps < 2.0 {
        return None;
    }

    // Random events: index of the first step at which the per-step roll of the fixed-step run
    // would succeed (geometric law); the jump stops there.
    let mut draws: Vec<(f64, Option<usize>)> = Vec::new();
    if config.civ_birth_rate > 0.0 {
        let log_survival = pymath::log1p(-pymin(1.0, config.civ_birth_rate * config.dt));
        draws.push((first_success(log_survival, &mut streams.birth), None));
    }
    for &i in &active {
        let hazard = config.self_destruction_risk * self_destruction_shape(world.civs[i].tech_level, config);
        if hazard > 0.0 {
            draws.push((first_success(-hazard * config.dt, &mut streams.destruction), Some(i)));
        }
    }
    for &(k, _) in &draws {
        n_steps = pymin(n_steps, k);
    }
    let mut birth = false;
    let mut extinctions = vec![false; n];
    for &(k, civ) in &draws {
        if k == n_steps {
            match civ {
                None => birth = true,
                Some(i) => extinctions[i] = true,
            }
        }
    }
    Some(Jump { dt: n_steps * config.dt, birth, extinctions, frozen_tech: tech_touched, frozen_pop: pop_touched })
}

fn first_success(log_survival: f64, rng: &mut Rng) -> f64 {
    if log_survival == f64::NEG_INFINITY {
        return 1.0;
    }
    if log_survival >= 0.0 {
        return f64::INFINITY;
    }
    (pymath::log(1.0 - rng.random()) / log_survival).floor() + 1.0
}

/// A remembered (unseen) target stays actionable until belief_memory_years after it was last seen.
fn belief_expiry_limit(world: &mut World, active: &[usize], config: &Config, now: f64) -> f64 {
    let memory = config.belief_memory_years;
    let mut limit = f64::INFINITY;
    for &i in active {
        let recent = world.civs[i].recent_beliefs(now, memory);
        for b in recent {
            let entry = &world.civs[i].belief[b];
            let expiry = entry.last_seen_at + memory;
            if entry.last_seen_at != now && expiry >= now {
                limit = pymin(limit, expiry - now - config.dt);
            }
        }
    }
    limit
}

fn shrink(budget: &mut [Option<f64>], i: usize, value: f64) {
    if let Some(b) = budget[i] {
        budget[i] = Some(pymin(b, value));
    }
}

/// Mirrors the attack decisions: bound tech drift so that no attack decision can flip.
fn decision_budgets(world: &mut World, active: &[usize], config: &Config, now: f64, tech_budget: &mut [Option<f64>], pop_budget: &mut [Option<f64>]) {
    let memory = config.belief_memory_years;
    for &a in active {
        let recent = world.civs[a].recent_beliefs(now, memory);
        let civ = &world.civs[a];
        let s = &civ.strategy;
        let mut scored = Vec::new();
        for b in recent {
            let entry = &civ.belief[b];
            if now - entry.last_seen_at > memory {
                continue;
            }
            if entry.trust >= s.attack_when_trust_inferior_than {
                continue;
            }
            let target = entry.target;
            let lag = pymax(0.0, world.civs[target].tech_level - entry.estimated_tech_level);
            let delta = civ.tech_level - entry.estimated_tech_level;
            let safe_delta = delta - s.caution_k * entry.tech_level_uncertainty;
            // The score (safe_delta) must also stay on the same side of 0 (attack only if > 0).
            let margin = pymin(pymin((safe_delta - s.attack_gap_min).abs(), (s.attack_gap_max - delta).abs()), safe_delta.abs()) - lag;
            shrink(tech_budget, a, margin / 2.0);
            shrink(tech_budget, target, margin / 2.0);
            if safe_delta > s.attack_gap_min && delta < s.attack_gap_max && safe_delta > 0.0 {
                scored.push((safe_delta, target));
            }
        }

        let k = max_number_of_attack(civ);
        if (scored.len() as f64) > k {
            sort_scored(&mut scored, world);
            let k = k as usize;
            // The attacker's own tech shifts every score equally: only the targets can reorder them.
            let margin = scored[k - 1].0 - scored[k].0;
            for &(_, target) in &scored {
                shrink(tech_budget, target, margin / 2.0);
            }
            // The number of attacks k grows with tech * population: keep both below the next integer.
            let next = k as f64 + 1.0;
            let ceiling = next / (civ.tech_level + pymax(0.0, tech_budget[a].expect("active"))) - civ.population_size;
            pop_budget[a] = Some(pymin(pop_budget[a].expect("active"), ceiling));
            let value = next / (civ.population_size + pymax(0.0, pop_budget[a].expect("active"))) - civ.tech_level;
            shrink(tech_budget, a, value);
        }
    }
}

/// Unseen pairs: limit the drift of the emitter's broadcast radius and the time until the
/// observer's probe sphere reaches the target (see fast_forward._detection_limit).
fn detection_limit(world: &World, active: &[usize], config: &Config, now: f64, tech_budget: &mut [Option<f64>]) -> f64 {
    let mut limit = f64::INFINITY;
    let window_start = config.present_date_years - config.signal_window_years;
    let mut is_active = vec![false; world.civs.len()];
    for &i in active {
        is_active[i] = true;
    }
    for &yi in active {
        let y = &world.civs[yi];
        if y.is_human && now < window_start {
            continue;
        }
        let (distances, neighbors) = world.neighbors_by_distance(yi);
        let n_broadcast = distances.partition_point(|&d| d <= config.max_broadcast_radius);
        for (&d, &xi) in distances[..n_broadcast].iter().zip(&neighbors[..n_broadcast]) {
            let xi = xi as usize;
            let x = &world.civs[xi];
            if !is_active[xi] || x.tech_level <= 0.0 || seen_now(y, xi, now) {
                continue;
            }
            // Broadcast radius is proportional to tech.
            let critical_tech = if x.broadcast_radius > 0.0 { d * x.tech_level / x.broadcast_radius } else { f64::INFINITY };
            shrink(tech_budget, xi, critical_tech - x.tech_level);
        }
        for (&d, &xi) in distances.iter().zip(neighbors) {
            if d > config.max_probe_radius {
                break;
            }
            let xi = xi as usize;
            if !is_active[xi] || seen_now(y, xi, now) {
                continue;
            }
            if y.probe_radius >= d {
                return 0.0;
            }
            // Probe speed is proportional to tech: bound it by the end-of-jump tech.
            let budget = tech_budget[yi].expect("active");
            let gain = if y.tech_level > 0.0 { 1.0 + pymax(0.0, budget) / y.tech_level } else { 1.0 };
            let speed = y.probe_speed * gain;
            if speed > 0.0 {
                limit = pymin(limit, (d - y.probe_radius) / speed - config.dt);
            }
            break;
        }
    }
    limit
}

fn seen_now(y: &Civ, x: usize, now: f64) -> bool {
    y.belief_entry(x).is_some_and(|e| e.last_seen_at == now)
}

fn time_to_spend_pop_budget(civ: &Civ, config: &Config, pop_budget: f64) -> f64 {
    let cap = population_capacity(civ, config);
    let r = civ.natural_population_growth;
    if r <= 0.0 || cap.is_some_and(|cap| civ.population_size >= cap) {
        return f64::INFINITY;
    }
    time_to_reach(civ.population_size, civ.population_size + pop_budget, r, cap)
}

fn time_to_spend_tech_budget(civ: &Civ, config: &Config, tech_budget: f64, pop_budget: f64) -> f64 {
    // Fastest tech growth rate reachable during the jump (population only grows).
    let r = if civ.population_size > 0.0 {
        tech_rate(civ) * (1.0 + pymax(0.0, pop_budget) / civ.population_size)
    } else {
        0.0
    };
    if r <= 0.0 || civ.tech_level >= config.tech_cap {
        return f64::INFINITY;
    }
    time_to_reach(civ.tech_level, civ.tech_level + tech_budget, r, config.tech_growth_cap())
}
