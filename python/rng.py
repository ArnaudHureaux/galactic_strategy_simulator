import random
from math import exp


class Rng:
    def __init__(self, seed):
        self._r = random.Random(seed)

    def random(self):
        return self._r.random()

    def uniform(self, low, high):
        return self._r.uniform(low, high)

    def exponential(self, scale):
        return self._r.expovariate(1.0 / scale)

    def choice(self, seq):
        return self._r.choice(seq)

    def integers(self, low, high):
        return self._r.randrange(low, high)

    def poisson(self, lam):
        target = exp(-lam)
        k = 0
        p = 1.0
        while True:
            k += 1
            p *= self._r.random()
            if p <= target:
                return k - 1


def make_rng(seed):
    return Rng(seed)


def sample_ball(radius, rng):
    while True:
        x = rng.uniform(-1.0, 1.0)
        y = rng.uniform(-1.0, 1.0)
        z = rng.uniform(-1.0, 1.0)
        if x * x + y * y + z * z <= 1.0:
            return (x * radius, y * radius, z * radius)
