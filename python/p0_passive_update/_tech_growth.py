from p0_passive_update._growth_law import grow


def _tech_rate(civ):
    return civ.natural_tech_progress * (1 - civ.colonization_aggressiveness) * civ.population_size


def _tech_growth_cap(config):
    return config.tech_cap if config.tech_growth_model == "logistic" else None


def _tech_growth(civ, config, dt, exact=False):
    r = _tech_rate(civ)
    if exact:
        civ.tech_level = grow(civ.tech_level, r, _tech_growth_cap(config), dt)
    elif config.tech_growth_model == "logistic":
        civ.tech_level += r * civ.tech_level * (1 - civ.tech_level / config.tech_cap) * dt
    else:
        civ.tech_level += r * civ.tech_level * dt
    civ.tech_level = min(config.tech_cap, max(0.0, civ.tech_level))
