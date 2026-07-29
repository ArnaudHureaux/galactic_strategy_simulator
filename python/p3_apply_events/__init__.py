from p3_apply_events._share_tech_update import _share_tech_update
from p3_apply_events._share_trust_update import _share_trust_update
from p3_apply_events._attack_damage import _attack_damage


def apply_events(event, world, config):
    target = world.civ(event.dst)
    if target is None or target.status != "alive":
        return
    if event.kind == "share":
        _apply_share(event, target, world, config)
    elif event.kind == "attack":
        _apply_attack(event, target, config)


def _apply_share(event, target, world, config):
    target.tech_level = _share_tech_update(target.tech_level, event.shared_tech_level, config)
    target.natural_tech_progress = min(config.max_natural_tech_progress, target.natural_tech_progress * (1 + config.share_synergy_bonus))
    source = world.civ(event.src)
    if source is not None:
        source.natural_tech_progress = min(config.max_natural_tech_progress, source.natural_tech_progress * (1 + config.share_synergy_bonus))
    if event.src in target.belief:
        entry = target.belief[event.src]
        entry.trust = _share_trust_update(entry.trust, entry.attacked_me, config)


def _apply_attack(event, target, config):
    damage = _attack_damage(event.power, target.tech_level, config)
    target.tech_level *= (1 - damage)
    target.population_size *= (1 - damage)
    target.expansion_radius *= (1 - damage)
    if event.src in target.belief:
        entry = target.belief[event.src]
        entry.trust = 0.0
        entry.attacked_me = True
    target.attacked_by = event.src
    if target.tech_level <= 0 or target.population_size <= 0:
        target.status = "extinct"
