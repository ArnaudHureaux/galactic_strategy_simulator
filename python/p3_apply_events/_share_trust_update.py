from p3_apply_events._share_strength import _share_fraction


def _share_trust_update(trust, attacked_me, config):
    rate = config.share_trust_gain
    if attacked_me:
        rate *= config.forgiveness
    return trust + _share_fraction(rate, config) * (1 - trust)
