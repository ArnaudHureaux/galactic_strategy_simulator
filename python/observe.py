class Logger:
    def __init__(self):
        self.rows = []
        self.outcome = None
        self.metadata = None

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
