from math import sqrt

from constants import C_PC_PER_YEAR
from p0_passive_update._anchored import _anchored


def _compute_probe_speed(civ, config):
    return _probe_speed(config, civ.tech_level)


def _probe_speed(config, tech):
    """Probe speed (pc/year). The anchored law (see _anchored) applies to the kinetic energy per unit
    of rest mass energy, gamma - 1, from Voyager 1 for humanity to probe_speed_cap_c at the cap: each
    tech level multiplies the energy given to a kilogram of probe by the same factor, and the speed
    follows special relativity, so it rises fast at first and saturates below c."""
    if tech <= 0:
        return 0.0
    energy = _anchored(tech, _kinetic(config.probe_speed_human_c), _kinetic(config.probe_speed_cap_c), config)
    return _beta(energy) * C_PC_PER_YEAR


def _kinetic(beta):
    # gamma - 1 for a speed beta (fraction of c), written without cancellation at low speed.
    s = sqrt(1.0 - beta * beta)
    return beta * beta / (s * (1.0 + s))


def _beta(kinetic):
    # Speed (fraction of c) for a kinetic energy gamma - 1: sqrt(1 - 1 / gamma^2).
    return sqrt(kinetic * (kinetic + 2.0)) / (1.0 + kinetic)


def _probe_function_years(config, tech):
    """How long a probe launched at this tech keeps working (Voyager 1: about 50 years)."""
    return _anchored(tech, config.probe_function_human_years, config.probe_function_cap_years, config)


def _probe_persistence_years(config, tech):
    """How long a probe launched at this tech persists as an artefact (at least while it works)."""
    persistence = _anchored(tech, config.probe_persistence_human_years, config.probe_persistence_cap_years, config)
    return max(persistence, _probe_function_years(config, tech))


def _probe_range(config, tech):
    """Distance (pc) a working probe can cover from where it is launched: speed * functioning time."""
    if tech <= 0:
        return 0.0
    return _probe_speed(config, tech) * _probe_function_years(config, tech)
