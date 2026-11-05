"""Hypothesis registry (data_model/parameters.json): status and justification of every Config
parameter and of every hard-coded modelling rule.

    python registry.py check                      # validate the registry against Config
    python registry.py doc                        # regenerate HYPOTHESES.md
    python registry.py spec --n-points 500 --out specs/x.json [--design-seed 0] [--seeds-per-point 1]
                                                  # exploration spec over every explored (E) parameter
"""

import argparse
import json
import os
from dataclasses import fields

from config import Config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "data_model", "parameters.json")
HYPOTHESES_PATH = os.path.join(ROOT, "HYPOTHESES.md")
SPEC_STATUSES = ("E", "N")


def load(path=REGISTRY_PATH):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def validate(registry):
    errors = []
    statuses = registry["statuses"]
    bases = registry["range_bases"]
    params = registry["parameters"]
    config_fields = [f.name for f in fields(Config)]

    for name in config_fields:
        if name not in params:
            errors.append(f"{name}: Config field missing from the registry")
    for name in params:
        if name not in config_fields:
            errors.append(f"{name}: registry entry is not a Config field")

    for name, entry in params.items():
        errors += _check_entry(name, entry, statuses)
        status = entry.get("status")
        if status == "E":
            errors += _check_range(name, entry, bases)
        elif "range" in entry:
            errors.append(f"{name}: only explored (E) parameters have a range")
        if status == "S" and not entry.get("source"):
            errors.append(f"{name}: sourced (S) parameters need a source")
        if status == "M" and "alternatives" in entry and not entry["alternatives"]:
            errors.append(f"{name}: empty alternatives")

    for name, rule in registry["rules"].items():
        errors += _check_entry(name, rule, statuses, required=("description", "justification", "where"))
    return errors


def _check_entry(name, entry, statuses, required=("description", "justification", "unit")):
    errors = []
    if entry.get("status") not in statuses:
        errors.append(f"{name}: status must be one of {sorted(statuses)}")
    for key in required:
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            errors.append(f"{name}: missing {key}")
    todo = entry.get("todo", [])
    if not isinstance(todo, list) or not all(isinstance(t, str) and t.strip() for t in todo):
        errors.append(f"{name}: todo must be a list of non-empty strings")
    return errors


def _check_range(name, entry, bases):
    rng = entry.get("range")
    if not isinstance(rng, dict):
        return [f"{name}: explored (E) parameters need a range"]
    errors = []
    low, high, scale = rng.get("low"), rng.get("high"), rng.get("scale")
    if scale not in ("linear", "log"):
        errors.append(f"{name}: range scale must be 'linear' or 'log'")
    if not (isinstance(low, (int, float)) and isinstance(high, (int, float)) and low < high):
        errors.append(f"{name}: range needs low < high")
    elif scale == "log" and low <= 0:
        errors.append(f"{name}: log ranges need low > 0")
    else:
        for bound in (low, high):
            try:
                Config(**{name: bound})
            except (TypeError, ValueError) as error:
                errors.append(f"{name}: range bound {bound} is not a valid Config value ({error})")
    if entry.get("range_basis") not in bases:
        errors.append(f"{name}: range_basis must be one of {sorted(bases)}")
    elif entry["range_basis"] == "provisoire" and not entry.get("todo"):
        errors.append(f"{name}: provisional ranges need a todo")
    return errors


def explored(registry):
    return {name: entry for name, entry in registry["parameters"].items() if entry["status"] == "E"}


def make_spec(registry, n_points, design_seed=0, seeds_per_point=1, base=None, description=None):
    parameters = {
        name: {"low": entry["range"]["low"], "high": entry["range"]["high"], "scale": entry["range"]["scale"]}
        for name, entry in explored(registry).items()
    }
    return {
        "description": description or f"Generated from data_model/parameters.json: every explored (E) parameter ({len(parameters)} dims).",
        "design_seed": design_seed,
        "n_points": n_points,
        "seeds_per_point": seeds_per_point,
        "base": base or {},
        "parameters": parameters,
    }


