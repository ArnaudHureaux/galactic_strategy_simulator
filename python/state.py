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
    # Rank of the entry in its owner's belief dict (insertion order), used to keep decisions in that order.
    order: int = 0
    # (rounded trust, attacked_me) as of the last stationarity check (see fast_forward).
    signature: tuple = None


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
    # Beliefs seen recently enough to still be actionable (a superset, see recent_beliefs).
    recent: dict = field(default_factory=dict)
    attacked_by: str = None
    is_human: bool = False
    extinct_at: float = None
    extinction_cause: str = None
    probe_arrived_at_human: float = None
    artefact_rolled: bool = False
    history: list = field(default_factory=list)
    history_t: list = field(default_factory=list)
    _probes_end: float = field(default=None, repr=False, compare=False)

    def recent_beliefs(self, now, memory, ordered=True):
        """Beliefs that may still be actionable at now, in belief (insertion) order if ordered.
        Callers apply their own exact test; an entry is dropped once both forms of the memory
        test fail, which stays true as time goes on until the target is seen again."""
        recent = self.recent
        stale = [k for k, e in recent.items() if now - e.last_seen_at > memory and e.last_seen_at + memory < now]
        for k in stale:
            del recent[k]
        if not ordered or len(recent) < 2:
            return list(recent.values())
        return sorted(recent.values(), key=_entry_order)

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

    def go_extinct(self, t, cause):
        if self.status != "extinct":
            self.status = "extinct"
            self.extinct_at = t
            self.extinction_cause = cause

    def probes_end_at(self, config):
        # Probes are replenished while the creator lives, then survive it for a tech-dependent time.
        if self.extinct_at is None:
            return inf
        # A dead civ is never updated again: the date is computed once.
        if self._probes_end is None:
            tech_at_death = self.history[-1].tech_level if self.history else self.tech_level
            self._probes_end = self.extinct_at + config.probe_lifetime_per_tech * tech_at_death
        return self._probes_end


def _entry_order(entry):
    return entry.order


@dataclass
class World:
    civs: list
    humanity: Civilisation
    now: float
    config: object
    rejected: bool = False
    intractable: bool = False
    rejection_reason: str = None
    rejected_at: float = None

    def __post_init__(self):
        self.n_initial = len(self.civs)
        self._index = {c.id: c for c in self.civs}
        self._slot = {}
        self._pair_cache = {}
        self._neighbors = NeighborIndex()
        self._lo = None
        self._hi = None
        for c in self.civs:
            self._slot[c.id] = self._neighbors.add(c.position)
            self._extend_bounds(c.position)
        # Change tracking for the fast-forward belief signature (see note_* and beliefs_changed).
        self._tracking = bool(self.config.fast_forward)
        self._touched_beliefs = []
        self._detect_now = None
        self._prev_detect_now = None
        self._seen_count = 0
        self._prev_seen_count = 0
        self._seen_changed = False

    def reject(self, reason, t):
        # The run contradicts the observed silence: keep the first cause found.
        if not self.rejected:
            self.rejected = True
            self.rejection_reason = reason
            self.rejected_at = t

    def add_civ(self, civ):
        self.civs.append(civ)
        self._index[civ.id] = civ
        self._slot[civ.id] = self._neighbors.add(civ.position)
        self._extend_bounds(civ.position)

    def neighbors_within(self, civ, radius, allowed_ids):
        """Civs whose id is in allowed_ids (other than civ) at distance <= radius, in world.civs order."""
        civs = self.civs
        return [civs[j] for j in self._neighbors.within(self._slot[civ.id], radius) if civs[j].id in allowed_ids]

    def neighbor_pairs_within(self, civ, radius):
        """(other civ, distance) for every other civ at distance <= radius, in world.civs order.
        The result is cached: callers must not modify it."""
        slot = self._slot[civ.id]
        pairs = self._neighbors.within_pairs(slot, radius)
        cached = self._pair_cache.get(slot)
        if cached is not None and cached[0] is pairs:
            return cached[1]
        civs = self.civs
        result = [(civs[j], d) for j, d in pairs]
        self._pair_cache[slot] = (pairs, result)
        return result

    def neighbors_by_distance(self, civ):
        """(distances, civs) of every other civ, sorted by increasing distance."""
        row_d, row_i = self._neighbors.rows[self._slot[civ.id]]
        civs = self.civs
        return row_d, [civs[j] for j in row_i]

    # The fast-forward compares, step after step, the rounded trust and attacked_me of every
    # belief and which beliefs were refreshed this step. Instead of rebuilding that signature,
    # the world records what may have changed it since the previous step.
    def note_detection_step(self, now):
        self._prev_detect_now = self._detect_now
        self._detect_now = now
        self._prev_seen_count = self._seen_count
        self._seen_count = 0

    def note_seen(self, entry, created):
        # Called before entry.last_seen_at is set to the current step.
        if not self._tracking:
            return
        self._seen_count += 1
        if created or entry.last_seen_at != self._prev_detect_now:
            self._seen_changed = True
        if created:
            self._touched_beliefs.append(entry)

    def note_trust(self, entry):
        if self._tracking:
            self._touched_beliefs.append(entry)

    def beliefs_changed(self):
        """Whether the belief signature differs from the one at the previous call (one call per step).
        Trust converges geometrically (towards 1 through shares, 0 through reputation drops) and only
        matters through random thresholds: it is compared at 1e-9 to stop waiting for the last digits."""
        changed = self._seen_changed or self._seen_count != self._prev_seen_count
        for entry in self._touched_beliefs:
            signature = (round(entry.trust, 9), entry.attacked_me)
            if signature != entry.signature:
                entry.signature = signature
                changed = True
        self._touched_beliefs.clear()
        self._seen_changed = False
        return changed

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
        # Explicit sum: Python >= 3.12's sum() rounds differently (compensated summation).
        dx, dy, dz = (h - l for l, h in zip(self._lo, self._hi))
        diagonal = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
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
