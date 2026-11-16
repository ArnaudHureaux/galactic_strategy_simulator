from math import exp, pi

import pytest

from config import Config
from p0_passive_update._advance_fronts import (_advance_fronts, _cap_fraction, _holds, _sphere_worlds,
                                              _world_density)
from state import Civilisation, World


def _civ(civ_id, x, biochem="water", radius=0.0, is_human=False):
    return Civilisation(
        id=civ_id, position=(x, 0.0, 0.0), birth_year=0.0, status="alive", biochem_type=biochem,
        tech_level=1.0, population_size=1.0, nb_of_world=1.0,
        natural_tech_progress=0.0, natural_population_growth=0.0, colonization_aggressiveness=1.0,
        strategy={}, expansion_radius=radius, is_human=is_human)


def _density():
    # Density around a home in the mid-plane (the tests' civs sit at z = 0).
    config = Config()
    return _world_density(_civ("probe", 0.0), config)


def _worlds(radius):
    # Worlds within radius of a home in the mid-plane (disk profile, see _sphere_worlds).
    return _sphere_worlds(_civ("probe", 0.0), radius, Config())


def _world(*civs):
    return World(civs=list(civs), humanity=civs[-1], now=0.0, config=Config())


def _grow(world, steps, advance=1.0, movers=None):
    movers = movers or [c for c in world.civs if not c.is_human]
    for _ in range(steps):
        _advance_fronts(world, world.config, [(c, advance if c in movers else 0.0) for c in world.civs])


def test_cap_fraction():
    assert _cap_fraction(0.0, 10.0) == 0.0
    assert _cap_fraction(10.0, 10.0) == pytest.approx(0.5)
    # Small caps: share of the sky of a disc of radius r at distance d, r^2 / (4 d^2).
    assert _cap_fraction(1.0, 1000.0) == pytest.approx(1.0 / 4e6, rel=1e-5)


def test_a_lone_front_takes_the_whole_sphere():
    a = _civ("a", 0.0)
    world = _world(a, _civ("h", 1e6, is_human=True))
    _grow(world, 10)
    assert a.expansion_radius == 10.0 and a.free_fraction == 1.0
    assert a.nb_of_world == pytest.approx(1.0 + _worlds(10.0))


def test_competitors_in_contact_keep_growing_elsewhere():
    a, b = _civ("a", 0.0), _civ("b", 10.0)
    world = _world(a, b, _civ("h", 1e6, is_human=True))
    _grow(world, 20)
    # Formerly both fronts stopped at 5 pc; now they only lose the cap the other one hides.
    assert a.expansion_radius == 20.0 and not a.front_blocked
    assert b.id in a.contacts and a.id in b.contacts
    assert a.free_fraction == pytest.approx(0.5) and a.free_fraction == b.free_fraction
    full = 1.0 + _worlds(20.0)
    assert 1.0 + _worlds(5.0) < a.nb_of_world < full
    assert a.nb_of_world == b.nb_of_world


def test_other_biochem_does_not_block():
    a, b = _civ("a", 0.0), _civ("b", 10.0, biochem="ammonia")
    world = _world(a, b, _civ("h", 1e6, is_human=True))
    _grow(world, 20)
    assert not a.contacts and a.free_fraction == 1.0


def test_an_enclave_cannot_grow_and_does_not_block():
    a, b = _civ("a", 0.0, radius=50.0), _civ("b", 10.0)
    a.nb_of_world += _worlds(50.0)
    world = _world(a, b, _civ("h", 1e6, is_human=True))
    _grow(world, 5)
    assert b.front_blocked and b.expansion_radius == 0.0 and b.nb_of_world == 1.0
    assert a.free_fraction == 1.0 and not a.contacts


