//! Thin PyO3 layer over galactic_core: JSON config in, plain Python dicts out.

use galactic_core::{Config, Record, RunResult, Value};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

fn value<'py>(py: Python<'py>, v: &Value) -> PyResult<Bound<'py, PyAny>> {
    Ok(match v {
        Value::None => py.None().into_bound(py),
        Value::Bool(b) => b.into_pyobject(py)?.to_owned().into_any(),
        Value::Int(i) => i.into_pyobject(py)?.into_any(),
        Value::Float(f) => f.into_pyobject(py)?.into_any(),
        Value::Str(s) => s.into_pyobject(py)?.into_any(),
    })
}

fn record<'py>(py: Python<'py>, record: &Record) -> PyResult<Bound<'py, PyDict>> {
    let dict = PyDict::new(py);
    for (key, v) in record {
        dict.set_item(*key, value(py, v)?)?;
    }
    Ok(dict)
}

fn result<'py>(py: Python<'py>, r: &RunResult, keep_rows: bool) -> PyResult<Bound<'py, PyDict>> {
    let out = PyDict::new(py);
    out.set_item("outcome", r.outcome)?;
    out.set_item("metadata", r.metadata.as_ref().map(|m| record(py, m)).transpose()?)?;
    out.set_item("n_steps", r.n_steps)?;
    out.set_item("n_jumps", r.n_jumps)?;
    out.set_item("budget_exhausted", r.budget_exhausted)?;
    out.set_item("run", record(py, &r.run)?)?;
    let civs = PyList::empty(py);
    for c in &r.civs {
        civs.append(record(py, c)?)?;
    }
    out.set_item("civs", civs)?;
    if keep_rows {
        let rows = PyList::empty(py);
        for row in &r.rows {
            let d = PyDict::new(py);
            d.set_item("year", row.year)?;
            d.set_item("n_alive", row.n_alive)?;
            d.set_item("rejected", row.rejected)?;
            rows.append(d)?;
        }
        out.set_item("rows", rows)?;
    } else {
        out.set_item("rows", py.None())?;
    }
    Ok(out)
}

/// run(config_json, seed, time_budget_s=None, keep_rows=False) -> dict
///
/// Same simulation as python/simulation.run. Returns outcome, metadata, n_steps, n_jumps,
/// budget_exhausted, run (record without config_hash, seed and config parameters), civs
/// (records without config_hash and seed) and rows (per-step rows if keep_rows, else None).
#[pyfunction]
#[pyo3(signature = (config_json, seed, time_budget_s=None, keep_rows=false))]
fn run<'py>(py: Python<'py>, config_json: &str, seed: i64, time_budget_s: Option<f64>, keep_rows: bool) -> PyResult<Bound<'py, PyDict>> {
    let config = Config::from_json(config_json).map_err(PyValueError::new_err)?;
    let r = py.detach(|| galactic_core::run(&config, seed, time_budget_s, keep_rows));
    result(py, &r, keep_rows)
}

/// Default Config parameters as JSON, to check that Rust and Python share the same fields.
#[pyfunction]
fn default_config_json() -> String {
    Config::default_json()
}

#[pymodule]
fn galactic_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run, m)?)?;
    m.add_function(wrap_pyfunction!(default_config_json, m)?)?;
    Ok(())
}
