from generate_world._new_civ import _new_civ


def _make_humanity(config, rng):
    # Observed, not drawn: position near the centre of the region (the Sun), no colonization beyond
    # Earth, and a tech growth rate taking it from initial_tech_level to humanity_present_tech.
    position = (0.0, 0.0, config.sun_height_pc)
    humanity = _new_civ("human", position, config, rng, config.humanity_birth_date_years)
    humanity.is_human = True
    humanity.strategy["attack_when_trust_inferior_than"] = 0.0
    humanity.strategy["broadcast"] = False
    humanity.strategy["colonization_aggressiveness"] = 0.0
    humanity.colonization_aggressiveness = 0.0
    humanity.natural_tech_progress = config.humanity_tech_rate
    return humanity