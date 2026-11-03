from math import pi

FOUR_THIRDS_PI = 4.0 / 3.0 * pi


def _front_speed(civ, config):
    return civ.colonization_aggressiveness * config.front_speed_per_tech * civ.tech_level


def _world_density(civ, config):
    # Habitable worlds per pc^3 of the civ's own biochem type.
    return config.habitable_world_density * config.world_type_fractions[config.biochem_types.index(civ.biochem_type)]


def _nb_of_world(radius, density):
    return 1.0 + density * (FOUR_THIRDS_PI * radius * radius * radius)


def _radius_for_nb_of_world(nb, density):
    return ((nb - 1.0) / density / FOUR_THIRDS_PI) ** (1.0 / 3.0)


def _update_nb_of_world(civ, config):
    civ.nb_of_world = _nb_of_world(civ.expansion_radius, _world_density(civ, config))


def _advance_fronts(world, config, advances):
    """Grow the sphere of each civ by its proposed advance ([(civ, advance)], active civs only).

    Fronts only take empty worlds: two competitors (same biochem type) stop where their spheres
    meet, sharing the remaining gap in proportion to their advances, so the result does not depend
    on the order of the civs. A competitor born inside a sphere (an enclave) does not stop it, and
    cannot grow itself."""
    proposed = {civ.id: advance for civ, advance in advances}
    reach = 0.0
    for civ, advance in advances:
        reach = max(reach, civ.expansion_radius + advance)
    radii = []
    for civ, advance in advances:
        radius = civ.expansion_radius
        factor = 1.0
        if advance > 0:
            distances, neighbors = world.neighbors_by_distance(civ)
            limit = radius + advance + reach
            for d, other in zip(distances, neighbors):
                if d > limit:
                    break
                other_advance = proposed.get(other.id)
                if other_advance is None or other.biochem_type != civ.biochem_type or d <= radius:
                    continue
                gap = d - radius - other.expansion_radius
                if gap < advance + other_advance:
                    factor = min(factor, max(0.0, gap) / (advance + other_advance))
        civ.front_blocked = advance > 0 and factor == 0.0
        radii.append(radius + advance * factor)
    for (civ, _), radius in zip(advances, radii):
        civ.expansion_radius = radius
        _update_nb_of_world(civ, config)
