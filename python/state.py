from bisect import bisect_right
from dataclasses import dataclass, field
from math import inf

from constants import C_PC_PER_YEAR
from geometry import NeighborIndex


@dataclass
class Snapshot:
    t: float
    tech_level: float
    broadcast_radius: float
    probe_radius: float
    attacked_by: str = None


@dataclass
class BeliefEntry:
    target_id: str
    estimated_tech_level: float
    tech_level_uncertainty: float
    estimated_biochem: str
    is_competitor: bool
    trust: float
    channel: str
    attacked_me: bool = False
    position: tuple = (0.0, 0.0, 0.0)
    last_seen_at: float = None


@dataclass
class Civilisation:
    id: str
    position: tuple
    birth_year: float
    status: str
    biochem_type: str
    tech_level: float
    population_size: float
    nb_of_world: int
    natural_tech_progress: float
    natural_population_growth: float
    colonization_aggressiveness: float
    strategy: dict
    broadcast_radius: float = 0.0
    probe_speed: float = 0.0
    probe_radius: float = 0.0
    expansion_radius: float = 0.0
    belief: dict = field(default_factory=dict)
    attacked_by: str = None
    is_human: bool = False
    extinct_at: float = None
    probe_arrived_at_human: float = None
    artefact_rolled: bool = False
    history: list = field(default_factory=list)
    history_t: list = field(default_factory=list)

    def record(self, now, horizon):
        self.history_t.append(now)
        self.history.append(Snapshot(now, self.tech_level, self.broadcast_radius, self.probe_radius, self.attacked_by))
        # Keep the latest snapshot older than the horizon: it still describes the state at now - horizon.
        cutoff = now - horizon
        drop = 0
        while drop + 1 < len(self.history_t) and self.history_t[drop + 1] <= cutoff:
            drop += 1
        if drop:
            del self.history_t[:drop]
            del self.history[:drop]

    def state_at(self, t):
        if self.extinct_at is not None and t >= self.extinct_at:
            return None
        i = bisect_right(self.history_t, t) - 1
        if i < 0:
            return None
        return self.history[i]

    def go_extinct(self, t):
        if self.status != "extinct":
            self.status = "extinct"
            self.extinct_at = t

    def probes_end_at(self, config):
        # Probes are replenished while the creator lives, then survive it for a tech-dependent time.
        if self.extinct_at is None:
            return inf
        tech_at_death = self.history[-1].tech_level if self.history else self.tech_level
        return self.extinct_at + config.probe_lifetime_per_tech * tech_at_death


@dataclass
class World:
    civs: list
    humanity: Civilisation
    now: float
    config: object
    rejected: bool = False
    intractable: bool = False

    def __post_init__(self):
        self._index = {c.id: c for c in self.civs}
        self._slot = {}
        self._neighbors = NeighborIndex()
        self._lo = None
        self._hi = None
        for c in self.civs:
            self._slot[c.id] = self._neighbors.add(c.position)
            self._extend_bounds(c.position)

    def add_civ(self, civ):
        self.civs.append(civ)
        self._index[civ.id] = civ
        self._slot[civ.id] = self._neighbors.add(civ.position)
        self._extend_bounds(civ.position)

    def neighbors_within(self, civ, radius, allowed_ids):
        """Civs whose id is in allowed_ids (other than civ) at distance <= radius, in world.civs order."""
        civs = self.civs
        return [civs[j] for j in self._neighbors.within(self._slot[civ.id], radius) if civs[j].id in allowed_ids]

    def _extend_bounds(self, position):
        if self._lo is None:
            self._lo = list(position)
            self._hi = list(position)
            return
        for k in range(3):
            self._lo[k] = min(self._lo[k], position[k])
            self._hi[k] = max(self._hi[k], position[k])

    def light_crossing_years(self):
        if self._lo is None:
            return 0.0
        diagonal = sum((h - l) ** 2 for l, h in zip(self._lo, self._hi)) ** 0.5
        return diagonal / C_PC_PER_YEAR

    def history_horizon(self):
        return self.light_crossing_years() + self.config.signal_window_years

    def alive(self):
        return [c for c in self.civs if c.status == "alive"]

    def active(self, now):
        return [c for c in self.civs if c.status == "alive" and now >= c.birth_year]

    def orphan_probes(self, now):
        return [c for c in self.civs if c.status == "extinct" and now < c.probes_end_at(self.config)]

    def visible(self, now):
        # Extinct civs stay visible from afar until their last light has crossed the region.
        horizon = self.light_crossing_years()
        return [
            c for c in self.civs
            if now >= c.birth_year
            and (c.status == "alive" or (c.extinct_at is not None and now - c.extinct_at < horizon))
        ]

    def civ(self, civ_id):
        return self._index.get(civ_id)
