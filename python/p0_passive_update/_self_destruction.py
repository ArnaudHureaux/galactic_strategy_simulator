from math import exp

from p0_passive_update._self_destruction_shape import _self_destruction_shape


def _self_destruction(civ, config, rng, dt):
    hazard = config.self_destruction_risk * _self_destruction_shape(civ.tech_level, config)
    if rng.random() < 1 - exp(-hazard * dt):
        civ.status = "extinct"
