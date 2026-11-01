from p0_passive_update._growth_law import grow


def _population_capacity(civ, config):
    if config.population_growth_model == "logistic":
        return config.population_per_world * civ.nb_of_world
    return None


def _population_growth(civ, config, dt, exact=False):
    r = civ.natural_population_growth
    capacity = _population_capacity(civ, config)
    if exact:
        civ.population_size = grow(civ.population_size, r, capacity, dt)
    elif capacity is not None:
        civ.population_size += r * civ.population_size * (1 - civ.population_size / capacity) * dt
    else:
        civ.population_size += r * civ.population_size * dt
    if capacity is not None:
        civ.population_size = min(capacity, max(0.0, civ.population_size))
    else:
        civ.population_size = max(0.0, civ.population_size)
