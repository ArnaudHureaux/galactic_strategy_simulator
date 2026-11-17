from generate_world._seed_life_in_bubbles import _seed_life_in_bubbles
from generate_world._make_humanity import _make_humanity
from generate_world._sample_lens_position import _in_crop
from state import World


def generate_world(config, streams):
    civs = [c for c in _seed_life_in_bubbles(config, streams.world) if _in_crop(c.position, config)]
    humanity = _make_humanity(config, streams.humanity)
    civs.append(humanity)
    return World(civs=civs, humanity=humanity, now=config.start_date_years, config=config)
