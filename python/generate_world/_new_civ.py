from state import Civilisation
from generate_world._sample_strategy import _sample_strategy


def _new_civ(civ_id, position, config, rng, birth_year):
    strategy = _sample_strategy(config, rng)
    return Civilisation(
        id=civ_id,
        position=position,
        birth_year=birth_year,
        status="alive",
        biochem_type=rng.weighted_choice(config.biochem_types, config.world_type_fractions),
        tech_level=config.initial_tech_level,
        population_size=config.initial_population,
        nb_of_world=1.0,
        natural_tech_progress=config.natural_tech_progress_mean * _spread(config.natural_tech_progress_spread, rng),
        natural_population_growth=config.natural_population_growth_mean * _spread(
            config.natural_population_growth_spread, rng),
        colonization_aggressiveness=strategy["colonization_aggressiveness"],
        strategy=strategy,
    )


def _spread(spread, rng):
    return rng.uniform(1 - spread, 1 + spread)
