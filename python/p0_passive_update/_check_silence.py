from math import inf

from constants import C_PC_PER_YEAR
from geometry import dist


def _check_silence(world, config, now):
    human = world.humanity
    contacted = len(human.belief) > 0 or human.attacked_by is not None
    if now < config.present_date_years and contacted:
        world.rejected = True


def _received_signal_in_window(world, config):
    # Exact, dt-independent test: did any light reaching humanity during the
    # instrumental window carry a detectable signal, even from a now-dead civ?
    human = world.humanity
    present = config.present_date_years
    for civ in world.civs:
        if civ is human:
            continue
        d = dist(civ.position, human.position)
        if d > config.max_broadcast_radius:
            continue
        delay = d / C_PC_PER_YEAR
        if _was_detectable(civ, present - config.signal_window_years - delay, present - delay, d):
            return True
    return False


def _was_detectable(civ, start, end, d):
    death = inf if civ.extinct_at is None else civ.extinct_at
    next_t = civ.history_t[1:] + [inf]
    for snap, seg_end in zip(civ.history, next_t):
        if snap.broadcast_radius >= d and max(start, snap.t) < min(end, seg_end, death):
            return True
    return False


def _roll_artefacts(world, config, rng, until):
    # Contact (b): one discovery draw per civ whose probes sat near the Sun during the artefact window.
    window_start = config.present_date_years - config.artefact_window_years
    for civ in world.civs:
        arrival = civ.probe_arrived_at_human
        if arrival is None or civ.artefact_rolled or world.rejected:
            continue
        if max(arrival, window_start) > min(civ.probes_end_at(config), until):
            continue
        civ.artefact_rolled = True
        if rng.random() < config.artefact_detection_probability:
            world.rejected = True