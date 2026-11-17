from dataclasses import replace
from math import exp

import pytest

from config import Config
from events import Event
from p2_from_actions_to_events import from_actions_to_events
from p3_apply_events import apply_events
from p3_apply_events._attack_damage import _attack_damage, _attribution_probability, _damage_gap_scale
from p3_apply_events._rates import _fraction, _step_fraction
from state import BeliefEntry, Civilisation, World


class _Rng:
    def __init__(self, value):
        self.value = value
        self.calls = 0

    def random(self):
        self.calls += 1
        return self.value


def _civ(civ_id, tech):
    return Civilisation(
        id=civ_id, position=(0.0, 0.0, 0.0), birth_year=0.0, status="alive", biochem_type="water",
        tech_level=tech, population_size=1.0, nb_of_world=1.0, natural_tech_progress=0.0,
        natural_population_growth=0.0, colonization_aggressiveness=0.0, strategy={})


def _victim_knowing(attacker_id, tech=1.0):
    victim = _civ("v", tech)
    victim.belief[attacker_id] = BeliefEntry(attacker_id, 2.0, 0.0, "water", True, 0.8, "signal")
    return victim


def test_damage_grows_with_the_tech_gap():
    config = replace(Config(), damage_coef=0.1)
    k = _damage_gap_scale(config)
    expected = _fraction(min(1.0, 0.1 * exp(k * 0.5)), config.dt, config.interaction_period_years)
    assert _attack_damage(1.5, 1.0, config) == expected
    # Same gap, same damage, whatever the absolute level (tech is a log scale of power).
    assert _attack_damage(2.5, 2.0, config) == pytest.approx(expected, rel=1e-12)
    assert _attack_damage(1.0, 0.0, config) == 1.0


def test_an_attack_destroys_the_same_share_of_power_population_and_worlds():
    config = replace(Config(), damage_coef=0.1)
    attacker, victim = _civ("a", 1.1), _civ("v", 1.0)
    victim.population_size, victim.nb_of_world, victim.expansion_radius = 100.0, 1001.0, 10.0
    damage = _attack_damage(attacker.tech_level, victim.tech_level, config)
    _attack(config, _Rng(0.0), victim, attacker)
    kept = 1 - damage
    # The power follows the energy law: exp(k * tech), k = _damage_gap_scale.
    assert exp(_damage_gap_scale(config) * (victim.tech_level - 1.0)) == pytest.approx(kept, rel=1e-12)
    assert victim.population_size == pytest.approx(100.0 * kept, rel=1e-12)
    assert victim.nb_of_world - 1 == pytest.approx(1000.0 * kept, rel=1e-12)
    assert victim.expansion_radius ** 3 == pytest.approx(1000.0 * kept, rel=1e-12)


def test_an_attack_that_wipes_out_the_power_margin_kills():
    config = replace(Config(), damage_coef=1.0, interaction_period_years=Config().dt)
    victim = _civ("v", 0.1)
    _attack(config, _Rng(0.0), victim, _civ("a", 3.0))
    assert victim.tech_level == 0.0
    assert victim.status == "extinct"


def test_attribution_probability():
    config = replace(Config(), attack_stealth_per_tech=2.0)
    assert _attribution_probability(1.5, 1.0, config) == exp(-1.0)
    assert _attribution_probability(1.0, 1.5, config) == 1.0
    assert _attribution_probability(5.0, 1.0, Config()) == 1.0


def _attack(config, rng, victim, attacker):
    world = World(civs=[attacker, victim, _civ("h", 1.0)], humanity=None, now=0.0, config=config)
    world.humanity = world.civs[-1]
    apply_events(Event("attack", attacker.id, victim.id, 10.0, power=attacker.tech_level), world, config, rng)
    return world


def test_an_unattributed_attack_leaves_trust_and_witnesses_alone():
    config = replace(Config(), attack_stealth_per_tech=5.0)
    attacker, victim = _civ("a", 2.0), _victim_knowing("a")
    rng = _Rng(0.99)
    _attack(config, rng, victim, attacker)
    assert victim.tech_level < 1.0
    assert victim.belief["a"].trust == 0.8 and not victim.belief["a"].attacked_me
    assert victim.attacked_by == "a" and not victim.attack_attributed
    # Drawn once per war: the next attacks reuse the draw.
    _attack(config, rng, victim, attacker)
    assert rng.calls == 1 and victim.attributions == {"a": False}


def test_an_attributed_attack_breaks_trust():
    config = replace(Config(), attack_stealth_per_tech=5.0)
    attacker, victim = _civ("a", 2.0), _victim_knowing("a")
    _attack(config, _Rng(0.0), victim, attacker)
    assert victim.belief["a"].trust == 0.0 and victim.belief["a"].attacked_me and victim.attack_attributed


def test_no_stealth_draws_nothing():
    attacker, victim = _civ("a", 2.0), _victim_knowing("a")
    _attack(Config(), None, victim, attacker)
    assert victim.belief["a"].trust == 0.0 and victim.attack_attributed


def test_an_attacker_spends_a_share_of_its_power():
    config = replace(Config(), attack_cost_tech=0.2)
    attacker, victim = _civ("a", 2.0), _civ("v", 1.0)
    world = World(civs=[attacker, victim, _civ("h", 1.0)], humanity=None, now=0.0, config=config)
    from_actions_to_events([("attack", "v")], attacker, world, 0.0, config)
    # Same energy law as the damage: the cost is a share of power, not of the tech level.
    kept = 1 - _step_fraction(0.2, config)
    assert exp(_damage_gap_scale(config) * (attacker.tech_level - 2.0)) == pytest.approx(kept, rel=1e-12)
