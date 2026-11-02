//! Mirror of python/p0_passive_update.

use crate::config::{Config, SelfDestructionShape};
use crate::fast_forward::Jump;
use crate::geometry::{Position, dist};
use crate::pymath::{self, C_PC_PER_YEAR, pymax, pymin};
use crate::rng::{Rng, Streams};
use crate::state::{BeliefEntry, Channel, Civ, Snapshot, World};
use crate::world_gen::{new_civ, sample_lens_position};

/// dt is the time elapsed since the previous step; jump carries the events forced by the fast-forward.
pub fn passive_update(world: &mut World, config: &Config, now: f64, streams: &mut Streams, dt: f64, jump: Option<&Jump>) {
    let born = match jump {
        None => streams.birth.random() < config.civ_birth_rate * dt,
        Some(jump) => jump.birth,
    };
    if born {
        let position = sample_lens_position(config, &mut streams.birth);
        let id = format!("c_{}", world.civs.len());
        let civ = new_civ(id, position, config, &mut streams.birth, now);
        world.add_civ(civ);
    }

    let horizon = world.history_horizon(config);
    let human = world.humanity;
    let human_position = world.civs[human].position;
    for i in world.active(now) {
        let civ = &mut world.civs[i];
        // A civ born during this step only lives one regular step of it.
        let step = pymin(dt, now - civ.birth_year + config.dt);
        let exact = jump.is_some() && step > config.dt;
        let exact_tech = exact && !jump.is_some_and(|j| Jump::flag(&j.frozen_tech, i));
        let exact_pop = exact && !jump.is_some_and(|j| Jump::flag(&j.frozen_pop, i));
        let speed_before = civ.probe_speed;
        tech_growth(civ, config, if exact_tech { step } else { pymin(step, config.dt) }, exact_tech);
        population_growth(civ, config, if exact_pop { step } else { pymin(step, config.dt) }, exact_pop);
        civ.broadcast_radius = compute_broadcast_radius(civ, config);
        civ.probe_speed = config.probe_speed_per_tech * civ.tech_level;
        let speed = if exact { (speed_before + civ.probe_speed) / 2.0 } else { civ.probe_speed };
        advance_probes(civ, i == human, &human_position, config, now, step, speed);
        civ.record(now, horizon);
    }

    match jump {
        None => {
            for i in world.orphan_probes(now, config) {
                let civ = &mut world.civs[i];
                let speed = civ.probe_speed;
                advance_probes(civ, i == human, &human_position, config, now, dt, speed);
            }
        }
        Some(_) => {
            // Orphan probes expiring inside the jump still travel until their end of life.
            let start = now - dt;
            for i in world.orphan_probes(start, config) {
                let civ = &mut world.civs[i];
                let end = pymin(now, civ.probes_end_at(config));
                let speed = civ.probe_speed;
                advance_probes(civ, i == human, &human_position, config, end, end - start, speed);
            }
        }
    }

    detect(world, config, now);

    for i in world.active(now) {
        let destroyed = match jump {
            None => self_destruction(&world.civs[i], config, &mut streams.destruction, dt),
            Some(jump) => Jump::flag(&jump.extinctions, i),
        };
        let civ = &mut world.civs[i];
        if destroyed {
            civ.go_extinct(now, "self_destruction");
        } else if civ.tech_level <= 0.0 || civ.population_size <= 0.0 {
            civ.go_extinct(now, "collapse");
        }
    }

    roll_artefacts(world, config, &mut streams.artefact, now);
    check_silence(world, config, now);
}

pub fn final_silence_check(world: &mut World, config: &Config, streams: &mut Streams) {
    roll_artefacts(world, config, &mut streams.artefact, config.present_date_years);
    if received_signal_in_window(world, config) {
        world.reject("signal_in_window".into(), config.present_date_years);
    }
}

// _growth_law

/// Exact solution of dx/dt = r x (1 - x/cap) (logistic) or r x (cap is None) after time t.
pub fn grow(x: f64, r: f64, cap: Option<f64>, t: f64) -> f64 {
    if x <= 0.0 || r == 0.0 || t <= 0.0 {
        return x;
    }
    match cap {
        None => x * pymath::exp(pymin(r * t, 700.0)),
        Some(cap) => cap / (1.0 + (cap / x - 1.0) * pymath::exp(-r * t)),
    }
}

