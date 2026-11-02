"""Run one config over many seeds and write the results as Parquet.

Outputs, in --out (default: results/):
  runs_<config_hash>.parquet  one row per run: config parameters, outcome, rejection cause and date, metrics
  civs_<config_hash>.parquet  one row per civ and run: traits, strategy and fate

Both tables share the (config_hash, seed) key, so batches of different configs can be concatenated.

Usage: python run_batch.py [--config cfg.json] [--seeds 1-24 | --seeds 1,5,9] [--workers N] [--time-budget S] [--out DIR]
"""

import argparse
import os
from multiprocessing import Pool

import pandas as pd

import simulation
from config import Config


def parse_seeds(text):
    seeds = []
    for part in text.split(","):
        if "-" in part:
            low, high = part.split("-")
            seeds.extend(range(int(low), int(high) + 1))
        else:
            seeds.append(int(part))
    return seeds


def run_one(args):
    config, seed, time_budget_s = args
    log = simulation.run(config, seed, time_budget_s)
    return log.run, log.civs


def run_batch(config, seeds, workers=None, time_budget_s=None):
    jobs = [(config, seed, time_budget_s) for seed in seeds]
    if workers == 1:
        results = [run_one(job) for job in jobs]
    else:
        with Pool(workers) as pool:
            results = pool.map(run_one, jobs)
    runs = pd.DataFrame([run for run, _ in results])
    civs = pd.DataFrame([civ for _, run_civs in results for civ in run_civs])
    return runs, civs


def write_batch(runs, civs, config, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    tag = config.config_hash()
    paths = (os.path.join(out_dir, f"runs_{tag}.parquet"), os.path.join(out_dir, f"civs_{tag}.parquet"))
    runs.to_parquet(paths[0], index=False)
    civs.to_parquet(paths[1], index=False)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", help="JSON file overriding Config defaults")
    parser.add_argument("--seeds", default="1-8")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--time-budget", type=float, default=None,
                        help="wall-clock seconds per run (machine-dependent; prefer max_steps in the config)")
    parser.add_argument("--out", default="results")
    args = parser.parse_args()

    config = Config.from_json(args.config) if args.config else Config()
    runs, civs = run_batch(config, parse_seeds(args.seeds), args.workers, args.time_budget)
    for path in write_batch(runs, civs, config, args.out):
        print(path)
    print(runs.groupby(["outcome", "rejection_reason"], dropna=False).size().to_string())


if __name__ == "__main__":
    main()
