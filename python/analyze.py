"""First look at an exploration collected by explore.py.

Usage: python analyze.py --out DIR [--bins 4]

For every explored parameter, splits the points into equal-count bins (quantiles) and shows
the share of each outcome per bin, plus the rank correlation between the parameter and
each outcome. "consistent" runs are those compatible with the observed silence; timeouts
are runs cut by the compute budget, whose fate is unknown.
"""

import argparse
import json
import os

import pandas as pd


def load(out):
    with open(os.path.join(out, "spec.json")) as handle:
        spec = json.load(handle)
    runs = pd.read_parquet(os.path.join(out, "runs.parquet"))
    return spec, runs


def outcome_table(runs):
    labels = runs["outcome"].where(runs["rejection_reason"].isna(), runs["outcome"] + ":" + runs["rejection_reason"].fillna(""))
    return labels.value_counts().rename("runs").to_frame().assign(share=lambda t: (t["runs"] / t["runs"].sum()).round(3))


def by_parameter(runs, params, bins):
    indicators = pd.get_dummies(runs["outcome"]).astype(float)
    for column in ("consistent", "rejected", "timeout"):
        if column not in indicators:
            indicators[column] = 0.0
    lines = []
    correlations = {}
    for name in params:
        values = runs[name]
        groups = pd.qcut(values.rank(method="first"), bins, labels=False)
        table = indicators.groupby(groups).mean()[["consistent", "rejected", "timeout"]]
        table.insert(0, "range", values.groupby(groups).agg(lambda v: f"{v.min():.3g} .. {v.max():.3g}"))
        lines.append(f"\n{name}\n{table.round(2).to_string()}")
        correlations[name] = {k: values.corr(indicators[k], method="spearman") for k in ("consistent", "rejected", "timeout")}
    correlations = pd.DataFrame(correlations).T
    correlations["|consistent|"] = correlations["consistent"].abs()
    return "\n".join(lines), correlations.sort_values("|consistent|", ascending=False).drop(columns="|consistent|")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True)
    parser.add_argument("--bins", type=int, default=4)
    args = parser.parse_args()

    spec, runs = load(args.out)
    params = list(spec["parameters"])
    pd.set_option("display.width", 200)
    print(f"{len(runs)} runs\n")
    print(outcome_table(runs).to_string())
    print(f"\nwall time per run (s): median {runs['wall_time_s'].median():.0f}, "
          f"90% {runs['wall_time_s'].quantile(0.9):.0f}, max {runs['wall_time_s'].max():.0f}; "
          f"total {runs['wall_time_s'].sum() / 3600:.1f} cpu-hours")
    if "budget_exhausted" in runs:
        print(f"timeouts by budget: {runs['budget_exhausted'].value_counts().to_dict()}")
    detail, correlations = by_parameter(runs, params, args.bins)
    print("\nSpearman correlation between each parameter and each outcome (sorted by |consistent|):")
    print(correlations.round(2).to_string())
    print("\nShare of each outcome per quantile bin of each parameter:")
    print(detail)


if __name__ == "__main__":
    main()
