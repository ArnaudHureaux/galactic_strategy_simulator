from math import inf, pi, sqrt

from constants import C_PC_PER_YEAR
from geometry import dist
from p0_passive_update._anchored import _anchored_tech
from p0_passive_update._compute_probe_speed import _probe_speed

FOUR_THIRDS_PI = 4.0 / 3.0 * pi


# Mean distance to the nearest point of a Poisson process of unit density: Gamma(4/3) (4 pi / 3)^(-1/3).
NEAREST_NEIGHBOUR = 0.5539602783650904


def _front_speed(civ, config):
    return _front_speed_at(civ, config, civ.tech_level)


def _front_speed_at(civ, config, tech):
    """Settlement front speed (pc/year): probes hop to the nearest habitable world of the civ's type
    at the probe speed, and a settled world launches its own after colonization_launch_period_years
    (Carroll-Nellenback et al. 2019, high-density static limit)."""
    # Settlement probes are the same probes: one that stops working before the next world settles
    # nothing, so a civ only colonizes once its probe range covers a hop (_colonization_tech).
    speed = _probe_speed(config, tech)
    density = _world_density(civ, config)
    if speed <= 0 or density <= 0 or civ.colonization_aggressiveness <= 0 or tech < _colonization_tech(civ, config):
        return 0.0
    hop = _hop(density)
    return civ.colonization_aggressiveness * hop / (hop / speed + config.colonization_launch_period_years)


def _hop(density):
    # Mean distance to the nearest habitable world of the civ's type (density in worlds per pc^3).
    return NEAREST_NEIGHBOUR * density ** (-1.0 / 3.0)


def _colonization_tech(civ, config):
    """Tech from which the probe range (speed * functioning time, see _probe_range) covers a hop.
    Both factors follow the anchored law, so their product does too, with the products of the anchors."""
    density = _world_density(civ, config)
    if density <= 0:
        return inf
    human = config.probe_speed_human_c * C_PC_PER_YEAR * config.probe_function_human_years
    cap = config.probe_speed_cap_c * C_PC_PER_YEAR * config.probe_function_cap_years
    return _anchored_tech(_hop(density), human, cap, config)


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
