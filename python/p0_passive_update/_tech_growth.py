from p0_passive_update._growth_law import grow


def _tech_rate(civ, config):
    if civ.is_human:
        return civ.natural_tech_progress
    return (civ.natural_tech_progress * (1 - civ.colonization_aggressiveness)
            * civ.population_size ** config.tech_population_exponent)


def _tech_growth_cap(config):
    return config.tech_cap if config.tech_growth_model == "logistic" else None


def _tech_growth(civ, config, dt):
    # Exact solution of the growth law over the step, the rate held constant: the fastest explored
    # rates (~1e-5 per year, more with shares and population) are too fast for an Euler step.
    civ.tech_level = grow(civ.tech_level, _tech_rate(civ, config), _tech_growth_cap(config), dt)
    civ.tech_level = min(config.tech_cap, max(0.0, civ.tech_level))


def _human_tech(civ, config, now):
    # Humanity follows its observed trajectory exactly: its rate (up to ~5e-4 per year) is far
    # too fast for an Euler step, and events cannot perturb it (an attack or a share rejects the run).
    tech = grow(config.initial_tech_level, civ.natural_tech_progress, _tech_growth_cap(config), now - civ.birth_year)
    civ.tech_level = min(config.tech_cap, tech)