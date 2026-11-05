def _compute_max_number_of_attack(civ, config):
    return max(1, int(_attack_capacity(civ.tech_level, civ.population_size, config)))


def _attack_capacity(tech_level, population_size, config):
    return config.attacks_per_tech_population * tech_level * population_size
