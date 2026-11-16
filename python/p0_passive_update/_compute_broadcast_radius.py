from math import pi, sqrt

from constants import M_PER_PC
from p0_passive_update._anchored import _anchored, _anchored_tech


def _compute_signal_radii(civ, config, now):
    """(leak radius, beacon radius) in pc. Every civ leaks (EIRP * passive_leakage_factor, continuous
    and in all directions); a civ that broadcasts also has a beacon (full EIRP, intermittent and beamed)."""
    # Humanity's technosignatures only exist since it leaks radio signals.
    if civ.is_human and now < config.present_date_years - config.humanity_leak_years:
        return 0.0, 0.0
    leak = _signal_radius(config, civ.tech_level, _leak_factor(civ, config))
    beacon = _signal_radius(config, civ.tech_level, 1.0) if civ.strategy["broadcast"] else 0.0
    return leak, beacon


def _leak_factor(civ, config):
    # Humanity's leakage is observed; the other civs' is explored.
    return config.humanity_leakage_factor if civ.is_human else config.passive_leakage_factor


def _signal_radius(config, tech, factor):
    """Distance (pc) at which a signal of factor * EIRP(tech) stays above the observers' sensitivity:
    EIRP = 4 pi d^2 F_min, with the EIRP anchored on humanity (see _anchored)."""
    if tech <= 0:
        return 0.0
    eirp = _anchored(tech, config.eirp_human_w, config.eirp_cap_w, config) * factor
    return sqrt(eirp / (4.0 * pi * config.seti_flux_threshold_w_m2)) / M_PER_PC


def _tech_for_signal_radius(config, radius, factor):
    """Tech at which _signal_radius reaches radius (inf if never)."""
    meters = radius * M_PER_PC
    eirp = 4.0 * pi * config.seti_flux_threshold_w_m2 * meters * meters / factor
    return _anchored_tech(eirp, config.eirp_human_w, config.eirp_cap_w, config)
