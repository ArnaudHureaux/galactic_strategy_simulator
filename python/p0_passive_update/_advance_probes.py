from geometry import dist
from p0_passive_update._compute_probe_speed import _probe_range


def _advance_probes(civ, human, config, now, dt, speed=None):
    # Working probes are launched from the civ's territory and work for a limited time: their sphere
    # is capped at the territory plus their range (it shrinks if the range does, old probes dying).
    speed = civ.probe_speed if speed is None else speed
    before = civ.probe_radius
    reach = civ.expansion_radius + _probe_range(config, civ.tech_level)
    civ.probe_radius = min(config.max_probe_radius, before + speed * dt, reach)
    if civ is human or civ.probe_arrived_at_human is not None:
        return
    d = dist(civ.position, human.position)
    if civ.probe_radius >= d:
        # Interpolate the crossing inside the step so arrival time does not depend on dt.
        frac = max(0.0, (d - before) / (civ.probe_radius - before)) if civ.probe_radius > before else 0.0
        civ.probe_arrived_at_human = now - dt + frac * dt
