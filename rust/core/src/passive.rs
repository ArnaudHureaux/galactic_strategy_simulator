//! Mirror of python/p0_passive_update.

use crate::config::{Config, SelfDestructionShape};
use crate::fast_forward::Jump;
use crate::geometry::{Position, dist};
use crate::pymath::{self, C_PC_PER_YEAR, M_PER_PC, pymax, pymin};
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
    let active = world.active(now);
    let mut advances = Vec::with_capacity(active.len());
    for &i in &active {
        let civ = &mut world.civs[i];
        // A civ born during this step only lives one regular step of it.
        let step = pymin(dt, now - civ.birth_year + config.dt);
        let exact = jump.is_some() && step > config.dt;
        let exact_tech = exact && !jump.is_some_and(|j| Jump::flag(&j.frozen_tech, i));
        let exact_pop = exact && !jump.is_some_and(|j| Jump::flag(&j.frozen_pop, i));
        let speed_before = civ.probe_speed;
        let front_before = front_speed(civ, config);
        if civ.is_human {
            human_tech(civ, config, now);
        } else {
            tech_growth(civ, config, if exact_tech { step } else { pymin(step, config.dt) });
        }
        population_growth(civ, config, if exact_pop { step } else { pymin(step, config.dt) }, exact_pop);
        let (leak, beacon) = compute_signal_radii(civ, config, now);
        civ.leak_radius = leak;
        civ.beacon_radius = beacon;
        world.widest_broadcast = pymax(pymax(world.widest_broadcast, leak), beacon);
        let civ = &mut world.civs[i];
        civ.probe_speed = probe_speed(config, civ.tech_level);
        let speed = if exact { (speed_before + civ.probe_speed) / 2.0 } else { civ.probe_speed };
        advance_probes(civ, i == human, &human_position, config, now, step, speed);
        // The front of an attacked civ (shrunk by every attack) replays one regular step, like its population.
        let front_after = front_speed(civ, config);
        advances.push(if exact_pop { (front_before + front_after) / 2.0 * step } else { front_after * pymin(step, config.dt) });
    }
    advance_fronts(world, config, &active, &advances);
    for &i in &active {
        let rate = tech_rate(&world.civs[i], config);
        world.civs[i].record(now, horizon, rate);
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

    detect(world, config, now, dt, &mut streams.detection);

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
    if !world.rejected && received_signal_in_window(world, config, &mut streams.detection) {
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

pub fn tech_rate(civ: &Civ, config: &Config) -> f64 {
    if civ.is_human {
        return civ.natural_tech_progress;
    }
    civ.natural_tech_progress * (1.0 - civ.colonization_aggressiveness) * pymath::pow(civ.population_size, config.tech_population_exponent)
}

/// Exact solution of the growth law over the step, the rate held constant: the fastest explored
/// rates (~1e-5 per year, more with shares and population) are too fast for an Euler step.
fn tech_growth(civ: &mut Civ, config: &Config, dt: f64) {
    civ.tech_level = grow(civ.tech_level, tech_rate(civ, config), config.tech_growth_cap(), dt);
    civ.tech_level = pymin(config.tech_cap, pymax(0.0, civ.tech_level));
}

/// Humanity follows its observed trajectory exactly: its rate (up to ~5e-4 per year) is far
/// too fast for an Euler step, and events cannot perturb it (an attack or a share rejects the run).
fn human_tech(civ: &mut Civ, config: &Config, now: f64) {
    let tech = grow(config.initial_tech_level, civ.natural_tech_progress, config.tech_growth_cap(), now - civ.birth_year);
    civ.tech_level = pymin(config.tech_cap, tech);
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

/// (leak radius, beacon radius) in pc (see _compute_broadcast_radius._compute_signal_radii).
/// Humanity's leakage is observed; the other civs' is explored.
pub fn leak_factor(civ: &Civ, config: &Config) -> f64 {
    if civ.is_human { config.humanity_leakage_factor } else { config.passive_leakage_factor }
}

fn compute_signal_radii(civ: &Civ, config: &Config, now: f64) -> (f64, f64) {
    // Humanity's technosignatures only exist since it leaks radio signals.
    if civ.is_human && now < config.present_date_years - config.humanity_leak_years {
        return (0.0, 0.0);
    }
    let leak = signal_radius(config, civ.tech_level, leak_factor(civ, config));
    let beacon = if civ.strategy.broadcast { signal_radius(config, civ.tech_level, 1.0) } else { 0.0 };
    (leak, beacon)
}

/// Effect of a tech level, calibrated by two anchors (see _anchored.py): human_value at
/// humanity's present tech and cap_value at tech_cap; each level multiplies it by the same factor.
pub fn anchored(tech: f64, human_value: f64, cap_value: f64, config: &Config) -> f64 {
    let present = config.derived().humanity_present_tech;
    let x = (pymin(tech, config.tech_cap) - present) / (config.tech_cap - present);
    human_value * pymath::pow(cap_value / human_value, x)
}

/// Inverse of anchored: the tech level at which the effect reaches value (inf if never).
pub fn anchored_tech(value: f64, human_value: f64, cap_value: f64, config: &Config) -> f64 {
    if value >= cap_value {
        return f64::INFINITY;
    }
    let present = config.derived().humanity_present_tech;
    let x = pymath::log(value / human_value) / pymath::log(cap_value / human_value);
    present + x * (config.tech_cap - present)
}

/// Distance (pc) at which a signal of factor * EIRP(tech) stays above the observers' sensitivity.
pub fn signal_radius(config: &Config, tech: f64, factor: f64) -> f64 {
    if tech <= 0.0 {
        return 0.0;
    }
    let eirp = anchored(tech, config.eirp_human_w, config.eirp_cap_w, config) * factor;
    (eirp / (4.0 * std::f64::consts::PI * config.seti_flux_threshold_w_m2)).sqrt() / M_PER_PC
}

/// Tech at which signal_radius reaches radius (inf if never).
pub fn tech_for_signal_radius(config: &Config, radius: f64, factor: f64) -> f64 {
    let meters = radius * M_PER_PC;
    let eirp = 4.0 * std::f64::consts::PI * config.seti_flux_threshold_w_m2 * meters * meters / factor;
    anchored_tech(eirp, config.eirp_human_w, config.eirp_cap_w, config)
}

/// How long a probe launched at this tech keeps working (Voyager 1: about 50 years).
pub fn probe_function_years(config: &Config, tech: f64) -> f64 {
    anchored(tech, config.probe_function_human_years, config.probe_function_cap_years, config)
}

/// How long a probe launched at this tech persists as an artefact (at least while it works).
pub fn probe_persistence_years(config: &Config, tech: f64) -> f64 {
    let persistence = anchored(tech, config.probe_persistence_human_years, config.probe_persistence_cap_years, config);
    pymax(persistence, probe_function_years(config, tech))
}

/// Distance (pc) a working probe can cover from where it is launched: speed * functioning time.
pub fn probe_range(config: &Config, tech: f64) -> f64 {
    if tech <= 0.0 {
        return 0.0;
    }
    probe_speed(config, tech) * probe_function_years(config, tech)
}

/// Probe speed (pc/year), anchored on Voyager 1 for humanity.
pub fn probe_speed(config: &Config, tech: f64) -> f64 {
    if tech <= 0.0 {
        return 0.0;
    }
    // Anchored law on gamma - 1, speed from special relativity (see _compute_probe_speed._probe_speed).
    let energy = anchored(tech, kinetic(config.probe_speed_human_c), kinetic(config.probe_speed_cap_c), config);
    beta(energy) * C_PC_PER_YEAR
}

/// gamma - 1 for a speed beta (fraction of c), without cancellation at low speed.
fn kinetic(beta: f64) -> f64 {
    let s = (1.0 - beta * beta).sqrt();
    beta * beta / (s * (1.0 + s))
}

/// Speed (fraction of c) for a kinetic energy gamma - 1.
fn beta(kinetic: f64) -> f64 {
    (kinetic * (kinetic + 2.0)).sqrt() / (1.0 + kinetic)
}

// _advance_fronts

pub const FOUR_THIRDS_PI: f64 = 4.0 / 3.0 * std::f64::consts::PI;

pub fn front_speed(civ: &Civ, config: &Config) -> f64 {
    front_speed_at(civ, config, civ.tech_level)
}

/// Mean distance to the nearest point of a Poisson process of unit density.
const NEAREST_NEIGHBOUR: f64 = 0.5539602783650904;

/// Settlement front speed (pc/year), see _advance_fronts._front_speed_at.
pub fn front_speed_at(civ: &Civ, config: &Config, tech: f64) -> f64 {
    // A civ only colonizes once its probe range covers a hop (see _advance_fronts._front_speed_at).
    let speed = probe_speed(config, tech);
    let density = world_density(civ, config);
    if speed <= 0.0 || density <= 0.0 || civ.colonization_aggressiveness <= 0.0 || probe_range(config, tech) < hop(density) {
        return 0.0;
    }
    let h = hop(density);
    civ.colonization_aggressiveness * h / (h / speed + config.colonization_launch_period_years)
}

/// Mean distance to the nearest habitable world of the civ's type.
fn hop(density: f64) -> f64 {
    NEAREST_NEIGHBOUR * pymath::pow(density, -1.0 / 3.0)
}

/// Tech from which the probe range covers a hop (see _advance_fronts._colonization_tech).
pub fn colonization_tech(civ: &Civ, config: &Config) -> f64 {
    let density = world_density(civ, config);
    let h = if density > 0.0 { hop(density) } else { f64::INFINITY };
    if probe_range(config, config.tech_cap) < h {
        return f64::INFINITY;
    }
    let (mut low, mut high) = (0.0, config.tech_cap);
    for _ in 0..64 {
        let mid = (low + high) / 2.0;
        if probe_range(config, mid) < h {
            low = mid;
        } else {
            high = mid;
        }
    }
    high
}

/// Mid-plane habitable worlds per pc^3 of the civ's own biochem type (see _advance_fronts).
pub fn midplane_density(civ: &Civ, config: &Config) -> f64 {
    config.habitable_world_density * config.world_type_fractions[civ.biochem]
        * pymath::exp(config.sun_height_pc / config.scale_height_pc)
}

/// Habitable worlds per pc^3 of the civ's own biochem type around its home (disk profile).
pub fn world_density(civ: &Civ, config: &Config) -> f64 {
    midplane_density(civ, config) * pymath::exp(-civ.position[2].abs() / config.scale_height_pc)
}

/// Habitable worlds of the civ's type within radius of its home (see _advance_fronts._sphere_worlds).
fn sphere_worlds(civ: &Civ, radius: f64, config: &Config) -> f64 {
    let h = config.scale_height_pc;
    let volume = FOUR_THIRDS_PI * radius * radius * radius;
    let lift = pymath::exp(-pymax(0.0, civ.position[2].abs() - radius) / h);
    midplane_density(civ, config) * volume * lift / (1.0 + 2.0 * radius / (3.0 * h))
}

fn shell_worlds(civ: &Civ, radius: f64, new_radius: f64, config: &Config) -> f64 {
    sphere_worlds(civ, new_radius, config) - sphere_worlds(civ, radius, config)
}

/// Share of the sky that a sphere of radius other_radius at distance d hides from the observer.
pub fn cap_fraction(other_radius: f64, d: f64) -> f64 {
    let s = pymin(1.0, other_radius / d);
    let s2 = s * s;
    s2 / (2.0 * (1.0 + (1.0 - s2).sqrt()))
}

/// An attack shrinks the territory homothetically: kept is the share of the radius left.
/// An attack shrinks the territory homothetically: kept is the share of the colonized worlds
/// left (like the population), hence of the volume.
pub fn shrink_worlds(civ: &mut Civ, kept: f64) {
    civ.expansion_radius *= pymath::pow(kept, 1.0 / 3.0);
    civ.nb_of_world = 1.0 + (civ.nb_of_world - 1.0) * kept;
}

/// Whether the territory of civ covers point: within its front's reach, and not in the shadow
/// of an active competitor in contact (see _advance_fronts._holds).
pub fn holds(world: &World, i: usize, point: &Position, now: f64) -> bool {
    let civ = &world.civs[i];
    let d_point = dist(&civ.position, point);
    if civ.expansion_radius < d_point {
        return false;
    }
    for &j in &civ.contacts {
        let other = &world.civs[j];
        if !other.alive || now < other.birth_year {
            continue;
        }
        let d = dist(&civ.position, &other.position);
        let s = pymin(1.0, other.expansion_radius / d);
        let mut dot = 0.0;
        for k in 0..3 {
            dot += (other.position[k] - civ.position[k]) * (point[k] - civ.position[k]);
        }
        if d_point > 0.0 && dot > d * d_point * (1.0 - s * s).sqrt() {
            return false;
        }
    }
    true
}

/// Grows the territory of each active civ by its proposed advance (see _advance_fronts.py):
/// competitors in contact hide caps of the sky from each other; enclaves cannot grow.
fn advance_fronts(world: &mut World, config: &Config, active: &[usize], advances: &[f64]) {
    let mut new_radius: Vec<Option<f64>> = vec![None; world.civs.len()];
    let mut reach = 0.0;
    for (&i, &advance) in active.iter().zip(advances) {
        let radius = world.civs[i].expansion_radius + advance;
        new_radius[i] = Some(radius);
        reach = pymax(reach, radius);
    }
    let mut fractions = Vec::with_capacity(active.len());
    for (&i, &advance) in active.iter().zip(advances) {
        let mut free = 1.0;
        if advance > 0.0 {
            let radius = new_radius[i].unwrap();
            let limit = radius + reach;
            let mut new_contacts = Vec::new();
            {
                let civ = &world.civs[i];
                let (distances, neighbors) = world.neighbors_by_distance(i);
                for (&d, &j) in distances.iter().zip(neighbors) {
                    if d > limit {
                        break;
                    }
                    let j = j as usize;
                    let other = &world.civs[j];
                    let Some(other_radius) = new_radius[j] else { continue };
                    if other.biochem != civ.biochem {
                        continue;
                    }
                    if !civ.contacts.contains(&j) {
                        if d <= other.expansion_radius {
                            free = 0.0;
                            break;
                        }
                        if d <= civ.expansion_radius || d > radius + other_radius {
                            continue;
                        }
                        new_contacts.push(j);
                    }
                    free *= 1.0 - cap_fraction(other_radius, d);
                }
            }
            // Contact is symmetric, so recording it now does not depend on the order.
            for j in new_contacts {
                world.civs[i].contacts.insert(j);
                world.civs[j].contacts.insert(i);
            }
        }
        fractions.push(free);
    }
    for ((&i, &advance), &free) in active.iter().zip(advances).zip(&fractions) {
        let civ = &mut world.civs[i];
        civ.front_blocked = advance > 0.0 && free == 0.0;
        civ.free_fraction = free;
        if advance > 0.0 && free > 0.0 {
            let radius = new_radius[i].unwrap();
            let shell = shell_worlds(civ, civ.expansion_radius, radius, config);
            civ.nb_of_world += free * shell;
            civ.expansion_radius = radius;
        }
    }
}

fn advance_probes(civ: &mut Civ, is_human: bool, human_position: &Position, config: &Config, now: f64, dt: f64, speed: f64) {
    // Working probes are launched from the territory and work for a limited time (see _advance_probes).
    let before = civ.probe_radius;
    let reach = civ.expansion_radius + probe_range(config, civ.tech_level);
    civ.probe_radius = pymin(pymin(config.max_probe_radius, before + speed * dt), reach);
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

/// dt: time since the previous detection step, over which beacon exposures accumulate.
fn detect(world: &mut World, config: &Config, now: f64, dt: f64, rng: &mut Rng) {
    world.note_detection_step(now);
    let visible = world.visible(now);
    let mut widest_front = 0.0;
    for (j, civ) in world.civs.iter().enumerate() {
        if visible[j] {
            widest_front = pymax(widest_front, civ.expansion_radius);
        }
    }
    let window_start = config.present_date_years - config.humanity_listening_years;
    for i in world.active(now) {
        // Humanity only observes (through its own probes) since it searches the sky.
        if world.civs[i].is_human && now < window_start {
            continue;
        }
        let own_front = world.civs[i].expansion_radius;
        let reach = pymax(world.widest_broadcast + own_front + widest_front, world.civs[i].probe_radius);
        let pairs = world.neighbor_pairs_within(i, reach);
        for &(j, d) in pairs.iter() {
            let j = j as usize;
            if !visible[j] {
                continue;
            }
            // Light delay over the distance between the two homes (an upper bound for sphere edges).
            let seen_at = now - d / C_PC_PER_YEAR;
            let Some(view) = world.civs[j].state_at(seen_at) else { continue };
            // Signals carry from sphere edge to sphere edge. Humanity's signal detection is the
            // survey test of check_silence: here it only sees through its own probes.
            let gap = d - world.civs[i].expansion_radius - view.expansion_radius;
            // Probes see the target on reaching its territory (any of its systems).
            let by_probe = probe_reached(&world.civs[i], seen_at, d - view.expansion_radius);
            let mut by_signal = false;
            if !world.civs[i].is_human {
                by_signal = view.leak_radius >= gap;
                if !(by_signal || by_probe) && view.beacon_radius >= gap {
                    by_signal = beacon_caught(&mut world.civs[i], j, &view, config, dt, rng);
                }
            }
            if !(by_signal || by_probe) {
                continue;
            }
            let uncertainty = projected_progress(view.tech_level, view.tech_rate, d / C_PC_PER_YEAR, config);
            observe(world, i, j, &view, uncertainty, if by_signal { Channel::Signal } else { Channel::Probe }, now);
            // A witness of an ongoing war (the victim was hit during the step of the view) loses
            // trust in the attacker at reputation_trust_drop per interaction period.
            if let Some(attacker) = view.attacked_by
                && view.attack_attributed
                && view.attacked_at > view.t - config.dt
                && let Some(&b) = world.civs[i].belief_of.get(&attacker)
            {
                let entry = &mut world.civs[i].belief[b];
                let trust = pymax(0.0, entry.trust - config.derived().reputation_drop_additive);
                if trust != entry.trust {
                    entry.trust = trust;
                    world.note_trust(i, b);
                }
            }
        }
    }
}

/// Within a beacon sphere, detection is a coincidence: threshold Exp(1) drawn once per pair,
/// hazard accumulated while exposed (see _detect._beacon_caught).
fn beacon_caught(civ: &mut Civ, j: usize, view: &Snapshot, config: &Config, dt: f64, rng: &mut Rng) -> bool {
    let exposure = civ.exposures.entry(j).or_insert_with(|| (-pymath::log(1.0 - rng.random()), 0.0));
    if exposure.1 < exposure.0 {
        exposure.1 += beacon_hazard(view.nb_of_world, config) * dt;
    }
    exposure.1 >= exposure.0
}

/// Detection rate (per year) of a beacon covering nb_of_world systems.
pub fn beacon_hazard(nb_of_world: f64, config: &Config) -> f64 {
    let q = config.listen_coverage * config.beacon_duty;
    if q >= 1.0 {
        return f64::INFINITY;
    }
    -nb_of_world * pymath::log1p(-q) / config.interaction_period_years
}

/// The probe must have been on site at seen_at for its light-speed report to arrive now.
fn probe_reached(civ: &Civ, seen_at: f64, d: f64) -> bool {
    civ.state_at(seen_at).is_some_and(|own| own.probe_radius >= d)
}

/// Technological explosion: the tech a target may have gained while its light travelled to the
/// observer, at the growth rate seen with it. Cautious civs discount their advantage by it.
pub fn projected_progress(tech_level: f64, tech_rate: f64, delay: f64, config: &Config) -> f64 {
    grow(tech_level, tech_rate, config.tech_growth_cap(), delay) - tech_level
}

fn observe(world: &mut World, i: usize, j: usize, view: &Snapshot, uncertainty: f64, channel: Channel, now: f64) {
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
                tech_level_uncertainty: uncertainty,
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
            entry.tech_level_uncertainty = uncertainty;
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
    } else if now >= config.present_date_years - config.artefact_window_years && colonized(world, now) {
        world.reject("colonized".into(), now);
    } else if let Some(first) = world.civs[world.humanity].belief.first() {
        // Name the channel of the first contact.
        let reason = format!("contact_{}", first.channel.name());
        world.reject(reason, now);
    }
}

/// Hart's argument: a colonization front holding the Sun since the Solar System exists would be seen.
fn colonized(world: &World, now: f64) -> bool {
    let human = &world.civs[world.humanity];
    world.active(now).into_iter().any(|i| i != world.humanity && holds(world, i, &human.position, now))
}

/// Exact, dt-independent survey test (see _check_silence._received_signal_in_window): light
/// reaching humanity while it listens, above the survey sensitivity, caught with the survey
/// coverage c(d) (leak) or c(d) * beacon_duty (beacon) per system, one draw per exposed civ.
fn received_signal_in_window(world: &World, config: &Config, rng: &mut Rng) -> bool {
    let human = &world.civs[world.humanity];
    let present = config.present_date_years;
    for (i, civ) in world.civs.iter().enumerate() {
        if i == world.humanity {
            continue;
        }
        let d = dist(&civ.position, &human.position);
        let delay = d / C_PC_PER_YEAR;
        let (leak_n, beacon_n, edge) =
            exposure(civ, present - config.humanity_listening_years - delay, present - delay, d - human.expansion_radius);
        if leak_n == 0.0 && beacon_n == 0.0 {
            continue;
        }
        let c = seti_coverage(edge, config);
        let mut miss = 1.0;
        if leak_n > 0.0 {
            miss *= miss_probability(c, leak_n);
        }
        if beacon_n > 0.0 {
            miss *= miss_probability(c * config.beacon_duty, beacon_n);
        }
        if miss <= 0.0 || (miss < 1.0 && rng.random() >= miss) {
            return true;
        }
    }
    false
}

/// Probability that none of n systems is caught, each with probability q.
fn miss_probability(q: f64, n: f64) -> f64 {
    if q >= 1.0 {
        return 0.0;
    }
    pymath::exp(n * pymath::log1p(-q))
}

/// Share of the stars at distance d (pc) that humanity's surveys observed.
fn seti_coverage(d: f64, config: &Config) -> f64 {
    if d <= config.seti_complete_radius_pc {
        1.0
    } else if d <= 50.0 {
        config.seti_coverage_50pc
    } else {
        config.seti_coverage_beyond
    }
}

/// (systems seen through the leak, through the beacon, distance of the nearest system) over the
/// light emitted between start and end that reaches the observer at distance d.
fn exposure(civ: &Civ, start: f64, end: f64, d: f64) -> (f64, f64, f64) {
    let death = civ.extinct_at.unwrap_or(f64::INFINITY);
    let history = &civ.history;
    let mut leak_n = 0.0;
    let mut beacon_n = 0.0;
    let mut edge = d;
    for k in 0..history.len() {
        let snap = &history[k];
        let seg_end = if k + 1 < history.len() { history[k + 1].t } else { f64::INFINITY };
        if pymax(start, snap.t) >= pymin(pymin(end, seg_end), death) {
            continue;
        }
        let gap = d - snap.expansion_radius;
        if snap.beacon_radius >= gap {
            beacon_n = pymax(beacon_n, snap.nb_of_world);
            edge = pymin(edge, pymax(0.0, gap));
        }
        if snap.leak_radius >= gap {
            leak_n = pymax(leak_n, snap.nb_of_world);
            edge = pymin(edge, pymax(0.0, gap));
        }
    }
    (leak_n, beacon_n, edge)
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
        if pymax(arrival, window_start) > pymin(civ.artefacts_end_at(config), until) {
            continue;
        }
        world.civs[i].artefact_rolled = true;
        // The least advanced (least discreet) probes present during the window set the odds.
        let stealth = config.artefact_stealth_per_tech * pymax(0.0, owner_tech(&world.civs[i]) - config.derived().humanity_present_tech);
        if rng.random() < config.artefact_detection_probability * pymath::exp(-stealth) {
            world.reject("artefact".into(), until);
        }
    }
}

/// A dead civ is never updated again: its last snapshot holds its tech at death.
fn owner_tech(civ: &Civ) -> f64 {
    match (civ.extinct_at, civ.history.back()) {
        (Some(_), Some(last)) => last.tech_level,
        _ => civ.tech_level,
    }
}
