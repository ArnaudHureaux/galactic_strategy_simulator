import hashlib
import json
from dataclasses import asdict, dataclass, fields
from math import isfinite

# Strategy parameters drawn uniformly per civ in [<name>_low, <name>_high].
STRATEGY_RANGES = (
    "attack_gap_min",
    "attack_gap_max",
    "caution_k",
    "attack_when_trust_inferior_than",
    "trust_default_competitor",
    "trust_default_noncompetitor",
    "share_trust_threshold",
    "colonization_aggressiveness",
)
_UNIT_RANGES = (
    "attack_when_trust_inferior_than",
    "trust_default_competitor",
    "trust_default_noncompetitor",
    "share_trust_threshold",
    "colonization_aggressiveness",
)

GROWTH_MODELS = ("logistic", "exponential")
SELF_DESTRUCTION_SHAPES = ("constant", "increasing", "danger_window")


@dataclass
class Config:
    dt: float = 1000.0
    max_civs: int = 100000
    # Deterministic compute budget: runs still going after max_steps steps end as "timeout" (0 = no limit).
    max_steps: int = 0

    # Fast-forward over stationary regimes (see fast_forward.py).
    fast_forward: bool = True
    max_jump_years: float = 1.0e7
    jump_max_relative_change: float = 0.01

    region_radius_pc: float = 1000.0
    scale_height_pc: float = 300.0

    biochem_types: tuple = ("water", "ammonia", "silicon")
    # Probability for a civ to arise on each biochem type (same order as biochem_types).
    world_type_fractions: tuple = (0.7, 0.2, 0.1)

    panspermia_range_pc: float = 300.0
    expected_bubbles: float = 5.0
    civs_per_bubble: float = 20.0
    civ_birth_rate: float = 1e-8

    last_grb_date_years: float = 1.0e9
    humanity_birth_date_years: float = 1.3799e10
    present_date_years: float = 1.38e10
    signal_window_years: float = 100.0
    artefact_window_years: float = 4.5e9
    artefact_detection_probability: float = 0.1

    tech_growth_model: str = "logistic"
    population_growth_model: str = "logistic"
    tech_cap: float = 3.0
    population_per_world: float = 1.0

    initial_tech_level: float = 0.1
    initial_population: float = 1.0

    self_destruction_risk: float = 1e-8
    self_destruction_shape: str = "danger_window"
    danger_window_center: float = 1.5
    danger_window_width: float = 0.5

    emit_radius_per_tech: float = 10.0
    passive_leakage_factor: float = 0.1
    max_broadcast_radius: float = 100.0
    probe_speed_per_tech: float = 1e-4
    max_probe_radius: float = 1e12
    probe_lifetime_per_tech: float = 1e6

    belief_memory_years: float = 0.0

    # share_catchup, share_backflow, share_synergy_bonus and share_trust_gain are rates per
    # share_period_years of continuous sharing; each share event applies one dt worth of them.
    share_period_years: float = 1000.0
    share_catchup: float = 0.5
    share_backflow: float = 0.05
    share_decay: float = 0.5
    share_synergy_bonus: float = 0.1
    share_trust_gain: float = 0.3
    forgiveness: float = 0.2

    damage_coef: float = 0.3
    attack_cost_tech: float = 0.05
    reputation_trust_drop: float = 0.3

    natural_tech_progress_mean: float = 1e-10
    natural_population_growth_mean: float = 1e-9
    max_natural_tech_progress: float = 1e-7

    # Strategy sampling (see STRATEGY_RANGES); humanity's strategy is then partly overridden.
    broadcast_probability: float = 0.5
    attack_gap_min_low: float = -2.0
    attack_gap_min_high: float = 2.0
    attack_gap_max_low: float = 2.0
    attack_gap_max_high: float = 10.0
    caution_k_low: float = 0.0
    caution_k_high: float = 3.0
    attack_when_trust_inferior_than_low: float = 0.0
    attack_when_trust_inferior_than_high: float = 1.0
    trust_default_competitor_low: float = 0.0
    trust_default_competitor_high: float = 1.0
    trust_default_noncompetitor_low: float = 0.0
    trust_default_noncompetitor_high: float = 1.0
    share_trust_threshold_low: float = 0.0
    share_trust_threshold_high: float = 1.0
    colonization_aggressiveness_low: float = 0.0
    colonization_aggressiveness_high: float = 1.0

    def __post_init__(self):
        # JSON gives lists: keep tuples so configs stay hashable and comparable.
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(f.default, tuple) and isinstance(value, list):
                setattr(self, f.name, tuple(value))
        errors = _validate(self)
        if errors:
            raise ValueError("invalid Config:\n  " + "\n  ".join(errors))

    def to_dict(self):
        return asdict(self)

    def config_hash(self):
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    @classmethod
    def from_dict(cls, data):
        unknown = sorted(set(data) - set(cls.__dataclass_fields__))
        if unknown:
            raise ValueError(f"unknown Config parameters: {', '.join(unknown)}")
        return cls(**data)

    @classmethod
    def from_json(cls, path):
        with open(path) as handle:
            return cls.from_dict(json.load(handle))


