from constants import C_PC_PER_YEAR
from p3_apply_events._rates import _step_additive
from state import BeliefEntry


def _detect(world, config, now):
    world.note_detection_step(now)
    visible_civs = world.visible(now)
    visible = {c.id for c in visible_civs}
    widest_front = 0.0
    for c in visible_civs:
        widest_front = max(widest_front, c.expansion_radius)
    for civ in world.active(now):
        if civ.is_human and now < config.present_date_years - config.signal_window_years:
            continue
        reach = max(config.max_broadcast_radius + civ.expansion_radius + widest_front, civ.probe_radius)
        for other, d in world.neighbor_pairs_within(civ, reach):
            if other.id not in visible:
                continue
            # Light delay over the distance between the two homes (an upper bound for sphere edges).
            seen_at = now - d / C_PC_PER_YEAR
            view = other.state_at(seen_at)
            if view is None:
                continue
            # Signals carry from sphere edge to sphere edge.
            by_signal = view.broadcast_radius >= d - civ.expansion_radius - view.expansion_radius
            by_probe = _probe_reached(civ, seen_at, d)
            if not (by_signal or by_probe):
                continue
            _observe(world, civ, other, view, "signal" if by_signal else "probe", now)
            # A witness of an ongoing war (the victim was hit during the step of the view) loses
            # trust in the attacker at reputation_trust_drop per interaction period.
            if view.attacked_by in civ.belief and view.attacked_at > view.t - config.dt:
                entry = civ.belief[view.attacked_by]
                trust = max(0.0, entry.trust - _step_additive(config.reputation_trust_drop, config))
                if trust != entry.trust:
                    entry.trust = trust
                    world.note_trust(entry)


def _probe_reached(civ, seen_at, d):
    # The probe must have been on site at seen_at for its light-speed report to arrive now.
    own = civ.state_at(seen_at)
    return own is not None and own.probe_radius >= d


def _observe(world, civ, other, view, channel, now):
    is_competitor = civ.biochem_type == other.biochem_type
    if other.id not in civ.belief:
        entry = BeliefEntry(
            target_id=other.id,
            estimated_tech_level=view.tech_level,
            tech_level_uncertainty=0.0,
            estimated_biochem=other.biochem_type,
            is_competitor=is_competitor,
            trust=_default_trust(civ, is_competitor),
            channel=channel,
            position=other.position,
            order=len(civ.belief),
        )
        world.note_seen(entry, created=True)
        entry.last_seen_at = now
        civ.belief[other.id] = entry
    else:
        entry = civ.belief[other.id]
        world.note_seen(entry, created=False)
        entry.estimated_tech_level = view.tech_level
        entry.channel = channel
        entry.position = other.position
        entry.last_seen_at = now
    civ.recent[other.id] = entry


def _default_trust(civ, is_competitor):
    if is_competitor:
        return civ.strategy["trust_default_competitor"]
    return civ.strategy["trust_default_noncompetitor"]