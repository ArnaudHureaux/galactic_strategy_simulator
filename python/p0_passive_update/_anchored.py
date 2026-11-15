from math import inf, log


def _anchored(tech, human_value, cap_value, config):
    """Effect of a tech level, calibrated by two anchors (phase 2, points 4 and 11): human_value at
    humanity's present tech (observed) and cap_value at tech_cap. Each tech level multiplies the
    effect by the same factor; beyond the cap the effect stays at cap_value."""
    present = config.humanity_present_tech
    x = (min(tech, config.tech_cap) - present) / (config.tech_cap - present)
    return human_value * (cap_value / human_value) ** x


def _anchored_tech(value, human_value, cap_value, config):
    """Inverse of _anchored: the tech level at which the effect reaches value (inf if never)."""
    if value >= cap_value:
        return inf
    present = config.humanity_present_tech
    x = log(value / human_value) / log(cap_value / human_value)
    return present + x * (config.tech_cap - present)
