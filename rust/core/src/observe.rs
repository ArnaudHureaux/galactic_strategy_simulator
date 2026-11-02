//! Mirror of python/observe.py: run summary, per-civ records and final metadata.
//! The config parameters, config_hash and seed are added on the Python side.

use crate::config::Config;
use crate::geometry::dist;
use crate::pymath::pymax;
use crate::state::World;

#[derive(Clone, Debug, PartialEq)]
pub enum Value {
    None,
    Bool(bool),
    Int(i64),
    Float(f64),
    Str(String),
}

impl From<bool> for Value {
    fn from(v: bool) -> Value {
        Value::Bool(v)
    }
}
impl From<usize> for Value {
    fn from(v: usize) -> Value {
        Value::Int(v as i64)
    }
}
impl From<u64> for Value {
    fn from(v: u64) -> Value {
        Value::Int(v as i64)
    }
}
impl From<f64> for Value {
    fn from(v: f64) -> Value {
        Value::Float(v)
    }
}
impl From<&str> for Value {
    fn from(v: &str) -> Value {
        Value::Str(v.to_string())
    }
}
impl<T: Into<Value>> From<Option<T>> for Value {
    fn from(v: Option<T>) -> Value {
        v.map_or(Value::None, Into::into)
    }
}

/// Ordered (column, value) pairs.
pub type Record = Vec<(&'static str, Value)>;

/// Plain left-to-right float sum, as Python's sum() before 3.12.
fn total(values: impl Iterator<Item = f64>) -> f64 {
    values.fold(0.0, |acc, v| acc + v)
}

pub fn capture(world: &World, now: f64) -> Record {
    let active = world.active(now);
    let others: Vec<_> = active.iter().map(|&i| &world.civs[i]).filter(|c| !c.is_human).collect();
    let detected = active.iter().any(|&i| world.civs[i].belief_of.contains_key(&world.humanity));
    let n = others.len();
    if n == 0 {
        return vec![("n_alive", Value::Int(0)), ("humanity_detected_by_others", false.into())];
    }
    let nf = n as f64;
    let mean = |f: &dyn Fn(&crate::state::Civ) -> f64| total(others.iter().map(|c| f(c))) / nf;
    vec![
        ("n_alive", n.into()),
        ("mean_tech", mean(&|c| c.tech_level).into()),
        ("broadcast_frac", (others.iter().filter(|c| c.strategy.broadcast).count() as f64 / nf).into()),
        ("mean_attack_when_trust", mean(&|c| c.strategy.attack_when_trust_inferior_than).into()),
        ("mean_caution_k", mean(&|c| c.strategy.caution_k).into()),
        ("mean_share_trust_threshold", mean(&|c| c.strategy.share_trust_threshold).into()),
        ("mean_trust_default_competitor", mean(&|c| c.strategy.trust_default_competitor).into()),
        ("mean_trust_default_noncompetitor", mean(&|c| c.strategy.trust_default_noncompetitor).into()),
        ("humanity_detected_by_others", detected.into()),
    ]
}

pub struct RunCounters {
    pub outcome: &'static str,
    pub n_steps: u64,
    pub n_jumps: u64,
    pub budget_exhausted: Option<&'static str>,
    pub end: f64,
    pub wall_time_s: f64,
}

/// observe.run_record without config_hash, seed and the config parameters.
pub fn run_record(world: &World, run: &RunCounters) -> Record {
    let h = world.humanity;
    let human = &world.civs[h];
    let end = run.end;
    let others = || world.civs.iter().filter(|c| !c.is_human);
    vec![
        ("outcome", run.outcome.into()),
        ("rejection_reason", world.rejection_reason.as_deref().into()),
        ("rejected_at", world.rejected_at.into()),
        ("end_year", end.into()),
        ("n_steps", run.n_steps.into()),
        ("n_jumps", run.n_jumps.into()),
        ("budget_exhausted", run.budget_exhausted.into()),
        ("wall_time_s", run.wall_time_s.into()),
        ("n_civs_initial", (world.n_initial - 1).into()),
        ("n_civs_born", (world.civs.len() - world.n_initial).into()),
        ("n_alive_end", others().filter(|c| c.alive && c.birth_year <= end).count().into()),
        ("n_extinct_end", others().filter(|c| !c.alive).count().into()),
        ("humanity_born", (human.birth_year <= end).into()),
        ("humanity_alive", (human.alive && human.birth_year <= end).into()),
        (
            "humanity_detected_by_others",
            world.civs.iter().enumerate().any(|(i, c)| i != h && c.belief_of.contains_key(&h)).into(),
        ),
        ("humanity_reached_by_probe", world.civs.iter().any(|c| c.probe_arrived_at_human.is_some()).into()),
    ]
}

/// observe.civ_records without config_hash and seed: one record per civ (humanity included).
pub fn civ_records(world: &World, config: &Config, end: f64) -> Vec<Record> {
    let h = world.humanity;
    let human = &world.civs[h];
    world
        .civs
        .iter()
        .map(|c| {
            let death = c.extinct_at.unwrap_or(end);
            let mut record: Record = vec![
                ("civ_id", c.id.as_str().into()),
                ("is_human", c.is_human.into()),
                ("birth_year", c.birth_year.into()),
                ("born", (c.birth_year <= end).into()),
                ("biochem_type", config.biochem_types[c.biochem].as_str().into()),
                ("x_pc", c.position[0].into()),
                ("y_pc", c.position[1].into()),
                ("z_pc", c.position[2].into()),
                ("distance_to_humanity_pc", dist(&c.position, &human.position).into()),
                ("status", (if c.alive { "alive" } else { "extinct" }).into()),
                ("extinct_at", c.extinct_at.into()),
                ("extinction_cause", c.extinction_cause.into()),
                ("lifetime_years", pymax(0.0, death - c.birth_year).into()),
                ("tech_level", c.tech_level.into()),
                ("population_size", c.population_size.into()),
                ("natural_tech_progress", c.natural_tech_progress.into()),
                ("natural_population_growth", c.natural_population_growth.into()),
                ("probe_radius", c.probe_radius.into()),
                ("was_attacked", c.attacked_by.is_some().into()),
                ("n_known_civs", c.belief.len().into()),
                ("detected_humanity", c.belief_of.contains_key(&h).into()),
                ("probe_reached_humanity", c.probe_arrived_at_human.is_some().into()),
                ("strategy_broadcast", c.strategy.broadcast.into()),
            ];
            record.extend(c.strategy.values().into_iter().map(|(name, v)| (name, v.into())));
            record
        })
        .collect()
}
