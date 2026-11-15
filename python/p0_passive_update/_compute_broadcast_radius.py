from math import pi, sqrt

from constants import M_PER_PC
from p0_passive_update._anchored import _anchored, _anchored_tech


def _compute_broadcast_radius(civ, config, now):
    # Humanity's technosignatures only exist since the start of the signal window.
    if civ.is_human and now < config.present_date_years - config.signal_window_years:
        return 0.0
    return _broadcast_radius(civ, config, civ.tech_level)


def _broadcast_radius(civ, config, tech):
    """Distance (pc) at which the civ's signal is still above the observers' sensitivity:
    EIRP = 4 pi d^2 F_min, with the EIRP anchored on humanity (see _anchored)."""
    if tech <= 0:
        return 0.0
    eirp = _anchored(tech, config.eirp_human_w, config.eirp_cap_w, config) * _leakage(civ, config)
    return sqrt(eirp / (4.0 * pi * config.seti_flux_threshold_w_m2)) / M_PER_PC


def _tech_for_broadcast_radius(civ, config, radius):
    """Tech at which the broadcast radius reaches radius (inf if never)."""
    meters = radius * M_PER_PC
    eirp = 4.0 * pi * config.seti_flux_threshold_w_m2 * meters * meters / _leakage(civ, config)
    return _anchored_tech(eirp, config.eirp_human_w, config.eirp_cap_w, config)


def _leakage(civ, config):
    return 1.0 if civ.strategy["broadcast"] else config.passive_leakage_factor