def test_the_result_does_not_depend_on_the_order():
    def run(order):
        civs = {k: _civ(k, x) for k, x in (("a", 0.0), ("b", 10.0), ("c", 25.0))}
        world = _world(*[civs[k] for k in order], _civ("h", 1e6, is_human=True))
        _grow(world, 30)
        return {k: (c.expansion_radius, c.nb_of_world, c.free_fraction) for k, c in civs.items()}
    assert run("abc") == run("cba") == run("bca")


def test_the_sun_in_a_competitor_shadow_is_not_held():
    a, b = _civ("a", 0.0), _civ("b", 10.0)
    human = _civ("h", 30.0, is_human=True)
    world = _world(a, b, human)
    _grow(world, 40, movers=[a, b])
    assert a.expansion_radius >= 30.0
    assert not _holds(world, a, human.position, 0.0)
    assert _holds(world, b, human.position, 0.0)
    off_axis = (0.0, 30.0, 0.0)
    assert _holds(world, a, off_axis, 0.0)


def test_front_speed_follows_the_hop_model():
    from dataclasses import replace as _replace

    from p0_passive_update._advance_fronts import NEAREST_NEIGHBOUR, _front_speed_at
    from p0_passive_update._compute_probe_speed import _probe_speed

    # Long-lived probes: the range covers a hop from tech 1 on (see the threshold test below).
    config = _replace(Config(), colonization_launch_period_years=500.0,
                     probe_function_human_years=1e6, probe_function_cap_years=1e9)
    civ = _civ("a", 0.0)
    civ.colonization_aggressiveness = 0.5
    hop = NEAREST_NEIGHBOUR * _density() ** (-1.0 / 3.0)
    v = _probe_speed(config, 1.0)
    assert _front_speed_at(civ, config, 1.0) == pytest.approx(0.5 * hop / (hop / v + 500.0))
    # Faster probes or a shorter launch period make faster fronts.
    assert _front_speed_at(civ, config, 2.0) > _front_speed_at(civ, config, 1.0)
    civ.colonization_aggressiveness = 0.0
    assert _front_speed_at(civ, config, 1.0) == 0.0


def test_colonization_needs_a_probe_range_of_one_hop():
    from p0_passive_update._advance_fronts import _colonization_tech, _front_speed_at, _hop
    from p0_passive_update._compute_probe_speed import _probe_range

    config = Config()
    civ = _civ("a", 0.0)
    threshold = _colonization_tech(civ, config)
    assert config.humanity_present_tech < threshold < config.tech_cap
    assert _probe_range(config, threshold) == pytest.approx(_hop(_density()))
    assert _front_speed_at(civ, config, threshold * 0.999) == 0.0
    assert _front_speed_at(civ, config, threshold * 1.001) > 0.0


def test_worlds_follow_the_disk():
    config = Config()
    h = config.scale_height_pc
    home, high = _civ("a", 0.0), _civ("b", 0.0)
    high.position = (0.0, 0.0, 600.0)
    # Small spheres: the density around the home, which falls with the height.
    assert _sphere_worlds(home, 1.0, config) == pytest.approx(_world_density(home, config) * 4.0 / 3.0 * pi, rel=1e-2)
    assert _world_density(high, config) == pytest.approx(_world_density(home, config) * exp(-600.0 / h))
    # Local density at the Sun's height is habitable_world_density (times the type's share).
    sun = _civ("s", 0.0)
    sun.position = (0.0, 0.0, config.sun_height_pc)
    assert _world_density(sun, config) == pytest.approx(config.habitable_world_density * config.world_type_fractions[0])
    # Much wider than the disk: the column density 2 h n over the disc pi R^2, whatever the height.
    for civ in (home, high):
        assert _sphere_worlds(civ, 1e6, config) == pytest.approx(_world_density(home, config) * 2 * h * pi * 1e12, rel=1e-3)
    radii = [0.0, 1.0, 100.0, 600.0, 601.0, 1e4]
    for civ in (home, high):
        counts = [_sphere_worlds(civ, r, config) for r in radii]
        assert counts == sorted(counts)
