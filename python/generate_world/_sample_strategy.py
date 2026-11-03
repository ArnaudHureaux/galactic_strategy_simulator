from config import ARCHETYPES, STRATEGY_RANGES

ARCHETYPE_NAMES = tuple(ARCHETYPES)


def _sample_strategy(config, rng):
    weights = [getattr(config, f"strategy_mix_{name}") for name in ARCHETYPE_NAMES]
    archetype = rng.weighted_choice(ARCHETYPE_NAMES, weights)
    pinned = ARCHETYPES[archetype]
    strategy = {"broadcast": rng.random() < config.broadcast_probability}
    if "broadcast" in pinned:
        strategy["broadcast"] = pinned["broadcast"]
    for name in STRATEGY_RANGES:
        low, high = getattr(config, f"{name}_low"), getattr(config, f"{name}_high")
        if name in pinned:
            value = pinned[name] + config.strategy_noise * (high - low) * rng.uniform(-1.0, 1.0)
            strategy[name] = min(high, max(low, value))
        else:
            strategy[name] = rng.uniform(low, high)
    strategy["archetype"] = archetype
    return strategy
