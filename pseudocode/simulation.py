from engine import (
    Config,
    EventQueue,
    Logger,
    generate_world,
    apply_event,
    tech_growth,
    expand_front,
    update_detection,
    check_silence,
    decide,
    apply_action,
)


def run(config):
    world = generate_world(config)
    queue = EventQueue()
    log = Logger()
    now = world.now

    while now < config.horizon and world.alive() and not world.rejected:
        for scheduled in queue.pop_due(now):
            queue.push_all(apply_event(scheduled.payload, world))

        for civ in world.alive():
            tech_growth(civ, config.dt)
            expand_front(civ, config.dt)
            update_detection(civ, world)

        check_silence(world, now)

        snapshot = world.freeze()
        for civ in snapshot.alive():
            for action in decide(civ, civ.beliefs, civ.strategy):
                queue.push_all(apply_action(action, civ, snapshot, now))

        log.flush(world, now)
        now += config.dt

    return log


if __name__ == "__main__":
    run(Config())
