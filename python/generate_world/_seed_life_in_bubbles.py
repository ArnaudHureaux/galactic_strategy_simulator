from generate_world._sample_lens_position import _sample_lens_position
from generate_world._new_civ import _new_civ
from rng import sample_ball


def _seed_life_in_bubbles(config, rng):
    civs = []
    for _ in range(rng.poisson(config.expected_bubbles)):
        center = _sample_lens_position(config, rng)
        for _ in range(rng.poisson(config.civs_per_bubble)):
            offset = sample_ball(config.panspermia_range_pc, rng)
            position = (center[0] + offset[0], center[1] + offset[1], center[2] + offset[2])
            civs.append(_new_civ(f"c_{len(civs)}", position, config, rng, config.last_grb_date_years))
    return civs
