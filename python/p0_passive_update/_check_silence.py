from math import exp, inf, log1p

from constants import C_PC_PER_YEAR
from geometry import dist
from p0_passive_update._advance_fronts import _holds


def _check_silence(world, config, now):
    human = world.humanity
    if now >= config.present_date_years:
        return
    if human.attacked_by is not None:
        world.reject("attacked", now)
    elif now >= config.present_date_years - config.artefact_window_years and _colonized(world, now):
        world.reject("colonized", now)
    elif human.belief:
        # Name the channel of the first contact.
        channel = next(iter(human.belief.values())).channel
        world.reject(f"contact_{channel}", now)


def _colonized(world, now):
    # Hart's argument: a colonization front holding the Sun since the Solar System exists would be seen.
    human = world.humanity
    for civ in world.active(now):
        if civ is not human and _holds(world, civ, human.position, now):
            return True
    return False


def _received_signal_in_window(world, config, rng):
    """Exact, dt-independent survey test: did light reaching humanity while it listens carry a
    signal above the survey sensitivity (even from a now-dead civ), and did the surveys catch it?
    The surveys observed only a share c(d) of the stars at distance d (seti coverage); each system of
    the source is caught with probability c (leak, continuous) or c * beacon_duty (beacon), one draw
    per exposed civ. Signals carry from sphere edge to sphere edge (light delay between homes)."""
    human = world.humanity
    present = config.present_date_years
    for civ in world.civs:
        if civ is human:
            continue
        d = dist(civ.position, human.position)
        delay = d / C_PC_PER_YEAR
        leak_n, beacon_n, edge = _exposure(civ, present - config.humanity_listening_years - delay, present - delay,
                                           d - human.expansion_radius)
        if leak_n == 0 and beacon_n == 0:
            continue
        c = _seti_coverage(edge, config)
        miss = 1.0
        if leak_n > 0:
            miss *= _miss(c, leak_n)
        if beacon_n > 0:
            miss *= _miss(c * config.beacon_duty, beacon_n)
        if miss <= 0.0 or (miss < 1.0 and rng.random() >= miss):
            return True
    return False


def _miss(q, n):
    # Probability that none of n systems is caught, each with probability q.
    if q >= 1.0:
        return 0.0
    return exp(n * log1p(-q))


def _seti_coverage(d, config):
    """Share of the stars at distance d (pc) that humanity's surveys observed: every star within
    seti_complete_radius_pc (Isaacson et al. 2017), then about 1 in 27 within 50 pc and 1 in 2500
    beyond (Wlodarczyk-Sroka et al. 2020 against the Gaia census of nearby stars)."""
    if d <= config.seti_complete_radius_pc:
        return 1.0
    if d <= 50.0:
        return config.seti_coverage_50pc
    return config.seti_coverage_beyond


def _exposure(civ, start, end, d):
    """(systems seen through the leak, systems seen through the beacon, distance of the nearest
    system) over the light emitted between start and end that reaches the observer at distance d."""
    death = inf if civ.extinct_at is None else civ.extinct_at
    next_t = civ.history_t[1:] + [inf]
    leak_n = 0.0
    beacon_n = 0.0
    edge = d
    for snap, seg_end in zip(civ.history, next_t):
        if max(start, snap.t) >= min(end, seg_end, death):
            continue
        gap = d - snap.expansion_radius
        if snap.beacon_radius >= gap:
            beacon_n = max(beacon_n, snap.nb_of_world)
            edge = min(edge, max(0.0, gap))
        if snap.leak_radius >= gap:
            leak_n = max(leak_n, snap.nb_of_world)
            edge = min(edge, max(0.0, gap))
    return leak_n, beacon_n, edge


def _roll_artefacts(world, config, rng, until):
    # Contact (b): one discovery draw per civ whose probes sat near the Sun during the artefact window
    # (working, or inert but still there: artefacts_end_at).
    # The draw happens when the probes are first there during the window: the least advanced (least
    # discreet) of them set the odds, against the tech humanity searches with today.
    window_start = config.present_date_years - config.artefact_window_years
    for civ in world.civs:
        arrival = civ.probe_arrived_at_human
        if arrival is None or civ.artefact_rolled or world.rejected:
            continue
        if max(arrival, window_start) > min(civ.artefacts_end_at(config), until):
            continue
        civ.artefact_rolled = True
        stealth = config.artefact_stealth_per_tech * max(0.0, _owner_tech(civ) - config.humanity_present_tech)
        if rng.random() < config.artefact_detection_probability * exp(-stealth):
            world.reject("artefact", until)


def _owner_tech(civ):
    # A dead civ is never updated again: its last snapshot holds its tech at death.
    if civ.extinct_at is not None and civ.history:
        return civ.history[-1].tech_level
    return civ.tech_level