from functools import lru_cache
from math import expm1, log1p


# Interactions (shares, wars, reputation) are continuous processes whose rates are defined per
# interaction_period_years. Each event or observation stands for one regular step (dt) of them
# and applies the rate rescaled to that step, so their yearly effect does not depend on dt.

def _step_fraction(rate, config):
    # Fraction done in one step when `rate` is the fraction done per interaction period.
    return _cached_fraction(rate, config.dt, config.interaction_period_years)


def _step_growth(rate, config):
    # Growth factor over one step when (1 + rate) is the growth factor per interaction period.
    return _growth(rate, config.dt, config.interaction_period_years)


def _step_additive(amount, config):
    return amount * (config.dt / config.interaction_period_years)


def _fraction(rate, dt, period):
    if rate >= 1:
        return 1.0
    return -expm1(dt / period * log1p(-rate))


@lru_cache(maxsize=None)
def _cached_fraction(rate, dt, period):
    return _fraction(rate, dt, period)


@lru_cache(maxsize=None)
def _growth(rate, dt, period):
    return (1 + rate) ** (dt / period)