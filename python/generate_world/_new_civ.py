from state import Civilisation
from generate_world._sample_strategy import _sample_strategy


def _new_civ(civ_id, position, config, rng, birth_year):
    strategy = _sample_strategy(rng)
    return Civilisation(
        id=civ_id,
        position=position,
        birth_year=birth_year,
        status="alive",
        biochem_type=rng.choice(config.biochem_types),
        tech_level=config.initial_tech_level,
        population_size=config.initial_population,
        nb_of_world=1,
        natural_tech_progress=config.natural_tech_progress_mean * rng.uniform(0.5, 1.5),
        natural_population_growth=config.natural_population_growth_mean * rng.uniform(0.5, 1.5),
        colonization_aggressiveness=strategy["colonization_aggressiveness"],
        strategy=strategy,
    )
