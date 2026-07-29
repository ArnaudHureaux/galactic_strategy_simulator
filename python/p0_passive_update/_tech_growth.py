def _tech_growth(civ, config):
    r = civ.natural_tech_progress * (1 - civ.colonization_aggressiveness) * civ.population_size
    if config.tech_growth_model == "logistic":
        civ.tech_level += r * civ.tech_level * (1 - civ.tech_level / config.tech_cap) * config.dt
    else:
        civ.tech_level += r * civ.tech_level * config.dt
    civ.tech_level = min(config.tech_cap, max(0.0, civ.tech_level))
