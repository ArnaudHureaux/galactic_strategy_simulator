from p1_from_strat_to_actions._compute_attack_interest_score import _compute_attack_interest_score
from p1_from_strat_to_actions._compute_max_number_of_attack import _compute_max_number_of_attack


def from_strat_to_actions(civ, config, now):
    actions = []
    if civ.strategy["broadcast"]:
        actions.append(("broadcast", None))

    scored = []
    for target_id, entry in civ.belief.items():
        # A target that went silent (dead, or too weak to be seen) is only remembered, not acted upon.
        if now - entry.last_seen_at > config.belief_memory_years:
            continue
        score = _compute_attack_interest_score(civ, entry)
        if score > 0:
            scored.append((score, target_id))
        elif entry.trust > civ.strategy["share_trust_threshold"]:
            # Between two civs at the tech cap, sharing only keeps the relationship going
            # (trust, synergy): it is applied directly instead of travelling as an event.
            actions.append(("implicit_share" if _both_at_tech_cap(civ, entry, config) else "share", target_id))

    scored.sort(reverse=True)
    for _, target_id in scored[: _compute_max_number_of_attack(civ)]:
        actions.append(("attack", target_id))

    return actions


def _both_at_tech_cap(civ, entry, config):
    # As seen by civ: a share would not change any tech level.
    return civ.tech_level >= config.tech_cap and entry.estimated_tech_level >= config.tech_cap
