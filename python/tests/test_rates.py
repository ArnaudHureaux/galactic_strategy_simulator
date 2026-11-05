from dataclasses import replace

import pytest

from config import Config
from p3_apply_events._attack_damage import _attack_damage
from p3_apply_events._rates import _step_additive, _step_fraction, _step_growth


@pytest.mark.parametrize("n_steps", [1, 10, 100])
def test_war_and_shares_do_not_depend_on_dt(n_steps):
    # n steps of period / n years have the effect of a single step of one period.
    base = Config()
    config = replace(base, dt=base.interaction_period_years / n_steps)

    remaining = 1.0
    for _ in range(n_steps):
        remaining *= 1 - _attack_damage(1.0, 1.0, config)
    assert remaining == pytest.approx(1 - base.damage_coef)

    tech = 1.0
    for _ in range(n_steps):
        tech -= _step_fraction(base.attack_cost_tech, config) * tech
    assert tech == pytest.approx(1 - base.attack_cost_tech)

    trust = 1.0
    for _ in range(n_steps):
        trust -= _step_additive(base.reputation_trust_drop, config)
    assert trust == pytest.approx(1 - base.reputation_trust_drop)

    growth = 1.0
    for _ in range(n_steps):
        growth *= _step_growth(base.share_synergy_bonus, config)
    assert growth == pytest.approx(1 + base.share_synergy_bonus)


def test_overwhelming_attack_destroys_at_once_whatever_dt():
    config = replace(Config(), dt=1.0)
    assert _attack_damage(10.0, 1.0, config) == 1.0
