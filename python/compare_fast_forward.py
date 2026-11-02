"""Compare fixed-step and fast-forward runs of the same seeds on a shortened scenario.

Apart from rare random events (births, self-destruction), the dynamics is deterministic,
so both modes should tell nearly the same story for a given seed. Artefact discovery is
switched off: it is a pure random draw that would stop runs at unrelated dates. Only the
civs generated at the start are compared, since civs born later differ between runs.

Several fast-forward variants can be compared with the same fixed-step reference, e.g.
to measure what a looser jump budget costs in accuracy:

  python compare_fast_forward.py --seeds 12 --span 1e8 [--config base.json]
      [--variant loose:jump_max_relative_change=0.05 ...]

--config gives Config overrides (JSON) applied before the scenario is shortened. Without
--variant, the fast-forward is compared as configured ("ff").
"""

import argparse
import json
import time
from dataclasses import replace
from multiprocessing import Pool
from statistics import median

import simulation
from config import Config


def scenario(span, base=None):
    base = base or Config()
    start = base.last_grb_date_years
    present = start + span
    return replace(
        base,
        present_date_years=present,
        humanity_birth_date_years=present - (base.present_date_years - base.humanity_birth_date_years),
        artefact_window_years=span * base.artefact_window_years / (base.present_date_years - start),
        artefact_detection_probability=0.0,
    )


def run_one(args):
    seed, span, base, overrides = args
    config = replace(scenario(span, Config.from_dict(base)), **overrides)
    holder = {}
    generate = simulation.generate_world

    def keep_world(cfg, streams):
        holder["world"] = generate(cfg, streams)
        holder["initial"] = {c.id for c in holder["world"].civs}
        return holder["world"]

    simulation.generate_world = keep_world
    t0 = time.perf_counter()
    log = simulation.run(config, seed)
    elapsed = time.perf_counter() - t0
    simulation.generate_world = generate
    world = holder["world"]
    others = [c for c in world.civs if not c.is_human and c.id in holder["initial"]]
    return {
        "seed": seed,
        "outcome": log.outcome,
        "end": log.rows[-1]["year"] if log.rows else None,
        "steps": log.n_steps,
        "jumps": log.n_jumps,
        "time": elapsed,
        "births": len(world.civs) - len(holder["initial"]),
        "alive": {c.id for c in others if c.status == "alive"},
        "extinct_at": {c.id: c.extinct_at for c in others if c.extinct_at is not None},
        "tech": {c.id: c.tech_level for c in others if c.status == "alive"},
    }


def compare(fixed, fast):
    common_dead = set(fixed["extinct_at"]) & set(fast["extinct_at"])
    shifts = [abs(fixed["extinct_at"][k] - fast["extinct_at"][k]) for k in common_dead]
    common_alive = fixed["alive"] & fast["alive"]
    tech_gap = max((abs(fixed["tech"][k] - fast["tech"][k]) for k in common_alive), default=0.0)
    return {
        "same_outcome": fixed["outcome"] == fast["outcome"],
        "alive_mismatch": len(fixed["alive"] ^ fast["alive"]),
        "max_extinction_shift": max(shifts, default=0.0),
        "max_tech_gap": tech_gap,
    }


def parse_variant(text):
    name, _, assignments = text.partition(":")
    overrides = {}
    for assignment in filter(None, assignments.split(",")):
        key, _, value = assignment.partition("=")
        try:
            overrides[key] = json.loads(value)
        except json.JSONDecodeError:
            overrides[key] = value
    return name, overrides


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--span", type=float, default=1.0e8)
    parser.add_argument("--config", help="JSON file of Config overrides")
    parser.add_argument("--variant", action="append", type=parse_variant, default=None)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    base = {}
    if args.config:
        with open(args.config) as handle:
            base = json.load(handle)
    base = Config.from_dict(base).to_dict()
    variants = dict(args.variant or [("ff", {})])
    variants = {name: {**overrides, "fast_forward": True} for name, overrides in variants.items()}
    runs = {"fixed": {"fast_forward": False}, **variants}
    seeds = range(1, args.seeds + 1)
    jobs = [(seed, args.span, base, overrides) for seed in seeds for overrides in runs.values()]
    with Pool(args.workers) as pool:
        results = pool.map(run_one, jobs)
    by_key = {}
    for (seed, _, _, _), name, result in zip(jobs, [n for _ in seeds for n in runs], results):
        by_key[(seed, name)] = result

    for name in variants:
        print(f"\n=== {name}: {variants[name]}")
        print(f"{'seed':>4} {'outcome fixed/ff':>24} {'end fixed':>12} {'end ff':>12} {'births':>7} {'alive diff':>10} "
              f"{'max ext. shift':>14} {'max tech gap':>12} {'steps fixed/ff':>16} {'time fixed/ff':>15}")
        for seed in seeds:
            fixed, fast = by_key[(seed, "fixed")], by_key[(seed, name)]
            c = compare(fixed, fast)
            print(
                f"{seed:>4} {fixed['outcome'] + '/' + fast['outcome']:>24} {fixed['end']:>12.5g} {fast['end']:>12.5g} "
                f"{str(fixed['births']) + '/' + str(fast['births']):>7} "
                f"{c['alive_mismatch']:>10} {c['max_extinction_shift']:>14.4g} {c['max_tech_gap']:>12.3g} "
                f"{str(fixed['steps']) + '/' + str(fast['steps']):>16} {fixed['time']:>7.1f}/{fast['time']:<7.1f}"
            )

    print(f"\n{'variant':>10} {'same outcome':>13} {'alive diff (mean)':>18} {'tech gap (median/max)':>22} "
          f"{'steps':>10} {'time (s)':>9} {'speed-up vs fixed':>18}")
    fixed_time = sum(by_key[(s, "fixed")]["time"] for s in seeds)
    print(f"{'fixed':>10} {'':>13} {'':>18} {'':>22} {sum(by_key[(s, 'fixed')]['steps'] for s in seeds):>10} "
          f"{fixed_time:>9.0f} {'1':>18}")
    for name in variants:
        comparisons = [compare(by_key[(s, "fixed")], by_key[(s, name)]) for s in seeds]
        gaps = [c["max_tech_gap"] for c in comparisons]
        total_time = sum(by_key[(s, name)]["time"] for s in seeds)
        print(f"{name:>10} {sum(c['same_outcome'] for c in comparisons):>6}/{len(comparisons):<6} "
              f"{sum(c['alive_mismatch'] for c in comparisons) / len(comparisons):>18.2f} "
              f"{median(gaps):>11.3g}/{max(gaps):<10.3g} {sum(by_key[(s, name)]['steps'] for s in seeds):>10} "
              f"{total_time:>9.0f} {fixed_time / max(total_time, 1e-9):>18.1f}")


if __name__ == "__main__":
    main()
