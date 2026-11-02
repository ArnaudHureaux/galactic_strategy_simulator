//! Mirror of python/p3_apply_events.

use crate::config::Config;
use crate::events::{Event, Kind};
use crate::pymath::{self, pymin};
use crate::state::World;

pub fn apply_event(event: &Event, world: &mut World, config: &Config) {
    if !world.civs[event.dst].alive {
        return;
    }
    match event.kind {
        Kind::Share => {
            let target = &mut world.civs[event.dst];
            target.tech_level = share_tech_update(target.tech_level, event.shared_tech_level, config);
            apply_share_relationship(event, world, config);
        }
        Kind::ImplicitShare => apply_share_relationship(event, world, config),
        Kind::Attack => apply_attack(event, world, config),
    }
}

fn share_tech_update(tech_level: f64, shared_tech_level: f64, config: &Config) -> f64 {
    let derived = config.derived();
    let gap = shared_tech_level - tech_level;
    let updated = if gap > 0.0 {
        tech_level + derived.share_catchup_fraction * gap
    } else {
        tech_level + derived.share_backflow_additive * shared_tech_level * pymath::exp(gap / config.share_decay)
    };
    pymin(config.tech_cap, updated)
}

fn apply_share_relationship(event: &Event, world: &mut World, config: &Config) {
    let cap = config.max_natural_tech_progress;
    let (src, dst) = (event.src, event.dst);
    // Most relationships are saturated: skip the synergy update when it cannot change anything.
    if world.civs[dst].natural_tech_progress != cap || world.civs[src].natural_tech_progress != cap {
        let synergy = config.derived().share_synergy;
        for c in [dst, src] {
            let civ = &mut world.civs[c];
            civ.natural_tech_progress = pymin(cap, civ.natural_tech_progress * synergy);
        }
    }
    let target = &mut world.civs[dst];
    if let Some(&b) = target.belief_of.get(&src) {
        let entry = &mut target.belief[b];
        let fraction = if entry.attacked_me {
            config.derived().share_trust_fraction_forgiven
        } else {
            config.derived().share_trust_fraction
        };
        let trust = entry.trust + fraction * (1.0 - entry.trust);
        // Converged relationships (trust 1.0) are the common case: only report actual changes.
        if trust != entry.trust {
            entry.trust = trust;
            world.note_trust(dst, b);
        }
    }
}

fn apply_attack(event: &Event, world: &mut World, config: &Config) {
    let target = &mut world.civs[event.dst];
    let damage = if target.tech_level <= 0.0 {
        1.0
    } else {
        pymin(1.0, config.damage_coef * (event.power / target.tech_level))
    };
    target.tech_level *= 1.0 - damage;
    target.population_size *= 1.0 - damage;
    target.expansion_radius *= 1.0 - damage;
    if let Some(&b) = target.belief_of.get(&event.src) {
        let entry = &mut target.belief[b];
        if entry.trust != 0.0 || !entry.attacked_me {
            entry.trust = 0.0;
            entry.attacked_me = true;
            world.note_trust(event.dst, b);
        }
    }
    let target = &mut world.civs[event.dst];
    target.attacked_by = Some(event.src);
    if target.tech_level <= 0.0 || target.population_size <= 0.0 {
        target.go_extinct(event.t, "attack");
    }
}
