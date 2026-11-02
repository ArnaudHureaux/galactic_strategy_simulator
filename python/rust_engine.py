"""Rust engine: same contract and bit-identical results as simulation.run, much faster.

The simulation core is ported to Rust in rust/core (galactic_core) and exposed by the
galactic_rs extension module (rust/py). Config validation, config_hash and the config
columns of the records stay here, in Python. Build and install the extension once (see
rust/README.md):

    cd rust/py && python -m maturin build --release -o dist && pip install dist/galactic_rs-*.whl

Every change to the Python simulation must be ported to rust/core: tests/test_rust_parity.py
compares both engines record by record.
"""

import json
from types import SimpleNamespace

import galactic_rs

from observe import add_config


def run(config, seed, time_budget_s=None, keep_rows=False):
    """Like simulation.run; per-step rows (log.rows) are only kept if keep_rows."""
    result = galactic_rs.run(json.dumps(config.to_dict()), seed, time_budget_s, keep_rows)
    config_hash = config.config_hash()
    return SimpleNamespace(
        outcome=result["outcome"],
        metadata=result["metadata"],
        n_steps=result["n_steps"],
        n_jumps=result["n_jumps"],
        budget_exhausted=result["budget_exhausted"],
        run=add_config({"config_hash": config_hash, "seed": seed, **result["run"]}, config),
        civs=[{"config_hash": config_hash, "seed": seed, **c} for c in result["civs"]],
        rows=result["rows"],
    )
