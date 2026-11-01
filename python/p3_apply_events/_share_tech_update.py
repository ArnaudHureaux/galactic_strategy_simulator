from math import exp


def _share_tech_update(tech_level, shared_tech_level, config):
    gap = shared_tech_level - tech_level
    if gap > 0:
        updated = tech_level + config.share_catchup * gap
    else:
        updated = tech_level + config.share_backflow * shared_tech_level * exp(gap / config.share_decay)
    return min(config.tech_cap, updated)
