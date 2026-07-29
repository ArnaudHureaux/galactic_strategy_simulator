from dataclasses import dataclass, field


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

    def add_civ(self, civ):
        self.civs.append(civ)
        self._index[civ.id] = civ

    def alive(self):
        return [c for c in self.civs if c.status == "alive"]

    def active(self, now):
        return [c for c in self.civs if c.status == "alive" and now >= c.birth_year]

    def civ(self, civ_id):
        return self._index.get(civ_id)
