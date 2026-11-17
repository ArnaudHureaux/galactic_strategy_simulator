//! Mirror of python/generate_world.

use std::f64::consts::PI;

use crate::config::{ARCHETYPES, Config};
use crate::geometry::Position;
use crate::pymath::{self, pymax, pymin};
use crate::rng::{Rng, Streams, substream};
use crate::state::{Civ, Strategy, World};

pub fn generate_world(config: &Config, streams: &mut Streams) -> World {
    // Initial civs, then every later birth (taking part once their birth_year comes), humanity last.
    let mut civs = seed_life_in_bubbles(config, streams);
    civs.extend(draw_births(config, streams));
    civs.push(make_humanity(config, &mut streams.humanity));
    World::new(civs, config)
}

/// The annulus is drawn on a proposal disc reaching GHZ_CUTOFF widths beyond the Sun's radius.
const GHZ_CUTOFF: f64 = 6.0;

fn galaxy_radius(config: &Config) -> f64 {
    config.galactic_radius_sun_pc + GHZ_CUTOFF * config.ghz_width_pc
}

/// _candidate_mean: expected candidates on the proposal disc for a density per kpc^2 at the Sun's radius.
fn candidate_mean(density_kpc2: f64, config: &Config) -> f64 {
    let radius_kpc = galaxy_radius(config) / 1000.0;
    density_kpc2 * PI * radius_kpc * radius_kpc
}

/// _poisson_count: Poisson draw counted as unit-rate arrivals (exact for any mean).
fn poisson_count(mean: f64, rng: &mut Rng) -> u64 {
    if mean <= 0.0 {
        return 0;
    }
    let mut n = 0;
    let mut t = rng.exponential(1.0);
    while t <= mean {
        n += 1;
        t += rng.exponential(1.0);
    }
    n
}

/// _sample_galactic_position: uniform on the proposal disc, kept with probability
/// exp(-(r - R_sun)^2 / (2 w^2)) (Gaussian annulus); position in the Sun's frame.
fn sample_galactic_position(config: &Config, rng: &mut Rng) -> (Position, bool) {
    let r = galaxy_radius(config) * rng.random().sqrt();
    let theta = 2.0 * PI * rng.random();
    let u = (r - config.galactic_radius_sun_pc) / config.ghz_width_pc;
    let kept = rng.random() < pymath::exp(-0.5 * u * u);
    // `rng.exponential(...) * rng.choice([-1, 1])`: the exponential is drawn first.
    let height = rng.exponential(config.scale_height_pc);
    let sign = if rng.randbelow(2) == 0 { -1.0 } else { 1.0 };
    ([r * pymath::cos(theta) - config.galactic_radius_sun_pc, r * pymath::sin(theta), height * sign], kept)
}

/// _in_region: horizontal distance from the Sun within region_radius_pc (+ margin); 0 = whole galaxy.
fn in_region(position: &Position, config: &Config, margin: f64) -> bool {
    if config.region_radius_pc <= 0.0 {
        return true;
    }
    let reach = config.region_radius_pc + margin;
    position[0] * position[0] + position[1] * position[1] <= reach * reach
}

fn seed_life_in_bubbles(config: &Config, streams: &mut Streams) -> Vec<Civ> {
    let mut civs = Vec::new();
    let rng = &mut streams.world;
    for i in 0..poisson_count(candidate_mean(config.bubble_density_kpc2, config), rng) {
        let (center, kept) = sample_galactic_position(config, rng);
        if !kept || !in_region(&center, config, config.panspermia_range_pc) {
            continue;
        }
        let mut bubble = substream(streams.seed, &format!("bubble/{i}"));
        for k in 0..bubble.poisson(config.civs_per_bubble) {
            let offset = sample_ball(config.panspermia_range_pc, &mut bubble);
            let position = [center[0] + offset[0], center[1] + offset[1], center[2] + offset[2]];
            let birth = birth_date(config, &mut bubble);
            let civ = new_civ(format!("c_{i}_{k}"), position, config, &mut bubble, birth);
            if in_region(&position, config, 0.0) {
                civs.push(civ);
            }
        }
    }
    civs
}

/// _draw_births: every later birth, drawn up front over the whole annulus.
fn draw_births(config: &Config, streams: &mut Streams) -> Vec<Civ> {
    let rate = candidate_mean(config.civ_birth_rate_kpc2, config);
    let mut births = Vec::new();
    if rate <= 0.0 {
        return births;
    }
    let rng = &mut streams.birth;
    let mut j: u64 = 0;
    let mut elapsed = rng.exponential(1.0);
    loop {
        let birth = config.start_date_years() + elapsed / rate;
        if birth >= config.present_date_years {
            return births;
        }
        let (position, kept) = sample_galactic_position(config, rng);
        if kept && in_region(&position, config, 0.0) {
            let mut own = substream(streams.seed, &format!("birth/{j}"));
            births.push(new_civ(format!("b_{j}"), position, config, &mut own, birth));
        }
        j += 1;
        elapsed += rng.exponential(1.0);
    }
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
