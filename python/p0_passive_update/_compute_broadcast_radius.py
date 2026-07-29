def _compute_broadcast_radius(civ, config):
    active_radius = config.emit_radius_per_tech * civ.tech_level
    if civ.strategy["broadcast"]:
        return active_radius
    return active_radius * config.passive_leakage_factor
