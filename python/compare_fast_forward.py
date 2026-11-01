"""Compare fixed-step and fast-forward runs of the same seeds on a shortened scenario.

Apart from rare random events (births, self-destruction), the dynamics is deterministic,
so both modes should tell nearly the same story for a given seed. Artefact discovery is
switched off: it is a pure random draw that would stop runs at unrelated dates. Only the
civs generated at the start are compared, since civs born later differ between runs.

Usage: python compare_fast_forward.py [n_seeds] [span_years]
"""

import sys
import time
from dataclasses import replace
from multiprocessing import Pool

import simulation
from config import Config


def scenario(span):
    base = Config()
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
    seed, span, fast_forward = args
    config = replace(scenario(span), fast_forward=fast_forward)
    holder = {}
    generate = simulation.generate_world

    def keep_world(cfg, rng):
        holder["world"] = generate(cfg, rng)
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


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    span = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0e8
    jobs = [(seed, span, ff) for seed in range(1, n_seeds + 1) for ff in (False, True)]
    with Pool() as pool:
        results = pool.map(run_one, jobs)
    by_key = {(r["seed"], ff): r for r, (_, _, ff) in zip(results, jobs)}

    header = f"{'seed':>4} {'outcome fixed/ff':>24} {'end fixed':>12} {'end ff':>12} {'births':>7} {'alive diff':>10} {'max ext. shift':>14} {'max tech gap':>12} {'steps fixed/ff':>16} {'time fixed/ff':>15}"
    print(header)
    total_fixed = total_fast = 0.0
    agree = 0
    for seed in range(1, n_seeds + 1):
        fixed, fast = by_key[(seed, False)], by_key[(seed, True)]
        c = compare(fixed, fast)
        agree += c["same_outcome"]
        total_fixed += fixed["time"]
        total_fast += fast["time"]
        print(
            f"{seed:>4} {fixed['outcome'] + '/' + fast['outcome']:>24} {fixed['end']:>12.5g} {fast['end']:>12.5g} "
            f"{str(fixed['births']) + '/' + str(fast['births']):>7} "
            f"{c['alive_mismatch']:>10} {c['max_extinction_shift']:>14.4g} {c['max_tech_gap']:>12.3g} "
            f"{str(fixed['steps']) + '/' + str(fast['steps']):>16} {fixed['time']:>7.1f}/{fast['time']:<7.1f}"
        )
    print(f"\nsame outcome: {agree}/{n_seeds}   cumulated time fixed {total_fixed:.0f}s, fast-forward {total_fast:.0f}s "
          f"(x{total_fixed / max(total_fast, 1e-9):.0f})")


if __name__ == "__main__":
    main()
