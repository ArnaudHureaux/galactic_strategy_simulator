from config import Config
from rng import make_rng
from events import EventQueue
from observe import Logger, capture
from generate_world import generate_world
from p0_passive_update import passive_update
from p1_from_strat_to_actions import from_strat_to_actions
from p2_from_actions_to_events import from_actions_to_events
from p3_apply_events import apply_events


def run(config, seed):
    rng = make_rng(seed)
    world = generate_world(config, rng)
    queue = EventQueue()
    log = Logger()
    now = world.now

    while now < config.present_date_years and not world.rejected and not world.intractable:
        for event in queue.pop_due(now):
            apply_events(event, world, config)

        passive_update(world, config, now, rng)

        if len(world.civs) > config.max_civs:
            world.intractable = True
            break

        for civ in world.active(now):
            actions = from_strat_to_actions(civ, config)
            queue.push_all(from_actions_to_events(actions, civ, world, now, config))

        log.flush(world, now)
        now += config.dt

    log.outcome = _outcome(world)
    if log.outcome == "consistent":
        log.metadata = capture(world, now)
    return log


def _outcome(world):
    if world.intractable:
        return "intractable"
    if world.rejected:
        return "rejected"
    return "consistent"


if __name__ == "__main__":
    run(Config(), 42)
