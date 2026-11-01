from config import Config
from rng import make_rng
from events import EventQueue
from observe import Logger, capture
from generate_world import generate_world
from fast_forward import FastForward
from p0_passive_update import passive_update, final_silence_check
from p1_from_strat_to_actions import from_strat_to_actions
from p2_from_actions_to_events import from_actions_to_events
from p3_apply_events import apply_events


def run(config, seed):
    rng = make_rng(seed)
    world = generate_world(config, rng)
    queue = EventQueue()
    log = Logger()
    now = world.now
    dt = config.dt
    jump = None
    fast_forward = FastForward(config) if config.fast_forward else None

    while now < config.present_date_years and not world.rejected and not world.intractable:
        applied = queue.pop_due(now)
        for event in applied:
            apply_events(event, world, config)

        passive_update(world, config, now, rng, dt, jump)

        if len(world.civs) > config.max_civs:
            world.intractable = True
            break

        emitted = []
        for civ in world.active(now):
            actions = from_strat_to_actions(civ, config, now)
            emitted.extend(from_actions_to_events(actions, civ, world, now, config))
        queue.push_all(emitted)

        log.flush(world, now)
        log.n_steps += 1

        jump = None
        if fast_forward is not None and not world.rejected:
            jump = fast_forward.step(world, applied, emitted, now, rng)
        if jump is None:
            dt = config.dt
        else:
            # Translate in-flight events so the step ending the jump replays the stationary cycle.
            queue.shift(jump.dt - config.dt)
            dt = jump.dt
            log.n_jumps += 1
        now += dt

    if not world.rejected and not world.intractable:
        final_silence_check(world, config, rng)

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
