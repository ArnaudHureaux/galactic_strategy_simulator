from generate_world._galaxy import _candidate_mean, _in_region, _poisson_count, _sample_galactic_position
from generate_world._new_civ import _new_civ
from rng import sample_ball, substream


def _seed_life_in_bubbles(config, streams):
    """Bubble centres over the whole annulus (world stream); the civs of a bubble come from a stream
    of its own, drawn only when the bubble can reach the region. Civs outside it are dropped."""
    rng = streams.world
    civs = []
    for i in range(_poisson_count(_candidate_mean(config.bubble_density_kpc2, config), rng)):
        center, kept = _sample_galactic_position(config, rng)
        if not kept or not _in_region(center, config, config.panspermia_range_pc):
            continue
        bubble = substream(streams.seed, f"bubble/{i}")
        for k in range(bubble.poisson(config.civs_per_bubble)):
            offset = sample_ball(config.panspermia_range_pc, bubble)
            position = (center[0] + offset[0], center[1] + offset[1], center[2] + offset[2])
            birth = _birth_date(config, bubble)
            civ = _new_civ(f"c_{i}_{k}", position, config, bubble, birth)
            if _in_region(position, config):
                civs.append(civ)
    return civs


def _draw_births(config, streams):
    """Every later birth, drawn up front over the whole annulus: a Poisson process in time (birth
    stream), each civ then drawn from a stream of its own. Births outside the region are dropped, so
    nested regions share theirs, and the run draws nothing at birth (same births with or without
    fast-forward)."""
    rate = _candidate_mean(config.civ_birth_rate_kpc2, config)
    if rate <= 0:
        return []
    rng = streams.birth
    births = []
    j = 0
    elapsed = rng.exponential(1.0)
    while True:
        birth = config.start_date_years + elapsed / rate
        if birth >= config.present_date_years:
            return births
        position, kept = _sample_galactic_position(config, rng)
        if kept and _in_region(position, config):
            births.append(_new_civ(f"b_{j}", position, config, substream(streams.seed, f"birth/{j}"), birth))
        j += 1
        elapsed += rng.exponential(1.0)


def _birth_date(config, rng):
    # The sterilizing event resynchronizes life; intelligence then takes a variable time.
    spread = config.birth_spread_fraction * config.start_lookback_years
    if spread <= 0:
        return config.start_date_years
    return config.start_date_years + rng.uniform(0.0, spread)
