from math import exp, inf

from constants import C_PC_PER_YEAR
from geometry import dist


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
        if civ is not human and civ.expansion_radius >= dist(civ.position, human.position):
            return True
    return False


def _received_signal_in_window(world, config):
    # Exact, dt-independent test: did any light reaching humanity during the
    # instrumental window carry a detectable signal, even from a now-dead civ?
    # Signals carry from sphere edge to sphere edge (light delay over the distance between homes).
    human = world.humanity
    present = config.present_date_years
    for civ in world.civs:
        if civ is human:
            continue
        d = dist(civ.position, human.position)
        delay = d / C_PC_PER_YEAR
        if _was_detectable(civ, present - config.signal_window_years - delay, present - delay,
                           d - human.expansion_radius):
            return True
    return False


def _was_detectable(civ, start, end, d):
    death = inf if civ.extinct_at is None else civ.extinct_at
    next_t = civ.history_t[1:] + [inf]
    for snap, seg_end in zip(civ.history, next_t):
        if snap.broadcast_radius >= d - snap.expansion_radius and max(start, snap.t) < min(end, seg_end, death):
            return True
    return False


def _roll_artefacts(world, config, rng, until):
    # Contact (b): one discovery draw per civ whose probes sat near the Sun during the artefact window.
    # The draw happens when the probes are first there during the window: the least advanced (least
    # discreet) of them set the odds, against the tech humanity searches with today.
    window_start = config.present_date_years - config.artefact_window_years
    for civ in world.civs:
        arrival = civ.probe_arrived_at_human
        if arrival is None or civ.artefact_rolled or world.rejected:
            continue
        if max(arrival, window_start) > min(civ.probes_end_at(config), until):
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