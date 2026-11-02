"""Latin hypercube exploration of the Config space, on one machine or split across several.

  python explore.py plan    SPEC.json --out DIR    # freeze the design: DIR/spec.json + DIR/design.json
  python explore.py run     --out DIR [--shard I/N] [--workers W] [--time-budget S] [--engine python|rust]
  python explore.py status  --out DIR
  python explore.py collect --out DIR              # DIR/design.parquet, runs.parquet, civs.parquet

plan, run and status only need the standard library, so they also run under PyPy (about
2x faster than CPython on this simulator, same results); collect needs pandas + pyarrow.
`run --engine rust` uses the Rust engine (rust_engine.py: same results bit for bit, about
30x faster than CPython; CPython only, see rust/README.md). Engines can be mixed between
shards or machines: the parts they write are identical (apart from wall_time_s).

The design only depends on the spec (design_seed included); copying DIR (spec.json,
design.json) to each server is enough. A job is one (point, seed) pair; `--shard I/N` keeps
jobs whose index is I modulo N. Each finished job is written at once in DIR/parts, so an
interrupted `run` resumes where it stopped. Merge the parts directories of all machines
before `collect`.

Spec format:
{
  "description": "...",
  "design_seed": 0,
  "n_points": 200,
  "seeds_per_point": 1,
  "base": {"max_steps": 200000},                       # Config overrides shared by every point
  "parameters": {"self_destruction_risk": {"low": 1e-10, "high": 1e-6, "scale": "log"}, ...}
}
"""

import argparse
import json
import os
import random
import statistics
import sys
from collections import Counter
from dataclasses import fields
from math import exp, log
from multiprocessing import Pool
from time import perf_counter

import simulation
from config import Config

SPEC_KEYS = {"description", "design_seed", "n_points", "seeds_per_point", "base", "parameters"}


def load_spec(path):
    with open(path) as handle:
        spec = json.load(handle)
    unknown = set(spec) - SPEC_KEYS
    if unknown:
        raise ValueError(f"unknown spec keys: {', '.join(sorted(unknown))}")
    known = {f.name for f in fields(Config)}
    for name, dim in spec["parameters"].items():
        if name not in known:
            raise ValueError(f"unknown Config parameter in spec: {name}")
        if name in spec.get("base", {}):
            raise ValueError(f"{name} is both explored and fixed in base")
        if dim.get("scale", "linear") not in ("linear", "log"):
            raise ValueError(f"{name}: scale must be 'linear' or 'log'")
        if not dim["low"] < dim["high"] or (dim.get("scale") == "log" and dim["low"] <= 0):
            raise ValueError(f"{name}: need 0 < low < high for log scale, low < high otherwise")
    return spec


def _int_fields():
    return {f.name for f in fields(Config) if f.type is int}


def latin_hypercube(spec):
    """n_points rows (dicts); in each dimension every one of the n_points strata holds exactly one point."""
    rng = random.Random(spec["design_seed"])
    n = spec["n_points"]
    int_fields = _int_fields()
    rows = [{"point_id": k} for k in range(n)]
    for name, dim in spec["parameters"].items():
        strata = list(range(n))
        rng.shuffle(strata)
        u = [(k + rng.random()) / n for k in strata]
        low, high = dim["low"], dim["high"]
        if dim.get("scale", "linear") == "log":
            values = [exp(log(low) + x * (log(high) - log(low))) for x in u]
        else:
            values = [low + x * (high - low) for x in u]
        for row, value in zip(rows, values):
            row[name] = round(value) if name in int_fields else value
    return rows


def point_config(spec, row):
    int_fields = _int_fields()
    params = {name: int(row[name]) if name in int_fields else float(row[name]) for name in spec["parameters"]}
    return Config.from_dict({**spec.get("base", {}), **params})


def jobs(spec, design):
    seeds = range(1, spec["seeds_per_point"] + 1)
    return [(row["point_id"], seed) for row in design for seed in seeds]


def plan(spec_path, out):
    spec = load_spec(spec_path)
    design = latin_hypercube(spec)
    for row in design:
        row["config_hash"] = point_config(spec, row).config_hash()
    spec_out = os.path.join(out, "spec.json")
    if os.path.exists(spec_out):
        with open(spec_out) as handle:
            if json.load(handle) != spec:
                sys.exit(f"{out} already holds a different spec: use another --out")
    os.makedirs(os.path.join(out, "parts"), exist_ok=True)
    with open(spec_out, "w") as handle:
        json.dump(spec, handle, indent=2)
    with open(os.path.join(out, "design.json"), "w") as handle:
        json.dump(design, handle)
    print(f"{len(design)} points x {spec['seeds_per_point']} seeds = {len(jobs(spec, design))} jobs -> {out}")


def _load(out):
    spec = load_spec(os.path.join(out, "spec.json"))
    with open(os.path.join(out, "design.json")) as handle:
        design = json.load(handle)
    return spec, design


