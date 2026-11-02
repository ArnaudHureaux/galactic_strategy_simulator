import hashlib
import random
from dataclasses import dataclass
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

    def weighted_choice(self, seq, weights):
        return self._r.choices(seq, weights)[0]

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


@dataclass
class Streams:
    """Independent random streams derived from one seed. Each source of randomness draws
    from its own stream, so changing a parameter that only affects one of them (e.g. the
    self-destruction risk) leaves the others, and in particular the initial world, unchanged."""

    world: Rng
    humanity: Rng
    birth: Rng
    destruction: Rng
    artefact: Rng


def make_streams(seed):
    return Streams(**{name: Rng(_derive_seed(seed, name)) for name in Streams.__dataclass_fields__})


def _derive_seed(seed, name):
    digest = hashlib.sha256(f"{seed}/{name}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def sample_ball(radius, rng):
    while True:
        x = rng.uniform(-1.0, 1.0)
        y = rng.uniform(-1.0, 1.0)
        z = rng.uniform(-1.0, 1.0)
        if x * x + y * y + z * z <= 1.0:
            return (x * radius, y * radius, z * radius)
