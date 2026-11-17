from math import cos, sin, pi, sqrt


def _sample_lens_position(config, rng):
    r = config.region_radius_pc * sqrt(rng.random())
    theta = 2 * pi * rng.random()
    z = rng.exponential(config.scale_height_pc) * rng.choice([-1, 1])
    return (r * cos(theta), r * sin(theta), z)


def _in_crop(position, config):
    # Nested galaxies (crop_radius_pc): keep only what lies within the crop radius of the axis.
    crop = config.crop_radius_pc
    return crop <= 0 or position[0] * position[0] + position[1] * position[1] <= crop * crop
