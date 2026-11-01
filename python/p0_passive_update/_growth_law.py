from math import exp, inf, log


def grow(x, r, cap, t):
    # Exact solution of dx/dt = r x (1 - x/cap) (logistic) or r x (cap is None) after time t.
    if x <= 0 or r == 0 or t <= 0:
        return x
    if cap is None:
        return x * exp(min(r * t, 700.0))
    return cap / (1 + (cap / x - 1) * exp(-r * t))


def time_to_reach(x, target, r, cap):
    if target <= x:
        return 0.0
    if x <= 0 or r <= 0:
        return inf
    if cap is None:
        return log(target / x) / r
    if target >= cap:
        return inf
    return log((cap / x - 1) / (cap / target - 1)) / r
