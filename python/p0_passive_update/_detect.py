from math import inf, log, log1p

from constants import C_PC_PER_YEAR
from p0_passive_update._growth_law import grow
from p0_passive_update._tech_growth import _tech_growth_cap
from p3_apply_events._rates import _step_additive
from state import BeliefEntry


def _detect(world, config, now, dt, rng):
    # dt: time since the previous detection step, over which beacon exposures accumulate.
    world.note_detection_step(now)
    visible_civs = world.visible(now)
    visible = {c.id for c in visible_civs}
    widest_front = 0.0
    for c in visible_civs:
        widest_front = max(widest_front, c.expansion_radius)
    for civ in world.active(now):
        # Humanity only observes (through its own probes) since it searches the sky.
        if civ.is_human and now < config.present_date_years - config.humanity_listening_years:
            continue
        reach = max(world.widest_broadcast + civ.expansion_radius + widest_front, civ.probe_radius)
        for other, d in world.neighbor_pairs_within(civ, reach):
            if other.id not in visible:
                continue
            # Light delay over the distance between the two homes (an upper bound for sphere edges).
            seen_at = now - d / C_PC_PER_YEAR
            view = other.state_at(seen_at)
            if view is None:
                continue
            # Signals carry from sphere edge to sphere edge. Humanity's signal detection is the
            # survey test of _check_silence: here it only sees through its own probes.
            gap = d - civ.expansion_radius - view.expansion_radius
            by_probe = _probe_reached(civ, seen_at, d)
            by_signal = False
            if not civ.is_human:
                by_signal = view.leak_radius >= gap
                if not (by_signal or by_probe) and view.beacon_radius >= gap:
                    by_signal = _beacon_caught(civ, other, view, config, dt, rng)
            if not (by_signal or by_probe):
                continue
            uncertainty = _projected_progress(view.tech_level, view.tech_rate, d / C_PC_PER_YEAR, config)
            _observe(world, civ, other, view, uncertainty, "signal" if by_signal else "probe", now)
            # A witness of an ongoing war (the victim was hit during the step of the view) loses
            # trust in the attacker at reputation_trust_drop per interaction period, if the
            # victim identified it.
            if (view.attack_attributed and view.attacked_by in civ.belief
                    and view.attacked_at > view.t - config.dt):
                entry = civ.belief[view.attacked_by]
                trust = max(0.0, entry.trust - _step_additive(config.reputation_trust_drop, config))
                if trust != entry.trust:
                    entry.trust = trust
                    world.note_trust(entry)


def _beacon_caught(civ, other, view, config, dt, rng):
    """Within a beacon sphere, detection is a coincidence (beam towards the observer, in its band,
    while it listens): each system of the source, each interaction period, is caught with
    probability listen_coverage * beacon_duty. The exposure threshold is drawn once per pair
    (Exp(1)) and the hazard accumulates while the pair is exposed; once caught, the observer keeps
    seeing the source while it stays within the sphere."""
    exposure = civ.exposures.get(other.id)
    if exposure is None:
        exposure = [-log(1.0 - rng.random()), 0.0]
        civ.exposures[other.id] = exposure
    if exposure[1] < exposure[0]:
        exposure[1] += _beacon_hazard(view.nb_of_world, config) * dt
    return exposure[1] >= exposure[0]


def _beacon_hazard(nb_of_world, config):
    # Detection rate (per year) of a beacon covering nb_of_world systems.
    q = config.listen_coverage * config.beacon_duty
    if q >= 1.0:
        return inf
    return -nb_of_world * log1p(-q) / config.interaction_period_years


def _probe_reached(civ, seen_at, d):
    # The probe must have been on site at seen_at for its light-speed report to arrive now.
    own = civ.state_at(seen_at)
    return own is not None and own.probe_radius >= d


def _projected_progress(tech_level, tech_rate, delay, config):
    # Technological explosion: the tech a target may have gained while its light travelled to
    # the observer, at the growth rate seen with it. Cautious civs discount their advantage by it.
    return grow(tech_level, tech_rate, _tech_growth_cap(config), delay) - tech_level


def _observe(world, civ, other, view, uncertainty, channel, now):
    is_competitor = civ.biochem_type == other.biochem_type
    if other.id not in civ.belief:
        entry = BeliefEntry(
            target_id=other.id,
            estimated_tech_level=view.tech_level,
            tech_level_uncertainty=uncertainty,
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
        entry.tech_level_uncertainty = uncertainty
        entry.channel = channel
        entry.position = other.position
        entry.last_seen_at = now
    civ.recent[other.id] = entry


def _default_trust(civ, is_competitor):
    if is_competitor:
        return civ.strategy["trust_default_competitor"]
    return civ.strategy["trust_default_noncompetitor"]