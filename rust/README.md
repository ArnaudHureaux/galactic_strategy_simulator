# Rust engine

Port of the simulation core (`python/simulation.run` and everything it calls) to Rust,
giving **bit-identical** results about 30 times faster than CPython. Python remains the
reference implementation and keeps everything around the core: `Config` and its
validation, `config_hash`, exploration (`explore.py`), batches (`run_batch.py`), Parquet
outputs and analysis.

```
rust/
  core/   galactic_core: the simulation, pure Rust (no PyO3), one module per Python module
  py/     galactic_rs: PyO3 extension (JSON config in, the records of simulation.run out)
python/
  rust_engine.py          run(config, seed, ...) with the same contract as simulation.run
  compare_engines.py      compare both engines run by run (seeds, configs, exploration specs)
  tests/test_rust_parity.py
```

Usage: `--engine rust` in `explore.py run` and `run_batch.py`, or `rust_engine.run(config, seed)`.
Records are identical whatever the engine (except `wall_time_s`), so engines can be mixed
between shards of the same exploration.

## Bit-identical results: how and what to keep in mind

`galactic_core` mirrors the Python modules function by function, in the same order of
floating-point operations. On top of that:

- **Random numbers**: `rng.rs` reimplements CPython's `random.Random` (MT19937, integer
  seeding, `random`, `uniform`, `expovariate`, `choice`, `choices`) and the SHA-256 derived
  streams of `rng.make_streams`.
- **Math functions**: `exp`, `log`, `log1p`, `expm1`, `sin`, `cos` and `**` call the same C
  library as CPython (ucrtbase on Windows, libm elsewhere), with CPython's special cases
  (`pymath.rs`). Python's `min`/`max` and `round(x, 9)` are reproduced exactly.
- **Event ties**: the event queue reproduces `heapq`'s algorithm, since events arriving at
  the same date are applied in heap order.
- **Order**: dict insertion order (beliefs) and sort orders on civ ids are kept.

Two consequences:

1. **Any change to the Python simulation must be ported to `rust/core`.** The parity
   test fails otherwise. For a broader check after a change:
   `python compare_engines.py --spec specs/pilot.json --points 0-39 --span 1e7`.
2. Parity holds with CPython on the same machine. `sum()` is not used on floats in the core
   (CPython >= 3.12 compensates its rounding), so the Python version does not matter.

## Build (Windows, without Visual Studio)

The toolchain is rustup with the GNU target, installed on D: (`RUSTUP_HOME=D:\rust\rustup`,
`CARGO_HOME=D:\rust\cargo`, user environment variables). `rust/.cargo/config.toml` sets
`PYO3_USE_RAW_DYLIB=0` so that PyO3 links the interpreter's own `libs\python3XY.lib`
(raw-dylib would need a full binutils on windows-gnu).

```powershell
python -m pip install "maturin>=1.7,<2"
cd rust\py
$env:CARGO_TARGET_DIR = "D:\rust\targets\galactic"   # optional: keep build files off C:
python -m maturin build --release -i python -o D:\rust\wheels
python -m pip install --force-reinstall (Get-ChildItem D:\rust\wheels\galactic_rs-*.whl | Select-Object -Last 1)
```

The wheel is built for the interpreter given by `-i` (rebuild after changing Python version
or after any change in `rust/`). Then:

```powershell
cd rust; cargo test -p galactic_core          # Rust unit tests (RNG and math against CPython values)
cd python; python -m pytest tests              # includes tests/test_rust_parity.py
```

On Linux/macOS the same commands work with the default rustup toolchain.
