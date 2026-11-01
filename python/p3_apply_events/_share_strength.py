from functools import lru_cache
from math import expm1, log1p


# A share event stands for one regular step (dt) of continuous sharing. The share_* rates
# are defined per share_period_years and rescaled here, so the yearly effect of sharing
# does not depend on dt.

def _share_fraction(rate, config):
    # Fraction closed in one step when `rate` is the fraction closed per share period.
    return _fraction(rate, config.dt, config.share_period_years)


def _share_growth(rate, config):
    # Growth factor over one step when (1 + rate) is the growth factor per share period.
    return _growth(rate, config.dt, config.share_period_years)


def _share_additive(amount, config):
    return amount * (config.dt / config.share_period_years)


@lru_cache(maxsize=None)
def _fraction(rate, dt, period):
    return -expm1(dt / period * log1p(-rate))


@lru_cache(maxsize=None)
def _growth(rate, dt, period):
    return (1 + rate) ** (dt / period)
