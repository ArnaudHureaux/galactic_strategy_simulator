from dataclasses import replace

import pytest

from config import Config
from p0_passive_update._self_destruction import _self_destruction_hazard
from p0_passive_update._self_destruction_shape import _self_destruction_shape
from state import Civilisation


def _civ(nb_of_world):
    return Civilisation(
        id="c", position=(0.0, 0.0, 0.0), birth_year=0.0, status="alive", biochem_type="water",
        tech_level=1.5, population_size=1.0, nb_of_world=nb_of_world, natural_tech_progress=0.0,
        natural_population_growth=0.0, colonization_aggressiveness=0.0, strategy={})


def test_a_spread_civ_only_dies_of_correlated_catastrophes():
    config = replace(Config(), self_destruction_correlation=0.1)
    full = config.self_destruction_risk * _self_destruction_shape(1.5, config)
    assert _self_destruction_hazard(_civ(1.0), config) == pytest.approx(full)
    assert _self_destruction_hazard(_civ(1.5), config) == pytest.approx(0.55 * full)
    assert _self_destruction_hazard(_civ(2.0), config) == pytest.approx(0.1 * full)
    assert _self_destruction_hazard(_civ(1e9), config) == pytest.approx(0.1 * full)


def test_full_correlation_ignores_the_number_of_worlds():
    config = replace(Config(), self_destruction_correlation=1.0)
    assert _self_destruction_hazard(_civ(1e9), config) == _self_destruction_hazard(_civ(1.0), config)
