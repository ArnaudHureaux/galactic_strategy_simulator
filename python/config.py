import json
from dataclasses import dataclass


@dataclass
class Config:
    seed: int = 42
    dt: float = 1000.0
    max_civs: int = 100000

    # Fast-forward over stationary regimes (see fast_forward.py).
    fast_forward: bool = True
    max_jump_years: float = 1.0e7
    jump_max_relative_change: float = 0.01

    region_radius_pc: float = 1000.0
    scale_height_pc: float = 300.0
    star_density_pc3: float = 0.08

    biochem_types: tuple = ("water", "ammonia", "silicon")
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

    @classmethod
    def from_json(cls, path):
        with open(path) as handle:
            data = json.load(handle)
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)
