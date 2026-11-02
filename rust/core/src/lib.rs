//! Simulation core of galactic_strategy_simulator, ported from python/ (the reference
//! implementation). `run` gives bit-identical results to `simulation.run` for the same
//! config and seed: every module mirrors its Python counterpart, including the order of
//! floating-point operations, random draws and event ties. Any change of the Python
//! simulation must be ported here (python/tests/test_rust_parity.py checks it).

pub mod apply;
pub mod config;
pub mod decisions;
pub mod events;
pub mod fast_forward;
pub mod geometry;
pub mod observe;
pub mod passive;
pub mod pymath;
pub mod rng;
pub mod simulation;
pub mod state;
pub mod world_gen;

pub use config::Config;
pub use observe::{Record, Value};
pub use simulation::{Row, RunResult, run};
