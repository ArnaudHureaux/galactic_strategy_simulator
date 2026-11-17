from math import exp

from p0_passive_update._self_destruction_shape import _self_destruction_shape


def _self_destruction(civ, config, rng, dt):
    return rng.random() < 1 - exp(-_self_destruction_hazard(civ, config) * dt)


def _self_destruction_hazard(civ, config):
    # A share self_destruction_correlation of catastrophes reaches every world; the others stay local
    # to one world and only end a single-world civ (the loss of one world among several is neglected).
    # The local share fades linearly from 1 world to 2, since nb_of_world is continuous.
    local = config.self_destruction_correlation
    exposed = local + (1.0 - local) * min(1.0, max(0.0, 2.0 - civ.nb_of_world))
    return config.self_destruction_risk * _self_destruction_shape(civ.tech_level, config) * exposed
