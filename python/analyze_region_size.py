"""Region-size convergence on nested galaxies (crop_radius_pc): does the silence seen in a
region survive when the same galaxy is extended, and which criterion predicts when it does not?

  python analyze_region_size.py [--root ../explorations] [--out FILE.md]

Reads the explorations nested_r4000_c1000, nested_r4000_c2000 and nested_r4000_full (specs
python/specs/nested_r4000_*.json): the same 4 kpc galaxy cropped to 1 kpc, to 2 kpc, or whole.
The full galaxy is only run on the points silent at 1 or 2 kpc plus random controls
(nested_r4000_full_points.json). Prints, and writes with --out, a Markdown report:
  - outcome transitions per point between sizes;
  - who breaks the silence: distance to humanity of the nearest civ whose territory covers it;
  - three candidate criteria for the size needed, against the silence lost by extending:
      density   civs ever born per kpc^2 of disc (initial + births, from the full 4 kpc draw);
      reach_obs widest settlement front reached in the 2 kpc run (pc);
      reach_cfg prior reach from the config alone: front speed at tech_cap with full
                aggressiveness, on the mid-plane water-world density, times start_lookback_years.
"""

import argparse
import glob
import json
import os
from collections import Counter
from math import pi

import explore
from p0_passive_update._advance_fronts import _front_speed_at
from state import Civilisation

SIZES = ("c1000", "c2000", "full")


def _label(run):
    if run["outcome"] == "rejected":
        return run["rejection_reason"]
    return run["outcome"]


def load_configs(root):
    # The specs of these runs use parameters of the code at 6f59540: with later code, reach_cfg is skipped.
    try:
        spec, design = explore._load(os.path.join(root, "nested_r4000_c1000"))
        return {row["point_id"]: explore.point_config(spec, row) for row in design}
    except ValueError:
        return None


def load(root):
    runs, civs = {}, {}
    for size in SIZES:
        for path in glob.glob(os.path.join(root, f"nested_r4000_{size}", "parts", "*.json")):
            with open(path) as handle:
                part = json.load(handle)
            k = part["run"]["point_id"]
            runs[size, k] = part["run"]
            civs[size, k] = [c for c in part["civs"] if not c["is_human"] and c["born"]]
    return runs, civs


def _culprit_distance(civs):
    covering = [c["distance_to_humanity_pc"] for c in civs
                if c["probe_reached_humanity"] or (c["expansion_radius_pc"] or 0) >= c["distance_to_humanity_pc"]]
    return min(covering) if covering else None


def reach_cfg(config):
    probe = Civilisation(
        id="probe", position=(0.0, 0.0, 0.0), birth_year=0.0, status="alive", biochem_type=config.biochem_types[0],
        tech_level=config.tech_cap, population_size=1.0, nb_of_world=1.0, natural_tech_progress=0.0,
        natural_population_growth=0.0, colonization_aggressiveness=1.0, strategy={})
    return _front_speed_at(probe, config, config.tech_cap) * config.start_lookback_years


def density(run):
    # Civs ever born in the whole 4 kpc disc, per kpc^2: expected initial civs + births over the run.
    born = run["expected_bubbles"] * run["civs_per_bubble"] + run["civ_birth_rate"] * run["start_lookback_years"]
    return born / (pi * (run["region_radius_pc"] / 1000.0) ** 2)


def _quantiles(values):
    values = sorted(values)
    if not values:
        return "-"
    pick = [values[int(q * (len(values) - 1))] for q in (0, 0.25, 0.5, 0.75, 1)]
    return " / ".join(f"{v:.3g}" for v in pick)


