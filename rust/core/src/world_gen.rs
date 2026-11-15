//! Mirror of python/generate_world.

use std::f64::consts::PI;

use crate::config::{ARCHETYPES, Config};
use crate::geometry::Position;
use crate::pymath::{self, pymax, pymin};
use crate::rng::{Rng, Streams};
use crate::state::{Civ, Strategy, World};

pub fn generate_world(config: &Config, streams: &mut Streams) -> World {
    let mut civs = seed_life_in_bubbles(config, &mut streams.world);
    civs.push(make_humanity(config, &mut streams.humanity));
    World::new(civs, config)
}

fn seed_life_in_bubbles(config: &Config, rng: &mut Rng) -> Vec<Civ> {
    let mut civs = Vec::new();
    for _ in 0..rng.poisson(config.expected_bubbles) {
        let center = sample_lens_position(config, rng);
        for _ in 0..rng.poisson(config.civs_per_bubble) {
            let offset = sample_ball(config.panspermia_range_pc, rng);
            let position = [center[0] + offset[0], center[1] + offset[1], center[2] + offset[2]];
            let id = format!("c_{}", civs.len());
            let birth = birth_date(config, rng);
            civs.push(new_civ(id, position, config, rng, birth));
        }
    }
    civs
}

/// The sterilizing event resynchronizes life; intelligence then takes a variable time.
fn birth_date(config: &Config, rng: &mut Rng) -> f64 {
    let spread = config.birth_spread_fraction * config.start_lookback_years;
    if spread <= 0.0 {
        return config.start_date_years();
    }
    config.start_date_years() + rng.uniform(0.0, spread)
}

fn make_humanity(config: &Config, rng: &mut Rng) -> Civ {
    // Observed, not drawn: position near the centre of the region (the Sun), no colonization beyond
    // Earth, and a tech growth rate taking it from initial_tech_level to humanity_present_tech.
    let position = [0.0, 0.0, config.sun_height_pc];
    let mut humanity = new_civ("human".into(), position, config, rng, config.humanity_birth_date_years);
    humanity.is_human = true;
    humanity.strategy.attack_when_trust_inferior_than = 0.0;
    humanity.strategy.broadcast = false;
    humanity.strategy.colonization_aggressiveness = 0.0;
    humanity.colonization_aggressiveness = 0.0;
    humanity.natural_tech_progress = config.derived().humanity_tech_rate;
    humanity
}

pub fn sample_lens_position(config: &Config, rng: &mut Rng) -> Position {
    let r = config.region_radius_pc * rng.random().sqrt();
    let theta = 2.0 * PI * rng.random();
    // `rng.exponential(...) * rng.choice([-1, 1])`: the exponential is drawn first.
    let height = rng.exponential(config.scale_height_pc);
    let sign = if rng.randbelow(2) == 0 { -1.0 } else { 1.0 };
    let z = height * sign;
    [r * pymath::cos(theta), r * pymath::sin(theta), z]
}

fn sample_ball(radius: f64, rng: &mut Rng) -> Position {
    loop {
        let x = rng.uniform(-1.0, 1.0);
        let y = rng.uniform(-1.0, 1.0);
        let z = rng.uniform(-1.0, 1.0);
        if x * x + y * y + z * z <= 1.0 {
            return [x * radius, y * radius, z * radius];
        }
    }
}

fn sample_strategy(config: &Config, rng: &mut Rng) -> Strategy {
    let archetype = rng.weighted_index(&config.strategy_mix());
    let pinned = &ARCHETYPES[archetype];
    let mut broadcast = rng.random() < config.broadcast_probability;
    if let Some(b) = pinned.broadcast {
        broadcast = b;
    }
    let mut values = [0.0; 8];
    for ((value, (low, high)), pin) in values.iter_mut().zip(config.strategy_ranges()).zip(pinned.traits) {
        *value = match pin {
            Some(v) => pymin(high, pymax(low, v + config.strategy_noise * (high - low) * rng.uniform(-1.0, 1.0))),
            None => rng.uniform(low, high),
        };
    }
    Strategy::from_values(broadcast, values, archetype)
}

pub fn new_civ(id: String, position: Position, config: &Config, rng: &mut Rng, birth_year: f64) -> Civ {
    let strategy = sample_strategy(config, rng);
    let biochem = rng.weighted_index(&config.world_type_fractions);
    let natural_tech_progress = config.natural_tech_progress_mean * spread(config.natural_tech_progress_spread, rng);
    let natural_population_growth = config.natural_population_growth_mean * spread(config.natural_population_growth_spread, rng);
    Civ {
        id,
        position,
        birth_year,
        alive: true,
        biochem,
        tech_level: config.initial_tech_level,
        population_size: config.initial_population,
        nb_of_world: 1.0,
        natural_tech_progress,
        natural_population_growth,
        colonization_aggressiveness: strategy.colonization_aggressiveness,
        strategy,
        leak_radius: 0.0,
        beacon_radius: 0.0,
        probe_speed: 0.0,
        probe_radius: 0.0,
        expansion_radius: 0.0,
        front_blocked: false,
        free_fraction: 1.0,
        contacts: Default::default(),
        belief: Vec::new(),
        belief_of: Default::default(),
        recent: Default::default(),
        attacked_by: None,
        attacked_at: f64::NEG_INFINITY,
        attack_attributed: true,
        attributions: Default::default(),
        exposures: Default::default(),
        is_human: false,
        extinct_at: None,
        extinction_cause: None,
        probe_arrived_at_human: None,
        artefact_rolled: false,
        history: Default::default(),
    }
}

/// _spread: a civ's own rate is the mean times U(1 - spread, 1 + spread).
fn spread(spread: f64, rng: &mut Rng) -> f64 {
    rng.uniform(1.0 - spread, 1.0 + spread)
}
