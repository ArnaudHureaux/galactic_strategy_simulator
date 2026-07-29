from generate_world._seed_life_in_bubbles import _seed_life_in_bubbles
from generate_world._make_humanity import _make_humanity
from state import World


def generate_world(config, rng):
    civs = _seed_life_in_bubbles(config, rng)
    humanity = _make_humanity(config, rng)
    civs.append(humanity)
    return World(civs=civs, humanity=humanity, now=config.last_grb_date_years, config=config)
