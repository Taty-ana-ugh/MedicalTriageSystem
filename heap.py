"""
heap.py
-------
A custom Max-Heap / Priority Queue implementation for the Hospital Queue
Management System.

Why a custom heap instead of Python's built-in `heapq`?
- `heapq` is a MIN-heap and only sorts plain comparable items.
- We need a MAX-heap (highest urgency score = highest priority = popped first).
- We need each entry to carry a patient's data, not just a bare number.
- We need O(1) lookup of a patient's current position for the Aging
  Algorithm to efficiently bump scores (via an index map), instead of
  scanning the whole heap.

This module has ZERO dependencies on FastAPI, sockets, or the DB. It is pure
data-structure logic so Joe can hook events onto it and Elvis/Ray can test
and integrate it without pulling in the rest of the stack.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
import itertools


@dataclass
class HeapNode:
    """
    A single entry living inside the heap.

    patient_id   : unique id (matches Elvis's DB primary key / hash table key)
    priority     : the urgency score (higher = more critical = served first)
    data         : arbitrary payload (name, symptoms, vitals, department...)
    seq          : insertion order, used as a tie-breaker so two patients
                   with the same priority are served in arrival order
                   (FIFO within the same urgency tier) rather than randomly.
    """
    patient_id: str
    priority: float
    data: dict = field(default_factory=dict)
    seq: int = 0

    def sort_key(self) -> tuple:
        # Max-heap on priority, then earliest-arrival-first as tie-breaker.
        # We negate seq because our heap logic compares "bigger is better"
        # and an earlier (smaller) seq should win ties.
        return (self.priority, -self.seq)


class MaxHeapPriorityQueue:
    """
    Array-based binary max-heap.

    Index math for a 0-indexed array:
        parent(i) = (i - 1) // 2
        left(i)   = 2 * i + 1
        right(i)  = 2 * i + 2

    Supports:
        insert(patient_id, priority, data)   -> O(log n)
        pop()                                -> O(log n)  (removes & returns highest priority)
        peek()                               -> O(1)       (highest priority, no removal)
        update_priority(patient_id, new_p)   -> O(log n)   (used by the Aging Algorithm)
        remove(patient_id)                   -> O(log n)   (e.g. patient leaves / is rerouted)
        get(patient_id)                      -> O(1)
        __len__, is_empty, to_sorted_list

    An internal `_position` dict maps patient_id -> current index in the
    array. This is what makes update_priority/remove O(log n) instead of
    O(n): we don't need to search the heap to find the patient first.
    """

    def __init__(self) -> None:
        self._array: list[HeapNode] = []
        self._position: dict[str, int] = {}   # patient_id -> index in _array
        self._counter = itertools.count()      # monotonically increasing seq

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def __len__(self) -> int:
        return len(self._array)

    def is_empty(self) -> bool:
        return len(self._array) == 0

    def insert(self, patient_id: str, priority: float, data: Optional[dict] = None) -> HeapNode:
        """
        Add a new patient to the queue.
        Raises ValueError if patient_id already exists (use update_priority instead).
        """
        if patient_id in self._position:
            raise ValueError(
                f"Patient '{patient_id}' is already in the queue. "
                f"Use update_priority() to change their score."
            )

        node = HeapNode(
            patient_id=patient_id,
            priority=priority,
            data=data or {},
            seq=next(self._counter),
        )
        self._array.append(node)
        idx = len(self._array) - 1
        self._position[patient_id] = idx
        self._sift_up(idx)
        return node

    def pop(self) -> Optional[HeapNode]:
        """
        Remove and return the highest-priority patient (root of the heap).
        Returns None if the queue is empty.
        """
        if self.is_empty():
            return None

        top = self._array[0]
        last_idx = len(self._array) - 1
        self._swap(0, last_idx)
        self._array.pop()
        del self._position[top.patient_id]

        if not self.is_empty():
            self._sift_down(0)

        return top

    def peek(self) -> Optional[HeapNode]:
        """Look at the highest-priority patient without removing them."""
        return self._array[0] if self._array else None

    def get(self, patient_id: str) -> Optional[HeapNode]:
        """Fetch a patient's current node (priority + data) without removing them."""
        idx = self._position.get(patient_id)
        return self._array[idx] if idx is not None else None

    def update_priority(self, patient_id: str, new_priority: float) -> Optional[HeapNode]:
        """
        Change a patient's urgency score and re-heapify around them.
        This is the core hook the Aging Algorithm calls repeatedly.
        Returns the updated node, or None if the patient isn't in the queue.
        """
        idx = self._position.get(patient_id)
        if idx is None:
            return None

        node = self._array[idx]
        old_priority = node.priority
        node.priority = new_priority

        if new_priority > old_priority:
            self._sift_up(idx)
        elif new_priority < old_priority:
            self._sift_down(idx)
        # if unchanged, no movement needed

        return node

    def remove(self, patient_id: str) -> Optional[HeapNode]:
        """
        Remove a specific patient from anywhere in the queue (e.g. they were
        discharged, routed to another department's queue, or left).
        """
        idx = self._position.get(patient_id)
        if idx is None:
            return None

        last_idx = len(self._array) - 1
        node = self._array[idx]
        self._swap(idx, last_idx)
        self._array.pop()
        del self._position[patient_id]

        if idx < len(self._array):
            self._sift_up(idx)
            self._sift_down(idx)

        return node

    def to_sorted_list(self) -> list[HeapNode]:
        """
        Return all patients sorted by priority (highest first) WITHOUT
        mutating the heap. O(n log n). Intended for snapshotting the full
        queue state to send over the WebSocket or REST /queue endpoint.
        """
        return sorted(self._array, key=lambda n: n.sort_key(), reverse=True)

    # ------------------------------------------------------------------ #
    # Internal heap mechanics
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parent(i: int) -> int:
        return (i - 1) // 2

    @staticmethod
    def _left(i: int) -> int:
        return 2 * i + 1

    @staticmethod
    def _right(i: int) -> int:
        return 2 * i + 2

    def _swap(self, i: int, j: int) -> None:
        self._array[i], self._array[j] = self._array[j], self._array[i]
        self._position[self._array[i].patient_id] = i
        self._position[self._array[j].patient_id] = j

    def _sift_up(self, i: int) -> None:
        while i > 0:
            p = self._parent(i)
            if self._array[i].sort_key() > self._array[p].sort_key():
                self._swap(i, p)
                i = p
            else:
                break

    def _sift_down(self, i: int) -> None:
        n = len(self._array)
        while True:
            l, r = self._left(i), self._right(i)
            largest = i

            if l < n and self._array[l].sort_key() > self._array[largest].sort_key():
                largest = l
            if r < n and self._array[r].sort_key() > self._array[largest].sort_key():
                largest = r

            if largest == i:
                break

            self._swap(i, largest)
            i = largest
