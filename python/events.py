import heapq
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    kind: str
    src: str
    dst: str
    t: float
    power: float = 0.0
    shared_tech_level: float = 0.0


@dataclass(order=True)
class ScheduledEvent:
    t: float
    payload: Any = field(compare=False)


class EventQueue:
    def __init__(self):
        self._heap = []

    def push(self, event):
        heapq.heappush(self._heap, ScheduledEvent(event.t, event))

    def push_all(self, events):
        for event in events:
            self.push(event)

    def pop_due(self, now):
        due = []
        while self._heap and self._heap[0].t <= now:
            due.append(heapq.heappop(self._heap).payload)
        return due
