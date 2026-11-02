import json
from dataclasses import replace

import pytest

from config import Config


def test_defaults_are_valid():
    Config()


def test_from_json_rejects_unknown_parameters(tmp_path):
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({"dt": 500.0, "self_destrcution_risk": 1e-9}))
    with pytest.raises(ValueError, match="self_destrcution_risk"):
        Config.from_json(path)


def test_from_json_turns_lists_into_tuples(tmp_path):
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({"biochem_types": ["water", "ammonia"], "world_type_fractions": [0.5, 0.5]}))
    config = Config.from_json(path)
    assert config.biochem_types == ("water", "ammonia")
    assert config.world_type_fractions == (0.5, 0.5)
    assert config.config_hash() == Config(biochem_types=("water", "ammonia"), world_type_fractions=(0.5, 0.5)).config_hash()


@pytest.mark.parametrize(
    "changes",
    [
        {"dt": 0.0},
        {"world_type_fractions": (0.5, 0.5)},
        {"world_type_fractions": (0.5, 0.4, 0.2)},
        {"humanity_birth_date_years": 1.5e10},
        {"tech_growth_model": "logistc"},
        {"caution_k_low": 2.0, "caution_k_high": 1.0},
        {"share_trust_threshold_high": 1.5},
        {"attack_gap_min_high": 3.0},
        {"share_catchup": 1.0},
        {"artefact_detection_probability": float("nan")},
    ],
)
def test_invalid_configs_are_rejected(changes):
    with pytest.raises(ValueError):
        replace(Config(), **changes)


def test_hash_is_stable_and_tracks_every_parameter():
    assert Config().config_hash() == Config().config_hash()
    assert Config().config_hash() != Config(self_destruction_risk=2e-8).config_hash()
    assert Config.from_dict(Config().to_dict()) == Config()
