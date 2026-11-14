from p3_apply_events._share_tech_update import _share_tech_update
from p3_apply_events._share_trust_update import _share_trust_update
from p3_apply_events._rates import _step_growth
from p3_apply_events._attack_damage import _attack_damage
from p0_passive_update._advance_fronts import _update_nb_of_world


def apply_events(event, world, config):
    target = world.civ(event.dst)
    if target is None or target.status != "alive":
        return
    if event.kind in ("share", "implicit_share") and target is world.humanity:
        # Receiving technology is a contact humanity would have noticed.
        world.reject("contact_share", event.t)
        return
    if event.kind == "share":
        _apply_share(event, target, world, config)
    elif event.kind == "implicit_share":
        _apply_share_relationship(event, target, world, config)
    elif event.kind == "attack":
        _apply_attack(event, target, world)


def _apply_share(event, target, world, config):
    target.tech_level = _share_tech_update(target.tech_level, event.shared_tech_level, config)
    _apply_share_relationship(event, target, world, config)


def _apply_share_relationship(event, target, world, config):
    cap = config.max_natural_tech_progress
    source = world.civ(event.src)
    # Most relationships are saturated: skip the synergy update when it cannot change anything.
    if target.natural_tech_progress != cap or (source is not None and source.natural_tech_progress != cap):
        synergy = _step_growth(config.share_synergy_bonus, config)
        target.natural_tech_progress = min(cap, target.natural_tech_progress * synergy)
        if source is not None:
            source.natural_tech_progress = min(cap, source.natural_tech_progress * synergy)
    entry = target.belief.get(event.src)
    if entry is not None:
        trust = _share_trust_update(entry.trust, entry.attacked_me, config)
        # Converged relationships (trust 1.0) are the common case: only report actual changes.
        if trust != entry.trust:
            entry.trust = trust
            world.note_trust(entry)


def _apply_attack(event, target, world):
    damage = _attack_damage(event.power, target.tech_level, world.config)
    target.tech_level *= (1 - damage)
    target.population_size *= (1 - damage)
    target.expansion_radius *= (1 - damage)
    _update_nb_of_world(target, world.config)
    if event.src in target.belief:
        entry = target.belief[event.src]
        if entry.trust != 0.0 or not entry.attacked_me:
            entry.trust = 0.0
            entry.attacked_me = True
            world.note_trust(entry)
    target.attacked_by = event.src
    target.attacked_at = event.t
    if target.tech_level <= 0 or target.population_size <= 0:
        target.go_extinct(event.t, "attack")
