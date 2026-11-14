"""Fast-forward over stationary regimes.

Once every civ in contact repeats exactly the same cycle (same events received and
emitted, same beliefs, same trust up to 1e-9...), the step-by-step simulation only
replays copies of that cycle while a few slow variables drift (tech of civs that
receive no events, population of civs that are not attacked, probe radii, colonization
fronts of civs that are not attacked).
FastForward detects such a regime and plans a single long step ("jump"), a whole
number of regular steps long, that stops before anything can break it:
  - a slow variable moving by more than `jump_max_relative_change` (for a front: the
    number of worlds it holds), or crossing a decision threshold (attack window, attack
    ranking, number of attacks);
  - a probe sphere, a broadcast radius or colonization fronts reaching a civ that is not
    seen yet, or a front reaching the Sun;
  - a remembered belief expiring (belief_memory_years);
  - a fixed date (humanity birth, start of the artefact and human signal windows, present);
  - a random event (civ birth, self-destruction), placed at the first step where the
    per-step roll of the fixed-step run would succeed (same geometric law).
During the jump the event queue is translated in time, so the step that ends the jump
looks exactly like the next regular step of the stationary regime.
"""

from bisect import bisect_right
from dataclasses import dataclass
from math import exp, floor, inf, log, log1p, sqrt

from constants import C_PC_PER_YEAR
from geometry import dist
from p0_passive_update._growth_law import grow, time_to_reach
from p0_passive_update._tech_growth import _tech_rate, _tech_growth_cap
from p0_passive_update._population_growth import _population_capacity
from p0_passive_update._self_destruction_shape import _self_destruction_shape
from p0_passive_update._advance_fronts import FOUR_THIRDS_PI, _world_density
from p1_from_strat_to_actions._compute_max_number_of_attack import _attack_capacity, _compute_max_number_of_attack


@dataclass
class Jump:
    dt: float
    birth: bool = False
    extinctions: frozenset = frozenset()
    # Civs whose tech/population is held periodic by events: they replay one regular
    # step of growth instead of drifting over the whole jump.
    frozen_tech: frozenset = frozenset()
    frozen_pop: frozenset = frozenset()


class FastForward:
    def __init__(self, config):
        self.config = config
        self._quick = None
        self._beliefs_tracked = False
        self._stable_since = None

    def step(self, world, applied, emitted, now, streams):
        tech_touched, pop_touched = _touched(applied, emitted)
        # Consumed at every step, so that it always compares with the previous step.
        beliefs_changed = world.beliefs_changed()
        quick = _quick_signature(world, applied, emitted, tech_touched, pop_touched)
        if quick != self._quick:
            self._quick = quick
            self._beliefs_tracked = False
            self._stable_since = now
            return None
        # The belief part (rounded trust, attacked_me and which beliefs were refreshed this step,
        # for every alive civ) only counts from the second step of an unchanged quick signature.
        if not self._beliefs_tracked or beliefs_changed:
            self._beliefs_tracked = True
            self._stable_since = now
            return None
        # Every event still in flight must have been emitted by the stationary cycle.
        if now - self._stable_since < world.history_horizon():
            return None
        return _plan_jump(world, self.config, now, streams, tech_touched, pop_touched)


def _touched(applied, emitted):
    tech_touched = frozenset({e.dst for e in applied} | {e.src for e in emitted if e.kind == "attack"})
    pop_touched = frozenset(e.dst for e in applied if e.kind == "attack")
    return tech_touched, pop_touched


def _quick_signature(world, applied, emitted, tech_touched, pop_touched):
    # Everything that drives decisions must repeat exactly; only slow, analytically
    # integrable variables may drift: tech of civs untouched by events, population and
    # colonization front of civs that are not attacked.
    civs = []
    for c in world.civs:
        if c.status != "alive":
            civs.append((c.id, c.status))
            continue
        # Tech held periodic by events converges geometrically after each perturbation: compared
        # at 1e-9 (like trust, see World.beliefs_changed) to stop waiting for the last digits.
        tech = round(c.tech_level, 9) if c.id in tech_touched else None
        pop = c.population_size if c.id in pop_touched else None
        front = c.expansion_radius if c.id in pop_touched else None
        # The number of attacks only matters below the number of possible targets (beliefs):
        # populous civs would otherwise change it at almost every step.
        k = min(int(_attack_capacity(c.tech_level, c.population_size, world.config)), len(c.belief))
        civs.append((c.id, c.status, c.attacked_by, c.natural_tech_progress, k, tech, pop, front, c.front_blocked))
    # Events are emitted civ by civ (world.civs order) and, within a civ, shares in belief order,
    # then attacks by score: only attacks need sorting to compare the emitted sets. Arrivals
    # may tie in time and pop from the heap in any order, so applied events are sorted.
    return (
        tuple(sorted((e.kind, e.src, e.dst) for e in applied)),
        tuple((e.kind, e.src, e.dst) for e in emitted if e.kind != "attack"),
        tuple(sorted((e.kind, e.src, e.dst) for e in emitted if e.kind == "attack")),
        tuple(civs),
    )


