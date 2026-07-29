from math import exp


def _danger_window(tech_level, config):
    x = (tech_level - config.danger_window_center) / config.danger_window_width
    return exp(-x * x)
