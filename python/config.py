import hashlib
import json
from dataclasses import asdict, dataclass, fields
from math import isfinite, log

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

# Strategy archetypes (data_model/strategies/strategy_presets.json, unspecified fields at their
# strategy_vector.json default; +-inf stand for the bounds of the ranges). Each civ draws an
# archetype with probability proportional to strategy_mix_<name>, then each pinned trait is the
# archetype value plus a uniform noise of +-strategy_noise times the width of its range, clipped
# to the range. Traits an archetype does not pin (all of them for "random", and
# colonization_aggressiveness for every archetype) are drawn uniformly in their range, and
# broadcast with probability broadcast_probability.
_INF = float("inf")
ARCHETYPES = {
    "random": {},
    "full_aggressive": {"broadcast": False, "attack_gap_min": -_INF, "attack_gap_max": _INF, "caution_k": 0.0,
                        "attack_when_trust_inferior_than": 1.0, "trust_default_competitor": 0.0,
                        "trust_default_noncompetitor": 0.0, "share_trust_threshold": 0.8},
    "full_passive": {"broadcast": False, "attack_gap_min": 0.5, "attack_gap_max": 5.0, "caution_k": 1.0,
                     "attack_when_trust_inferior_than": 0.0, "trust_default_competitor": 0.2,
                     "trust_default_noncompetitor": 0.7, "share_trust_threshold": 0.8},
    "anti_competitors": {"broadcast": False, "attack_gap_min": -_INF, "attack_gap_max": _INF, "caution_k": 1.0,
                         "attack_when_trust_inferior_than": 0.3, "trust_default_competitor": 0.0,
                         "trust_default_noncompetitor": 1.0, "share_trust_threshold": 0.8},
    "anti_weaker_competitors": {"broadcast": False, "attack_gap_min": 0.0, "attack_gap_max": _INF, "caution_k": 1.5,
                                "attack_when_trust_inferior_than": 0.3, "trust_default_competitor": 0.0,
                                "trust_default_noncompetitor": 1.0, "share_trust_threshold": 0.8},
    "dark_forest": {"broadcast": False, "attack_gap_min": 0.0, "attack_gap_max": _INF, "caution_k": 2.0,
                    "attack_when_trust_inferior_than": 0.9, "trust_default_competitor": 0.0,
                    "trust_default_noncompetitor": 0.0, "share_trust_threshold": 0.8},
    "broadcaster": {"broadcast": True, "attack_gap_min": 0.5, "attack_gap_max": 5.0, "caution_k": 1.0,
                    "attack_when_trust_inferior_than": 0.0, "trust_default_competitor": 0.2,
                    "trust_default_noncompetitor": 0.7, "share_trust_threshold": 0.8},
    "cooperative": {"broadcast": True, "attack_gap_min": 0.5, "attack_gap_max": 5.0, "caution_k": 1.0,
                    "attack_when_trust_inferior_than": 0.2, "trust_default_competitor": 0.5,
                    "trust_default_noncompetitor": 0.9, "share_trust_threshold": 0.4},
}

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
    # Humanity sits at the centre of the region, sun_height_pc above the mid-plane.
    sun_height_pc: float = 20.8

    biochem_types: tuple = ("water", "ammonia", "silicon")
    # Probability for a civ to arise on each biochem type (same order as biochem_types).
    world_type_fractions: tuple = (0.7, 0.2, 0.1)

    panspermia_range_pc: float = 300.0
    expected_bubbles: float = 5.0
    civs_per_bubble: float = 20.0
    civ_birth_rate: float = 1e-8

    # The simulation starts start_lookback_years before the present, at the last sterilizing event
    # (galactic GRB, Annis 1999); the initial civs are all born then.
    start_lookback_years: float = 1.0e9
    # Initial civs are born at start + U(0, birth_spread_fraction * start_lookback_years):
    # the sterilizing event resynchronizes life, but intelligence then takes a variable time (0 = all at start).
    birth_spread_fraction: float = 0.0
    # Start of human civilization: from then on, humanity can be seen by probes on site (and attacked).
    humanity_birth_date_years: float = 1.379999e10
    present_date_years: float = 1.38e10
    # Humanity leaks radio signals since humanity_leak_years before the present (television, 1930s)
    # and listens since humanity_listening_years (Project Ozma, 1960).
    humanity_leak_years: float = 90.0
    humanity_listening_years: float = 66.0
    artefact_window_years: float = 4.5e9
    artefact_detection_probability: float = 0.1
    # Advanced civs make discreet probes: the discovery probability above is multiplied by
    # exp(-artefact_stealth_per_tech * max(0, owner tech - humanity_present_tech)) (0 = no stealth).
    artefact_stealth_per_tech: float = 0.0

    tech_growth_model: str = "logistic"
    population_growth_model: str = "logistic"
    tech_cap: float = 3.0
    population_per_world: float = 1.0

    initial_tech_level: float = 0.1
    # Humanity follows its observed trajectory: born at initial_tech_level, it reaches
    # humanity_present_tech today, humanity_tech_fraction of the way to tech_cap in orders of magnitude.
    humanity_tech_fraction: float = 1e-3
    initial_population: float = 1.0

    self_destruction_risk: float = 1e-8
    self_destruction_shape: str = "danger_window"
    danger_window_center: float = 1.5
    danger_window_width: float = 0.5

    # Laws "per tech level" are calibrated by two anchors (see p0_passive_update/_anchored.py):
    # the observed human value at humanity_present_tech and an explored value at tech_cap.
    # Emission: EIRP in watts (Arecibo planetary radar for humanity), times passive_leakage_factor
    # for a civ that does not broadcast on purpose (humanity: LTE leakage / Arecibo radar).
    eirp_human_w: float = 2.0e13
    eirp_cap_w: float = 1.0e21
    passive_leakage_factor: float = 2.0e-4
    # Humanity's own leakage is observed (LTE networks / Arecibo radar), not explored.
    humanity_leakage_factor: float = 2.0e-4
    # Sensitivity of the observers: a signal is seen while EIRP >= 4 pi d^2 seti_flux_threshold_w_m2.
    seti_flux_threshold_w_m2: float = 3.3e-25
    # Every civ leaks (continuous, all directions: seen for sure within its leak sphere); a civ that
    # broadcasts also has a beacon (full EIRP, but intermittent and beamed). Within a beacon sphere,
    # an observer detects the source at a hazard rate: each system of the source, each interaction
    # period, is caught with probability listen_coverage * beacon_duty.
    beacon_duty: float = 1e-3
    listen_coverage: float = 0.1
    # Humanity's surveys: share of the stars observed at a given distance (see _check_silence).
    seti_complete_radius_pc: float = 5.1
    seti_coverage_50pc: float = 0.037
    seti_coverage_beyond: float = 4.0e-4
    # Probe speed as a fraction of c (Voyager 1 for humanity).
    probe_speed_human_c: float = 5.67e-5
    probe_speed_cap_c: float = 0.1
    max_probe_radius: float = 1e12
    # Probes work for probe_function_*_years (Voyager 1 for humanity), which caps their range at
    # speed * functioning time beyond the civ's territory, then persist as inert artefacts for
    # probe_persistence_*_years (at least as long as they work). Both anchored on the tech at launch.
    probe_function_human_years: float = 50.0
    probe_function_cap_years: float = 1.0e6
    probe_persistence_human_years: float = 1.0e9
    probe_persistence_cap_years: float = 1.0e10

    # Colonization front (see p0_passive_update/_advance_fronts.py): settlement probes hop to the nearest
    # free habitable world at the probe speed, and a settled world launches its own probes after
    # colonization_launch_period_years (Carroll-Nellenback et al. 2019): the front advances at
    # colonization_aggressiveness * hop / (hop / probe speed + launch period) pc/year.
    colonization_launch_period_years: float = 1.0e4
    habitable_world_density: float = 0.01

    belief_memory_years: float = 0.0

    # Shares and wars are continuous processes: share_catchup, share_backflow, share_synergy_bonus,
    # share_trust_gain, damage_coef, attack_cost_tech and reputation_trust_drop are rates per
    # interaction_period_years; each event (or observation) applies one dt worth of them.
    interaction_period_years: float = 1000.0
    share_catchup: float = 0.5
    share_backflow: float = 0.05
    share_decay: float = 0.5
    share_synergy_bonus: float = 0.1
    share_trust_gain: float = 0.3
    forgiveness: float = 0.2

    # A war destroys min(1, damage_coef * power ratio) of the target per interaction period, the power
    # ratio following the energy law anchored on humanity (eirp_human_w, eirp_cap_w): each tech level of
    # advance multiplies the damage by the same factor (phase 2, points 4, 7 and 11).
    damage_coef: float = 0.3
    # The victim (and its witnesses) identifies the attacker with probability
    # exp(-attack_stealth_per_tech * max(0, attacker tech - victim tech)), drawn once per war (0 = always).
    attack_stealth_per_tech: float = 0.0
    # A civ wages war on at most max(1, int(attacks_per_tech_population * tech * population)) targets at once.
    attacks_per_tech_population: float = 1.0
    attack_cost_tech: float = 0.05
    reputation_trust_drop: float = 0.3

    natural_tech_progress_mean: float = 1e-10
    # Each civ draws its own rates uniformly in mean * [1 - spread, 1 + spread].
    natural_tech_progress_spread: float = 0.5
    natural_population_growth_spread: float = 0.5
    # Tech grows at natural_tech_progress * (1 - colonization_aggressiveness) * population ** this:
    # expanding costs tech now but brings population, hence tech later (1 = linear returns).
    tech_population_exponent: float = 1.0
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
    # Strategy archetypes (see ARCHETYPES): relative weights, normalized when drawing.
    strategy_mix_random: float = 1.0
    strategy_mix_full_aggressive: float = 0.0
    strategy_mix_full_passive: float = 0.0
    strategy_mix_anti_competitors: float = 0.0
    strategy_mix_anti_weaker_competitors: float = 0.0
    strategy_mix_dark_forest: float = 0.0
    strategy_mix_broadcaster: float = 0.0
    strategy_mix_cooperative: float = 0.0
    strategy_noise: float = 0.05

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

    @property
    def start_date_years(self):
        return self.present_date_years - self.start_lookback_years

    @property
    def humanity_present_tech(self):
        return self.initial_tech_level * (self.tech_cap / self.initial_tech_level) ** self.humanity_tech_fraction

    @property
    def humanity_tech_rate(self):
        # Rate taking humanity from initial_tech_level to humanity_present_tech since its birth
        # (inverse of time_to_reach in p0_passive_update/_growth_law.py).
        x, target = self.initial_tech_level, self.humanity_present_tech
        if target <= x:
            return 0.0
        span = self.present_date_years - self.humanity_birth_date_years
        if self.tech_growth_model == "logistic":
            return log((self.tech_cap / x - 1) / (self.tech_cap / target - 1)) / span
        return log(target / x) / span

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

    check(c.start_lookback_years > 0, "start_lookback_years must be > 0")
    check(c.start_date_years <= c.humanity_birth_date_years < c.present_date_years,
          "dates must satisfy present_date_years - start_lookback_years <= humanity_birth_date_years"
          " < present_date_years")
    check(c.humanity_leak_years > 0, "humanity_leak_years must be > 0")
    check(c.humanity_listening_years > 0, "humanity_listening_years must be > 0")
    check(c.artefact_window_years >= 0, "artefact_window_years must be >= 0")

    check(c.tech_growth_model in GROWTH_MODELS, f"tech_growth_model must be one of {GROWTH_MODELS}")
    check(c.population_growth_model in GROWTH_MODELS, f"population_growth_model must be one of {GROWTH_MODELS}")
    check(c.self_destruction_shape in SELF_DESTRUCTION_SHAPES,
          f"self_destruction_shape must be one of {SELF_DESTRUCTION_SHAPES}")
    check(c.tech_cap > 0, "tech_cap must be > 0")
    check(0 < c.initial_tech_level <= c.tech_cap, "initial_tech_level must be in (0, tech_cap]")
    check(0 < c.humanity_tech_fraction < 1, "humanity_tech_fraction must be in (0, 1)")
    check(c.initial_population > 0, "initial_population must be > 0")
    check(c.population_per_world > 0, "population_per_world must be > 0")
    check(c.danger_window_width > 0, "danger_window_width must be > 0")
    check(c.interaction_period_years > 0, "interaction_period_years must be > 0")
    check(c.share_decay > 0, "share_decay must be > 0")

    check(0 < c.eirp_human_w <= c.eirp_cap_w, "eirp_human_w must be in (0, eirp_cap_w]")
    check(0 < c.probe_speed_human_c <= c.probe_speed_cap_c < 1, "probe speeds must satisfy 0 < human <= cap < 1")
    check(c.seti_flux_threshold_w_m2 > 0, "seti_flux_threshold_w_m2 must be > 0")
    check(0 < c.probe_function_human_years <= c.probe_function_cap_years,
          "probe_function_human_years must be in (0, probe_function_cap_years]")
    check(0 < c.probe_persistence_human_years <= c.probe_persistence_cap_years,
          "probe_persistence_human_years must be in (0, probe_persistence_cap_years]")
    for name in ("self_destruction_risk", "passive_leakage_factor", "humanity_leakage_factor", "max_probe_radius",
                 "colonization_launch_period_years", "habitable_world_density",
                 "tech_population_exponent", "artefact_stealth_per_tech", "belief_memory_years", "share_backflow",
                 "share_synergy_bonus", "damage_coef", "attack_stealth_per_tech",
                 "attacks_per_tech_population", "reputation_trust_drop",
                 "natural_tech_progress_mean", "natural_population_growth_mean",
                 "max_natural_tech_progress"):
        check(getattr(c, name) >= 0, f"{name} must be >= 0")
    # These rates are fractions closed per interaction period (log1p(-rate) must exist).
    for name in ("share_catchup", "share_trust_gain"):
        check(0 <= getattr(c, name) < 1, f"{name} must be in [0, 1)")
    for name in ("beacon_duty", "listen_coverage", "seti_coverage_50pc", "seti_coverage_beyond",
                 "birth_spread_fraction", "forgiveness", "attack_cost_tech", "artefact_detection_probability", "broadcast_probability",
                 "natural_tech_progress_spread", "natural_population_growth_spread"):
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
    mix = [getattr(c, f"strategy_mix_{name}") for name in ARCHETYPES]
    check(all(w >= 0 for w in mix) and sum(mix) > 0, "strategy_mix_* must be >= 0 and not all 0")
    check(c.strategy_noise >= 0, "strategy_noise must be >= 0")
    return errors
