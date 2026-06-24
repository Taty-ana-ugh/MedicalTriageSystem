"""
triage.py
---------
Contains:
  1. UrgencyLevel        - the 3 priority tiers from the proposal
                            (Emergency > Urgent > Normal)
  2. TriageAlgorithm      - turns raw vitals/symptoms into a numeric urgency score
  3. AgingAlgorithm       - slowly raises a waiting patient's score over time
                            so nobody waits forever
  4. TriageQueue          - the class everyone else actually imports.
                            Wraps heap.py + the two algorithms above and
                            exposes insert/pop/age_tick as event-emitting
                            hooks for Joe's WebSocket layer.

This is the main entry point for the rest of the team:
    Joe     -> imports TriageQueue, calls .insert()/.pop()/.age_tick(),
               and registers on_event() callbacks to broadcast over sockets.
    Elvis   -> imports TriageAlgorithm to score a patient on POST /patient,
               and TriageQueue.snapshot() to serve GET /queue.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Optional
import time

from heap import MaxHeapPriorityQueue, HeapNode


# ====================================================================== #
# 1. Priority tiers
# ====================================================================== #

class UrgencyLevel(IntEnum):
    """
    Base tiers from the project proposal. These set the FLOOR for a
    patient's score - the Triage Algorithm fine-tunes within a tier using
    vitals, and the Aging Algorithm nudges scores up over time, but a
    NORMAL patient who has aged a lot still won't outrank an actual
    EMERGENCY (tiers are spaced far apart on purpose - see _BAND_WIDTH).
    """
    NORMAL = 0
    URGENT = 1
    EMERGENCY = 2


# How much numeric "room" each tier gets. Keeping tiers far apart means
# aging (which adds small amounts over time) can reorder patients WITHIN
# a tier, but can't accidentally let a NORMAL patient leapfrog an
# EMERGENCY patient just by waiting a long time.
_BAND_WIDTH = 1000.0


# ====================================================================== #
# 2. Triage Algorithm — vitals/symptoms -> urgency score
# ====================================================================== #

@dataclass
class VitalSigns:
    """
    Raw inputs collected at intake. All fields optional since not every
    patient/department will measure every vital (e.g. a walk-in with a
    sprained ankle won't get a respiratory-rate reading).
    """
    heart_rate: Optional[float] = None          # beats per minute
    systolic_bp: Optional[float] = None         # mmHg
    diastolic_bp: Optional[float] = None        # mmHg
    respiratory_rate: Optional[float] = None     # breaths per minute
    oxygen_saturation: Optional[float] = None    # SpO2 %
    temperature_c: Optional[float] = None        # Celsius
    pain_score: Optional[int] = None             # self-reported 0-10
    consciousness: Optional[str] = None          # "alert" | "verbal" | "pain" | "unresponsive"


@dataclass
class TriageInput:
    """Everything the algorithm needs to score one patient at intake."""
    vitals: VitalSigns
    symptom_tags: list[str] = None  # e.g. ["chest_pain", "severe_bleeding"]
    age: Optional[int] = None

    def __post_init__(self):
        if self.symptom_tags is None:
            self.symptom_tags = []


# Symptom tags that immediately force EMERGENCY regardless of vitals -
# these mirror real-world triage red flags (ESI/CTAS-style).
_RED_FLAG_SYMPTOMS = {
    "chest_pain", "severe_bleeding", "stroke_signs", "not_breathing",
    "unresponsive", "anaphylaxis", "seizure_active", "severe_burn",
}

# Tags that bump someone to at least URGENT.
_URGENT_SYMPTOMS = {
    "high_fever", "fracture", "moderate_bleeding", "persistent_vomiting",
    "dehydration", "abdominal_pain_severe", "breathing_difficulty",
}


class TriageAlgorithm:
    """
    Converts a TriageInput into:
        (UrgencyLevel, numeric_score)

    The numeric score is what actually goes into the heap. It's computed as:

        base = tier_floor(level)            # which band we're in
        + vital_sign_points                  # how abnormal the vitals are
        + symptom_points                     # red-flag / urgent symptom hits
        + age_risk_points                     # very young / elderly get a small boost

    The result is clamped to stay inside its tier's band so a patient
    can never accidentally jump tiers purely from point accumulation -
    only an explicit red-flag symptom or genuinely critical vitals change
    the *tier*. Points only affect ordering *within* a tier.
    """

    def score(self, intake: TriageInput) -> tuple[UrgencyLevel, float]:
        level = self._determine_level(intake)
        points = self._vital_points(intake.vitals) + self._symptom_points(intake.symptom_tags) \
                 + self._age_risk_points(intake.age)

        floor = level.value * _BAND_WIDTH
        # keep extra points from spilling into the next tier's band
        capped_points = min(points, _BAND_WIDTH - 1)
        score = floor + capped_points
        return level, score

    # ------------------------------------------------------------------ #

    def _determine_level(self, intake: TriageInput) -> UrgencyLevel:
        tags = set(intake.symptom_tags)

        if tags & _RED_FLAG_SYMPTOMS:
            return UrgencyLevel.EMERGENCY

        v = intake.vitals
        if self._vitals_are_critical(v):
            return UrgencyLevel.EMERGENCY

        if tags & _URGENT_SYMPTOMS or self._vitals_are_concerning(v):
            return UrgencyLevel.URGENT

        return UrgencyLevel.NORMAL

    @staticmethod
    def _vitals_are_critical(v: VitalSigns) -> bool:
        checks = [
            v.oxygen_saturation is not None and v.oxygen_saturation < 90,
            v.systolic_bp is not None and v.systolic_bp < 90,
            v.heart_rate is not None and (v.heart_rate > 140 or v.heart_rate < 40),
            v.respiratory_rate is not None and (v.respiratory_rate > 30 or v.respiratory_rate < 8),
            v.consciousness in ("pain", "unresponsive"),
        ]
        return any(checks)

    @staticmethod
    def _vitals_are_concerning(v: VitalSigns) -> bool:
        checks = [
            v.oxygen_saturation is not None and v.oxygen_saturation < 95,
            v.systolic_bp is not None and (v.systolic_bp < 100 or v.systolic_bp > 180),
            v.heart_rate is not None and (v.heart_rate > 110 or v.heart_rate < 50),
            v.temperature_c is not None and v.temperature_c >= 39.0,
            v.pain_score is not None and v.pain_score >= 7,
        ]
        return any(checks)

    @staticmethod
    def _vital_points(v: VitalSigns) -> float:
        """Finer-grained scoring used to break ties WITHIN a tier."""
        points = 0.0
        if v.pain_score is not None:
            points += v.pain_score * 2
        if v.temperature_c is not None and v.temperature_c > 37.5:
            points += (v.temperature_c - 37.5) * 5
        if v.oxygen_saturation is not None and v.oxygen_saturation < 97:
            points += (97 - v.oxygen_saturation) * 3
        if v.heart_rate is not None and (v.heart_rate > 100 or v.heart_rate < 60):
            points += abs(v.heart_rate - 75) * 0.3
        return points

    @staticmethod
    def _symptom_points(tags: list[str]) -> float:
        points = 0.0
        tagset = set(tags)
        points += len(tagset & _RED_FLAG_SYMPTOMS) * 50
        points += len(tagset & _URGENT_SYMPTOMS) * 20
        return points

    @staticmethod
    def _age_risk_points(age: Optional[int]) -> float:
        if age is None:
            return 0.0
        if age <= 2 or age >= 75:
            return 15.0
        if age <= 12 or age >= 65:
            return 8.0
        return 0.0


# ====================================================================== #
# 3. Aging Algorithm — score creeps up the longer someone waits
# ====================================================================== #

class AgingAlgorithm:
    """
    Prevents starvation: a NORMAL patient who has been waiting a long
    time should slowly climb toward the top of their tier (and could,
    in extreme cases, be promoted into the next tier up — but never past
    EMERGENCY, which always wins).

    points_per_second  : how fast the score grows per second of waiting
    promotion_threshold: how many "extra" points accumulated before we
                          promote the patient one tier up
    max_level          : aging will never push anyone above this
                          (default URGENT, so true emergencies always stay #1)
    """

    def __init__(
        self,
        points_per_second: float = 0.05,
        promotion_threshold: float = _BAND_WIDTH * 0.9,
        max_level: UrgencyLevel = UrgencyLevel.URGENT,
    ) -> None:
        self.points_per_second = points_per_second
        self.promotion_threshold = promotion_threshold
        self.max_level = max_level

    def aged_score(self, original_score: float, level: UrgencyLevel, waited_seconds: float) -> tuple[UrgencyLevel, float]:
        """
        Given how long a patient has waited, return their (possibly
        promoted) level and new score. Pure function — no side effects,
        easy to unit test.
        """
        accrued = self.points_per_second * waited_seconds
        floor = level.value * _BAND_WIDTH
        offset = original_score - floor + accrued

        # Promote a tier if we've accrued enough AND we're allowed to
        if offset >= self.promotion_threshold and level < self.max_level:
            level = UrgencyLevel(level.value + 1)
            floor = level.value * _BAND_WIDTH
            offset = offset - self.promotion_threshold  # carry remainder into new tier

        capped_offset = min(offset, _BAND_WIDTH - 1)
        return level, floor + capped_offset


# ====================================================================== #
# 4. TriageQueue — the manager class Joe/Elvis actually integrate with
# ====================================================================== #

EventCallback = Callable[[str, Optional[HeapNode]], None]
# event name examples: "insert", "pop", "age_tick", "remove", "update_priority"


class TriageQueue:
    """
    High-level façade over MaxHeapPriorityQueue + TriageAlgorithm +
    AgingAlgorithm. This is the ONE class the rest of the team should
    import and use day-to-day.

    Event hooks
    -----------
    Call `on_event(callback)` to register a function that fires every time
    the queue changes. Joe can register a callback here that broadcasts
    the new queue state over WebSockets — he doesn't need to touch the
    heap internals at all.

        queue = TriageQueue()
        queue.on_event(lambda evt, node: websocket_broadcast(evt, node))

    Every mutating method (insert, pop, age_tick, remove, requeue) calls
    `_emit(event_name, node)` internally after the mutation completes.
    """

    def __init__(self, aging: Optional[AgingAlgorithm] = None) -> None:
        self._heap = MaxHeapPriorityQueue()
        self._triage = TriageAlgorithm()
        self._aging = aging or AgingAlgorithm()
        self._arrival_time: dict[str, float] = {}   # patient_id -> arrival timestamp
        self._base_score: dict[str, float] = {}      # patient_id -> score BEFORE aging
        self._base_level: dict[str, UrgencyLevel] = {}
        self._listeners: list[EventCallback] = []

    # ------------------------------------------------------------------ #
    # Event system (Joe's hook point)
    # ------------------------------------------------------------------ #

    def on_event(self, callback: EventCallback) -> None:
        """Register a callback fired on every queue mutation."""
        self._listeners.append(callback)

    def _emit(self, event: str, node: Optional[HeapNode]) -> None:
        for cb in self._listeners:
            cb(event, node)

    # ------------------------------------------------------------------ #
    # Core operations
    # ------------------------------------------------------------------ #

    def insert(self, patient_id: str, intake: TriageInput, data: Optional[dict] = None,
               arrival_time: Optional[float] = None) -> HeapNode:
        """
        Register a new patient: run the Triage Algorithm to get their
        starting level/score, push them onto the heap, and emit "insert".
        """
        level, score = self._triage.score(intake)
        now = arrival_time if arrival_time is not None else time.time()

        self._arrival_time[patient_id] = now
        self._base_score[patient_id] = score
        self._base_level[patient_id] = level

        payload = dict(data or {})
        payload["urgency_level"] = level.name

        node = self._heap.insert(patient_id, score, payload)
        self._emit("insert", node)
        return node

    def pop(self) -> Optional[HeapNode]:
        """Remove and return the next patient to be seen. Emits 'pop'."""
        node = self._heap.pop()
        if node is not None:
            self._arrival_time.pop(node.patient_id, None)
            self._base_score.pop(node.patient_id, None)
            self._base_level.pop(node.patient_id, None)
        self._emit("pop", node)
        return node

    def peek(self) -> Optional[HeapNode]:
        return self._heap.peek()

    def remove(self, patient_id: str) -> Optional[HeapNode]:
        """Pull a patient out of the queue without them being 'seen' (e.g. left, rerouted)."""
        node = self._heap.remove(patient_id)
        if node is not None:
            self._arrival_time.pop(patient_id, None)
            self._base_score.pop(patient_id, None)
            self._base_level.pop(patient_id, None)
        self._emit("remove", node)
        return node

    def age_tick(self, now: Optional[float] = None) -> list[HeapNode]:
        """
        Run one pass of the Aging Algorithm over EVERY waiting patient and
        update their scores accordingly. Intended to be called on a timer
        (e.g. every 30s) by Joe's WebSocket server, which then broadcasts
        the refreshed queue. Returns the list of nodes that actually changed.

        Patients are recomputed from their immutable base_score/base_level
        + elapsed wait time, NOT by repeatedly compounding the previous
        score. This keeps aging deterministic and replay-safe.
        """
        now = now if now is not None else time.time()
        changed: list[HeapNode] = []

        for patient_id in list(self._arrival_time.keys()):
            waited = now - self._arrival_time[patient_id]
            base_level = self._base_level[patient_id]
            base_score = self._base_score[patient_id]

            new_level, new_score = self._aging.aged_score(base_score, base_level, waited)

            node = self._heap.get(patient_id)
            if node is None:
                continue

            if new_score != node.priority:
                node.data["urgency_level"] = new_level.name
                updated = self._heap.update_priority(patient_id, new_score)
                if updated is not None:
                    changed.append(updated)

        self._emit("age_tick", None)
        return changed

    # ------------------------------------------------------------------ #
    # Read-only helpers for Elvis's REST endpoints
    # ------------------------------------------------------------------ #

    def snapshot(self) -> list[dict]:
        """
        Full current queue state, highest priority first. This is what
        Elvis's GET /queue endpoint and Joe's WebSocket broadcast should
        serialize to JSON.
        """
        return [
            {
                "patient_id": n.patient_id,
                "priority": round(n.priority, 2),
                "urgency_level": n.data.get("urgency_level"),
                "waited_seconds": round(time.time() - self._arrival_time.get(n.patient_id, time.time()), 1),
                **{k: v for k, v in n.data.items() if k != "urgency_level"},
            }
            for n in self._heap.to_sorted_list()
        ]

    def __len__(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return self._heap.is_empty()
