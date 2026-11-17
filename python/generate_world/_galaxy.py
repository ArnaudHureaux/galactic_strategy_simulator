from math import cos, exp, pi, sin, sqrt

# The annulus is drawn on a proposal disc reaching GHZ_CUTOFF widths beyond the Sun's radius: further
# out the density is below exp(-18) of its peak.
GHZ_CUTOFF = 6.0


def _galaxy_radius(config):
    return config.galactic_radius_sun_pc + GHZ_CUTOFF * config.ghz_width_pc


def _candidate_mean(density_kpc2, config):
    # Expected candidates on the proposal disc for a density given per kpc^2 at the Sun's radius.
    radius_kpc = _galaxy_radius(config) / 1000.0
    return density_kpc2 * pi * radius_kpc * radius_kpc


def _poisson_count(mean, rng):
    # Poisson draw counted as unit-rate arrivals: exact for any mean (the multiplication method of
    # Rng.poisson underflows past a few hundred).
    if mean <= 0:
        return 0
    n = 0
    t = rng.exponential(1.0)
    while t <= mean:
        n += 1
        t += rng.exponential(1.0)
    return n


def _sample_galactic_position(config, rng):
    """Uniform on the proposal disc, kept with probability exp(-(r - R_sun)^2 / (2 w^2)): thinning a
    uniform Poisson process this way gives the Gaussian annulus of the habitable zone, of peak density
    the uniform one at the Sun's radius. Returns the position in the Sun's frame (galactic centre at
    (-R_sun, 0), height from the mid-plane) and whether it is kept; always the same 5 draws."""
    r = _galaxy_radius(config) * sqrt(rng.random())
    theta = 2 * pi * rng.random()
    u = (r - config.galactic_radius_sun_pc) / config.ghz_width_pc
    kept = rng.random() < exp(-0.5 * u * u)
    z = rng.exponential(config.scale_height_pc) * rng.choice([-1, 1])
    return (r * cos(theta) - config.galactic_radius_sun_pc, r * sin(theta), z), kept


def _in_region(position, config, margin=0.0):
    # Horizontal distance from the Sun within region_radius_pc (+ margin); 0 = the whole galaxy.
    if config.region_radius_pc <= 0:
        return True
    reach = config.region_radius_pc + margin
    return position[0] * position[0] + position[1] * position[1] <= reach * reach
