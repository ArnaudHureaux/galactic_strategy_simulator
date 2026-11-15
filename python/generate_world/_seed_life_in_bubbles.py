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
            civs.append(_new_civ(f"c_{len(civs)}", position, config, rng, _birth_date(config, rng)))
    return civs


def _birth_date(config, rng):
    # The sterilizing event resynchronizes life; intelligence then takes a variable time.
    spread = config.birth_spread_fraction * config.start_lookback_years
    if spread <= 0:
        return config.start_date_years
    return config.start_date_years + rng.uniform(0.0, spread)