def _validate(c):
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    for f in fields(c):
        value = getattr(c, f.name)
        if isinstance(value, float) or (isinstance(value, int) and not isinstance(value, bool)):
            check(isfinite(value), f"{f.name} must be finite (got {value})")
    if errors:
        return errors

    check(c.dt > 0, "dt must be > 0")
    check(c.max_civs >= 1, "max_civs must be >= 1")
    check(c.max_steps >= 0, "max_steps must be >= 0 (0 = no limit)")
    check(c.max_jump_years > 0, "max_jump_years must be > 0")
    check(c.jump_max_relative_change > 0, "jump_max_relative_change must be > 0")

    check(c.region_radius_pc > 0, "region_radius_pc must be > 0")
    check(c.scale_height_pc > 0, "scale_height_pc must be > 0")
    check(len(c.biochem_types) >= 1, "biochem_types must not be empty")
    check(len(set(c.biochem_types)) == len(c.biochem_types), "biochem_types must be unique")
    check(len(c.world_type_fractions) == len(c.biochem_types),
          "world_type_fractions must have one entry per biochem type")
    check(all(x >= 0 for x in c.world_type_fractions), "world_type_fractions must be >= 0")
    check(abs(sum(c.world_type_fractions) - 1.0) < 1e-9, "world_type_fractions must sum to 1")

    for name in ("panspermia_range_pc", "expected_bubbles", "civs_per_bubble", "civ_birth_rate"):
        check(getattr(c, name) >= 0, f"{name} must be >= 0")

    check(c.last_grb_date_years <= c.humanity_birth_date_years < c.present_date_years,
          "dates must satisfy last_grb_date_years <= humanity_birth_date_years < present_date_years")
    check(c.signal_window_years > 0, "signal_window_years must be > 0")
    check(c.artefact_window_years >= 0, "artefact_window_years must be >= 0")

    check(c.tech_growth_model in GROWTH_MODELS, f"tech_growth_model must be one of {GROWTH_MODELS}")
    check(c.population_growth_model in GROWTH_MODELS, f"population_growth_model must be one of {GROWTH_MODELS}")
    check(c.self_destruction_shape in SELF_DESTRUCTION_SHAPES,
          f"self_destruction_shape must be one of {SELF_DESTRUCTION_SHAPES}")
    check(c.tech_cap > 0, "tech_cap must be > 0")
    check(0 < c.initial_tech_level <= c.tech_cap, "initial_tech_level must be in (0, tech_cap]")
    check(c.initial_population > 0, "initial_population must be > 0")
    check(c.population_per_world > 0, "population_per_world must be > 0")
    check(c.danger_window_width > 0, "danger_window_width must be > 0")
    check(c.share_period_years > 0, "share_period_years must be > 0")
    check(c.share_decay > 0, "share_decay must be > 0")

    for name in ("self_destruction_risk", "emit_radius_per_tech", "passive_leakage_factor",
                 "max_broadcast_radius", "probe_speed_per_tech", "max_probe_radius",
                 "probe_lifetime_per_tech", "belief_memory_years", "share_backflow",
                 "share_synergy_bonus", "damage_coef", "reputation_trust_drop",
                 "natural_tech_progress_mean", "natural_population_growth_mean",
                 "max_natural_tech_progress"):
        check(getattr(c, name) >= 0, f"{name} must be >= 0")
    # These rates are fractions closed per share period (log1p(-rate) must exist).
    for name in ("share_catchup", "share_trust_gain"):
        check(0 <= getattr(c, name) < 1, f"{name} must be in [0, 1)")
    for name in ("forgiveness", "attack_cost_tech", "artefact_detection_probability", "broadcast_probability"):
        check(0 <= getattr(c, name) <= 1, f"{name} must be in [0, 1]")

    for name in STRATEGY_RANGES:
        low, high = getattr(c, f"{name}_low"), getattr(c, f"{name}_high")
        check(low <= high, f"{name}_low must be <= {name}_high")
    for name in _UNIT_RANGES:
        low, high = getattr(c, f"{name}_low"), getattr(c, f"{name}_high")
        check(0 <= low and high <= 1, f"{name} range must lie in [0, 1]")
    check(c.caution_k_low >= 0, "caution_k_low must be >= 0")
    check(c.attack_gap_max_low >= c.attack_gap_min_high,
          "attack_gap_max_low must be >= attack_gap_min_high (every civ needs attack_gap_max >= attack_gap_min)")
    return errors
