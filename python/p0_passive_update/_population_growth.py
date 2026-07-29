def _population_growth(civ, config):
    r = civ.natural_population_growth
    capacity = config.population_per_world * civ.nb_of_world
    if config.population_growth_model == "logistic":
        civ.population_size += r * civ.population_size * (1 - civ.population_size / capacity) * config.dt
        civ.population_size = min(capacity, max(0.0, civ.population_size))
    else:
        civ.population_size += r * civ.population_size * config.dt
        civ.population_size = max(0.0, civ.population_size)
