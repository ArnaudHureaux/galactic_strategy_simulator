import json

from geometry import dist


class Logger:
    def __init__(self):
        self.rows = []
        self.outcome = None
        self.metadata = None
        self.n_steps = 0
        self.n_jumps = 0
        # "steps" (config.max_steps) or "wall_time" (time_budget_s) when the run was cut short.
        self.budget_exhausted = None
        # One record for the run and one per civ, filled whatever the outcome (see run_record, civ_records).
        self.run = None
        self.civs = None

    def flush(self, world, now):
        self.rows.append(
            {
                "year": now,
                "n_alive": len(world.alive()),
                "rejected": world.rejected,
            }
        )


def capture(world, now):
    others = [c for c in world.active(now) if not c.is_human]
    n = len(others)
    if n == 0:
        return {"n_alive": 0, "humanity_detected_by_others": False}

    def mean(key):
        return sum(c.strategy[key] for c in others) / n

    return {
        "n_alive": n,
        "mean_tech": sum(c.tech_level for c in others) / n,
        "broadcast_frac": sum(1 for c in others if c.strategy["broadcast"]) / n,
        "mean_attack_when_trust": mean("attack_when_trust_inferior_than"),
        "mean_caution_k": mean("caution_k"),
        "mean_share_trust_threshold": mean("share_trust_threshold"),
        "mean_trust_default_competitor": mean("trust_default_competitor"),
        "mean_trust_default_noncompetitor": mean("trust_default_noncompetitor"),
        "humanity_detected_by_others": any(world.humanity.id in c.belief for c in world.active(now)),
    }


def run_record(world, config, seed, log, end, wall_time_s):
    """Flat record of one run: config parameters, outcome and summary metrics."""
    human = world.humanity
    record = {
        "config_hash": config.config_hash(),
        "seed": seed,
        "outcome": log.outcome,
        "rejection_reason": world.rejection_reason,
        "rejected_at": world.rejected_at,
        "end_year": end,
        "n_steps": log.n_steps,
        "n_jumps": log.n_jumps,
        "budget_exhausted": log.budget_exhausted,
        "wall_time_s": wall_time_s,
        "n_civs_initial": world.n_initial - 1,
        "n_civs_born": len(world.civs) - world.n_initial,
        "n_alive_end": sum(1 for c in world.civs if not c.is_human and c.status == "alive" and c.birth_year <= end),
        "n_extinct_end": sum(1 for c in world.civs if not c.is_human and c.status == "extinct"),
        "humanity_born": human.birth_year <= end,
        "humanity_alive": human.status == "alive" and human.birth_year <= end,
        "humanity_detected_by_others": any(human.id in c.belief for c in world.civs if c is not human),
        "humanity_reached_by_probe": any(c.probe_arrived_at_human is not None for c in world.civs),
    }
    for key, value in config.to_dict().items():
        if key in record:
            raise KeyError(f"config parameter {key} collides with a run metric")
        record[key] = json.dumps(value) if isinstance(value, tuple) else value
    return record


def civ_records(world, config, seed, end):
    """One record per civ (humanity included): traits, strategy and fate at the end of the run."""
    human = world.humanity
    config_hash = config.config_hash()
    records = []
    for c in world.civs:
        born = c.birth_year <= end
        death = c.extinct_at if c.extinct_at is not None else end
        record = {
            "config_hash": config_hash,
            "seed": seed,
            "civ_id": c.id,
            "is_human": c.is_human,
            "birth_year": c.birth_year,
            "born": born,
            "biochem_type": c.biochem_type,
            "x_pc": c.position[0],
            "y_pc": c.position[1],
            "z_pc": c.position[2],
            "distance_to_humanity_pc": dist(c.position, human.position),
            "status": c.status,
            "extinct_at": c.extinct_at,
            "extinction_cause": c.extinction_cause,
            "lifetime_years": max(0.0, death - c.birth_year),
            "tech_level": c.tech_level,
            "population_size": c.population_size,
            "natural_tech_progress": c.natural_tech_progress,
            "natural_population_growth": c.natural_population_growth,
            "probe_radius": c.probe_radius,
            "was_attacked": c.attacked_by is not None,
            "n_known_civs": len(c.belief),
            "detected_humanity": human.id in c.belief,
            "probe_reached_humanity": c.probe_arrived_at_human is not None,
        }
        for key, value in c.strategy.items():
            record[f"strategy_{key}"] = value
        records.append(record)
    return records
