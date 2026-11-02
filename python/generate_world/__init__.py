from generate_world._seed_life_in_bubbles import _seed_life_in_bubbles
from generate_world._make_humanity import _make_humanity
from state import World


def generate_world(config, streams):
    civs = _seed_life_in_bubbles(config, streams.world)
    humanity = _make_humanity(config, streams.humanity)
    civs.append(humanity)
    return World(civs=civs, humanity=humanity, now=config.last_grb_date_years, config=config)
