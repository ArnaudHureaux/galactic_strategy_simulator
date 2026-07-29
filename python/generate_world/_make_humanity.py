from generate_world._sample_lens_position import _sample_lens_position
from generate_world._new_civ import _new_civ


def _make_humanity(config, rng):
    humanity = _new_civ("human", _sample_lens_position(config, rng), config, rng, config.humanity_birth_date_years)
    humanity.is_human = True
    humanity.strategy["attack_when_trust_inferior_than"] = 0.0
    humanity.strategy["broadcast"] = False
    return humanity
