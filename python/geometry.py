from math import sqrt, floor


def dist(a, b):
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def neighbors_within(civs, center, radius):
    return [c for c in civs if dist(c.position, center) <= radius]


class SpatialGrid:
    def __init__(self, civs, cell_size):
        self.cell_size = cell_size
        self.all = list(civs)
        self.cells = {}
        for c in self.all:
            self.cells.setdefault(self._key(c.position), []).append(c)

    def _key(self, position):
        s = self.cell_size
        return (floor(position[0] / s), floor(position[1] / s), floor(position[2] / s))

    def query(self, center, radius):
        span = int(radius // self.cell_size) + 1
        if (2 * span + 1) ** 3 > len(self.all):
            return neighbors_within(self.all, center, radius)
        cx, cy, cz = self._key(center)
        found = []
        for ix in range(cx - span, cx + span + 1):
            for iy in range(cy - span, cy + span + 1):
                for iz in range(cz - span, cz + span + 1):
                    for c in self.cells.get((ix, iy, iz), ()):
                        if dist(c.position, center) <= radius:
                            found.append(c)
        return found
