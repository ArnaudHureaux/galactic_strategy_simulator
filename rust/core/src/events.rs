//! Mirror of python/events.py. The queue reproduces CPython's heapq exactly: events are
//! ordered on their date only, so ties pop in an order that depends on the heap algorithm,
//! and that order matters (e.g. two shares reaching the same civ in the same step).

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Kind {
    Share,
    ImplicitShare,
    Attack,
}

#[derive(Clone, Debug)]
pub struct Event {
    pub kind: Kind,
    pub src: usize,
    pub dst: usize,
    pub t: f64,
    pub power: f64,
    pub shared_tech_level: f64,
}

#[derive(Default)]
pub struct EventQueue {
    heap: Vec<Event>,
}

impl EventQueue {
    pub fn push(&mut self, event: Event) {
        self.heap.push(event);
        let last = self.heap.len() - 1;
        self.sift_down(0, last);
    }

    /// A uniform time translation keeps the heap ordered.
    pub fn shift(&mut self, delta: f64) {
        for event in &mut self.heap {
            event.t += delta;
        }
    }

    pub fn pop_due(&mut self, now: f64) -> Vec<Event> {
        let mut due = Vec::new();
        while !self.heap.is_empty() && self.heap[0].t <= now {
            due.push(self.pop());
        }
        due
    }

    fn pop(&mut self) -> Event {
        let last = self.heap.pop().expect("heap is not empty");
        if self.heap.is_empty() {
            return last;
        }
        let top = std::mem::replace(&mut self.heap[0], last);
        self.sift_up(0);
        top
    }

    // heapq._siftdown
    fn sift_down(&mut self, start: usize, mut pos: usize) {
        while pos > start {
            let parent = (pos - 1) >> 1;
            if self.heap[pos].t < self.heap[parent].t {
                self.heap.swap(pos, parent);
                pos = parent;
            } else {
                break;
            }
        }
    }

    // heapq._siftup: move the smaller child up until hitting a leaf, then sift down.
    #[allow(clippy::neg_cmp_op_on_partial_ord)] // `not a < b`, exactly as heapq
    fn sift_up(&mut self, mut pos: usize) {
        let end = self.heap.len();
        let start = pos;
        let mut child = 2 * pos + 1;
        while child < end {
            let right = child + 1;
            if right < end && !(self.heap[child].t < self.heap[right].t) {
                child = right;
            }
            self.heap.swap(pos, child);
            pos = child;
            child = 2 * pos + 1;
        }
        self.sift_down(start, pos);
    }
}