def _fmt(value):
    if isinstance(value, bool):
        return "oui" if value else "non"
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, tuple):
        return ", ".join(_fmt(v) for v in value)
    return str(value)


def _cell(text):
    return text.replace("|", "\\|").replace("\n", " ")


def _range(entry):
    rng = entry.get("range")
    if not rng:
        return ""
    return f"[{_fmt(float(rng['low']))} ; {_fmt(float(rng['high']))}] {rng['scale']} ({entry['range_basis']})"


def render_doc(registry):
    defaults = Config()
    params = registry["parameters"]
    statuses = registry["statuses"]
    lines = [
        "# Registre des hypothèses",
        "",
        "Fichier généré par `python registry.py doc` depuis [data_model/parameters.json](data_model/parameters.json) : ne pas le modifier à la main.",
        "",
        "Statuts :",
        "",
    ]
    lines += [f"- **{code}** {text}" for code, text in statuses.items()]
    counts = {code: sum(1 for e in params.values() if e["status"] == code) for code in statuses}
    open_items = sum(len(e.get("todo", [])) for e in list(params.values()) + list(registry["rules"].values()))
    lines += [
        "",
        f"{len(params)} paramètres : " + ", ".join(f"{n} {code}" for code, n in counts.items() if n) + ".",
        f"{len(registry['rules'])} règles codées en dur. {open_items} points ouverts.",
        "",
    ]
    for code, text in statuses.items():
        group = [(name, e) for name, e in params.items() if e["status"] == code]
        if not group:
            continue
        lines += [f"## {code} : {text.split(' : ')[0]}", ""]
        lines += ["| Paramètre | Valeur par défaut | Unité | Intervalle | Description | Justification | Points ouverts |",
                  "|---|---|---|---|---|---|---|"]
        for name, e in group:
            justification = e["justification"] + (f" Source : {e['source']}" if e.get("source") else "")
            if e.get("alternatives"):
                justification += " Alternatives : " + ", ".join(e["alternatives"]) + "."
            lines.append("| " + " | ".join(_cell(x) for x in (
                f"`{name}`", _fmt(getattr(defaults, name)), e["unit"], _range(e), e["description"],
                justification, " ".join(e.get("todo", [])))) + " |")
        lines.append("")
    lines += ["## Règles codées en dur", "",
              "| Règle | Statut | Où | Description | Justification | Points ouverts |",
              "|---|---|---|---|---|---|"]
    for name, r in registry["rules"].items():
        lines.append("| " + " | ".join(_cell(x) for x in (
            f"`{name}`", r["status"], r["where"], r["description"], r["justification"],
            " ".join(r.get("todo", [])))) + " |")
    lines.append("")
    return "\n".join(lines)


def _base_value(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    doc = sub.add_parser("doc")
    doc.add_argument("--out", default=HYPOTHESES_PATH)
    spec = sub.add_parser("spec")
    spec.add_argument("--n-points", type=int, required=True)
    spec.add_argument("--design-seed", type=int, default=0)
    spec.add_argument("--seeds-per-point", type=int, default=1)
    spec.add_argument("--base", action="append", default=[], metavar="KEY=VALUE")
    spec.add_argument("--out", required=True)
    args = parser.parse_args()

    registry = load()
    errors = validate(registry)
    if errors:
        raise SystemExit("invalid registry:\n  " + "\n  ".join(errors))
    if args.command == "check":
        print(f"registry OK: {len(registry['parameters'])} parameters, {len(registry['rules'])} rules")
    elif args.command == "doc":
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(render_doc(registry))
        print(f"wrote {args.out}")
    else:
        base = dict(item.split("=", 1) for item in args.base)
        made = make_spec(registry, args.n_points, args.design_seed, args.seeds_per_point,
                         {k: _base_value(v) for k, v in base.items()})
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(made, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        print(f"wrote {args.out}: {len(made['parameters'])} explored parameters")


if __name__ == "__main__":
    main()
