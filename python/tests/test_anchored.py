from dataclasses import replace

import pytest

from config import Config
from constants import C_PC_PER_YEAR
from p0_passive_update._anchored import _anchored, _anchored_tech
from p0_passive_update._compute_broadcast_radius import _broadcast_radius, _tech_for_broadcast_radius
from p0_passive_update._compute_probe_speed import _probe_speed


class _Civ:
    def __init__(self, broadcast):
        self.strategy = {"broadcast": broadcast}


@pytest.mark.parametrize("fraction", [1e-6, 1e-3, 0.5])
def test_anchored_law_goes_through_both_anchors(fraction):
    config = replace(Config(), humanity_tech_fraction=fraction)
    assert _anchored(config.humanity_present_tech, 2.0, 2e6, config) == pytest.approx(2.0)
    assert _anchored(config.tech_cap, 2.0, 2e6, config) == pytest.approx(2e6)
    assert _anchored(10 * config.tech_cap, 2.0, 2e6, config) == pytest.approx(2e6)
    # Each tech level multiplies the effect by the same factor.
    t = config.humanity_present_tech + 0.3
    assert _anchored(t + 0.5, 2.0, 2e6, config) / _anchored(t, 2.0, 2e6, config) == pytest.approx(
        _anchored(t + 1.0, 2.0, 2e6, config) / _anchored(t + 0.5, 2.0, 2e6, config))
    assert _anchored_tech(_anchored(t, 2.0, 2e6, config), 2.0, 2e6, config) == pytest.approx(t)


def test_human_signals_match_the_sources():
    config = Config()
    t = config.humanity_present_tech
    # Arecibo radar (2e13 W) against Breakthrough Listen (1e13 W at 50 pc): sqrt(2) * 50 pc.
    assert _broadcast_radius(_Civ(True), config, t) == pytest.approx(50 * 2 ** 0.5, rel=0.01)
    # LTE leakage (4 GW) at the same sensitivity: about 1 pc.
    assert _broadcast_radius(_Civ(False), config, t) == pytest.approx(1.0, rel=0.01)
    assert _broadcast_radius(_Civ(True), config, 0.0) == 0.0
    r = _broadcast_radius(_Civ(False), config, 1.7)
    assert _tech_for_broadcast_radius(_Civ(False), config, r) == pytest.approx(1.7)


def test_probe_speed_goes_from_voyager_to_the_cap():
    config = replace(Config(), probe_speed_cap_c=0.2)
    assert _probe_speed(config, config.humanity_present_tech) == pytest.approx(5.67e-5 * C_PC_PER_YEAR)
    assert _probe_speed(config, config.tech_cap) == pytest.approx(0.2 * C_PC_PER_YEAR)
    assert _probe_speed(config, 0.0) == 0.0
