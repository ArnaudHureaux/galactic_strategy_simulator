from dataclasses import replace

import pandas as pd
import pytest

from config import Config

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
    config = replace(scenario(SHORT), artefact_detection_probability=1.0, probe_speed_human_c=0.3, probe_speed_cap_c=0.99, probe_function_human_years=1e7, probe_function_cap_years=1e8,
                     artefact_window_years=SHORT)
    log = simulation.run(config, 1)
    assert log.outcome == "rejected"
    assert log.run["rejection_reason"] == "artefact"
    assert log.run["end_year"] == log.run["rejected_at"] <= config.present_date_years
    assert log.civs


def test_discreet_probes_of_advanced_civs_are_not_found():
    # Owners more advanced than humanity (fast tech growth, humanity at the bottom of the scale, no
    # late births at humanity's level) and attacks cost nothing and do no damage (both lower tech).
    # Probes may arrive while their owners are only ~1e-3 ahead: the stealth must be strong.
    config = replace(scenario(SHORT), artefact_detection_probability=1.0, probe_speed_human_c=0.3, probe_speed_cap_c=0.99, probe_function_human_years=1e7, probe_function_cap_years=1e8,
                     artefact_window_years=SHORT, artefact_stealth_per_tech=1e5,
                     natural_tech_progress_mean=1e-4, civ_birth_rate=0.0, attack_cost_tech=0.0, damage_coef=0.0,
                     humanity_tech_fraction=1e-6, max_steps=50)
    log = simulation.run(config, 1)
    assert log.run["humanity_reached_by_probe"]
    assert log.run["rejection_reason"] != "artefact"
    assert simulation.run(replace(config, artefact_stealth_per_tech=0.0), 1).run["rejection_reason"] == "artefact"


def test_batch_round_trips_through_parquet(tmp_path):
    config = scenario(SHORT)
    runs, civs = run_batch(config, [1, 2], workers=1)
    runs_path, civs_path = write_batch(runs, civs, config, tmp_path)
    assert config.config_hash() in runs_path
    back = pd.read_parquet(runs_path)
    assert list(back["seed"]) == [1, 2]
    assert len(pd.read_parquet(civs_path)) == len(civs)


def test_selection_metrics():
    from observe import _selection_metrics
    from state import Civilisation, World

    def civ(civ_id, archetype, threshold, status):
        return Civilisation(
            id=civ_id, position=(0.0, 0.0, 0.0), birth_year=0.0, status=status, biochem_type="water",
            tech_level=1.0, population_size=1.0, nb_of_world=1.0, natural_tech_progress=0.0,
            natural_population_growth=0.0, colonization_aggressiveness=0.0,
            strategy={"archetype": archetype, "attack_when_trust_inferior_than": threshold})

    civs = [civ("a", "full_aggressive", 1.0, "extinct"), civ("b", "full_aggressive", 1.0, "alive"),
            civ("c", "full_passive", 0.0, "alive"), civ("d", "full_passive", 0.0, "alive")]
    human = civ("h", "random", 0.0, "alive")
    human.is_human = True
    world = World(civs=civs + [human], humanity=human, now=0.0, config=Config())
    metrics = _selection_metrics(world, 1.0)
    assert metrics["attack_threshold_born_mean"] == 0.5
    assert metrics["attack_threshold_alive_mean"] == pytest.approx(1 / 3)
    assert metrics["strategy_selection"] == pytest.approx(1 / 3 - 0.5)
    assert metrics["survival_full_aggressive"] == 0.5 and metrics["survival_full_passive"] == 1.0
    assert metrics["survival_dark_forest"] is None
