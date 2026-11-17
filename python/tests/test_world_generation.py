from dataclasses import replace

from config import ARCHETYPES, Config, STRATEGY_RANGES
from generate_world import generate_world
from rng import make_streams


def _world(config, seed=7):
    return generate_world(config, make_streams(seed))


def _snapshot(world):
    return [(c.id, c.position, c.biochem_type, c.strategy) for c in world.civs]


def test_streams_are_reproducible_and_independent():
    a, b = make_streams(3), make_streams(3)
    assert [a.world.random() for _ in range(5)] == [b.world.random() for _ in range(5)]
    assert make_streams(3).world.random() != make_streams(3).birth.random()
    assert make_streams(3).world.random() != make_streams(4).world.random()


def test_dynamics_parameters_do_not_change_the_initial_world():
    base = Config()
    changed = replace(base, self_destruction_risk=1e-6, artefact_detection_probability=0.9, civ_birth_rate=1e-7)
    assert _snapshot(_world(base)) == _snapshot(_world(changed))


def test_humanity_does_not_depend_on_the_other_civs():
    base = Config()
    human = _world(base).humanity
    other = _world(replace(base, civs_per_bubble=3.0)).humanity
    assert (human.position, human.biochem_type, human.strategy) == (other.position, other.biochem_type, other.strategy)


def test_world_type_fractions_drive_biochem():
    config = replace(Config(), world_type_fractions=(0.0, 1.0, 0.0), expected_bubbles=20.0)
    assert {c.biochem_type for c in _world(config).civs} == {"ammonia"}


def test_strategies_are_drawn_in_the_configured_ranges():
    narrow = {}
    for name in STRATEGY_RANGES:
        low = getattr(Config(), f"{name}_low")
        narrow[f"{name}_low"] = low
        narrow[f"{name}_high"] = low + 0.1
    config = replace(Config(), broadcast_probability=1.0, expected_bubbles=20.0, **narrow)
    civs = [c for c in _world(config).civs if not c.is_human]
    assert civs
    for c in civs:
        assert c.strategy["broadcast"] is True
        for name in STRATEGY_RANGES:
            assert narrow[f"{name}_low"] <= c.strategy[name] <= narrow[f"{name}_high"]


def test_archetypes_pin_their_traits_up_to_the_noise():
    config = replace(Config(), strategy_mix_random=0.0, strategy_mix_dark_forest=1.0, strategy_mix_cooperative=1.0,
                     strategy_noise=0.0, expected_bubbles=20.0)
    civs = [c for c in _world(config).civs if not c.is_human]
    assert {c.strategy["archetype"] for c in civs} == {"dark_forest", "cooperative"}
    for c in civs:
        pinned = ARCHETYPES[c.strategy["archetype"]]
        assert c.strategy["broadcast"] is pinned["broadcast"]
        expected_gap_max = min(config.attack_gap_max_high, max(config.attack_gap_max_low, pinned["attack_gap_max"]))
        assert c.strategy["attack_gap_max"] == expected_gap_max  # +inf is clipped to the range
        assert c.strategy["caution_k"] == pinned["caution_k"]
        assert c.strategy["trust_default_noncompetitor"] == pinned["trust_default_noncompetitor"]
    # Unpinned for every archetype: still drawn in its range.
    assert len({c.strategy["colonization_aggressiveness"] for c in civs}) == len(civs)

    noisy = [c for c in _world(replace(config, strategy_noise=0.1)).civs if not c.is_human]
    gaps = [abs(c.strategy["caution_k"] - ARCHETYPES[c.strategy["archetype"]]["caution_k"]) for c in noisy]
    assert 0 < max(gaps) <= 0.1 * (config.caution_k_high - config.caution_k_low)


def test_initial_births_are_spread_after_the_start():
    from dataclasses import replace as _replace

    from config import Config as _Config
    from generate_world import generate_world as _generate
    from rng import make_streams as _streams

    config = _replace(_Config(), expected_bubbles=20.0, birth_spread_fraction=0.5)
    civs = [c for c in _generate(config, _streams(3)).civs if not c.is_human]
    births = [c.birth_year for c in civs]
    assert len(set(births)) == len(births) > 1
    end = config.start_date_years + 0.5 * config.start_lookback_years
    assert all(config.start_date_years <= b <= end for b in births)
    # Default: the whole cohort is born at the start.
    default = _replace(config, birth_spread_fraction=0.0)
    assert all(c.birth_year == config.start_date_years
               for c in _generate(default, _streams(3)).civs if not c.is_human)


def test_a_cropped_world_keeps_the_same_civs_inside_the_crop():
    big = replace(Config(), region_radius_pc=4000.0, expected_bubbles=80.0)
    full, cropped = _world(big), _world(replace(big, crop_radius_pc=1000.0))
    inside = [c for c in full.civs if c.position[0] ** 2 + c.position[1] ** 2 <= 1000.0 ** 2]
    assert len(inside) < len(full.civs)
    assert _snapshot(cropped) == [(c.id, c.position, c.biochem_type, c.strategy) for c in inside]
