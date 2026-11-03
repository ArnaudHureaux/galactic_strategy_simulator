def _compute_broadcast_radius(civ, config, now):
    # Humanity's technosignatures only exist since the start of the signal window.
    if civ.is_human and now < config.present_date_years - config.signal_window_years:
        return 0.0
    active_radius = config.emit_radius_per_tech * civ.tech_level
    if civ.strategy["broadcast"]:
        return active_radius
    return active_radius * config.passive_leakage_factor
