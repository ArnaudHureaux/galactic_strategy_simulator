from geometry import dist


def _advance_probes(civ, human, config, now, dt, speed=None):
    speed = civ.probe_speed if speed is None else speed
    before = civ.probe_radius
    civ.probe_radius = min(config.max_probe_radius, before + speed * dt)
    if civ is human or civ.probe_arrived_at_human is not None:
        return
    d = dist(civ.position, human.position)
    if civ.probe_radius >= d:
        # Interpolate the crossing inside the step so arrival time does not depend on dt.
        frac = max(0.0, (d - before) / (civ.probe_radius - before)) if civ.probe_radius > before else 0.0
        civ.probe_arrived_at_human = now - dt + frac * dt
