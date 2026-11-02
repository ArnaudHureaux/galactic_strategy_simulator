from dataclasses import replace

import pandas as pd

import simulation
from compare_fast_forward import scenario
from run_batch import run_batch, write_batch

SHORT = 1.0e6


def _without_wall_time(record):
    return {k: v for k, v in record.items() if k != "wall_time_s"}


def test_runs_are_reproducible():
    config = scenario(SHORT)
    a, b = simulation.run(config, 1), simulation.run(config, 1)
    assert _without_wall_time(a.run) == _without_wall_time(b.run)
    assert a.civs == b.civs


def test_records_describe_every_run_and_civ():
    config = scenario(SHORT)
    log = simulation.run(config, 2)
    run = log.run
    assert run["config_hash"] == config.config_hash()
    assert run["seed"] == 2
    assert run["outcome"] in ("consistent", "rejected", "intractable")
    assert run["self_destruction_risk"] == config.self_destruction_risk
    assert run["n_civs_initial"] + run["n_civs_born"] + 1 == len(log.civs)
    assert sum(c["is_human"] for c in log.civs) == 1
    assert all(c["config_hash"] == run["config_hash"] for c in log.civs)


def test_rejected_runs_keep_their_cause_and_date():
    # Every probe that reaches the Sun during the artefact window is found.
    config = replace(scenario(SHORT), artefact_detection_probability=1.0, probe_speed_per_tech=1.0,
                     artefact_window_years=SHORT)
    log = simulation.run(config, 1)
    assert log.outcome == "rejected"
    assert log.run["rejection_reason"] == "artefact"
    assert log.run["end_year"] == log.run["rejected_at"] <= config.present_date_years
    assert log.civs


def test_batch_round_trips_through_parquet(tmp_path):
    config = scenario(SHORT)
    runs, civs = run_batch(config, [1, 2], workers=1)
    runs_path, civs_path = write_batch(runs, civs, config, tmp_path)
    assert config.config_hash() in runs_path
    back = pd.read_parquet(runs_path)
    assert list(back["seed"]) == [1, 2]
    assert len(pd.read_parquet(civs_path)) == len(civs)
