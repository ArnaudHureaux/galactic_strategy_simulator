from geometry import dist
from events import Event
from constants import C_PC_PER_YEAR
from p3_apply_events._attack_damage import _damaged_tech
from p3_apply_events._rates import _step_fraction


def from_actions_to_events(actions, civ, world, now, config):
    events = []
    for kind, target_id in actions:
        if kind == "broadcast":
            continue
        if kind == "implicit_share":
            # Applied at the end of the step, without travelling (see simulation.run).
            events.append(Event("implicit_share", civ.id, target_id, now))
            continue
        # No liveness check here: the sender cannot know yet; dead targets just absorb the event on arrival.
        target = world.civ(target_id)
        if target is None:
            continue
        arrival = now + dist(civ.position, target.position) / C_PC_PER_YEAR
        if kind == "attack":
            # attack_cost_tech: share of its power a civ spends per interaction period of war, lost
            # on the log scale of the energy law like the damage it inflicts (_damaged_tech).
            civ.tech_level = _damaged_tech(civ.tech_level, _step_fraction(config.attack_cost_tech, config), config)
            events.append(Event("attack", civ.id, target_id, arrival, power=civ.tech_level))
        elif kind == "share":
            events.append(Event("share", civ.id, target_id, arrival, shared_tech_level=civ.tech_level))
    return events
