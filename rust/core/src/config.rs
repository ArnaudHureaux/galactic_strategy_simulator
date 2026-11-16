//! Mirror of python/config.py. Validation stays in Python (Config.__post_init__): this side
//! only parses, rejects unknown fields and derives a few constants used in hot paths.

use serde::{Deserialize, Serialize};

use crate::pymath;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SelfDestructionShape {
    Constant,
    Increasing,
    DangerWindow,
}

/// Values derived once from the config (what the Python code recomputes or caches).
#[derive(Clone, Debug)]
pub struct Derived {
    pub tech_logistic: bool,
    pub population_logistic: bool,
    pub shape: SelfDestructionShape,
    /// dt / interaction_period_years.
    pub interaction_step: f64,
    pub share_catchup_fraction: f64,
    pub share_backflow_additive: f64,
    pub share_trust_fraction: f64,
    pub share_trust_fraction_forgiven: f64,
    pub share_synergy: f64,
    pub attack_cost_fraction: f64,
    pub reputation_drop_additive: f64,
    pub humanity_present_tech: f64,
    pub humanity_tech_rate: f64,
}

/// p3_apply_events._rates._fraction: fraction done in one step (`step` interaction periods)
/// when `rate` is the fraction done per interaction period.
pub fn step_fraction(rate: f64, step: f64) -> f64 {
    if rate >= 1.0 {
        return 1.0;
    }
    -pymath::expm1(step * pymath::log1p(-rate))
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Config {
    pub dt: f64,
    pub max_civs: f64,
    pub max_steps: f64,

    pub fast_forward: bool,
    pub max_jump_years: f64,
    pub jump_max_relative_change: f64,

    pub region_radius_pc: f64,
    pub scale_height_pc: f64,
    pub sun_height_pc: f64,

    pub biochem_types: Vec<String>,
    pub world_type_fractions: Vec<f64>,

    pub panspermia_range_pc: f64,
    pub expected_bubbles: f64,
    pub civs_per_bubble: f64,
    pub civ_birth_rate: f64,

    pub start_lookback_years: f64,
    pub birth_spread_fraction: f64,
    pub humanity_birth_date_years: f64,
    pub present_date_years: f64,
    pub humanity_leak_years: f64,
    pub humanity_listening_years: f64,
    pub artefact_window_years: f64,
    pub artefact_detection_probability: f64,
    pub artefact_stealth_per_tech: f64,

    pub tech_growth_model: String,
    pub population_growth_model: String,
    pub tech_cap: f64,
    pub population_per_world: f64,

    pub initial_tech_level: f64,
    pub humanity_tech_fraction: f64,
    pub initial_population: f64,

    pub self_destruction_risk: f64,
    pub self_destruction_shape: String,
    pub danger_window_center: f64,
    pub danger_window_width: f64,

    pub eirp_human_w: f64,
    pub eirp_cap_w: f64,
    pub passive_leakage_factor: f64,
    pub humanity_leakage_factor: f64,
    pub seti_flux_threshold_w_m2: f64,
    pub beacon_duty: f64,
    pub listen_coverage: f64,
    pub seti_complete_radius_pc: f64,
    pub seti_coverage_50pc: f64,
    pub seti_coverage_beyond: f64,
    pub probe_speed_human_c: f64,
    pub probe_speed_cap_c: f64,
    pub max_probe_radius: f64,
    pub probe_function_human_years: f64,
    pub probe_function_cap_years: f64,
    pub probe_persistence_human_years: f64,
    pub probe_persistence_cap_years: f64,

    pub colonization_launch_period_years: f64,
    pub habitable_world_density: f64,

    pub belief_memory_years: f64,

    pub interaction_period_years: f64,
    pub share_catchup: f64,
    pub share_backflow: f64,
    pub share_decay: f64,
    pub share_synergy_bonus: f64,
    pub share_trust_gain: f64,
    pub forgiveness: f64,

    pub damage_coef: f64,
    pub attack_stealth_per_tech: f64,
    pub attacks_per_tech_population: f64,
    pub attack_cost_tech: f64,
    pub reputation_trust_drop: f64,

    pub natural_tech_progress_mean: f64,
    pub natural_tech_progress_spread: f64,
    pub natural_population_growth_spread: f64,
    pub tech_population_exponent: f64,
    pub natural_population_growth_mean: f64,
    pub max_natural_tech_progress: f64,

    pub broadcast_probability: f64,
    pub attack_gap_min_low: f64,
    pub attack_gap_min_high: f64,
    pub attack_gap_max_low: f64,
    pub attack_gap_max_high: f64,
    pub caution_k_low: f64,
    pub caution_k_high: f64,
    pub attack_when_trust_inferior_than_low: f64,
    pub attack_when_trust_inferior_than_high: f64,
    pub trust_default_competitor_low: f64,
    pub trust_default_competitor_high: f64,
    pub trust_default_noncompetitor_low: f64,
    pub trust_default_noncompetitor_high: f64,
    pub share_trust_threshold_low: f64,
    pub share_trust_threshold_high: f64,
    pub colonization_aggressiveness_low: f64,
    pub colonization_aggressiveness_high: f64,
    pub strategy_mix_random: f64,
    pub strategy_mix_full_aggressive: f64,
    pub strategy_mix_full_passive: f64,
    pub strategy_mix_anti_competitors: f64,
    pub strategy_mix_anti_weaker_competitors: f64,
    pub strategy_mix_dark_forest: f64,
    pub strategy_mix_broadcaster: f64,
    pub strategy_mix_cooperative: f64,
    pub strategy_noise: f64,

    #[serde(skip)]
    derived: Option<Derived>,
}

impl Default for Config {
    fn default() -> Config {
        Config {
            dt: 1000.0,
            max_civs: 100000.0,
            max_steps: 0.0,
            fast_forward: true,
            max_jump_years: 1.0e7,
            jump_max_relative_change: 0.01,
            region_radius_pc: 1000.0,
            scale_height_pc: 300.0,
            sun_height_pc: 20.8,
            biochem_types: vec!["water".into(), "ammonia".into(), "silicon".into()],
            world_type_fractions: vec![0.7, 0.2, 0.1],
            panspermia_range_pc: 300.0,
            expected_bubbles: 5.0,
            civs_per_bubble: 20.0,
            civ_birth_rate: 1e-8,
            start_lookback_years: 1.0e9,
            birth_spread_fraction: 0.0,
            humanity_birth_date_years: 1.379999e10,
            present_date_years: 1.38e10,
            humanity_leak_years: 90.0,
            humanity_listening_years: 66.0,
            artefact_window_years: 4.5e9,
            artefact_detection_probability: 0.1,
            artefact_stealth_per_tech: 0.0,
            tech_growth_model: "logistic".into(),
            population_growth_model: "logistic".into(),
            tech_cap: 3.0,
            population_per_world: 1.0,
            initial_tech_level: 0.1,
            humanity_tech_fraction: 1e-3,
            initial_population: 1.0,
            self_destruction_risk: 1e-8,
            self_destruction_shape: "danger_window".into(),
            danger_window_center: 1.5,
            danger_window_width: 0.5,
            eirp_human_w: 2.0e13,
            eirp_cap_w: 1.0e21,
            passive_leakage_factor: 2.0e-4,
            humanity_leakage_factor: 2.0e-4,
            seti_flux_threshold_w_m2: 3.3e-25,
            beacon_duty: 1e-3,
            listen_coverage: 0.1,
            seti_complete_radius_pc: 5.1,
            seti_coverage_50pc: 0.037,
            seti_coverage_beyond: 4.0e-4,
            probe_speed_human_c: 5.67e-5,
            probe_speed_cap_c: 0.1,
            max_probe_radius: 1e12,
            probe_function_human_years: 50.0,
            probe_function_cap_years: 1.0e6,
            probe_persistence_human_years: 1.0e9,
            probe_persistence_cap_years: 1.0e10,
            colonization_launch_period_years: 1.0e4,
            habitable_world_density: 0.01,
            belief_memory_years: 0.0,
            interaction_period_years: 1000.0,
            share_catchup: 0.5,
            share_backflow: 0.05,
            share_decay: 0.5,
            share_synergy_bonus: 0.1,
            share_trust_gain: 0.3,
            forgiveness: 0.2,
            damage_coef: 0.3,
            attack_stealth_per_tech: 0.0,
            attacks_per_tech_population: 1.0,
            attack_cost_tech: 0.05,
            reputation_trust_drop: 0.3,
            natural_tech_progress_mean: 1e-10,
            natural_tech_progress_spread: 0.5,
            natural_population_growth_spread: 0.5,
            tech_population_exponent: 1.0,
            natural_population_growth_mean: 1e-9,
            max_natural_tech_progress: 1e-7,
            broadcast_probability: 0.5,
            attack_gap_min_low: -2.0,
            attack_gap_min_high: 2.0,
            attack_gap_max_low: 2.0,
            attack_gap_max_high: 10.0,
            caution_k_low: 0.0,
            caution_k_high: 3.0,
            attack_when_trust_inferior_than_low: 0.0,
            attack_when_trust_inferior_than_high: 1.0,
            trust_default_competitor_low: 0.0,
            trust_default_competitor_high: 1.0,
            trust_default_noncompetitor_low: 0.0,
            trust_default_noncompetitor_high: 1.0,
            share_trust_threshold_low: 0.0,
            share_trust_threshold_high: 1.0,
            colonization_aggressiveness_low: 0.0,
            colonization_aggressiveness_high: 1.0,
            strategy_mix_random: 1.0,
            strategy_mix_full_aggressive: 0.0,
            strategy_mix_full_passive: 0.0,
            strategy_mix_anti_competitors: 0.0,
            strategy_mix_anti_weaker_competitors: 0.0,
            strategy_mix_dark_forest: 0.0,
            strategy_mix_broadcaster: 0.0,
            strategy_mix_cooperative: 0.0,
            strategy_noise: 0.05,
            derived: None,
        }
    }
}

impl Config {
    /// Parses a JSON object of Config parameters (missing ones take their default value).
    pub fn from_json(text: &str) -> Result<Config, String> {
        let mut config: Config = serde_json::from_str(text).map_err(|e| format!("invalid Config: {e}"))?;
        config.prepare()?;
        Ok(config)
    }

    /// Default parameters as JSON (to check that both implementations share the same fields).
    pub fn default_json() -> String {
        serde_json::to_string(&Config::default()).expect("Config serializes")
    }

    /// Computes the derived values; must be called after any change of the parameters.
    pub fn prepare(&mut self) -> Result<(), String> {
        let logistic = |name: &str, value: &str| match value {
            "logistic" => Ok(true),
            "exponential" => Ok(false),
            _ => Err(format!("{name} must be 'logistic' or 'exponential' (got {value:?})")),
        };
        let shape = match self.self_destruction_shape.as_str() {
            "constant" => SelfDestructionShape::Constant,
            "increasing" => SelfDestructionShape::Increasing,
            "danger_window" => SelfDestructionShape::DangerWindow,
            other => return Err(format!("unknown self_destruction_shape {other:?}")),
        };
        if self.biochem_types.is_empty() || self.biochem_types.len() != self.world_type_fractions.len() {
            return Err("world_type_fractions must have one entry per biochem type".into());
        }
        // p3_apply_events._rates: rates per interaction period rescaled to one step.
        let step = self.dt / self.interaction_period_years;
        let fraction = |rate: f64| step_fraction(rate, step);
        let tech_logistic = logistic("tech_growth_model", &self.tech_growth_model)?;
        // Config.humanity_present_tech and Config.humanity_tech_rate.
        let x = self.initial_tech_level;
        let present_tech = x * pymath::pow(self.tech_cap / x, self.humanity_tech_fraction);
        let span = self.present_date_years - self.humanity_birth_date_years;
        let humanity_tech_rate = if present_tech <= x {
            0.0
        } else if tech_logistic {
            pymath::log((self.tech_cap / x - 1.0) / (self.tech_cap / present_tech - 1.0)) / span
        } else {
            pymath::log(present_tech / x) / span
        };
        let derived = Derived {
            tech_logistic,
            population_logistic: logistic("population_growth_model", &self.population_growth_model)?,
            shape,
            interaction_step: step,
            share_catchup_fraction: fraction(self.share_catchup),
            share_backflow_additive: self.share_backflow * step,
            share_trust_fraction: fraction(self.share_trust_gain),
            share_trust_fraction_forgiven: fraction(self.share_trust_gain * self.forgiveness),
            share_synergy: pymath::pow(1.0 + self.share_synergy_bonus, step),
            attack_cost_fraction: fraction(self.attack_cost_tech),
            reputation_drop_additive: self.reputation_trust_drop * step,
            humanity_present_tech: present_tech,
            humanity_tech_rate,
        };
        self.derived = Some(derived);
        Ok(())
    }

    #[inline]
    pub fn derived(&self) -> &Derived {
        self.derived.as_ref().expect("Config::prepare must be called first")
    }

    #[inline]
    pub fn start_date_years(&self) -> f64 {
        self.present_date_years - self.start_lookback_years
    }

    /// (low, high) of each strategy parameter, in config.STRATEGY_RANGES order.
    pub fn strategy_ranges(&self) -> [(f64, f64); 8] {
        [
            (self.attack_gap_min_low, self.attack_gap_min_high),
            (self.attack_gap_max_low, self.attack_gap_max_high),
            (self.caution_k_low, self.caution_k_high),
            (self.attack_when_trust_inferior_than_low, self.attack_when_trust_inferior_than_high),
            (self.trust_default_competitor_low, self.trust_default_competitor_high),
            (self.trust_default_noncompetitor_low, self.trust_default_noncompetitor_high),
            (self.share_trust_threshold_low, self.share_trust_threshold_high),
            (self.colonization_aggressiveness_low, self.colonization_aggressiveness_high),
        ]
    }

    pub fn tech_growth_cap(&self) -> Option<f64> {
        if self.derived().tech_logistic { Some(self.tech_cap) } else { None }
    }

    /// Weights of the strategy archetypes, in ARCHETYPES order.
    pub fn strategy_mix(&self) -> [f64; 8] {
        [
            self.strategy_mix_random,
            self.strategy_mix_full_aggressive,
            self.strategy_mix_full_passive,
            self.strategy_mix_anti_competitors,
            self.strategy_mix_anti_weaker_competitors,
            self.strategy_mix_dark_forest,
            self.strategy_mix_broadcaster,
            self.strategy_mix_cooperative,
        ]
    }
}

/// A strategy archetype (config.ARCHETYPES): pinned broadcast and pinned traits, in
/// config.STRATEGY_RANGES order (None: drawn uniformly in the range).
pub struct Archetype {
    pub name: &'static str,
    pub broadcast: Option<bool>,
    pub traits: [Option<f64>; 8],
}

const INF: f64 = f64::INFINITY;

/// Traits: attack_gap_min, attack_gap_max, caution_k, attack_when_trust_inferior_than,
/// trust_default_competitor, trust_default_noncompetitor, share_trust_threshold,
/// colonization_aggressiveness (never pinned).
pub const ARCHETYPES: [Archetype; 8] = [
    Archetype { name: "random", broadcast: None, traits: [None; 8] },
    Archetype {
        name: "full_aggressive",
        broadcast: Some(false),
        traits: [Some(-INF), Some(INF), Some(0.0), Some(1.0), Some(0.0), Some(0.0), Some(0.8), None],
    },
    Archetype {
        name: "full_passive",
        broadcast: Some(false),
        traits: [Some(0.5), Some(5.0), Some(1.0), Some(0.0), Some(0.2), Some(0.7), Some(0.8), None],
    },
    Archetype {
        name: "anti_competitors",
        broadcast: Some(false),
        traits: [Some(-INF), Some(INF), Some(1.0), Some(0.3), Some(0.0), Some(1.0), Some(0.8), None],
    },
    Archetype {
        name: "anti_weaker_competitors",
        broadcast: Some(false),
        traits: [Some(0.0), Some(INF), Some(1.5), Some(0.3), Some(0.0), Some(1.0), Some(0.8), None],
    },
    Archetype {
        name: "dark_forest",
        broadcast: Some(false),
        traits: [Some(0.0), Some(INF), Some(2.0), Some(0.9), Some(0.0), Some(0.0), Some(0.8), None],
    },
    Archetype {
        name: "broadcaster",
        broadcast: Some(true),
        traits: [Some(0.5), Some(5.0), Some(1.0), Some(0.0), Some(0.2), Some(0.7), Some(0.8), None],
    },
    Archetype {
        name: "cooperative",
        broadcast: Some(true),
        traits: [Some(0.5), Some(5.0), Some(1.0), Some(0.2), Some(0.5), Some(0.9), Some(0.4), None],
    },
];
