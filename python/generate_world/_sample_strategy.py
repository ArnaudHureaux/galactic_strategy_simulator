from config import STRATEGY_RANGES


def _sample_strategy(config, rng):
    strategy = {"broadcast": rng.random() < config.broadcast_probability}
    for name in STRATEGY_RANGES:
        strategy[name] = rng.uniform(getattr(config, f"{name}_low"), getattr(config, f"{name}_high"))
    return strategy
