from math import exp, log

from p3_apply_events._rates import _fraction


def _attack_damage(power, target_tech_level, config):
    # A war destroys min(1, damage_coef * power ratio) of the target per interaction period; an attack
    # event stands for one regular step of it (1 = destroyed at once).
    if target_tech_level <= 0:
        return 1.0
    per_period = min(1.0, config.damage_coef * exp(_damage_gap_scale(config) * (power - target_tech_level)))
    return _fraction(per_period, config.dt, config.interaction_period_years)


def _damage_gap_scale(config):
    # Power ratio per tech level of the energy law anchored on humanity (see _anchored): each level
    # multiplies the power by (eirp_cap_w / eirp_human_w)^(1 / (tech_cap - humanity_present_tech)).
    return log(config.eirp_cap_w / config.eirp_human_w) / (config.tech_cap - config.humanity_present_tech)


def _attribution_probability(power, target_tech_level, config):
    # A more advanced attacker hides better: probability that the victim identifies it.
    gap = power - target_tech_level
    if config.attack_stealth_per_tech <= 0 or gap <= 0:
        return 1.0
    return exp(-config.attack_stealth_per_tech * gap)