pub fn time_to_reach(x: f64, target: f64, r: f64, cap: Option<f64>) -> f64 {
    if target <= x {
        return 0.0;
    }
    if x <= 0.0 || r <= 0.0 {
        return f64::INFINITY;
    }
    match cap {
        None => pymath::log(target / x) / r,
        Some(cap) if target >= cap => f64::INFINITY,
        Some(cap) => pymath::log((cap / x - 1.0) / (cap / target - 1.0)) / r,
    }
}

// _tech_growth, _population_growth

pub fn tech_rate(civ: &Civ) -> f64 {
    civ.natural_tech_progress * (1.0 - civ.colonization_aggressiveness) * civ.population_size
}

fn tech_growth(civ: &mut Civ, config: &Config, dt: f64, exact: bool) {
    let r = tech_rate(civ);
    let t = civ.tech_level;
    civ.tech_level = if exact {
        grow(t, r, config.tech_growth_cap(), dt)
    } else if config.derived().tech_logistic {
        t + r * t * (1.0 - t / config.tech_cap) * dt
    } else {
        t + r * t * dt
    };
    civ.tech_level = pymin(config.tech_cap, pymax(0.0, civ.tech_level));
}

pub fn population_capacity(civ: &Civ, config: &Config) -> Option<f64> {
    if config.derived().population_logistic { Some(config.population_per_world * civ.nb_of_world) } else { None }
}

fn population_growth(civ: &mut Civ, config: &Config, dt: f64, exact: bool) {
    let r = civ.natural_population_growth;
    let capacity = population_capacity(civ, config);
    let p = civ.population_size;
    civ.population_size = if exact {
        grow(p, r, capacity, dt)
    } else if let Some(capacity) = capacity {
        p + r * p * (1.0 - p / capacity) * dt
    } else {
        p + r * p * dt
    };
    civ.population_size = match capacity {
        Some(capacity) => pymin(capacity, pymax(0.0, civ.population_size)),
        None => pymax(0.0, civ.population_size),
    };
}

fn compute_broadcast_radius(civ: &Civ, config: &Config) -> f64 {
    let active_radius = config.emit_radius_per_tech * civ.tech_level;
    if civ.strategy.broadcast { active_radius } else { active_radius * config.passive_leakage_factor }
}

fn advance_probes(civ: &mut Civ, is_human: bool, human_position: &Position, config: &Config, now: f64, dt: f64, speed: f64) {
    let before = civ.probe_radius;
    civ.probe_radius = pymin(config.max_probe_radius, before + speed * dt);
    if is_human || civ.probe_arrived_at_human.is_some() {
        return;
    }
    let d = dist(&civ.position, human_position);
    if civ.probe_radius >= d {
        // Interpolate the crossing inside the step so arrival time does not depend on dt.
        let frac = if civ.probe_radius > before { pymax(0.0, (d - before) / (civ.probe_radius - before)) } else { 0.0 };
        civ.probe_arrived_at_human = Some(now - dt + frac * dt);
    }
}

// _self_destruction

pub fn self_destruction_shape(tech_level: f64, config: &Config) -> f64 {
    match config.derived().shape {
        SelfDestructionShape::Constant => 1.0,
        SelfDestructionShape::Increasing => tech_level / config.tech_cap,
        SelfDestructionShape::DangerWindow => {
            let x = (tech_level - config.danger_window_center) / config.danger_window_width;
            pymath::exp(-x * x)
        }
    }
}

fn self_destruction(civ: &Civ, config: &Config, rng: &mut Rng, dt: f64) -> bool {
    let hazard = config.self_destruction_risk * self_destruction_shape(civ.tech_level, config);
    rng.random() < 1.0 - pymath::exp(-hazard * dt)
}

// _detect

fn detect(world: &mut World, config: &Config, now: f64) {
    world.note_detection_step(now);
    let visible = world.visible(now);
    let window_start = config.present_date_years - config.signal_window_years;
    for i in world.active(now) {
        if world.civs[i].is_human && now < window_start {
            continue;
        }
        let reach = pymax(config.max_broadcast_radius, world.civs[i].probe_radius);
        let pairs = world.neighbor_pairs_within(i, reach);
        for &(j, d) in pairs.iter() {
            let j = j as usize;
            if !visible[j] {
                continue;
            }
            let seen_at = now - d / C_PC_PER_YEAR;
            let Some(view) = world.civs[j].state_at(seen_at) else { continue };
            let by_signal = view.broadcast_radius >= d;
            let by_probe = probe_reached(&world.civs[i], seen_at, d);
            if !(by_signal || by_probe) {
                continue;
            }
            observe(world, i, j, &view, if by_signal { Channel::Signal } else { Channel::Probe }, now);
            if let Some(attacker) = view.attacked_by
                && let Some(&b) = world.civs[i].belief_of.get(&attacker)
            {
                let entry = &mut world.civs[i].belief[b];
                let trust = pymax(0.0, entry.trust - config.reputation_trust_drop);
                if trust != entry.trust {
                    entry.trust = trust;
                    world.note_trust(i, b);
                }
            }
        }
    }
}

