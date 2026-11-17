//! Mirror of python/p3_apply_events.

use crate::config::{Config, step_fraction};
use crate::events::{Event, Kind};
use crate::passive::shrink_worlds;
use crate::pymath::{self, pymax, pymin};
use crate::rng::Rng;
use crate::state::World;

/// rng: the attribution stream, drawn from only when an attacker may stay unidentified.
pub fn apply_event(event: &Event, world: &mut World, config: &Config, rng: &mut Rng) {
    if !world.civs[event.dst].alive {
        return;
    }
    if event.dst == world.humanity && matches!(event.kind, Kind::Share | Kind::ImplicitShare) {
        // Receiving technology is a contact humanity would have noticed.
        world.reject("contact_share".into(), event.t);
        return;
    }
    match event.kind {
        Kind::Share => {
            let target = &mut world.civs[event.dst];
            target.tech_level = share_tech_update(target.tech_level, event.shared_tech_level, config);
            apply_share_relationship(event, world, config);
        }
        Kind::ImplicitShare => apply_share_relationship(event, world, config),
        Kind::Attack => apply_attack(event, world, config, rng),
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

/// A more advanced attacker hides better: probability that the victim identifies it.
fn attribution_probability(power: f64, target_tech_level: f64, config: &Config) -> f64 {
    let gap = power - target_tech_level;
    if config.attack_stealth_per_tech <= 0.0 || gap <= 0.0 {
        return 1.0;
    }
    pymath::exp(-config.attack_stealth_per_tech * gap)
}

fn apply_attack(event: &Event, world: &mut World, config: &Config, rng: &mut Rng) {
    let target = &mut world.civs[event.dst];
    // A war destroys min(1, damage_coef * power ratio) of the target per
    // interaction period; an attack event stands for one regular step of it.
    // Power ratio per tech level of the energy law anchored on humanity (see _attack_damage).
    let scale = pymath::log(config.eirp_cap_w / config.eirp_human_w)
        / (config.tech_cap - config.derived().humanity_present_tech);
    let damage = if target.tech_level <= 0.0 {
        1.0
    } else {
        let gain = pymath::exp(scale * (event.power - target.tech_level));
        let per_period = pymin(1.0, config.damage_coef * gain);
        step_fraction(per_period, config.derived().interaction_step)
    };
    // Whether the victim identifies the attacker is drawn once per war (first attack of the pair).
    let attributed = match target.attributions.get(&event.src) {
        Some(&attributed) => attributed,
        None => {
            let p = attribution_probability(event.power, target.tech_level, config);
            let attributed = p >= 1.0 || rng.random() < p;
            target.attributions.insert(event.src, attributed);
            attributed
        }
    };
    // The target loses the share damage of its power: ln(1 - damage) / scale tech levels (_damaged_tech).
    target.tech_level = if damage >= 1.0 {
        0.0
    } else {
        pymax(0.0, target.tech_level + pymath::log1p(-damage) / scale)
    };
    target.population_size *= 1.0 - damage;
    shrink_worlds(target, 1.0 - damage);
    if let Some(&b) = target.belief_of.get(&event.src).filter(|_| attributed) {
        let entry = &mut target.belief[b];
        if entry.trust != 0.0 || !entry.attacked_me {
            entry.trust = 0.0;
            entry.attacked_me = true;
            world.note_trust(event.dst, b);
        }
    }
    let target = &mut world.civs[event.dst];
    target.attacked_by = Some(event.src);
    target.attacked_at = event.t;
    target.attack_attributed = attributed;
    if target.tech_level <= 0.0 || target.population_size <= 0.0 {
        target.go_extinct(event.t, "attack");
    }
}