def _plan_jump(world, config, now, streams, tech_touched, pop_touched):
    limit = config.max_jump_years
    milestones = (
        config.humanity_birth_date_years,
        config.present_date_years - config.artefact_window_years,
        config.present_date_years - config.signal_window_years,
        config.present_date_years,
    )
    for milestone in milestones:
        if milestone > now:
            # Stop one regular step early so the milestone itself is crossed at normal resolution.
            limit = min(limit, milestone - now - config.dt)
    if limit < 2 * config.dt:
        return None

    active = world.active(now)
    rel = config.jump_max_relative_change
    tech_budget = {c.id: rel * c.tech_level for c in active}
    pop_budget = {c.id: rel * c.population_size for c in active}
    # Fronts of attacked civs replay one regular step per jump (see passive_update): they do not drift.
    moving = {c.id for c in active if c.id not in pop_touched and _front_moves(c, config)}
    front_budget = {c.id: _front_budget(c, config, rel) for c in active if c.id in moving}

    limit = min(limit, _belief_expiry_limit(active, config, now))
    _decision_budgets(active, world, config, now, tech_budget, pop_budget)
    _colonization_budgets(world, active, front_budget)
    limit = min(limit, _detection_limit(world, active, config, now, tech_budget, front_budget))

    for c in active:
        if c.id not in tech_touched:
            limit = min(limit, _time_to_spend_tech_budget(c, config, tech_budget[c.id], pop_budget[c.id]))
        if c.id not in pop_touched:
            limit = min(limit, _time_to_spend_pop_budget(c, config, pop_budget[c.id]))
        if c.id in moving:
            limit = min(limit, _time_to_spend_front_budget(c, config, front_budget[c.id], tech_budget[c.id]))

    # Jumps last a whole number of regular steps so the time grid of the fixed-step run is kept.
    n_steps = floor(limit / config.dt)
    if n_steps < 2:
        return None

    # Random events: draw the index of the first step at which the per-step roll of the
    # fixed-step run would succeed (geometric law), and stop the jump there.
    draws = []
    if config.civ_birth_rate > 0:
        draws.append((_first_success(log1p(-min(1.0, config.civ_birth_rate * config.dt)), streams.birth), None))
    for c in active:
        hazard = config.self_destruction_risk * _self_destruction_shape(c.tech_level, config)
        if hazard > 0:
            draws.append((_first_success(-hazard * config.dt, streams.destruction), c.id))
    n_steps = min([n_steps] + [k for k, _ in draws])
    forced = [civ_id for k, civ_id in draws if k == n_steps]
    return Jump(
        dt=n_steps * config.dt,
        birth=None in forced,
        extinctions=frozenset(civ_id for civ_id in forced if civ_id is not None),
        frozen_tech=tech_touched,
        frozen_pop=pop_touched,
    )


def _first_success(log_survival, rng):
    if log_survival == -inf:
        return 1
    if log_survival >= 0:
        return inf
    return floor(log(1.0 - rng.random()) / log_survival) + 1


def _belief_expiry_limit(active, config, now):
    # A remembered (unseen) target stays actionable until belief_memory_years after it was last seen.
    limit = inf
    for c in active:
        for entry in c.recent_beliefs(now, config.belief_memory_years, ordered=False):
            expiry = entry.last_seen_at + config.belief_memory_years
            if entry.last_seen_at != now and expiry >= now:
                limit = min(limit, expiry - now - config.dt)
    return limit


