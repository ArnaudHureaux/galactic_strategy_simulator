from dataclasses import replace
from math import exp, log1p

import pytest

from config import Config
from p0_passive_update._check_silence import _exposure, _received_signal_in_window, _seti_coverage
from p0_passive_update._compute_broadcast_radius import (_compute_signal_radii, _listening_gain, _observer_gain,
                                                          _tech_for_listening_gain)
from p0_passive_update._detect import _beacon_caught, _beacon_hazard
from state import Civilisation, Snapshot, World


class _Rng:
    def __init__(self, value):
        self.value = value
        self.calls = 0

    def random(self):
        self.calls += 1
        return self.value


def _civ(civ_id, x, broadcast=False, is_human=False, tech=1.0):
    return Civilisation(
        id=civ_id, position=(x, 0.0, 0.0), birth_year=0.0, status="alive", biochem_type="water",
        tech_level=tech, population_size=1.0, nb_of_world=1.0, natural_tech_progress=0.0,
        natural_population_growth=0.0, colonization_aggressiveness=0.0, strategy={"broadcast": broadcast},
        is_human=is_human)


def test_every_civ_leaks_and_only_broadcasters_have_a_beacon():
    config = Config()
    leak, beacon = _compute_signal_radii(_civ("a", 0.0, broadcast=True), config, config.present_date_years)
    assert 0 < leak < beacon
    leak, beacon = _compute_signal_radii(_civ("b", 0.0), config, config.present_date_years)
    assert leak > 0 and beacon == 0.0
    # Humanity only leaks since the 1930s.
    human = _civ("h", 0.0, is_human=True, tech=config.humanity_present_tech)
    assert _compute_signal_radii(human, config, config.present_date_years - 100.0) == (0.0, 0.0)
    assert _compute_signal_radii(human, config, config.present_date_years - 50.0)[0] > 0


def test_advanced_civs_listen_better():
    config = replace(Config(), seti_flux_threshold_cap_w_m2=3.3e-33)
    # Breakthrough Listen at humanity's level, the explored sensitivity at the cap: 1e8 in flux, 1e4 in range.
    assert _listening_gain(config, config.humanity_present_tech) == pytest.approx(1.0)
    assert _listening_gain(config, config.tech_cap) == pytest.approx(1e4)
    assert _tech_for_listening_gain(config, 100.0) == pytest.approx(
        (config.humanity_present_tech + config.tech_cap) / 2)
    # Humanity keeps its observed sensitivity whatever its tech.
    assert _observer_gain(_civ("h", 0.0, is_human=True, tech=3.0), config) == 1.0
    assert _observer_gain(_civ("a", 0.0, tech=3.0), config) == pytest.approx(1e4)
    # Nobody listens better than us: the gain stays 1.
    flat = replace(config, seti_flux_threshold_cap_w_m2=config.seti_flux_threshold_w_m2)
    assert _listening_gain(flat, 3.0) == 1.0


def test_beacon_hazard_and_exposure():
    config = replace(Config(), listen_coverage=0.5, beacon_duty=0.2)
    rate = _beacon_hazard(3.0, config)
    assert rate == pytest.approx(-3.0 * log1p(-0.1) / config.interaction_period_years)
    observer, source = _civ("o", 0.0), _civ("s", 10.0)
    view = Snapshot(0.0, 1.0, 0.0, 100.0, 0.0, nb_of_world=3.0)
    # Threshold -log(1 - 0.5) = log 2: caught once rate * time reaches it.
    rng = _Rng(0.5)
    steps_needed = int(log1p(1.0) / (rate * config.dt)) + 1
    caught = [_beacon_caught(observer, source, view, config, config.dt, rng) for _ in range(steps_needed)]
    assert caught[-1] and not any(caught[:-1]) and rng.calls == 1
    # Once caught, the source stays seen.
    assert _beacon_caught(observer, source, view, config, config.dt, rng)


def test_seti_coverage():
    config = Config()
    assert _seti_coverage(3.0, config) == 1.0
    assert _seti_coverage(30.0, config) == config.seti_coverage_50pc
    assert _seti_coverage(300.0, config) == config.seti_coverage_beyond


def _listening_world(config, civ, snapshot):
    human = _civ("h", 0.0, is_human=True)
    civ.history = [snapshot]
    civ.history_t = [snapshot.t]
    return World(civs=[civ, human], humanity=human, now=config.present_date_years, config=config)


def test_humanity_catches_a_leak_with_the_survey_coverage():
    config = Config()
    # A leak covering the Sun from 3 pc (fully surveyed): caught for sure, without drawing.
    civ = _civ("a", 3.0)
    t = config.present_date_years - 100.0
    world = _listening_world(config, civ, Snapshot(t, 1.0, 10.0, 0.0, 0.0, nb_of_world=1.0))
    rng = _Rng(0.0)
    assert _received_signal_in_window(world, config, rng) and rng.calls == 0
    # From 30 pc, each of the n systems is caught with probability seti_coverage_50pc.
    civ = _civ("b", 30.0)
    t = config.present_date_years - 200.0
    world = _listening_world(config, civ, Snapshot(t, 1.0, 40.0, 0.0, 0.0, nb_of_world=4.0))
    assert _exposure(civ, config.present_date_years - 166.0, config.present_date_years - 100.0, 30.0)[0] == 4.0
    miss = exp(4.0 * log1p(-config.seti_coverage_50pc))
    # Caught when the draw falls above the miss probability.
    assert _received_signal_in_window(world, config, _Rng(miss + 1e-9))
    assert not _received_signal_in_window(world, config, _Rng(miss - 1e-9))


def test_a_beacon_is_caught_with_its_duty():
    config = replace(Config(), beacon_duty=0.01)
    civ = _civ("a", 3.0, broadcast=True)
    t = config.present_date_years - 100.0
    world = _listening_world(config, civ, Snapshot(t, 1.0, 0.0, 10.0, 0.0, nb_of_world=1.0))
    assert _received_signal_in_window(world, config, _Rng(0.99 + 1e-9))
    assert not _received_signal_in_window(world, config, _Rng(0.99 - 1e-9))
