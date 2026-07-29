def _attack_damage(power, target_tech_level, config):
    if target_tech_level <= 0:
        return 1.0
    ratio = power / target_tech_level
    return min(1.0, config.damage_coef * ratio)
