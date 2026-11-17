from generate_world._seed_life_in_bubbles import _draw_births, _seed_life_in_bubbles
from generate_world._make_humanity import _make_humanity
from state import World


def generate_world(config, streams):
    # Initial civs, then every later birth (taking part once their birth_year comes), humanity last.
    civs = _seed_life_in_bubbles(config, streams) + _draw_births(config, streams)
    humanity = _make_humanity(config, streams.humanity)
    civs.append(humanity)
    return World(civs=civs, humanity=humanity, now=config.start_date_years, config=config)
