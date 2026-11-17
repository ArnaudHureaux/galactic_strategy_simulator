import pytest
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
    changed = replace(base, self_destruction_risk=1e-6, artefact_detection_probability=0.9, civ_birth_rate_kpc2=1e-7)
    initial = lambda world: [c for c in _snapshot(world) if c[0].startswith("c_")]
    assert initial(_world(base)) == initial(_world(changed))


def test_humanity_does_not_depend_on_the_other_civs():
    base = Config()
    human = _world(base).humanity
    other = _world(replace(base, civs_per_bubble=3.0)).humanity
    assert (human.position, human.biochem_type, human.strategy) == (other.position, other.biochem_type, other.strategy)


def test_world_type_fractions_drive_biochem():
    config = replace(Config(), world_type_fractions=(0.0, 1.0, 0.0), bubble_density_kpc2=6.4)
    assert {c.biochem_type for c in _world(config).civs} == {"ammonia"}


def test_strategies_are_drawn_in_the_configured_ranges():
    narrow = {}
    for name in STRATEGY_RANGES:
        low = getattr(Config(), f"{name}_low")
        narrow[f"{name}_low"] = low
        narrow[f"{name}_high"] = low + 0.1
    config = replace(Config(), broadcast_probability=1.0, bubble_density_kpc2=6.4, **narrow)
    civs = [c for c in _world(config).civs if not c.is_human]
    assert civs
    for c in civs:
        assert c.strategy["broadcast"] is True
        for name in STRATEGY_RANGES:
            assert narrow[f"{name}_low"] <= c.strategy[name] <= narrow[f"{name}_high"]


def test_archetypes_pin_their_traits_up_to_the_noise():
    config = replace(Config(), strategy_mix_random=0.0, strategy_mix_dark_forest=1.0, strategy_mix_cooperative=1.0,
                     strategy_noise=0.0, bubble_density_kpc2=6.4)
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

    config = _replace(_Config(), bubble_density_kpc2=6.4, birth_spread_fraction=0.5)
    civs = [c for c in _generate(config, _streams(3)).civs if c.id.startswith("c_")]
    births = [c.birth_year for c in civs]
    assert len(set(births)) == len(births) > 1
    end = config.start_date_years + 0.5 * config.start_lookback_years
    assert all(config.start_date_years <= b <= end for b in births)
    # Default: the whole cohort is born at the start.
    default = _replace(config, birth_spread_fraction=0.0)
    assert all(c.birth_year == config.start_date_years
               for c in _generate(default, _streams(3)).civs if c.id.startswith("c_"))


def _inside(civ, radius):
    return civ.position[0] ** 2 + civ.position[1] ** 2 <= radius ** 2


def test_regions_are_nested():
    # A smaller region holds exactly the civs, initial and born, of a larger one inside it.
    small = replace(Config(), region_radius_pc=1000.0, civ_birth_rate_kpc2=3e-8)
    large = replace(small, region_radius_pc=2000.0)
    small_world, large_world = _world(small), _world(large)
    inside = [c for c in large_world.civs if _inside(c, 1000.0)]
    assert len(inside) < len(large_world.civs)
    assert any(c.id.startswith("b_") for c in inside)
    assert _snapshot(small_world) == [(c.id, c.position, c.biochem_type, c.strategy) for c in inside]
    assert [c.birth_year for c in small_world.civs] == [c.birth_year for c in inside]


def test_life_follows_the_habitable_annulus():
    # Kept positions: galactocentric radius of mean ~ R + w^2 / R (the disc area grows with r) and
    # spread ~ w; the density at the Sun's radius is the configured one.
    from math import hypot, pi
    from generate_world._galaxy import _galaxy_radius, _sample_galactic_position
    from rng import Rng

    config = replace(Config(), ghz_width_pc=1000.0)
    rng = Rng(1)
    n = 200000
    kept = []
    for _ in range(n):
        position, ok = _sample_galactic_position(config, rng)
        if ok:
            kept.append(hypot(position[0] + config.galactic_radius_sun_pc, position[1]))
    mean = sum(kept) / len(kept)
    assert abs(mean - (8200.0 + 1000.0 ** 2 / 8200.0)) < 30.0
    near_sun = sum(1 for r in kept if abs(r - 8200.0) < 100.0)
    # Uniform density on the proposal disc, thinned by exp(-u^2 / 2) ~ 1 within 100 pc of the peak.
    ring = pi * ((8300.0 ** 2) - (8100.0 ** 2)) / (pi * _galaxy_radius(config) ** 2)
    assert near_sun / n == pytest.approx(ring, rel=0.05)


def test_births_are_drawn_up_front_and_take_part_on_their_date():
    config = replace(Config(), civ_birth_rate_kpc2=1e-7)
    world = _world(config)
    births = [c for c in world.civs if c.id.startswith("b_")]
    assert births and all(config.start_date_years < c.birth_year < config.present_date_years for c in births)
    first = min(births, key=lambda c: c.birth_year)
    assert first not in world.active(first.birth_year - 1.0)
    assert first in world.active(first.birth_year)
