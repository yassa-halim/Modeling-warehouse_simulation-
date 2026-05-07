"""
============================================================================
simulation/event_queue.py — Hand-Coded Min-Heap Priority Queue
============================================================================
Custom binary min-heap for the DES event scheduler. Events are sorted by
event_time so the engine always processes the earliest event first.
Provides O(log n) push and pop operations via sift-up/sift-down.
NO external libraries — pure Python lists.
============================================================================
"""


class Event:
    """
    Represents a single discrete event in the simulation.

    Attributes:
        time (float):     Virtual clock time when this event fires.
        event_type (str): One of 'CUSTOMER_ORDER', 'INVENTORY_REVIEW',
                          'SHIPMENT_ARRIVAL'.
        data (dict):      Arbitrary payload (item_id, qty, etc.).
    """

    __slots__ = ("time", "event_type", "data")

    def __init__(self, time, event_type, data=None):
        self.time = time
        self.event_type = event_type
        self.data = data if data is not None else {}

    def __lt__(self, other):
        return self.time < other.time

    def __le__(self, other):
        return self.time <= other.time

    def __repr__(self):
        return f"Event(t={self.time:.2f}, type={self.event_type})"


class MinHeapEventQueue:
    """
    Binary min-heap priority queue storing Event objects.

    The heap invariant ensures _heap[parent] <= _heap[child] based on
    Event.time. This guarantees O(log n) insertion and O(log n)
    extraction of the minimum-time event.

    Methods:
        push(event):  Insert an event into the heap.
        pop():        Remove and return the earliest event.
        peek():       View the earliest event without removing it.
        is_empty():   Check if the queue has no events.
        __len__():    Return number of events in the queue.
    """

    def __init__(self):
        """Initialize an empty heap backed by a Python list."""
        self._heap = []

    def push(self, event):
        """
        Insert an event into the priority queue.

        Appends to the end of the list then sifts up to restore
        the heap invariant. Time complexity: O(log n).

        Args:
            event (Event): The event to schedule.
        """
        self._heap.append(event)
        self._sift_up(len(self._heap) - 1)

    def pop(self):
        """
        Remove and return the event with the smallest time.

        Swaps the root with the last element, removes the last,
        then sifts down from the root. Time complexity: O(log n).

        Returns:
            Event: The earliest-scheduled event.

        Raises:
            IndexError: If the queue is empty.
        """
        if not self._heap:
            raise IndexError("pop from empty event queue")

        # Swap root with last element
        self._swap(0, len(self._heap) - 1)
        min_event = self._heap.pop()
        if self._heap:
            self._sift_down(0)
        return min_event

    def peek(self):
        """Return the earliest event without removing it."""
        if not self._heap:
            return None
        return self._heap[0]

    def is_empty(self):
        """Check whether the queue contains zero events."""
        return len(self._heap) == 0

    def __len__(self):
        return len(self._heap)

    def __repr__(self):
        return f"MinHeapEventQueue(size={len(self._heap)})"

    # ── Internal heap operations ────────────────────────────────────────

    def _sift_up(self, idx):
        """
        Restore heap property by moving element at idx upward.

        Compares with parent and swaps if the child is smaller,
        repeating until the root or a valid position is reached.
        """
        while idx > 0:
            parent = (idx - 1) // 2
            if self._heap[idx] < self._heap[parent]:
                self._swap(idx, parent)
                idx = parent
            else:
                break

    def _sift_down(self, idx):
        """
        Restore heap property by moving element at idx downward.

        Compares with both children, swaps with the smaller child
        if it violates the invariant, and repeats.
        """
        size = len(self._heap)
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2

            if left < size and self._heap[left] < self._heap[smallest]:
                smallest = left
            if right < size and self._heap[right] < self._heap[smallest]:
                smallest = right

            if smallest != idx:
                self._swap(idx, smallest)
                idx = smallest
            else:
                break

    def _swap(self, i, j):
        """Swap two elements in the backing list."""
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
