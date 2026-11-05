from p3_apply_events._rates import _fraction


def _attack_damage(power, target_tech_level, config):
    # A war destroys min(1, damage_coef * tech ratio) of the target per interaction period;
    # an attack event stands for one regular step of it (1 = destroyed at once).
    if target_tech_level <= 0:
        return 1.0
    ratio = power / target_tech_level
    return _fraction(min(1.0, config.damage_coef * ratio), config.dt, config.interaction_period_years)