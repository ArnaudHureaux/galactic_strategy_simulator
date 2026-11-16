//! Mirror of python/fast_forward.py (see its docstring for the method).

use crate::config::Config;
use crate::decisions::{attack_capacity, max_number_of_attack, sort_scored};
use crate::events::{Event, Kind};
use crate::geometry::dist;
use crate::passive::{FOUR_THIRDS_PI, beacon_hazard, colonization_tech, front_speed_at, grow, probe_range, probe_speed, signal_radius, tech_for_signal_radius, population_capacity, self_destruction_shape, tech_rate, time_to_reach, world_density};
use crate::pymath::{self, C_PC_PER_YEAR, pymax, pymin};
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
    Alive {
        id: usize,
        attacked_by: Option<usize>,
        natural_tech_progress: f64,
        k: f64,
        tech: Option<f64>,
        pop: Option<f64>,
        front: Option<f64>,
        front_blocked: bool,
    },
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
        let quick = quick_signature(world, applied, emitted, &tech_touched, &pop_touched, config);
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

fn quick_signature(world: &World, applied: &[Event], emitted: &[Event], tech_touched: &[bool], pop_touched: &[bool], config: &Config) -> QuickSignature {
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
                // The number of attacks only matters below the number of possible targets (beliefs).
                k: pymin(attack_capacity(c.tech_level, c.population_size, config).trunc(), c.belief.len() as f64),
                // Compared at 1e-9 (see fast_forward._quick_signature).
                tech: tech_touched[i].then_some(pymath::round9(c.tech_level)),
                pop: pop_touched[i].then_some(c.population_size),
                front: pop_touched[i].then_some(c.expansion_radius),
                front_blocked: c.front_blocked,
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
        config.present_date_years - config.humanity_leak_years,
        config.present_date_years - config.humanity_listening_years,
        config.present_date_years,
    ];
    for milestone in milestones {
        if milestone > now {
            // Stop one regular step early so the milestone itself is crossed at normal resolution.
            limit = pymin(limit, milestone - now - config.dt);
        }
    }
    for c in &world.civs {
        if c.birth_year > now {
            // A civ yet to be born (spread initial cohort) is born at normal resolution.
            limit = pymin(limit, c.birth_year - now - config.dt);
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
    // A front starts at colonization_tech: the jump stops short of it (see _plan_jump).
    let growth_cap = config.tech_growth_cap();
    for &i in &active {
        let c = &world.civs[i];
        if c.colonization_aggressiveness > 0.0 && !c.front_blocked {
            let threshold = colonization_tech(c, config);
            if c.tech_level < threshold && growth_cap.map_or(true, |cap| threshold < cap) {
                tech_budget[i] = Some(pymin(tech_budget[i].expect("active"), threshold - c.tech_level));
            }
        }
    }
    // Fronts of attacked civs replay one regular step per jump (see passive_update): they do not drift.
    let mut front_budget: Vec<Option<f64>> = vec![None; n];
    for &i in &active {
        if !pop_touched[i] && front_moves(&world.civs[i], config) {
            front_budget[i] = Some(initial_front_budget(&world.civs[i], config, rel));
        }
    }

    limit = pymin(limit, belief_expiry_limit(world, &active, config, now));
    decision_budgets(world, &active, config, now, &mut tech_budget, &mut pop_budget);
    colonization_budgets(world, &active, &mut front_budget);
    limit = pymin(limit, detection_limit(world, &active, config, now, &mut tech_budget, &mut front_budget));

    for &i in &active {
        let c = &world.civs[i];
        let (tb, pb) = (tech_budget[i].expect("active"), pop_budget[i].expect("active"));
        if !tech_touched[i] {
            limit = pymin(limit, time_to_spend_tech_budget(c, config, tb, pb));
        }
        if !pop_touched[i] {
            limit = pymin(limit, time_to_spend_pop_budget(c, config, pb));
        }
        if let Some(fb) = front_budget[i] {
            limit = pymin(limit, time_to_spend_front_budget(c, config, fb, tb));
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
        // Largest drift of a score of `scored` through its target's uncertainty.
        let mut widest_drift = 0.0;
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
            // The uncertainty is refreshed at each observation and stays within [0, bound].
            let drift = if s.caution_k > 0.0 && world.civs[target].alive {
                s.caution_k * projected_progress_bound(civ, &world.civs[target], config, now)
            } else {
                0.0
            };
            // The score (safe_delta) must also stay on the same side of 0 (attack only if > 0).
            let margin = pymin(pymin((safe_delta - s.attack_gap_min).abs(), (s.attack_gap_max - delta).abs()), safe_delta.abs()) - lag - drift;
            shrink(tech_budget, a, margin / 2.0);
            shrink(tech_budget, target, margin / 2.0);
            if safe_delta > s.attack_gap_min && delta < s.attack_gap_max && safe_delta > 0.0 {
                scored.push((safe_delta, target));
                widest_drift = pymax(widest_drift, drift);
            }
        }

        let k = max_number_of_attack(civ, config);
        if (scored.len() as f64) > k {
            sort_scored(&mut scored, world);
            let k = k as usize;
            // The attacker's own tech shifts every score equally: only the targets can reorder them.
            let margin = scored[k - 1].0 - scored[k].0 - 2.0 * widest_drift;
            for &(_, target) in &scored {
                shrink(tech_budget, target, margin / 2.0);
            }
            // The number of attacks k grows with tech * population: keep both below the next integer.
            let rate = config.attacks_per_tech_population;
            if rate > 0.0 {
                let next = k as f64 + 1.0;
                let ceiling = next / (rate * (civ.tech_level + pymax(0.0, tech_budget[a].expect("active")))) - civ.population_size;
                pop_budget[a] = Some(pymin(pop_budget[a].expect("active"), ceiling));
                let value = next / (rate * (civ.population_size + pymax(0.0, pop_budget[a].expect("active")))) - civ.tech_level;
                shrink(tech_budget, a, value);
            }
        }
    }
}

/// Largest uncertainty (passive::projected_progress) the observer may compute during the jump:
/// from the snapshots it can still see, or from the target's state within the relative budgets.
fn projected_progress_bound(observer: &Civ, target: &Civ, config: &Config, now: f64) -> f64 {
    let rel = config.jump_max_relative_change;
    let delay = dist(&observer.position, &target.position) / C_PC_PER_YEAR;
    let mut low = target.tech_level * (1.0 - rel);
    let mut high = target.tech_level * (1.0 + rel);
    let mut rate = tech_rate(target, config) * pymath::pow(1.0 + rel, config.tech_population_exponent);
    for snapshot in target.states_since(now - delay) {
        low = pymin(low, snapshot.tech_level);
        high = pymax(high, snapshot.tech_level);
        rate = pymax(rate, snapshot.tech_rate);
    }
    max_progress(low, high, rate, delay, config)
}

/// Largest grow(x) - x for x in [low, high] (see fast_forward._max_progress).
fn max_progress(low: f64, high: f64, rate: f64, delay: f64, config: &Config) -> f64 {
    match config.tech_growth_cap() {
        None => grow(high, rate, None, delay) - high,
        Some(cap) => {
            let high = pymin(high, cap);
            let root = pymath::exp(-rate * delay).sqrt();
            let x = pymin(pymax(cap * root / (1.0 + root), low), high);
            grow(x, rate, Some(cap), delay) - x
        }
    }
}

/// Unseen pairs: limit the drift of the emitter's broadcast radius and of both fronts, and the
/// time until the observer's probe sphere reaches the target (see fast_forward._detection_limit).
fn detection_limit(
    world: &World,
    active: &[usize],
    config: &Config,
    now: f64,
    tech_budget: &mut [Option<f64>],
    front_budget: &mut [Option<f64>],
) -> f64 {
    let mut limit = f64::INFINITY;
    let mut is_active = vec![false; world.civs.len()];
    for &i in active {
        is_active[i] = true;
    }
    let mut widest_front = 0.0;
    // Largest signal radius reachable during the jump (tech budgets only shrink from here).
    let mut widest_signal = world.widest_broadcast;
    for &i in active {
        let c = &world.civs[i];
        widest_front = pymax(widest_front, front_end(c, front_budget[i]));
        if c.leak_radius > 0.0 || c.beacon_radius > 0.0 {
            let end_tech = c.tech_level + pymax(0.0, tech_budget[i].expect("active"));
            let factor = if c.beacon_radius > 0.0 { 1.0 } else { config.passive_leakage_factor };
            widest_signal = pymax(widest_signal, signal_radius(config, end_tech, factor));
        }
    }
    let window_start = config.present_date_years - config.humanity_listening_years;
    for &yi in active {
        let y = &world.civs[yi];
        if y.is_human && now < window_start {
            continue;
        }
        let (distances, neighbors) = world.neighbors_by_distance(yi);
        if !y.is_human {
            limit = pymin(limit, exposure_limit(world, y, config));
            let reach = widest_signal + front_end(y, front_budget[yi]) + widest_front;
            let n_signal = distances.partition_point(|&d| d <= reach);
            for (&d, &xi) in distances[..n_signal].iter().zip(&neighbors[..n_signal]) {
                let xi = xi as usize;
                let x = &world.civs[xi];
                if !is_active[xi] || x.tech_level <= 0.0 || seen_now(y, xi, now) {
                    continue;
                }
                signal_budget(x, xi, y, yi, d, x.leak_radius, config.passive_leakage_factor, config, tech_budget, front_budget);
                if x.beacon_radius > 0.0 && !y.exposures.contains_key(&xi) {
                    signal_budget(x, xi, y, yi, d, x.beacon_radius, 1.0, config, tech_budget, front_budget);
                }
            }
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
            // Probe speed and range grow with tech: bound them by the end-of-jump tech. The nearest
            // unseen target out of reach of the working probes cannot be reached during the jump.
            let budget = tech_budget[yi].expect("active");
            let end_tech = y.tech_level + pymax(0.0, budget);
            if d > front_end(y, front_budget[yi]) + probe_range(config, end_tech) {
                break;
            }
            let speed = pymax(y.probe_speed, probe_speed(config, end_tech));
            if speed > 0.0 {
                limit = pymin(limit, (d - y.probe_radius) / speed - config.dt);
            }
            break;
        }
    }
    limit
}

/// Share what is left of the gap (x's signal of this radius to y) between whatever can close it.
#[allow(clippy::too_many_arguments)]
fn signal_budget(
    x: &Civ,
    xi: usize,
    y: &Civ,
    yi: usize,
    d: f64,
    radius: f64,
    factor: f64,
    config: &Config,
    tech_budget: &mut [Option<f64>],
    front_budget: &mut [Option<f64>],
) {
    let movers: Vec<usize> = [xi, yi].into_iter().filter(|&m| front_budget[m].is_some()).collect();
    let n_moving = movers.len() + usize::from(radius > 0.0);
    if n_moving == 0 {
        return;
    }
    let share = (d - y.expansion_radius - x.expansion_radius - radius) / n_moving as f64;
    for m in movers {
        shrink(front_budget, m, share);
    }
    if radius > 0.0 {
        // Signal radii grow with tech (see compute_signal_radii).
        let critical_tech = tech_for_signal_radius(config, radius + share, factor);
        shrink(tech_budget, xi, critical_tech - x.tech_level);
    }
}

/// An exposed, not yet caught beacon is caught when its hazard reaches its threshold: stop before.
fn exposure_limit(world: &World, y: &Civ, config: &Config) -> f64 {
    let mut limit = f64::INFINITY;
    for (&xi, &(threshold, hazard)) in &y.exposures {
        if hazard >= threshold || !world.civs[xi].alive {
            continue;
        }
        let rate = beacon_hazard(world.civs[xi].nb_of_world, config);
        if rate > 0.0 {
            limit = pymin(limit, (threshold - hazard) / rate - config.dt);
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
        let gain = pymath::pow(1.0 + pymax(0.0, pop_budget) / civ.population_size, config.tech_population_exponent);
        tech_rate(civ, config) * gain
    } else {
        0.0
    };
    if r <= 0.0 || civ.tech_level >= config.tech_cap {
        return f64::INFINITY;
    }
    time_to_reach(civ.tech_level, civ.tech_level + tech_budget, r, config.tech_growth_cap())
}

/// An enclave stays blocked until the civ around it shrinks (attack) or dies (random event).
fn front_moves(civ: &Civ, config: &Config) -> bool {
    civ.colonization_aggressiveness > 0.0 && civ.tech_level > 0.0 && !civ.front_blocked
        && civ.tech_level >= colonization_tech(civ, config)
}

/// Worlds only matter through the population capacity, which a jump keeps at its start value:
/// the error on pop / capacity is kept within rel (see fast_forward._front_budget).
fn initial_front_budget(civ: &Civ, config: &Config, rel: f64) -> f64 {
    let density = world_density(civ, config);
    let capacity = population_capacity(civ, config);
    let Some(capacity) = capacity else { return f64::INFINITY };
    if density <= 0.0 || civ.population_size <= 0.0 || civ.free_fraction <= 0.0 {
        return f64::INFINITY;
    }
    let growth = rel * capacity / civ.population_size;
    // The territory grows by free_fraction of the shell swept by the front (see _advance_fronts).
    let radius = civ.expansion_radius;
    let extra = civ.nb_of_world * growth / (density * civ.free_fraction * FOUR_THIRDS_PI);
    pymath::pow(radius * radius * radius + extra, 1.0 / 3.0) - radius
}

fn front_end(civ: &Civ, budget: Option<f64>) -> f64 {
    match budget {
        None => civ.expansion_radius,
        Some(budget) => civ.expansion_radius + pymax(0.0, budget),
    }
}

/// A front must not reach the Sun during a jump (see check_silence).
fn colonization_budgets(world: &World, active: &[usize], front_budget: &mut [Option<f64>]) {
    let human = &world.civs[world.humanity];
    for &i in active {
        if i == world.humanity || front_budget[i].is_none() {
            continue;
        }
        let c = &world.civs[i];
        let gap = dist(&c.position, &human.position) - c.expansion_radius;
        if gap > 0.0 {
            shrink(front_budget, i, gap);
        }
    }
    // Nor two competitors come into contact (see advance_fronts): the moving fronts share the gap.
    let mut is_active = vec![false; world.civs.len()];
    for &i in active {
        is_active[i] = true;
    }
    let mut widest_front = 0.0;
    for &i in active {
        widest_front = pymax(widest_front, front_end(&world.civs[i], front_budget[i]));
    }
    for &xi in active {
        if front_budget[xi].is_none() {
            continue;
        }
        let x = &world.civs[xi];
        let (distances, neighbors) = world.neighbors_by_distance(xi);
        let reach = front_end(x, front_budget[xi]) + widest_front;
        for (&d, &yi) in distances.iter().zip(neighbors) {
            if d > reach {
                break;
            }
            let yi = yi as usize;
            let y = &world.civs[yi];
            if !is_active[yi] || y.biochem != x.biochem || x.contacts.contains(&yi) || yi == world.humanity {
                continue;
            }
            let gap = d - x.expansion_radius - y.expansion_radius;
            if gap <= 0.0 {
                continue;
            }
            let movers: Vec<usize> = [xi, yi].into_iter().filter(|&m| front_budget[m].is_some()).collect();
            let share = gap / movers.len() as f64;
            for m in movers {
                shrink(front_budget, m, share);
            }
        }
    }
}

fn time_to_spend_front_budget(civ: &Civ, config: &Config, front_budget: f64, tech_budget: f64) -> f64 {
    // Fastest front reachable during the jump (front speed grows with tech).
    let speed = front_speed_at(civ, config, civ.tech_level + pymax(0.0, tech_budget));
    if front_budget == f64::INFINITY {
        return f64::INFINITY;
    }
    front_budget / speed - config.dt
}
