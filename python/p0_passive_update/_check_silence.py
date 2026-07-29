def _check_silence(world, config, now):
    human = world.humanity
    contacted = len(human.belief) > 0 or human.attacked_by is not None
    if now < config.present_date_years and contacted:
        world.rejected = True