def report(root):
    runs, civs = load(root)
    configs = load_configs(root)
    with open(os.path.join(root, "nested_r4000_full_points.json")) as handle:
        chosen = json.load(handle)
    lines = ["# Region-size convergence (nested galaxies)", ""]
    points = sorted(k for (s, k) in runs if s == "c1000")
    full = sorted(k for (s, k) in runs if s == "full")
    lines += [f"Points: {len(points)} cropped to 1 and 2 kpc; {len(full)} run whole at 4 kpc "
              f"({len(chosen['silent'])} silent at 1 or 2 kpc, {len(chosen['controls'])} random controls).", ""]

    lines += ["## Outcomes", "", "| size | " + " | ".join(["consistent", "colonized", "attacked", "contact_share",
                                                          "artefact", "signal_in_window", "timeout"]) + " |",
              "|---|" + "---|" * 7]
    for size in SIZES:
        count = Counter(_label(runs[size, k]) for k in (full if size == "full" else points))
        lines.append(f"| {size} | " + " | ".join(str(count.get(x, 0)) for x in
                                                  ["consistent", "colonized", "attacked", "contact_share",
                                                   "artefact", "signal_in_window", "timeout"]) + " |")
    lines.append("")

    lines += ["## Transitions of the points silent at the smaller size", ""]
    for small, big, keys in (("c1000", "c2000", points), ("c1000", "full", full), ("c2000", "full", full)):
        silent = [k for k in keys if runs[small, k]["outcome"] == "consistent"]
        count = Counter(_label(runs[big, k]) for k in silent)
        lines.append(f"- silent at {small} ({len(silent)}) -> {big}: " + ", ".join(f"{x} {n}" for x, n in count.most_common()))
    back = [k for k in full if runs["c1000", k]["outcome"] != "consistent" and runs["full", k]["outcome"] == "consistent"]
    lines += [f"- not silent at c1000 but silent whole: {len(back)} {back}", ""]

    lines += ["## Who breaks the silence (nearest covering civ, pc)", ""]
    for size in SIZES:
        keys = full if size == "full" else points
        d = [_culprit_distance(civs[size, k]) for k in keys if runs[size, k]["rejection_reason"] == "colonized"]
        d = [x for x in d if x is not None]
        lines.append(f"- {size}: n={len(d)}, quantiles {_quantiles(d)}, beyond 1 kpc {sum(x > 1000 for x in d)}, "
                     f"beyond 2 kpc {sum(x > 2000 for x in d)}")
    lines.append("")

    lines += ["## Criteria", "",
              "Silence lost = silent at 1 kpc, rejected at a larger size of the same galaxy (2 kpc or whole).",
              "Kept = silent at 1 kpc and silent at every larger size run. Timeouts are left out.", "",
              "| criterion | lost (quantiles) | kept (quantiles) | not silent at 1 kpc (quantiles) |", "|---|---|---|---|"]
    lost, kept, loud = [], [], []
    for k in points:
        if runs["c1000", k]["outcome"] != "consistent":
            loud.append(k)
            continue
        bigger = [runs["c2000", k]] + ([runs["full", k]] if ("full", k) in runs else [])
        if any(r["outcome"] == "rejected" for r in bigger):
            lost.append(k)
        elif all(r["outcome"] == "consistent" for r in bigger):
            kept.append(k)
    criteria = {
        "density (civs/kpc^2)": lambda k: density(runs["c1000", k]),
        "reach_obs (pc)": lambda k: max([c["expansion_radius_pc"] or 0 for c in civs["c2000", k]] or [0]),
        "reach_cfg (pc)": lambda k: reach_cfg(configs[k]),
    }
    if configs is None:
        del criteria["reach_cfg (pc)"]
    for name, f in criteria.items():
        lines.append(f"| {name} | {_quantiles([f(k) for k in lost])} | {_quantiles([f(k) for k in kept])} | "
                     f"{_quantiles([f(k) for k in loud])} |")
    lines += ["", f"lost {len(lost)}: {lost}", f"kept {len(kept)}: {kept}", ""]

    lines += ["## Points silent at 1 kpc", "", "| point | c1000 | c2000 | full | density | reach_obs | reach_cfg | culprit (pc) |",
              "|---|---|---|---|---|---|---|---|"]
    for k in points:
        if runs["c1000", k]["outcome"] != "consistent":
            continue
        full_label = _label(runs["full", k]) if ("full", k) in runs else "-"
        last = "full" if ("full", k) in runs else "c2000"
        culprit = _culprit_distance(civs[last, k])
        lines.append(f"| {k} | {_label(runs['c1000', k])} | {_label(runs['c2000', k])} | {full_label} | "
                     f"{criteria['density (civs/kpc^2)'](k):.3g} | {criteria['reach_obs (pc)'](k):.0f} | "
                     f"{criteria['reach_cfg (pc)'](k) if configs else float('nan'):.3g} | {'-' if culprit is None else round(culprit)} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=os.path.join("..", "explorations"))
    parser.add_argument("--out")
    args = parser.parse_args()
    text = report(args.root)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)


if __name__ == "__main__":
    main()
