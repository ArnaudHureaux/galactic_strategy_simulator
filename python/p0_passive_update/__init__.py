from generate_world._sample_lens_position import _sample_lens_position
from generate_world._new_civ import _new_civ
from p0_passive_update._tech_growth import _tech_growth
from p0_passive_update._population_growth import _population_growth
from p0_passive_update._compute_broadcast_radius import _compute_broadcast_radius
from p0_passive_update._compute_probe_speed import _compute_probe_speed
from p0_passive_update._self_destruction import _self_destruction
from p0_passive_update._detect import _detect
from p0_passive_update._check_silence import _check_silence, _received_signal_in_window, _roll_artefacts
from p0_passive_update._advance_probes import _advance_probes


def passive_update(world, config, now, streams, dt=None, jump=None):
    # dt is the time elapsed since the previous step; jump carries the events forced by fast_forward.
    dt = config.dt if dt is None else dt
    if jump is None:
        born = streams.birth.random() < config.civ_birth_rate * dt
    else:
        born = jump.birth
    if born:
        position = _sample_lens_position(config, streams.birth)
        world.add_civ(_new_civ(f"c_{len(world.civs)}", position, config, streams.birth, now))

    horizon = world.history_horizon()
    for civ in world.active(now):
        # A civ born during this step only lives one regular step of it.
        step = min(dt, now - civ.birth_year + config.dt)
        exact = jump is not None and step > config.dt
        exact_tech = exact and civ.id not in jump.frozen_tech
        exact_pop = exact and civ.id not in jump.frozen_pop
        speed_before = civ.probe_speed
        _tech_growth(civ, config, step if exact_tech else min(step, config.dt), exact_tech)
        _population_growth(civ, config, step if exact_pop else min(step, config.dt), exact_pop)
        civ.broadcast_radius = _compute_broadcast_radius(civ, config)
        civ.probe_speed = _compute_probe_speed(civ, config)
        _advance_probes(civ, world.humanity, config, now, step, (speed_before + civ.probe_speed) / 2 if exact else None)
        civ.record(now, horizon)

    if jump is None:
        for civ in world.orphan_probes(now):
            _advance_probes(civ, world.humanity, config, now, dt)
    else:
        # Orphan probes expiring inside the jump still travel until their end of life.
        start = now - dt
        for civ in world.orphan_probes(start):
            end = min(now, civ.probes_end_at(config))
            _advance_probes(civ, world.humanity, config, end, end - start)

    _detect(world, config, now)

    for civ in world.active(now):
        if jump is None:
            destroyed = _self_destruction(civ, config, streams.destruction, dt)
        else:
            destroyed = civ.id in jump.extinctions
        if destroyed:
            civ.go_extinct(now, "self_destruction")
        elif civ.tech_level <= 0 or civ.population_size <= 0:
            civ.go_extinct(now, "collapse")

    _roll_artefacts(world, config, streams.artefact, now)
    _check_silence(world, config, now)


def final_silence_check(world, config, streams):
    _roll_artefacts(world, config, streams.artefact, config.present_date_years)
    if _received_signal_in_window(world, config):
        world.reject("signal_in_window", config.present_date_years)
