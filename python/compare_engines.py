"""Check that the Rust engine (rust_engine.run) reproduces simulation.run bit for bit, and time both.

Every record is compared with repr() (so 0.0 and -0.0 differ), except wall_time_s:
outcome, metadata, counters, the run record, every civ record and the per-step rows.

  python compare_engines.py --seeds 1-8 [--config cfg.json] [--set max_steps=2000 ...] [--workers N]
  python compare_engines.py --spec specs/pilot.json --points 0-19 [--set max_steps=2000]
  python compare_engines.py --spec specs/pilot.json --span 1e8      # runs that reach the present

--spec takes the points of a Latin hypercube spec (see explore.py) instead of one config.
--set values are applied last, after --span.
"""

import argparse
import json
import sys
import time
from dataclasses import replace
from multiprocessing import Pool

import explore
import rust_engine
import simulation
from compare_fast_forward import scenario
from config import Config
from run_batch import parse_seeds

FIELDS = ("outcome", "metadata", "n_steps", "n_jumps", "budget_exhausted")


def differences(py, rs):
    """Differences between two logs, as (where, python value, rust value)."""
    out = [(name, getattr(py, name), getattr(rs, name)) for name in FIELDS
           if repr(getattr(py, name)) != repr(getattr(rs, name))]
    out += [(f"run.{k}", v, rs.run.get(k)) for k, v in py.run.items()
            if k != "wall_time_s" and repr(v) != repr(rs.run.get(k))]
    if set(py.run) != set(rs.run):
        out.append(("run keys", sorted(py.run), sorted(rs.run)))
    if len(py.civs) != len(rs.civs):
        out.append(("civs", len(py.civs), len(rs.civs)))
    for a, b in zip(py.civs, rs.civs):
        if list(a) != list(b):
            out.append((f"civ {a['civ_id']} keys", list(a), list(b)))
        out += [(f"civ {a['civ_id']}.{k}", v, b.get(k)) for k, v in a.items() if repr(v) != repr(b.get(k))]
    if repr(py.rows) != repr(rs.rows):
        first = next((k for k, (x, y) in enumerate(zip(py.rows, rs.rows)) if x != y), min(len(py.rows), len(rs.rows)))
        out.append(("rows", f"first difference at step {first}", f"{len(py.rows)} vs {len(rs.rows)} rows"))
    return out


def compare_one(args):
    label, config_dict, seed = args
    config = Config.from_dict(config_dict)
    start = time.perf_counter()
    py = simulation.run(config, seed)
    py_time = time.perf_counter() - start
    start = time.perf_counter()
    rs = rust_engine.run(config, seed, keep_rows=True)
    rs_time = time.perf_counter() - start
    return label, seed, py.outcome, py.n_steps, len(py.civs), py_time, rs_time, differences(py, rs)


def _overrides(assignments):
    overrides = {}
    for assignment in assignments:
        key, _, value = assignment.partition("=")
        try:
            overrides[key] = json.loads(value)
        except json.JSONDecodeError:
            overrides[key] = value
    return overrides


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeds", default="1-4")
    parser.add_argument("--config", help="JSON file of Config overrides")
    parser.add_argument("--spec", help="Latin hypercube spec: compare its points instead of --config")
    parser.add_argument("--points", default="0-9", help="points of --spec to compare")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="Config override applied last (e.g. max_steps=2000)")
    parser.add_argument("--span", type=float, default=None,
                        help="shorten the scenario to this many years (compare_fast_forward.scenario), "
                             "so runs reach the present; artefacts stay as configured")
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    overrides = _overrides(args.set)
    seeds = parse_seeds(args.seeds)
    if args.spec:
        spec = explore.load_spec(args.spec)
        design = {row["point_id"]: row for row in explore.latin_hypercube(spec)}
        configs = [(f"point {p}", explore.point_config(spec, design[p])) for p in parse_seeds(args.points)]
    else:
        base = {}
        if args.config:
            with open(args.config) as handle:
                base = json.load(handle)
        configs = [("config", Config.from_dict(base))]
    if args.span:
        configs = [(label, replace(scenario(args.span, config), artefact_detection_probability=config.artefact_detection_probability))
                   for label, config in configs]
    configs = [(label, {**config.to_dict(), **overrides}) for label, config in configs]
    jobs = [(label, config, seed) for label, config in configs for seed in seeds]

    with Pool(args.workers) as pool:
        results = pool.map(compare_one, jobs)

    n_bad = 0
    total_py = total_rs = 0.0
    for label, seed, outcome, steps, civs, py_time, rs_time, diffs in results:
        total_py += py_time
        total_rs += rs_time
        status = "identical" if not diffs else f"{len(diffs)} DIFFERENCES"
        print(f"{label:>10} seed {seed:>3}: {outcome:12} {steps:>7} steps {civs:>5} civs  "
              f"python {py_time:8.2f}s  rust {rs_time:7.3f}s  {status}")
        for where, a, b in diffs[:5]:
            print(f"    {where}: python {a!r} / rust {b!r}")
        n_bad += bool(diffs)
    print(f"\n{len(results) - n_bad}/{len(results)} runs identical; "
          f"python {total_py:.1f}s, rust {total_rs:.2f}s (x{total_py / max(total_rs, 1e-9):.0f})")
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
