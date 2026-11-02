from dataclasses import replace

from config import Config, STRATEGY_RANGES
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