def _decision_budgets(active, world, config, now, tech_budget, pop_budget):
    # Mirrors from_strat_to_actions: bound tech drift so no attack decision can flip.
    def shrink(civ_id, value):
        if civ_id in tech_budget:
            tech_budget[civ_id] = min(tech_budget[civ_id], value)

    for a in active:
        s = a.strategy
        scored = []
        # Largest drift of a score of `scored` through its target's uncertainty.
        widest_drift = 0.0
        # Order does not matter here: budgets are minima and scored is fully sorted below.
        for entry in a.recent_beliefs(now, config.belief_memory_years, ordered=False):
            if now - entry.last_seen_at > config.belief_memory_years:
                continue
            if entry.trust >= s["attack_when_trust_inferior_than"]:
                continue
            target_id = entry.target_id
            target = world.civ(target_id)
            lag = max(0.0, target.tech_level - entry.estimated_tech_level) if target is not None else 0.0
            delta = a.tech_level - entry.estimated_tech_level
            safe_delta = delta - s["caution_k"] * entry.tech_level_uncertainty
            # The uncertainty is refreshed at each observation and stays within [0, bound].
            drift = 0.0
            if s["caution_k"] > 0 and target is not None and target.status == "alive":
                drift = s["caution_k"] * _projected_progress_bound(a, target, config, now)
            # The score (safe_delta) must also stay on the same side of 0 (attack only if > 0).
            margin = min(abs(safe_delta - s["attack_gap_min"]), abs(s["attack_gap_max"] - delta), abs(safe_delta)) - lag - drift
            shrink(a.id, margin / 2)
            shrink(target_id, margin / 2)
            if safe_delta > s["attack_gap_min"] and delta < s["attack_gap_max"] and safe_delta > 0:
                scored.append((safe_delta, target_id))
                widest_drift = max(widest_drift, drift)

        k = _compute_max_number_of_attack(a, config)
        if len(scored) > k:
            scored.sort(reverse=True)
            # The attacker's own tech shifts every score equally: only the targets can reorder them.
            margin = scored[k - 1][0] - scored[k][0] - 2 * widest_drift
            for _, target_id in scored:
                shrink(target_id, margin / 2)
            # The number of attacks k grows with tech * population: keep both below the next integer.
            rate = config.attacks_per_tech_population
            if rate > 0:
                ceiling = (k + 1) / (rate * (a.tech_level + max(0.0, tech_budget[a.id]))) - a.population_size
                pop_budget[a.id] = min(pop_budget[a.id], ceiling)
                shrink(a.id, (k + 1) / (rate * (a.population_size + max(0.0, pop_budget[a.id]))) - a.tech_level)


def _projected_progress_bound(observer, target, config, now):
    # Largest uncertainty (_detect._projected_progress) observer may compute during the jump: from
    # the snapshots it can still see, or from the target's state within the relative budgets.
    rel = config.jump_max_relative_change
    delay = dist(observer.position, target.position) / C_PC_PER_YEAR
    low = target.tech_level * (1 - rel)
    high = target.tech_level * (1 + rel)
    rate = _tech_rate(target, config) * (1 + rel) ** config.tech_population_exponent
    for snapshot in target.states_since(now - delay):
        low = min(low, snapshot.tech_level)
        high = max(high, snapshot.tech_level)
        rate = max(rate, snapshot.tech_rate)
    return _max_progress(low, high, rate, delay, config)


def _max_progress(low, high, rate, delay, config):
    # Largest grow(x) - x for x in [low, high] (the progress grows with the rate): increasing in
    # x without cap; concave when logistic, with its maximum at cap * sqrt(q) / (1 + sqrt(q)),
    # q = exp(-rate * delay).
    cap = _tech_growth_cap(config)
    if cap is None:
        return grow(high, rate, None, delay) - high
    high = min(high, cap)
    root = sqrt(exp(-rate * delay))
    x = min(max(cap * root / (1 + root), low), high)
    return grow(x, rate, cap, delay) - x


def _detection_limit(world, active, config, now, tech_budget, front_budget):
    # Unseen pairs: limit the drift of the emitter's broadcast radius and of both fronts
    # (signals carry from sphere edge to sphere edge), and the time until the observer's
    # probe sphere reaches the target. Neighbours are scanned by increasing distance: the
    # broadcast part only concerns pairs within max_broadcast_radius of the two spheres,
    # and the probe part only the nearest unseen target, since the time for the probe
    # sphere to reach a target grows with its distance.
    limit = inf
    window_start = config.present_date_years - config.signal_window_years
    active_ids = {c.id for c in active}
    widest_front = 0.0
    for c in active:
        widest_front = max(widest_front, _front_end(c, front_budget))
    for y in active:
        if y.is_human and now < window_start:
            continue
        distances, neighbors = world.neighbors_by_distance(y)
        reach = config.max_broadcast_radius + _front_end(y, front_budget) + widest_front
        n_broadcast = bisect_right(distances, reach)
        for d, x in zip(distances[:n_broadcast], neighbors[:n_broadcast]):
            if x.id not in active_ids or x.tech_level <= 0 or _seen_now(y, x, now):
                continue
            # Share what is left of the gap between whatever can close it.
            movers = [mover for mover in (x.id, y.id) if mover in front_budget]
            n_moving = len(movers) + (x.broadcast_radius > 0)
            if n_moving == 0:
                continue
            share = (d - y.expansion_radius - x.expansion_radius - x.broadcast_radius) / n_moving
            for mover in movers:
                front_budget[mover] = min(front_budget[mover], share)
            if x.broadcast_radius > 0:
                # Broadcast radius is proportional to tech.
                critical_tech = (x.broadcast_radius + share) * x.tech_level / x.broadcast_radius
                tech_budget[x.id] = min(tech_budget[x.id], critical_tech - x.tech_level)
        # tech_budget[y.id] only changes while scanning other observers, as in a pair-by-pair scan.
        for d, x in zip(distances, neighbors):
            if d > config.max_probe_radius:
                break
            if x.id not in active_ids or _seen_now(y, x, now):
                continue
            if y.probe_radius >= d:
                return 0.0
            # Probe speed is proportional to tech: bound it by the end-of-jump tech.
            gain = 1 + max(0.0, tech_budget[y.id]) / y.tech_level if y.tech_level > 0 else 1
            speed = y.probe_speed * gain
            if speed > 0:
                limit = min(limit, (d - y.probe_radius) / speed - config.dt)
            break
    return limit


