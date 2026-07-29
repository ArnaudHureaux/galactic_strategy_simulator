def _compute_attack_interest_score(civ, entry):
    strategy = civ.strategy
    delta = civ.tech_level - entry.estimated_tech_level
    safe_delta = delta - strategy["caution_k"] * entry.tech_level_uncertainty
    within_window = safe_delta > strategy["attack_gap_min"] and delta < strategy["attack_gap_max"]
    if within_window and entry.trust < strategy["attack_when_trust_inferior_than"]:
        return safe_delta
    return 0.0
