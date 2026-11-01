import heapq
from dataclasses import dataclass


@dataclass
class Event:
    kind: str
    src: str
    dst: str
    t: float
    power: float = 0.0
    shared_tech_level: float = 0.0


class ScheduledEvent:
    __slots__ = ("t", "payload")

    def __init__(self, t, payload):
        self.t = t
        self.payload = payload

    def __lt__(self, other):
        # heapq only needs <; ordering on t alone keeps ties in heap order.
        return self.t < other.t


class EventQueue:
    def __init__(self):
        self._heap = []

    def push(self, event):
        heapq.heappush(self._heap, ScheduledEvent(event.t, event))

    def push_all(self, events):
        for event in events:
            self.push(event)

    def shift(self, delta):
        # A uniform time translation keeps the heap ordered.
        for scheduled in self._heap:
            scheduled.t += delta
            scheduled.payload.t += delta

    def pop_due(self, now):
        due = []
        while self._heap and self._heap[0].t <= now:
            due.append(heapq.heappop(self._heap).payload)
        return due