/// The probe must have been on site at seen_at for its light-speed report to arrive now.
fn probe_reached(civ: &Civ, seen_at: f64, d: f64) -> bool {
    civ.state_at(seen_at).is_some_and(|own| own.probe_radius >= d)
}

fn observe(world: &mut World, i: usize, j: usize, view: &Snapshot, channel: Channel, now: f64) {
    let is_competitor = world.civs[i].biochem == world.civs[j].biochem;
    let civ = &mut world.civs[i];
    let (b, previous_seen) = match civ.belief_of.get(&j) {
        None => {
            let trust = if is_competitor {
                civ.strategy.trust_default_competitor
            } else {
                civ.strategy.trust_default_noncompetitor
            };
            let b = civ.belief.len();
            civ.belief.push(BeliefEntry {
                target: j,
                estimated_tech_level: view.tech_level,
                tech_level_uncertainty: 0.0,
                is_competitor,
                trust,
                channel,
                attacked_me: false,
                last_seen_at: now,
                signature: None,
            });
            civ.belief_of.insert(j, b);
            (b, None)
        }
        Some(&b) => {
            let entry = &mut civ.belief[b];
            let previous = entry.last_seen_at;
            entry.estimated_tech_level = view.tech_level;
            entry.channel = channel;
            entry.last_seen_at = now;
            (b, Some(previous))
        }
    };
    civ.recent.insert(b);
    world.note_seen(i, b, previous_seen);
}

// _check_silence

fn check_silence(world: &mut World, config: &Config, now: f64) {
    if now >= config.present_date_years {
        return;
    }
    let human = &world.civs[world.humanity];
    if human.attacked_by.is_some() {
        world.reject("attacked".into(), now);
    } else if let Some(first) = human.belief.first() {
        // Name the channel of the first contact.
        let reason = format!("contact_{}", first.channel.name());
        world.reject(reason, now);
    }
}

/// Exact, dt-independent test: did any light reaching humanity during the instrumental
/// window carry a detectable signal, even from a now-dead civ?
fn received_signal_in_window(world: &World, config: &Config) -> bool {
    let human = &world.civs[world.humanity];
    let present = config.present_date_years;
    world.civs.iter().enumerate().any(|(i, civ)| {
        if i == world.humanity {
            return false;
        }
        let d = dist(&civ.position, &human.position);
        if d > config.max_broadcast_radius {
            return false;
        }
        let delay = d / C_PC_PER_YEAR;
        was_detectable(civ, present - config.signal_window_years - delay, present - delay, d)
    })
}

fn was_detectable(civ: &Civ, start: f64, end: f64, d: f64) -> bool {
    let death = civ.extinct_at.unwrap_or(f64::INFINITY);
    let history = &civ.history;
    (0..history.len()).any(|k| {
        let snap = &history[k];
        let seg_end = if k + 1 < history.len() { history[k + 1].t } else { f64::INFINITY };
        snap.broadcast_radius >= d && pymax(start, snap.t) < pymin(pymin(end, seg_end), death)
    })
}

/// Contact (b): one discovery draw per civ whose probes sat near the Sun during the artefact window.
fn roll_artefacts(world: &mut World, config: &Config, rng: &mut Rng, until: f64) {
    let window_start = config.present_date_years - config.artefact_window_years;
    for i in 0..world.civs.len() {
        let civ = &world.civs[i];
        let Some(arrival) = civ.probe_arrived_at_human else { continue };
        if civ.artefact_rolled || world.rejected {
            continue;
        }
        if pymax(arrival, window_start) > pymin(civ.probes_end_at(config), until) {
            continue;
        }
        world.civs[i].artefact_rolled = true;
        if rng.random() < config.artefact_detection_probability {
            world.reject("artefact".into(), until);
        }
    }
}
