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


def _listening_gain_cap(config):
    return sqrt(config.seti_flux_threshold_w_m2 / config.seti_flux_threshold_cap_w_m2)


def _listening_gain(config, tech):
    """Factor on the range of the signals an observer of this tech catches, sqrt(F_human / F(tech)):
    its sensitivity F is anchored on Breakthrough Listen at humanity's level and on
    seti_flux_threshold_cap_w_m2 at tech_cap. Signal radii are those seen at F_human."""
    return _anchored(tech, 1.0, _listening_gain_cap(config), config)


def _observer_gain(civ, config):
    # Humanity listens with its observed sensitivity.
    return 1.0 if civ.is_human else _listening_gain(config, civ.tech_level)


def _tech_for_listening_gain(config, gain):
    """Tech at which _listening_gain reaches gain (inf if never)."""
    return _anchored_tech(gain, 1.0, _listening_gain_cap(config), config)


def _tech_for_signal_radius(config, radius, factor):
    """Tech at which _signal_radius reaches radius (inf if never)."""
    meters = radius * M_PER_PC
    eirp = 4.0 * pi * config.seti_flux_threshold_w_m2 * meters * meters / factor
    return _anchored_tech(eirp, config.eirp_human_w, config.eirp_cap_w, config)
