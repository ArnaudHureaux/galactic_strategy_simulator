//! Mirror of python/p1_from_strat_to_actions and python/p2_from_actions_to_events.

use std::cmp::Ordering;

use crate::config::Config;
use crate::events::{Event, Kind};
use crate::geometry::dist;
use crate::pymath::{C_PC_PER_YEAR, pymax};
use crate::state::{BeliefEntry, Civ, World};

/// Sorts (score, target) like Python's `scored.sort(reverse=True)` on (score, target id) tuples.
pub fn sort_scored(scored: &mut [(f64, usize)], world: &World) {
    scored.sort_by(|a, b| {
        b.0.partial_cmp(&a.0)
            .unwrap_or(Ordering::Equal)
            .then_with(|| world.civs[b.1].id.cmp(&world.civs[a.1].id))
    });
}

/// _compute_max_number_of_attack, as a float (Python ints compare exactly with it).
pub fn max_number_of_attack(civ: &Civ) -> f64 {
    pymax(1.0, (civ.tech_level * civ.population_size).trunc())
}

fn attack_interest_score(civ: &Civ, entry: &BeliefEntry) -> f64 {
    let s = &civ.strategy;
    let delta = civ.tech_level - entry.estimated_tech_level;
    let safe_delta = delta - s.caution_k * entry.tech_level_uncertainty;
    let within_window = safe_delta > s.attack_gap_min && delta < s.attack_gap_max;
    if within_window && entry.trust < s.attack_when_trust_inferior_than { safe_delta } else { 0.0 }
}

/// Decisions of civ i (from_strat_to_actions) turned into events (from_actions_to_events).
/// Broadcasting has no event: the broadcast radius is set in the passive update.
pub fn decide(world: &mut World, i: usize, config: &Config, now: f64, out: &mut Vec<Event>) {
    let memory = config.belief_memory_years;
    let recent = world.civs[i].recent_beliefs(now, memory);
    let civ = &world.civs[i];
    let mut shares = Vec::new();
    let mut scored = Vec::new();
    for b in recent {
        let entry = &civ.belief[b];
        // A target that went silent (dead, or too weak to be seen) is only remembered, not acted upon.
        if now - entry.last_seen_at > memory {
            continue;
        }
        let score = attack_interest_score(civ, entry);
        if score > 0.0 {
            scored.push((score, entry.target));
        } else if entry.trust > civ.strategy.share_trust_threshold {
            // Between two civs at the tech cap, sharing only keeps the relationship going.
            let both_at_cap = civ.tech_level >= config.tech_cap && entry.estimated_tech_level >= config.tech_cap;
            shares.push((if both_at_cap { Kind::ImplicitShare } else { Kind::Share }, entry.target));
        }
    }
    sort_scored(&mut scored, world);
    let k = max_number_of_attack(civ);
    let n_attacks = if (scored.len() as f64) <= k { scored.len() } else { k as usize };

    let position = civ.position;
    for (kind, target) in shares {
        let event = match kind {
            // Applied at the end of the step, without travelling.
            Kind::ImplicitShare => Event { kind, src: i, dst: target, t: now, power: 0.0, shared_tech_level: 0.0 },
            _ => {
                let arrival = now + dist(&position, &world.civs[target].position) / C_PC_PER_YEAR;
                let shared = world.civs[i].tech_level;
                Event { kind, src: i, dst: target, t: arrival, power: 0.0, shared_tech_level: shared }
            }
        };
        out.push(event);
    }
    for &(_, target) in &scored[..n_attacks] {
        let arrival = now + dist(&position, &world.civs[target].position) / C_PC_PER_YEAR;
        let civ = &mut world.civs[i];
        civ.tech_level -= config.attack_cost_tech * civ.tech_level;
        out.push(Event { kind: Kind::Attack, src: i, dst: target, t: arrival, power: civ.tech_level, shared_tech_level: 0.0 });
    }
}
