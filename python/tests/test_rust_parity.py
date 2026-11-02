"""The Rust engine must reproduce simulation.run bit for bit (see rust_engine.py).

Skipped when the galactic_rs extension is not installed (see rust/README.md). Broader
checks, e.g. over a whole exploration spec: python compare_engines.py --help.
"""

import json
from dataclasses import replace

import pytest

galactic_rs = pytest.importorskip("galactic_rs")

import explore  # noqa: E402
import rust_engine  # noqa: E402
import simulation  # noqa: E402
from compare_engines import differences  # noqa: E402
from compare_fast_forward import scenario  # noqa: E402
from config import Config  # noqa: E402

SHORT = scenario(1.0e6)
CASES = {
    "short": SHORT,
    "jumps": replace(scenario(1.0e7), max_steps=1500),
    "fixed_step": replace(SHORT, fast_forward=False),
    "exponential": replace(SHORT, tech_growth_model="exponential", population_growth_model="exponential"),
    "memory": replace(SHORT, belief_memory_years=20000.0),
    "constant_risk": replace(SHORT, self_destruction_shape="constant", self_destruction_risk=1e-6),
    "increasing_risk": replace(SHORT, self_destruction_shape="increasing", civ_birth_rate=1e-6),
    "artefact": replace(SHORT, artefact_detection_probability=1.0, probe_speed_per_tech=1.0,
                        artefact_window_years=1.0e6),
    "intractable": replace(SHORT, max_civs=10),
    "max_steps": replace(SHORT, max_steps=5),
}


def test_rust_config_has_the_same_parameters_and_defaults():
    assert json.loads(galactic_rs.default_config_json()) == json.loads(json.dumps(Config().to_dict()))


def test_rust_rejects_unknown_parameters():
    with pytest.raises(ValueError, match="unknown field"):
        galactic_rs.run(json.dumps({"no_such_parameter": 1.0}), 1)


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("case", sorted(CASES))
def test_rust_engine_is_bit_identical(case, seed):
    config = CASES[case]
    python_log = simulation.run(config, seed)
    rust_log = rust_engine.run(config, seed, keep_rows=True)
    assert differences(python_log, rust_log) == []


def test_rust_outcomes_cover_every_path():
    outcomes = {rust_engine.run(CASES[case], seed).outcome for case in CASES for seed in (1, 2, 3)}
    assert outcomes == {"consistent", "rejected", "intractable", "timeout"}


def test_rust_wall_time_budget():
    log = rust_engine.run(SHORT, 2, time_budget_s=0.0)
    assert log.outcome == "timeout"
    assert log.run["budget_exhausted"] == "wall_time"
    assert log.rows is None


def test_exploration_parts_do_not_depend_on_the_engine(tmp_path):
    from test_explore import _spec

    def parts(engine):
        out = str(tmp_path / engine)
        explore.plan(_spec(tmp_path), out)
        explore.run(out, (0, 1), workers=1, time_budget_s=None, engine=engine)
        found = list(explore._parts(out))
        for part in found:
            del part["run"]["wall_time_s"]
        return found

    assert parts("rust") == parts("python")
