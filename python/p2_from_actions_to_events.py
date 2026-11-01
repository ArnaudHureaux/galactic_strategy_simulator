from geometry import dist
from events import Event
from constants import C_PC_PER_YEAR


def from_actions_to_events(actions, civ, world, now, config):
    events = []
    for kind, target_id in actions:
        if kind == "broadcast":
            continue
        # No liveness check here: the sender cannot know yet; dead targets just absorb the event on arrival.
        target = world.civ(target_id)
        if target is None:
            continue
        arrival = now + dist(civ.position, target.position) / C_PC_PER_YEAR
        if kind == "attack":
            civ.tech_level -= config.attack_cost_tech * civ.tech_level
            events.append(Event("attack", civ.id, target_id, arrival, power=civ.tech_level))
        elif kind == "share":
            events.append(Event("share", civ.id, target_id, arrival, shared_tech_level=civ.tech_level))
    return events
