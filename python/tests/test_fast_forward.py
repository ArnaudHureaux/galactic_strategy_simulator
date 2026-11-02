from dataclasses import replace

import fast_forward
import simulation
from compare_fast_forward import scenario


def _full_belief_signature(world, now):
    # The signature fast_forward used to rebuild at every step.
    return tuple(
        tuple((k, round(e.trust, 9), e.attacked_me, e.last_seen_at == now) for k, e in c.belief.items())
        for c in world.civs
        if c.status == "alive"
    )


def test_incremental_belief_tracking_matches_the_full_signature(monkeypatch):
    original_step = fast_forward.FastForward.step
    previous = {}
    checked = {"compared": 0, "changed": 0}

    def step(self, world, applied, emitted, now, streams):
        signature = _full_belief_signature(world, now)
        alive = (len(world.civs), tuple(c.status for c in world.civs))
        changed = world.beliefs_changed()
        # beliefs_changed is consumed by step: put back what it saw so that step reads the same.
        world._seen_changed = changed
        world._prev_seen_count = world._seen_count
        if previous.get("alive") == alive:
            assert changed == (signature != previous["signature"]), now
            checked["compared"] += 1
            checked["changed"] += changed
        previous.update(alive=alive, signature=signature)
        return original_step(self, world, applied, emitted, now, streams)

    monkeypatch.setattr(fast_forward.FastForward, "step", step)
    log = simulation.run(replace(scenario(1.0e7), max_steps=1500), 2)
    assert log.n_steps == 1500
    assert checked["compared"] > 1000
    assert 0 < checked["changed"] < checked["compared"]
