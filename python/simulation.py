from time import perf_counter

from config import Config
from rng import make_streams
from events import EventQueue
from observe import Logger, capture, run_record, civ_records
from generate_world import generate_world
from fast_forward import FastForward
from p0_passive_update import passive_update, final_silence_check
from p1_from_strat_to_actions import from_strat_to_actions
from p2_from_actions_to_events import from_actions_to_events
from p3_apply_events import apply_events


def run(config, seed, time_budget_s=None):
    """time_budget_s is a wall-clock safety net: it depends on the machine, so a run it stops
    is not reproducible elsewhere. Prefer config.max_steps, which is deterministic."""
    start = perf_counter()
    streams = make_streams(seed)
    world = generate_world(config, streams)
    queue = EventQueue()
    log = Logger()
    now = world.now
    dt = config.dt
    jump = None
    fast_forward = FastForward(config) if config.fast_forward else None

    while now < config.present_date_years and not world.rejected and not world.intractable:
        if config.max_steps and log.n_steps >= config.max_steps:
            log.budget_exhausted = "steps"
            break
        if time_budget_s is not None and perf_counter() - start > time_budget_s:
            log.budget_exhausted = "wall_time"
            break

        applied = queue.pop_due(now)
        for event in applied:
            apply_events(event, world, config)

        passive_update(world, config, now, streams, dt, jump)

        if len(world.civs) > config.max_civs:
            world.intractable = True
            break

        emitted = []
        for civ in world.active(now):
            actions = from_strat_to_actions(civ, config, now)
            emitted.extend(from_actions_to_events(actions, civ, world, now, config))
        # Implicit shares are applied once every civ has decided, so decisions do not depend on civ order.
        for event in emitted:
            if event.kind == "implicit_share":
                apply_events(event, world, config)
        queue.push_all(e for e in emitted if e.kind != "implicit_share")

        log.flush(world, now)
        log.n_steps += 1

        jump = None
        if fast_forward is not None and not world.rejected:
            jump = fast_forward.step(world, applied, emitted, now, streams)
        if jump is None:
            dt = config.dt
        else:
            # Translate in-flight events so the step ending the jump replays the stationary cycle.
            queue.shift(jump.dt - config.dt)
            dt = jump.dt
            log.n_jumps += 1
        now += dt

    timed_out = log.budget_exhausted is not None
    if not world.rejected and not world.intractable and not timed_out:
        final_silence_check(world, config, streams)

    log.outcome = _outcome(world, timed_out)
    if log.outcome == "consistent":
        log.metadata = capture(world, now)
    end = _end_year(world, config, now, timed_out)
    log.run = run_record(world, config, seed, log, end, perf_counter() - start)
    log.civs = civ_records(world, config, seed, end)
    return log


def _end_year(world, config, now, timed_out):
    # Last simulated date: the rejection, the step where the run stopped, or the present.
    if world.rejected:
        return world.rejected_at
    if world.intractable or timed_out:
        return now
    return config.present_date_years


def _outcome(world, timed_out):
    if world.intractable:
        return "intractable"
    if world.rejected:
        return "rejected"
    if timed_out:
        return "timeout"
    return "consistent"


if __name__ == "__main__":
    run(Config(), 42)
