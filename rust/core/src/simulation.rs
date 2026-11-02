//! Mirror of python/simulation.run.

use std::time::Instant;

use crate::apply::apply_event;
use crate::config::Config;
use crate::decisions::decide;
use crate::events::{EventQueue, Kind};
use crate::fast_forward::FastForward;
use crate::observe::{self, Record, RunCounters};
use crate::passive::{final_silence_check, passive_update};
use crate::rng::Streams;
use crate::world_gen::generate_world;

/// One row per step (observe.Logger.rows), kept only on request.
#[derive(Clone, Debug, PartialEq)]
pub struct Row {
    pub year: f64,
    pub n_alive: usize,
    pub rejected: bool,
}

pub struct RunResult {
    pub outcome: &'static str,
    pub metadata: Option<Record>,
    pub n_steps: u64,
    pub n_jumps: u64,
    pub budget_exhausted: Option<&'static str>,
    pub run: Record,
    pub civs: Vec<Record>,
    pub rows: Vec<Row>,
}

/// `time_budget_s` is a wall-clock safety net: a run it stops is not reproducible elsewhere.
/// Prefer config.max_steps, which is deterministic.
pub fn run(config: &Config, seed: i64, time_budget_s: Option<f64>, keep_rows: bool) -> RunResult {
    let start = Instant::now();
    let mut streams = Streams::new(seed);
    let mut world = generate_world(config, &mut streams);
    let mut queue = EventQueue::default();
    let mut rows = Vec::new();
    let (mut n_steps, mut n_jumps) = (0u64, 0u64);
    let mut budget_exhausted = None;
    let mut now = config.last_grb_date_years;
    let mut dt = config.dt;
    let mut jump = None;
    let mut fast_forward = config.fast_forward.then(FastForward::default);
    let mut emitted = Vec::new();

    while now < config.present_date_years && !world.rejected && !world.intractable {
        if config.max_steps != 0.0 && n_steps as f64 >= config.max_steps {
            budget_exhausted = Some("steps");
            break;
        }
        if time_budget_s.is_some_and(|budget| start.elapsed().as_secs_f64() > budget) {
            budget_exhausted = Some("wall_time");
            break;
        }

        let applied = queue.pop_due(now);
        for event in &applied {
            apply_event(event, &mut world, config);
        }

        passive_update(&mut world, config, now, &mut streams, dt, jump.as_ref());

        if world.civs.len() as f64 > config.max_civs {
            world.intractable = true;
            break;
        }

        emitted.clear();
        for i in world.active(now) {
            decide(&mut world, i, config, now, &mut emitted);
        }
        // Implicit shares are applied once every civ has decided, so decisions do not depend on civ order.
        for event in &emitted {
            if event.kind == Kind::ImplicitShare {
                apply_event(event, &mut world, config);
            }
        }
        for event in &emitted {
            if event.kind != Kind::ImplicitShare {
                queue.push(event.clone());
            }
        }

        if keep_rows {
            rows.push(Row { year: now, n_alive: world.alive_count(), rejected: world.rejected });
        }
        n_steps += 1;

        jump = None;
        if let Some(ff) = fast_forward.as_mut()
            && !world.rejected
        {
            jump = ff.step(&mut world, &applied, &emitted, now, &mut streams, config);
        }
        match &jump {
            None => dt = config.dt,
            Some(j) => {
                // Translate in-flight events so the step ending the jump replays the stationary cycle.
                queue.shift(j.dt - config.dt);
                dt = j.dt;
                n_jumps += 1;
            }
        }
        now += dt;
    }

    let timed_out = budget_exhausted.is_some();
    if !world.rejected && !world.intractable && !timed_out {
        final_silence_check(&mut world, config, &mut streams);
    }

    let outcome = if world.intractable {
        "intractable"
    } else if world.rejected {
        "rejected"
    } else if timed_out {
        "timeout"
    } else {
        "consistent"
    };
    let metadata = (outcome == "consistent").then(|| observe::capture(&world, now));
    // Last simulated date: the rejection, the step where the run stopped, or the present.
    let end = match world.rejected_at {
        Some(t) if world.rejected => t,
        _ if world.intractable || timed_out => now,
        _ => config.present_date_years,
    };
    let counters = RunCounters { outcome, n_steps, n_jumps, budget_exhausted, end, wall_time_s: start.elapsed().as_secs_f64() };
    let run = observe::run_record(&world, &counters);
    let civs = observe::civ_records(&world, config, end);
    RunResult { outcome, metadata, n_steps, n_jumps, budget_exhausted, run, civs, rows }
}
