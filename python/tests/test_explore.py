import json
from dataclasses import replace

import pandas as pd
import pytest

import explore
import simulation
from compare_fast_forward import scenario

SHORT = 1.0e6


def test_step_budget_ends_runs_as_timeout():
    config = replace(scenario(SHORT), max_steps=3)
    log = simulation.run(config, 2)
    assert log.outcome == "timeout"
    assert log.run["budget_exhausted"] == "steps"
    assert log.n_steps == 3
    assert log.run["end_year"] < config.present_date_years


def test_wall_time_budget_ends_runs_as_timeout():
    log = simulation.run(scenario(SHORT), 2, time_budget_s=0.0)
    assert log.outcome == "timeout"
    assert log.run["budget_exhausted"] == "wall_time"


def _spec(tmp_path):
    base = scenario(SHORT)
    spec = {
        "description": "test",
        "design_seed": 3,
        "n_points": 4,
        "seeds_per_point": 2,
        "base": {
            "present_date_years": base.present_date_years,
            "humanity_birth_date_years": base.humanity_birth_date_years,
            "artefact_window_years": base.artefact_window_years,
            "artefact_detection_probability": 0.0,
        },
        "parameters": {
            "self_destruction_risk": {"low": 1e-10, "high": 1e-7, "scale": "log"},
            "damage_coef": {"low": 0.1, "high": 0.9},
            "max_steps": {"low": 100, "high": 1000},
        },
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path


def test_latin_hypercube_fills_every_stratum(tmp_path):
    spec = explore.load_spec(_spec(tmp_path))
    spec["n_points"] = 10
    design = explore.latin_hypercube(spec)
    assert design == explore.latin_hypercube(spec)
    strata = sorted(int(10 * (row["damage_coef"] - 0.1) / 0.8) for row in design)
    assert strata == list(range(10))
    assert all(1e-10 <= row["self_destruction_risk"] <= 1e-7 for row in design)
    assert all(isinstance(explore.point_config(spec, row).max_steps, int) for row in design)


def test_spec_errors_are_reported(tmp_path):
    path = _spec(tmp_path)
    spec = json.loads(path.read_text())
    spec["parameters"]["damage_cof"] = {"low": 0, "high": 1}
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="damage_cof"):
        explore.load_spec(path)


def test_sharded_resumable_exploration(tmp_path):
    out = str(tmp_path / "exp")
    explore.plan(_spec(tmp_path), out)
    explore.run(out, (0, 2), workers=1, time_budget_s=None)
    assert len(list(explore._parts(out))) == 4
    explore.run(out, (1, 2), workers=1, time_budget_s=None)
    explore.run(out, (0, 1), workers=1, time_budget_s=None)  # everything done: nothing to rerun
    explore.status(out)
    explore.collect(out)
    runs = pd.read_parquet(f"{out}/runs.parquet")
    civs = pd.read_parquet(f"{out}/civs.parquet")
    design = pd.read_parquet(f"{out}/design.parquet")
    assert sorted(zip(runs["point_id"], runs["seed"])) == [(p, s) for p in range(4) for s in (1, 2)]
    assert set(civs["point_id"]) == set(range(4))
    merged = runs.merge(design[["point_id", "config_hash"]], on="point_id", suffixes=("", "_design"))
    assert (merged["config_hash"] == merged["config_hash_design"]).all()


def test_plan_refuses_a_different_spec_in_the_same_directory(tmp_path):
    out = str(tmp_path / "exp")
    path = _spec(tmp_path)
    explore.plan(path, out)
    explore.plan(path, out)
    spec = json.loads(path.read_text())
    spec["design_seed"] = 4
    path.write_text(json.dumps(spec))
    with pytest.raises(SystemExit):
        explore.plan(path, out)