def _seen_now(y, x, now):
    entry = y.belief.get(x.id)
    return entry is not None and entry.last_seen_at == now


def _time_to_spend_pop_budget(civ, config, pop_budget):
    pop_cap = _population_capacity(civ, config)
    r_pop = civ.natural_population_growth
    if r_pop <= 0 or (pop_cap is not None and civ.population_size >= pop_cap):
        return inf
    return time_to_reach(civ.population_size, civ.population_size + pop_budget, r_pop, pop_cap)


def _time_to_spend_tech_budget(civ, config, tech_budget, pop_budget):
    # Fastest tech growth rate reachable during the jump (population only grows).
    if civ.population_size > 0:
        gain = (1 + max(0.0, pop_budget) / civ.population_size) ** config.tech_population_exponent
        r_tech = _tech_rate(civ, config) * gain
    else:
        r_tech = 0.0
    if r_tech <= 0 or civ.tech_level >= config.tech_cap:
        return inf
    return time_to_reach(civ.tech_level, civ.tech_level + tech_budget, r_tech, _tech_growth_cap(config))


def _front_moves(civ, config):
    # An enclave stays blocked until the civ around it shrinks (attack) or dies (random event).
    return (civ.colonization_aggressiveness > 0 and config.front_speed_per_tech > 0
            and civ.tech_level > 0 and not civ.front_blocked)


def _front_budget(civ, config, rel):
    # Worlds only matter through the population capacity, which a jump keeps at its start value:
    # the error on the logistic term pop / capacity is pop / capacity times the relative growth
    # of the capacity, kept within rel (a civ far below its capacity can expand a lot).
    density = _world_density(civ, config)
    capacity = _population_capacity(civ, config)
    if density <= 0 or capacity is None or civ.population_size <= 0 or civ.free_fraction <= 0:
        return inf
    growth = rel * capacity / civ.population_size
    # The territory grows by free_fraction of the shell swept by the front (see _advance_fronts).
    radius = civ.expansion_radius
    extra = civ.nb_of_world * growth / (density * civ.free_fraction * FOUR_THIRDS_PI)
    return (radius * radius * radius + extra) ** (1.0 / 3.0) - radius


def _front_end(civ, front_budget):
    budget = front_budget.get(civ.id)
    return civ.expansion_radius if budget is None else civ.expansion_radius + max(0.0, budget)


def _colonization_budgets(world, active, front_budget):
    # A front must not reach the Sun during a jump (see _check_silence).
    human = world.humanity
    for c in active:
        if c is human or c.id not in front_budget:
            continue
        gap = dist(c.position, human.position) - c.expansion_radius
        if gap > 0:
            front_budget[c.id] = min(front_budget[c.id], gap)
    # Nor two competitors come into contact (see _advance_fronts): the moving fronts share the gap.
    active_ids = {c.id for c in active}
    widest_front = 0.0
    for c in active:
        widest_front = max(widest_front, _front_end(c, front_budget))
    for x in active:
        if x.id not in front_budget:
            continue
        distances, neighbors = world.neighbors_by_distance(x)
        reach = _front_end(x, front_budget) + widest_front
        for d, y in zip(distances, neighbors):
            if d > reach:
                break
            if (y.id not in active_ids or y.biochem_type != x.biochem_type or y.id in x.contacts
                    or y is human):
                continue
            gap = d - x.expansion_radius - y.expansion_radius
            if gap <= 0:
                continue
            movers = [m for m in (x.id, y.id) if m in front_budget]
            share = gap / len(movers)
            for m in movers:
                front_budget[m] = min(front_budget[m], share)


def _time_to_spend_front_budget(civ, config, front_budget, tech_budget):
    # Fastest front reachable during the jump (front speed is proportional to tech).
    speed = civ.colonization_aggressiveness * config.front_speed_per_tech * (civ.tech_level + max(0.0, tech_budget))
    if front_budget == inf:
        return inf
    return front_budget / speed - config.dt