def _part_path(out, point_id, seed):
    return os.path.join(out, "parts", f"p{point_id:05d}_s{seed}.json")


def _run_job(args):
    out, config, point_id, seed, time_budget_s, engine = args
    log_ = simulation.engine(engine)(config, seed, time_budget_s)
    run_record = {"point_id": point_id, **log_.run}
    part = {"run": run_record, "civs": [{"point_id": point_id, **c} for c in log_.civs]}
    path = _part_path(out, point_id, seed)
    # Written then renamed: an existing part is always complete, and marks the job as done.
    with open(path + ".tmp", "w") as handle:
        json.dump(part, handle)
    os.replace(path + ".tmp", path)
    return point_id, seed, run_record["outcome"], run_record["rejection_reason"], run_record["wall_time_s"]


def run(out, shard, workers, time_budget_s, engine="python"):
    simulation.engine(engine)  # fail now, not in every worker, if the engine is unavailable
    spec, design = _load(out)
    index, count = shard
    rows = {row["point_id"]: row for row in design}
    todo = []
    for k, (point_id, seed) in enumerate(jobs(spec, design)):
        if k % count != index or os.path.exists(_part_path(out, point_id, seed)):
            continue
        config = point_config(spec, rows[point_id])
        if config.config_hash() != rows[point_id]["config_hash"]:
            sys.exit(f"point {point_id}: config hash differs from design.json (code or spec changed)")
        todo.append((out, config, point_id, seed, time_budget_s, engine))
    print(f"shard {index}/{count}: {len(todo)} jobs to run", flush=True)
    start = perf_counter()
    # One process per job: long runs, so the start-up cost is negligible and memory is returned each time.
    with Pool(workers, maxtasksperchild=1) as pool:
        for n, (point_id, seed, outcome, reason, wall) in enumerate(pool.imap_unordered(_run_job, todo), 1):
            print(f"[{n}/{len(todo)} {perf_counter() - start:7.0f}s] point {point_id} seed {seed}: "
                  f"{outcome}{' (' + reason + ')' if reason else ''} in {wall:.0f}s", flush=True)


def _parts(out):
    directory = os.path.join(out, "parts")
    for name in sorted(os.listdir(directory)):
        if name.endswith(".json"):
            with open(os.path.join(directory, name)) as handle:
                yield json.load(handle)


def status(out):
    spec, design = _load(out)
    runs = [part["run"] for part in _parts(out)]
    print(f"{len(runs)}/{len(jobs(spec, design))} jobs done")
    if runs:
        for (outcome, reason), n in sorted(Counter((r["outcome"], r["rejection_reason"] or "-") for r in runs).items()):
            print(f"  {outcome:12} {reason:18} {n}")
        walls = [r["wall_time_s"] for r in runs]
        print(f"wall time per run: median {statistics.median(walls):.0f}s, max {max(walls):.0f}s, "
              f"total {sum(walls) / 3600:.1f} cpu-hours")


def collect(out):
    import pandas as pd

    _, design = _load(out)
    runs, civs = [], []
    for part in _parts(out):
        runs.append(part["run"])
        civs.extend(part["civs"])
    runs = pd.DataFrame(runs)
    civs = pd.DataFrame(civs)
    if len(runs):
        runs = runs.sort_values(["point_id", "seed"])
    if len(civs):
        civs = civs.sort_values(["point_id", "seed", "civ_id"])
    pd.DataFrame(design).to_parquet(os.path.join(out, "design.parquet"), index=False)
    runs.to_parquet(os.path.join(out, "runs.parquet"), index=False)
    civs.to_parquet(os.path.join(out, "civs.parquet"), index=False)
    print(f"{len(runs)} runs, {len(civs)} civs -> {out}")


def _shard(text):
    index, count = (int(x) for x in text.split("/"))
    if not 0 <= index < count:
        raise argparse.ArgumentTypeError("shard must be I/N with 0 <= I < N")
    return index, count


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    p.add_argument("spec")
    p.add_argument("--out", required=True)
    p = sub.add_parser("run")
    p.add_argument("--out", required=True)
    p.add_argument("--shard", type=_shard, default=(0, 1))
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--time-budget", type=float, default=None,
                   help="wall-clock seconds per run, on top of max_steps (machine-dependent)")
    p.add_argument("--engine", choices=simulation.ENGINES, default="python",
                   help="rust: same results, ~30x faster (needs the galactic_rs extension)")
    for name in ("status", "collect"):
        sub.add_parser(name).add_argument("--out", required=True)
    args = parser.parse_args()

    if args.command == "plan":
        plan(args.spec, args.out)
    elif args.command == "run":
        run(args.out, args.shard, args.workers, args.time_budget, args.engine)
    elif args.command == "status":
        status(args.out)
    else:
        collect(args.out)


if __name__ == "__main__":
    main()
