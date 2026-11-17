from dataclasses import replace

import pytest

from config import Config
from events import Event
from generate_world import generate_world
from p0_passive_update._growth_law import grow
from p0_passive_update._tech_growth import _human_tech, _tech_growth_cap
from p3_apply_events import apply_events
from rng import make_streams


def _world(config, seed=7):
    return generate_world(config, make_streams(seed))


def test_humanity_sits_at_the_sun_and_does_not_colonize():
    human = _world(Config()).humanity
    assert human.position == (0.0, 0.0, Config().sun_height_pc)
    assert human.colonization_aggressiveness == 0.0
    assert human.strategy["colonization_aggressiveness"] == 0.0


@pytest.mark.parametrize("model", ["logistic", "exponential"])
@pytest.mark.parametrize("fraction", [1e-6, 1e-3, 0.5, 0.95])
def test_humanity_reaches_its_present_tech_today(model, fraction):
    config = replace(Config(), tech_growth_model=model, humanity_tech_fraction=fraction)
    human = _world(config).humanity
    expected = config.initial_tech_level * (config.tech_cap / config.initial_tech_level) ** fraction
    assert config.humanity_present_tech == pytest.approx(expected, rel=1e-12)
    _human_tech(human, config, config.present_date_years)
    assert human.tech_level == pytest.approx(config.humanity_present_tech, rel=1e-9)
    _human_tech(human, config, config.humanity_birth_date_years)
    assert human.tech_level == config.initial_tech_level


def test_humanity_trajectory_does_not_depend_on_the_steps():
    config = replace(Config(), humanity_tech_fraction=0.9)
    human = _world(config).humanity
    t = config.humanity_birth_date_years + 3000.0
    _human_tech(human, config, t)
    direct = grow(config.initial_tech_level, human.natural_tech_progress, _tech_growth_cap(config),
                  t - config.humanity_birth_date_years)
    assert human.tech_level == direct


@pytest.mark.parametrize("kind", ["share", "implicit_share"])
def test_a_share_received_by_humanity_is_a_contact(kind):
    world = _world(replace(Config(), bubble_density_kpc2=1.0))
    human = world.humanity
    source = next(c for c in world.civs if not c.is_human)
    tech = human.tech_level
    apply_events(Event(kind, source.id, human.id, 123.0, shared_tech_level=2.0), world, world.config)
    assert world.rejected and world.rejection_reason == "contact_share" and world.rejected_at == 123.0
    assert human.tech_level == tech