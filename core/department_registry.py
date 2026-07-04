"""
department_registry.py
-----------------------
Hash-map layer on top of TriageQueue: one dedicated Priority Queue per
hospital department (ER, Pediatrics, Radiology, ...).

Straight from the project brief:
    "we use a Hash Map (or Dictionary) where each key represents a
    specialty (e.g., ER, Pediatrics, Radiology) and the value is a
    dedicated Priority Queue for that department."

Each department gets its own independently-aging, independently-ordered
TriageQueue (itself backed by Tat's MaxHeapPriorityQueue). Joe's
WebSocket layer and Elvis's REST layer should go through this registry
rather than talking to a single global TriageQueue, so that department
routing (Elvis's PUT /patient/:id/route) and department-specific views
(Michelle's dashboard) have something real to operate on.

This module has ZERO new dependencies — it only imports from
core.triage, so it fits the same "pure logic, no FastAPI/DB" boundary
Tat set for heap.py and triage.py.
"""

from __future__ import annotations
import time
from typing import Optional

from core.triage import TriageQueue, AgingAlgorithm, HeapNode


DEFAULT_DEPARTMENTS = ["ER", "Pediatrics", "Radiology", "General"]


class DepartmentRegistry:
    """
    dict[str, TriageQueue] wrapper. Departments are created lazily on
    first use unless pre-seeded via `known_departments`.

    Each department's TriageQueue gets its OWN AgingAlgorithm instance,
    so wait-time pressure in a busy ER doesn't affect scoring in a quiet
    Radiology queue.
    """

    def __init__(self, known_departments: Optional[list[str]] = None) -> None:
        self._queues: dict[str, TriageQueue] = {}
        self._listeners: list = []
        for dept in (known_departments or DEFAULT_DEPARTMENTS):
            self._queues[dept] = self._new_queue()

    def _new_queue(self) -> TriageQueue:
        """
        Build a fresh TriageQueue and attach every listener already
        registered via on_event(), so a department created lazily later
        (e.g. Elvis routing a patient to a brand-new specialty) still
        broadcasts correctly instead of silently going unheard.
        """
        q = TriageQueue(aging=AgingAlgorithm())
        for cb in self._listeners:
            q.on_event(cb)
        return q

    def on_event(self, callback) -> None:
        """
        Register a callback on EVERY department queue — existing ones now,
        and any created later via get_queue(). Mirrors TriageQueue.on_event
        so Joe's server.py can hook in with the same pattern:

            departments.on_event(sync_event_handler)

        Without this, a department's insert/pop/age_tick would mutate its
        heap silently with nothing broadcasting the change over the socket.
        """
        self._listeners.append(callback)
        for q in self._queues.values():
            q.on_event(callback)

    def get_queue(self, department: str) -> TriageQueue:
        """Fetch (or lazily create) the queue for a department."""
        if department not in self._queues:
            self._queues[department] = self._new_queue()
        return self._queues[department]

    def departments(self) -> list[str]:
        return list(self._queues.keys())

    def has_department(self, department: str) -> bool:
        return department in self._queues

    def move_patient(self, patient_id: str, from_dept: str, to_dept: str) -> bool:
        """
        Reroute a patient from one department's queue to another,
        preserving their intake payload and priority score. Used by
        Elvis's PUT /patient/:id/route endpoint.

        Returns True if the move happened, False if the patient wasn't
        found in from_dept.

        Note: the heap doesn't retain the original TriageInput, so a
        moved patient keeps their existing numeric priority/urgency tier
        rather than being re-triaged from scratch in the new department.
        That's intentional -- routing is a logistics decision, not a
        medical re-assessment.
        """
        if from_dept == to_dept:
            # No-op move: succeed only if the patient is actually there.
            return self.get_queue(from_dept)._heap.get(patient_id) is not None

        source = self.get_queue(from_dept)
        node: Optional[HeapNode] = source._heap.remove(patient_id)
        if node is None:
            return False

        source._arrival_time.pop(patient_id, None)
        source._base_score.pop(patient_id, None)
        source._base_level.pop(patient_id, None)

        dest = self.get_queue(to_dept)
        dest._heap.insert(node.patient_id, node.priority, node.data)
        dest._arrival_time[patient_id] = time.time()
        dest._base_score[patient_id] = node.priority
        from core.triage import UrgencyLevel
        try:
            dest._base_level[patient_id] = UrgencyLevel[node.data.get("urgency_level", "NORMAL")]
        except KeyError:
            dest._base_level[patient_id] = UrgencyLevel.NORMAL

        return True

    def full_snapshot(self) -> dict[str, list[dict]]:
        """All departments' queues, keyed by department name. This is
        what Elvis's GET /queue should return when department-level
        breakdown is requested, and what Michelle's routing views need."""
        return {dept: q.snapshot() for dept, q in self._queues.items()}

    def total_patients(self) -> int:
        return sum(len(q) for q in self._queues.values())