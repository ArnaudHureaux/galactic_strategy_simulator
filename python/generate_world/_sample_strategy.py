def _sample_strategy(rng):
    return {
        "broadcast": bool(rng.integers(0, 2)),
        "attack_gap_min": rng.uniform(-2.0, 2.0),
        "attack_gap_max": rng.uniform(2.0, 10.0),
        "caution_k": rng.uniform(0.0, 3.0),
        "attack_when_trust_inferior_than": rng.random(),
        "trust_default_competitor": rng.random(),
        "trust_default_noncompetitor": rng.random(),
        "share_trust_threshold": rng.random(),
        "colonization_aggressiveness": rng.random(),
    }
