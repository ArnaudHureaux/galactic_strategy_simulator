from geometry import dist, SpatialGrid
from state import BeliefEntry


def _detect(world, config, now):
    active = world.active(now)
    grid = SpatialGrid(active, config.max_broadcast_radius)
    for civ in active:
        reach = max(config.max_broadcast_radius, civ.probe_radius)
        for other in grid.query(civ.position, reach):
            if other is civ:
                continue
            d = dist(civ.position, other.position)
            by_signal = other.broadcast_radius >= d
            by_probe = civ.probe_radius >= d
            if not (by_signal or by_probe):
                continue
            _observe(civ, other, "signal" if by_signal else "probe")
            if other.attacked_by in civ.belief:
                entry = civ.belief[other.attacked_by]
                entry.trust = max(0.0, entry.trust - config.reputation_trust_drop)


def _observe(civ, other, channel):
    is_competitor = civ.biochem_type == other.biochem_type
    if other.id not in civ.belief:
        civ.belief[other.id] = BeliefEntry(
            target_id=other.id,
            estimated_tech_level=other.tech_level,
            tech_level_uncertainty=0.0,
            estimated_biochem=other.biochem_type,
            is_competitor=is_competitor,
            trust=_default_trust(civ, is_competitor),
            channel=channel,
            position=other.position,
        )
    else:
        entry = civ.belief[other.id]
        entry.estimated_tech_level = other.tech_level
        entry.channel = channel
        entry.position = other.position


def _default_trust(civ, is_competitor):
    if is_competitor:
        return civ.strategy["trust_default_competitor"]
    return civ.strategy["trust_default_noncompetitor"]
