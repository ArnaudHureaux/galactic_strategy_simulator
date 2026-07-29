from generate_world._sample_lens_position import _sample_lens_position
from generate_world._new_civ import _new_civ
from p0_passive_update._tech_growth import _tech_growth
from p0_passive_update._population_growth import _population_growth
from p0_passive_update._compute_broadcast_radius import _compute_broadcast_radius
from p0_passive_update._compute_probe_speed import _compute_probe_speed
from p0_passive_update._self_destruction import _self_destruction
from p0_passive_update._detect import _detect
from p0_passive_update._check_silence import _check_silence


def passive_update(world, config, now, rng):
    if rng.random() < config.civ_birth_rate * config.dt:
        position = _sample_lens_position(config, rng)
        world.add_civ(_new_civ(f"c_{len(world.civs)}", position, config, rng, now))

    for civ in world.active(now):
        _tech_growth(civ, config)
        _population_growth(civ, config)
        civ.broadcast_radius = _compute_broadcast_radius(civ, config)
        civ.probe_speed = _compute_probe_speed(civ, config)
        civ.probe_radius = min(config.max_probe_radius, civ.probe_radius + civ.probe_speed * config.dt)

    _detect(world, config, now)

    for civ in world.active(now):
        _self_destruction(civ, config, rng, config.dt)
        if civ.tech_level <= 0 or civ.population_size <= 0:
            civ.status = "extinct"

    _check_silence(world, config, now)
