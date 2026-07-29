from p0_passive_update._danger_window import _danger_window


def _self_destruction_shape(tech_level, config):
    if config.self_destruction_shape == "constant":
        return 1.0
    if config.self_destruction_shape == "increasing":
        return tech_level / config.tech_cap
    return _danger_window(tech_level, config)
