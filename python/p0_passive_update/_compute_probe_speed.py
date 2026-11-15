from constants import C_PC_PER_YEAR
from p0_passive_update._anchored import _anchored


def _compute_probe_speed(civ, config):
    return _probe_speed(config, civ.tech_level)


def _probe_speed(config, tech):
    """Probe speed (pc/year), anchored on Voyager 1 for humanity (see _anchored)."""
    if tech <= 0:
        return 0.0
    return _anchored(tech, config.probe_speed_human_c, config.probe_speed_cap_c, config) * C_PC_PER_YEAR
