from math import pi, sqrt

from geometry import dist

FOUR_THIRDS_PI = 4.0 / 3.0 * pi


def _front_speed(civ, config):
    return civ.colonization_aggressiveness * config.front_speed_per_tech * civ.tech_level


def _world_density(civ, config):
    # Habitable worlds per pc^3 of the civ's own biochem type.
    return config.habitable_world_density * config.world_type_fractions[config.biochem_types.index(civ.biochem_type)]


def _shell_worlds(radius, new_radius, density):
    return density * (FOUR_THIRDS_PI * (new_radius * new_radius * new_radius - radius * radius * radius))


def _cap_fraction(other_radius, d):
    # Share of the sky that a sphere of radius other_radius at distance d hides from the observer:
    # a spherical cap of half-angle asin(other_radius / d), (1 - cos) / 2, written without cancellation.
    s = min(1.0, other_radius / d)
    s2 = s * s
    return s2 / (2.0 * (1.0 + sqrt(1.0 - s2)))


def _shrink_worlds(civ, kept):
    # An attack shrinks the territory homothetically: kept is the share of the radius left.
    civ.expansion_radius *= kept
    civ.nb_of_world = 1.0 + (civ.nb_of_world - 1.0) * (kept * kept * kept)


def _advance_fronts(world, config, advances):
    """Grow the territory of each civ by its proposed advance ([(civ, advance)], active civs only).

    A front only takes empty worlds. The radius R is the front's reach in the free directions;
    the territory only grows in the free share of the sky, free_fraction. Two competitors (same
    biochem type) come into contact when their spheres meet, and keep that contact: from then on
    each hides from the other the cap its sphere covers, asin(R_other / d), and the free share is
    the product of (1 - cap) over the competitors in contact (caps taken as independent, so they
    may overlap). A competitor inside the sphere of another one it never met (an enclave) cannot
    grow, and does not stop the other one. The result does not depend on the order of the civs."""
    new_radius = {civ.id: civ.expansion_radius + advance for civ, advance in advances}
    reach = 0.0
    for civ, advance in advances:
        reach = max(reach, new_radius[civ.id])
    fractions = []
    for civ, advance in advances:
        free = 1.0
        if advance > 0:
            radius = new_radius[civ.id]
            distances, neighbors = world.neighbors_by_distance(civ)
            limit = radius + reach
            for d, other in zip(distances, neighbors):
                if d > limit:
                    break
                other_radius = new_radius.get(other.id)
                if other_radius is None or other.biochem_type != civ.biochem_type:
                    continue
                if other.id not in civ.contacts:
                    if d <= other.expansion_radius:
                        free = 0.0
                        break
                    if d <= civ.expansion_radius or d > radius + other_radius:
                        continue
                    # Contact is symmetric, so recording it now does not depend on the order.
                    civ.contacts.add(other.id)
                    other.contacts.add(civ.id)
                free *= 1.0 - _cap_fraction(other_radius, d)
        fractions.append(free)
    for (civ, advance), free in zip(advances, fractions):
        civ.front_blocked = advance > 0 and free == 0.0
        civ.free_fraction = free
        if advance > 0 and free > 0.0:
            radius = new_radius[civ.id]
            civ.nb_of_world += free * _shell_worlds(civ.expansion_radius, radius, _world_density(civ, config))
            civ.expansion_radius = radius


def _holds(world, civ, point, now):
    """Whether the territory of civ covers point: within its front's reach, and not in the
    shadow of an active competitor in contact (the cone its sphere hides from civ's home)."""
    d_point = dist(civ.position, point)
    if civ.expansion_radius < d_point:
        return False
    for other_id in civ.contacts:
        other = world.civ(other_id)
        if other.status != "alive" or now < other.birth_year:
            continue
        d = dist(civ.position, other.position)
        s = min(1.0, other.expansion_radius / d)
        # cos of the angle between the two directions, against cos of the cap's half-angle.
        dot = 0.0
        for k in range(3):
            dot += (other.position[k] - civ.position[k]) * (point[k] - civ.position[k])
        if d_point > 0 and dot > d * d_point * sqrt(1.0 - s * s):
            return False
    return True
