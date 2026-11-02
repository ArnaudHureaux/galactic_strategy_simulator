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
    pub share_catchup_fraction: f64,
    pub share_backflow_additive: f64,
    pub share_trust_fraction: f64,
    pub share_trust_fraction_forgiven: f64,
    pub share_synergy: f64,
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

    pub biochem_types: Vec<String>,
    pub world_type_fractions: Vec<f64>,

    pub panspermia_range_pc: f64,
    pub expected_bubbles: f64,
    pub civs_per_bubble: f64,
    pub civ_birth_rate: f64,

    pub last_grb_date_years: f64,
    pub humanity_birth_date_years: f64,
    pub present_date_years: f64,
    pub signal_window_years: f64,
    pub artefact_window_years: f64,
    pub artefact_detection_probability: f64,

    pub tech_growth_model: String,
    pub population_growth_model: String,
    pub tech_cap: f64,
    pub population_per_world: f64,

    pub initial_tech_level: f64,
    pub initial_population: f64,

    pub self_destruction_risk: f64,
    pub self_destruction_shape: String,
    pub danger_window_center: f64,
    pub danger_window_width: f64,

    pub emit_radius_per_tech: f64,
    pub passive_leakage_factor: f64,
    pub max_broadcast_radius: f64,
    pub probe_speed_per_tech: f64,
    pub max_probe_radius: f64,
    pub probe_lifetime_per_tech: f64,

    pub belief_memory_years: f64,

    pub share_period_years: f64,
    pub share_catchup: f64,
    pub share_backflow: f64,
    pub share_decay: f64,
    pub share_synergy_bonus: f64,
    pub share_trust_gain: f64,
    pub forgiveness: f64,

    pub damage_coef: f64,
    pub attack_cost_tech: f64,
    pub reputation_trust_drop: f64,

    pub natural_tech_progress_mean: f64,
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
            biochem_types: vec!["water".into(), "ammonia".into(), "silicon".into()],
            world_type_fractions: vec![0.7, 0.2, 0.1],
            panspermia_range_pc: 300.0,
            expected_bubbles: 5.0,
            civs_per_bubble: 20.0,
            civ_birth_rate: 1e-8,
            last_grb_date_years: 1.0e9,
            humanity_birth_date_years: 1.3799e10,
            present_date_years: 1.38e10,
            signal_window_years: 100.0,
            artefact_window_years: 4.5e9,
            artefact_detection_probability: 0.1,
            tech_growth_model: "logistic".into(),
            population_growth_model: "logistic".into(),
            tech_cap: 3.0,
            population_per_world: 1.0,
            initial_tech_level: 0.1,
            initial_population: 1.0,
            self_destruction_risk: 1e-8,
            self_destruction_shape: "danger_window".into(),
            danger_window_center: 1.5,
            danger_window_width: 0.5,
            emit_radius_per_tech: 10.0,
            passive_leakage_factor: 0.1,
            max_broadcast_radius: 100.0,
            probe_speed_per_tech: 1e-4,
            max_probe_radius: 1e12,
            probe_lifetime_per_tech: 1e6,
            belief_memory_years: 0.0,
            share_period_years: 1000.0,
            share_catchup: 0.5,
            share_backflow: 0.05,
            share_decay: 0.5,
            share_synergy_bonus: 0.1,
            share_trust_gain: 0.3,
            forgiveness: 0.2,
            damage_coef: 0.3,
            attack_cost_tech: 0.05,
            reputation_trust_drop: 0.3,
            natural_tech_progress_mean: 1e-10,
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
        // p3_apply_events._share_strength: rates per share period rescaled to one step.
        let step = self.dt / self.share_period_years;
        let fraction = |rate: f64| -pymath::expm1(step * pymath::log1p(-rate));
        let derived = Derived {
            tech_logistic: logistic("tech_growth_model", &self.tech_growth_model)?,
            population_logistic: logistic("population_growth_model", &self.population_growth_model)?,
            shape,
            share_catchup_fraction: fraction(self.share_catchup),
            share_backflow_additive: self.share_backflow * step,
            share_trust_fraction: fraction(self.share_trust_gain),
            share_trust_fraction_forgiven: fraction(self.share_trust_gain * self.forgiveness),
            share_synergy: pymath::pow(1.0 + self.share_synergy_bonus, step),
        };
        self.derived = Some(derived);
        Ok(())
    }

    #[inline]
    pub fn derived(&self) -> &Derived {
        self.derived.as_ref().expect("Config::prepare must be called first")
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
}
