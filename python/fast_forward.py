"""Fast-forward over stationary regimes.

Once every civ in contact repeats exactly the same cycle (same events received and
emitted, same beliefs, same trust up to 1e-9...), the step-by-step simulation only
replays copies of that cycle while a few slow variables drift (tech of civs that
receive no events, population of civs that are not attacked, probe radii).
FastForward detects such a regime and plans a single long step ("jump"), a whole
number of regular steps long, that stops before anything can break it:
  - a slow variable moving by more than `jump_max_relative_change`, or crossing a
    decision threshold (attack window, attack ranking, number of attacks);
  - a probe sphere or a broadcast radius reaching a civ that is not seen yet;
  - a remembered belief expiring (belief_memory_years);
  - a fixed date (humanity birth, start of the artefact and human signal windows, present);
  - a random event (civ birth, self-destruction), placed at the first step where the
    per-step roll of the fixed-step run would succeed (same geometric law).
During the jump the event queue is translated in time, so the step that ends the jump
looks exactly like the next regular step of the stationary regime.
"""

from dataclasses import dataclass
from math import floor, inf, log, log1p

from geometry import dist
from p0_passive_update._growth_law import time_to_reach
from p0_passive_update._tech_growth import _tech_rate, _tech_growth_cap
from p0_passive_update._population_growth import _population_capacity
from p0_passive_update._self_destruction_shape import _self_destruction_shape


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
        self._signature = None
        self._stable_since = None

    def step(self, world, applied, emitted, now, rng):
        tech_touched, pop_touched = _touched(applied, emitted)
        signature = _cycle_signature(world, applied, emitted, now, tech_touched, pop_touched)
        if signature != self._signature:
            self._signature = signature
            self._stable_since = now
            return None
        # Every event still in flight must have been emitted by the stationary cycle.
        if now - self._stable_since < world.history_horizon():
            return None
        return _plan_jump(world, self.config, now, rng, tech_touched, pop_touched)


def _touched(applied, emitted):
    tech_touched = frozenset({e.dst for e in applied} | {e.src for e in emitted if e.kind == "attack"})
    pop_touched = frozenset(e.dst for e in applied if e.kind == "attack")
    return tech_touched, pop_touched


def _cycle_signature(world, applied, emitted, now, tech_touched, pop_touched):
    # Everything that drives decisions must repeat exactly; only slow, analytically
    # integrable variables may drift: tech of civs untouched by events, population of
    # civs that are not attacked.
    civs = []
    for c in world.civs:
        if c.status != "alive":
            civs.append((c.id, c.status))
            continue
        # Trust converges geometrically (towards 1 through shares, 0 through reputation drops)
        # and only matters through random thresholds: compare it at 1e-9 to stop waiting for
        # the last float digits.
        beliefs = tuple((k, round(e.trust, 9), e.attacked_me, e.last_seen_at == now) for k, e in c.belief.items())
        tech = c.tech_level if c.id in tech_touched else None
        pop = c.population_size if c.id in pop_touched else None
        civs.append((c.id, c.status, c.attacked_by, c.natural_tech_progress,
                     int(c.tech_level * c.population_size), tech, pop, beliefs))
    return (
        tuple(civs),
        tuple(sorted((e.kind, e.src, e.dst) for e in applied)),
        tuple(sorted((e.kind, e.src, e.dst) for e in emitted)),
    )


