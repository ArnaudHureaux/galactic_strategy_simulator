def _share_trust_update(trust, attacked_me, config):
    gain = config.share_trust_gain * (1 - trust)
    if attacked_me:
        gain *= config.forgiveness
    return trust + gain
