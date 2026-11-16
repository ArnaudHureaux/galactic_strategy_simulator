from constants import C_PC_PER_YEAR
from p0_passive_update._anchored import _anchored


def _compute_probe_speed(civ, config):
    return _probe_speed(config, civ.tech_level)


def _probe_speed(config, tech):
    """Probe speed (pc/year), anchored on Voyager 1 for humanity (see _anchored)."""
    if tech <= 0:
        return 0.0
    return _anchored(tech, config.probe_speed_human_c, config.probe_speed_cap_c, config) * C_PC_PER_YEAR


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
