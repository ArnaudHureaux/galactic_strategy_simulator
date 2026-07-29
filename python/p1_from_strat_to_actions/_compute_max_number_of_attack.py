def _compute_max_number_of_attack(civ):
    return max(1, int(civ.tech_level * civ.population_size))