def _plan_jump(world, config, now, rng, tech_touched, pop_touched):
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

    limit = min(limit, _belief_expiry_limit(active, config, now))
    _decision_budgets(active, world, config, now, tech_budget, pop_budget)
    limit = min(limit, _detection_limit(active, config, now, tech_budget))

    for c in active:
        if c.id not in tech_touched:
            limit = min(limit, _time_to_spend_tech_budget(c, config, tech_budget[c.id], pop_budget[c.id]))
        if c.id not in pop_touched:
            limit = min(limit, _time_to_spend_pop_budget(c, config, pop_budget[c.id]))

    # Jumps last a whole number of regular steps so the time grid of the fixed-step run is kept.
    n_steps = floor(limit / config.dt)
    if n_steps < 2:
        return None

    # Random events: draw the index of the first step at which the per-step roll of the
    # fixed-step run would succeed (geometric law), and stop the jump there.
    draws = []
    if config.civ_birth_rate > 0:
        draws.append((_first_success(log1p(-min(1.0, config.civ_birth_rate * config.dt)), rng), None))
    for c in active:
        hazard = config.self_destruction_risk * _self_destruction_shape(c.tech_level, config)
        if hazard > 0:
            draws.append((_first_success(-hazard * config.dt, rng), c.id))
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
        for entry in c.belief.values():
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
        for target_id, entry in a.belief.items():
            if now - entry.last_seen_at > config.belief_memory_years:
                continue
            if entry.trust >= s["attack_when_trust_inferior_than"]:
                continue
            target = world.civ(target_id)
            lag = max(0.0, target.tech_level - entry.estimated_tech_level) if target is not None else 0.0
            delta = a.tech_level - entry.estimated_tech_level
            safe_delta = delta - s["caution_k"] * entry.tech_level_uncertainty
            # The score (safe_delta) must also stay on the same side of 0 (attack only if > 0).
            margin = min(abs(safe_delta - s["attack_gap_min"]), abs(s["attack_gap_max"] - delta), abs(safe_delta)) - lag
            shrink(a.id, margin / 2)
            shrink(target_id, margin / 2)
            if safe_delta > s["attack_gap_min"] and delta < s["attack_gap_max"] and safe_delta > 0:
                scored.append((safe_delta, target_id))

        k = max(1, int(a.tech_level * a.population_size))
        if len(scored) > k:
            scored.sort(reverse=True)
            # The attacker's own tech shifts every score equally: only the targets can reorder them.
            margin = scored[k - 1][0] - scored[k][0]
            for _, target_id in scored:
                shrink(target_id, margin / 2)
            # The number of attacks k grows with tech * population: keep both below the next integer.
            ceiling = (k + 1) / (a.tech_level + max(0.0, tech_budget[a.id])) - a.population_size
            pop_budget[a.id] = min(pop_budget[a.id], ceiling)
            shrink(a.id, (k + 1) / (a.population_size + max(0.0, pop_budget[a.id])) - a.tech_level)


def _detection_limit(active, config, now, tech_budget):
    # Unseen pairs: limit the drift of the emitter's broadcast radius and the time
    # until the observer's probe sphere reaches the target.
    limit = inf
    window_start = config.present_date_years - config.signal_window_years
    for y in active:
        if y.is_human and now < window_start:
            continue
        for x in active:
            if x is y:
                continue
            entry = y.belief.get(x.id)
            if entry is not None and entry.last_seen_at == now:
                continue
            d = dist(y.position, x.position)
            if d <= config.max_broadcast_radius and x.tech_level > 0:
                # Broadcast radius is proportional to tech.
                critical_tech = d * x.tech_level / x.broadcast_radius if x.broadcast_radius > 0 else inf
                tech_budget[x.id] = min(tech_budget[x.id], critical_tech - x.tech_level)
            if d <= config.max_probe_radius:
                if y.probe_radius >= d:
                    return 0.0
                # Probe speed is proportional to tech: bound it by the end-of-jump tech.
                gain = 1 + max(0.0, tech_budget[y.id]) / y.tech_level if y.tech_level > 0 else 1
                speed = y.probe_speed * gain
                if speed > 0:
                    limit = min(limit, (d - y.probe_radius) / speed - config.dt)
    return limit


def _time_to_spend_pop_budget(civ, config, pop_budget):
    pop_cap = _population_capacity(civ, config)
    r_pop = civ.natural_population_growth
    if r_pop <= 0 or (pop_cap is not None and civ.population_size >= pop_cap):
        return inf
    return time_to_reach(civ.population_size, civ.population_size + pop_budget, r_pop, pop_cap)


def _time_to_spend_tech_budget(civ, config, tech_budget, pop_budget):
    # Fastest tech growth rate reachable during the jump (population only grows).
    r_tech = _tech_rate(civ) * (1 + max(0.0, pop_budget) / civ.population_size) if civ.population_size > 0 else 0.0
    if r_tech <= 0 or civ.tech_level >= config.tech_cap:
        return inf
    return time_to_reach(civ.tech_level, civ.tech_level + tech_budget, r_tech, _tech_growth_cap(config))
