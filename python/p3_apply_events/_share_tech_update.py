from math import exp

from p3_apply_events._share_strength import _share_fraction, _share_additive


def _share_tech_update(tech_level, shared_tech_level, config):
    gap = shared_tech_level - tech_level
    if gap > 0:
        updated = tech_level + _share_fraction(config.share_catchup, config) * gap
    else:
        updated = tech_level + _share_additive(config.share_backflow, config) * shared_tech_level * exp(gap / config.share_decay)
    return min(config.tech_cap, updated)
