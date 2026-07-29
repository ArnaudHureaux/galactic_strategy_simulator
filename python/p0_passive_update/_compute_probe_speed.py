def _compute_probe_speed(civ, config):
    return config.probe_speed_per_tech * civ.tech_level
