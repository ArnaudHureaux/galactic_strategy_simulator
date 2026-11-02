//! Mirror of python/generate_world.

use std::f64::consts::PI;

use crate::config::Config;
use crate::geometry::Position;
use crate::pymath;
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
            civs.push(new_civ(id, position, config, rng, config.last_grb_date_years));
        }
    }
    civs
}

fn make_humanity(config: &Config, rng: &mut Rng) -> Civ {
    let position = sample_lens_position(config, rng);
    let mut humanity = new_civ("human".into(), position, config, rng, config.humanity_birth_date_years);
    humanity.is_human = true;
    humanity.strategy.attack_when_trust_inferior_than = 0.0;
    humanity.strategy.broadcast = false;
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
    let broadcast = rng.random() < config.broadcast_probability;
    let mut values = [0.0; 8];
    for (value, (low, high)) in values.iter_mut().zip(config.strategy_ranges()) {
        *value = rng.uniform(low, high);
    }
    Strategy::from_values(broadcast, values)
}

pub fn new_civ(id: String, position: Position, config: &Config, rng: &mut Rng, birth_year: f64) -> Civ {
    let strategy = sample_strategy(config, rng);
    let biochem = rng.weighted_index(&config.world_type_fractions);
    let natural_tech_progress = config.natural_tech_progress_mean * rng.uniform(0.5, 1.5);
    let natural_population_growth = config.natural_population_growth_mean * rng.uniform(0.5, 1.5);
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
        broadcast_radius: 0.0,
        probe_speed: 0.0,
        probe_radius: 0.0,
        expansion_radius: 0.0,
        belief: Vec::new(),
        belief_of: Default::default(),
        recent: Default::default(),
        attacked_by: None,
        is_human: false,
        extinct_at: None,
        extinction_cause: None,
        probe_arrived_at_human: None,
        artefact_rolled: false,
        history: Default::default(),
    }
}
