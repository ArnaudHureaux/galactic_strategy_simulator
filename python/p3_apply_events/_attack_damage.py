from math import exp

from p3_apply_events._rates import _fraction


def _attack_damage(power, target_tech_level, config):
    # A war destroys min(1, damage_coef * exp(damage_gap_scale * tech gap)) of the target per
    # interaction period (tech is a log scale of power, so a gap is a power ratio); an attack
    # event stands for one regular step of it (1 = destroyed at once).
    if target_tech_level <= 0:
        return 1.0
    per_period = min(1.0, config.damage_coef * exp(config.damage_gap_scale * (power - target_tech_level)))
    return _fraction(per_period, config.dt, config.interaction_period_years)


def _attribution_probability(power, target_tech_level, config):
    # A more advanced attacker hides better: probability that the victim identifies it.
    gap = power - target_tech_level
    if config.attack_stealth_per_tech <= 0 or gap <= 0:
        return 1.0
    return exp(-config.attack_stealth_per_tech * gap)
