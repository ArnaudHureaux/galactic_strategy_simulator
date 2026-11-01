from bisect import bisect_right
from math import sqrt


def dist(a, b):
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


class NeighborIndex:
    """Civs never move: each point keeps the other points sorted by distance, so a
    radius query is a binary search instead of a scan over every civ."""

    def __init__(self):
        self.positions = []
        self.rows = []

    def add(self, position):
        new = len(self.positions)
        pairs = []
        for j, (other, (row_d, row_i)) in enumerate(zip(self.positions, self.rows)):
            d = dist(other, position)
            k = bisect_right(row_d, d)
            row_d.insert(k, d)
            row_i.insert(k, new)
            pairs.append((d, j))
        pairs.sort()
        self.positions.append(position)
        self.rows.append(([d for d, _ in pairs], [j for _, j in pairs]))
        return new

    def within(self, i, radius):
        """Indices of the other points at distance <= radius from point i, in insertion order."""
        row_d, row_i = self.rows[i]
        return sorted(row_i[: bisect_right(row_d, radius)])
