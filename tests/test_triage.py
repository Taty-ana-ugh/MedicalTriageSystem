"""
test_triage.py
--------------
Pytest suite for heap.py and triage.py.

Run with:
    pytest test_triage.py -v
"""

import time
import pytest

from core.heap import MaxHeapPriorityQueue
from core.triage import (
    TriageQueue, TriageAlgorithm, AgingAlgorithm,
    TriageInput, VitalSigns, UrgencyLevel,
)


# ====================================================================== #
# MaxHeapPriorityQueue tests
# ====================================================================== #

class TestMaxHeapPriorityQueue:

    def test_empty_queue(self):
        q = MaxHeapPriorityQueue()
        assert q.is_empty()
        assert len(q) == 0
        assert q.pop() is None
        assert q.peek() is None

    def test_insert_and_peek(self):
        q = MaxHeapPriorityQueue()
        q.insert("p1", 10)
        assert q.peek().patient_id == "p1"
        assert len(q) == 1

    def test_highest_priority_popped_first(self):
        q = MaxHeapPriorityQueue()
        q.insert("low", 5)
        q.insert("high", 100)
        q.insert("mid", 50)

        assert q.pop().patient_id == "high"
        assert q.pop().patient_id == "mid"
        assert q.pop().patient_id == "low"
        assert q.is_empty()

    def test_fifo_tie_break(self):
        """Equal priority -> earlier arrival served first."""
        q = MaxHeapPriorityQueue()
        q.insert("first", 10)
        q.insert("second", 10)
        q.insert("third", 10)

        assert q.pop().patient_id == "first"
        assert q.pop().patient_id == "second"
        assert q.pop().patient_id == "third"

    def test_duplicate_insert_raises(self):
        q = MaxHeapPriorityQueue()
        q.insert("p1", 10)
        with pytest.raises(ValueError):
            q.insert("p1", 20)

    def test_update_priority_up(self):
        q = MaxHeapPriorityQueue()
        q.insert("a", 10)
        q.insert("b", 20)
        q.update_priority("a", 100)
        assert q.pop().patient_id == "a"

    def test_update_priority_down(self):
        q = MaxHeapPriorityQueue()
        q.insert("a", 100)
        q.insert("b", 20)
        q.update_priority("a", 5)
        assert q.pop().patient_id == "b"

    def test_update_priority_missing_patient(self):
        q = MaxHeapPriorityQueue()
        assert q.update_priority("ghost", 50) is None

    def test_remove_from_middle(self):
        q = MaxHeapPriorityQueue()
        for i, pid in enumerate(["a", "b", "c", "d", "e"]):
            q.insert(pid, (5 - i) * 10)  # a=50 b=40 c=30 d=20 e=10
        removed = q.remove("c")
        assert removed.patient_id == "c"
        assert len(q) == 4
        remaining_ids = {n.patient_id for n in q.to_sorted_list()}
        assert remaining_ids == {"a", "b", "d", "e"}

    def test_remove_missing_patient_returns_none(self):
        q = MaxHeapPriorityQueue()
        q.insert("a", 1)
        assert q.remove("ghost") is None

    def test_heap_property_holds_under_stress(self):
        """Insert a bunch of random-ish priorities, pop all, confirm sorted desc."""
        import random
        q = MaxHeapPriorityQueue()
        priorities = [random.uniform(0, 1000) for _ in range(200)]
        for i, p in enumerate(priorities):
            q.insert(f"patient_{i}", p)

        popped = []
        while not q.is_empty():
            popped.append(q.pop().priority)

        assert popped == sorted(popped, reverse=True)

    def test_to_sorted_list_does_not_mutate(self):
        q = MaxHeapPriorityQueue()
        q.insert("a", 5)
        q.insert("b", 50)
        snapshot1 = q.to_sorted_list()
        snapshot2 = q.to_sorted_list()
        assert [n.patient_id for n in snapshot1] == [n.patient_id for n in snapshot2]
        assert len(q) == 2  # nothing removed


# ====================================================================== #
# TriageAlgorithm tests
# ====================================================================== #

class TestTriageAlgorithm:

    def setup_method(self):
        self.algo = TriageAlgorithm()

    def test_red_flag_symptom_forces_emergency(self):
        intake = TriageInput(vitals=VitalSigns(), symptom_tags=["chest_pain"])
        level, score = self.algo.score(intake)
        assert level == UrgencyLevel.EMERGENCY

    def test_critical_vitals_force_emergency(self):
        intake = TriageInput(vitals=VitalSigns(oxygen_saturation=85))
        level, _ = self.algo.score(intake)
        assert level == UrgencyLevel.EMERGENCY

    def test_urgent_symptom_without_red_flag(self):
        intake = TriageInput(vitals=VitalSigns(), symptom_tags=["high_fever"])
        level, _ = self.algo.score(intake)
        assert level == UrgencyLevel.URGENT

    def test_normal_case(self):
        intake = TriageInput(vitals=VitalSigns(heart_rate=72, pain_score=1), symptom_tags=["mild_cough"])
        level, _ = self.algo.score(intake)
        assert level == UrgencyLevel.NORMAL

    def test_score_within_tier_band(self):
        intake = TriageInput(vitals=VitalSigns(pain_score=10, temperature_c=40), symptom_tags=["high_fever"])
        level, score = self.algo.score(intake)
        floor = level.value * 1000.0
        assert floor <= score < floor + 1000.0

    def test_higher_pain_scores_higher_within_tier(self):
        low_pain = TriageInput(vitals=VitalSigns(pain_score=2))
        high_pain = TriageInput(vitals=VitalSigns(pain_score=9))
        _, score_low = self.algo.score(low_pain)
        _, score_high = self.algo.score(high_pain)
        assert score_high > score_low

    def test_elderly_gets_small_boost(self):
        young = TriageInput(vitals=VitalSigns(), age=30)
        elderly = TriageInput(vitals=VitalSigns(), age=80)
        _, score_young = self.algo.score(young)
        _, score_elderly = self.algo.score(elderly)
        assert score_elderly > score_young

    def test_emergency_always_outranks_urgent_and_normal(self):
        emergency = TriageInput(vitals=VitalSigns(), symptom_tags=["not_breathing"])
        urgent = TriageInput(vitals=VitalSigns(pain_score=10), symptom_tags=["fracture"])
        normal = TriageInput(vitals=VitalSigns(pain_score=10))

        _, e_score = self.algo.score(emergency)
        _, u_score = self.algo.score(urgent)
        _, n_score = self.algo.score(normal)

        assert e_score > u_score > n_score


# ====================================================================== #
# AgingAlgorithm tests
# ====================================================================== #

class TestAgingAlgorithm:

    def test_score_increases_with_wait_time(self):
        aging = AgingAlgorithm(points_per_second=1.0)
        _, score_0s = aging.aged_score(100.0, UrgencyLevel.NORMAL, waited_seconds=0)
        _, score_60s = aging.aged_score(100.0, UrgencyLevel.NORMAL, waited_seconds=60)
        assert score_60s > score_0s

    def test_promotion_after_enough_waiting(self):
        aging = AgingAlgorithm(points_per_second=10.0, promotion_threshold=500, max_level=UrgencyLevel.URGENT)
        level, score = aging.aged_score(0.0, UrgencyLevel.NORMAL, waited_seconds=100)  # 1000 points accrued
        assert level == UrgencyLevel.URGENT

    def test_never_promotes_past_max_level(self):
        aging = AgingAlgorithm(points_per_second=100.0, promotion_threshold=10, max_level=UrgencyLevel.URGENT)
        level, _ = aging.aged_score(0.0, UrgencyLevel.NORMAL, waited_seconds=10_000)
        assert level <= UrgencyLevel.URGENT

    def test_emergency_is_never_touched_past_its_own_tier(self):
        aging = AgingAlgorithm(points_per_second=100.0, max_level=UrgencyLevel.URGENT)
        level, _ = aging.aged_score(2000.0, UrgencyLevel.EMERGENCY, waited_seconds=10_000)
        assert level == UrgencyLevel.EMERGENCY


# ====================================================================== #
# TriageQueue (integration) tests
# ====================================================================== #

class TestTriageQueue:

    def test_insert_runs_triage_and_emergency_pops_first(self):
        q = TriageQueue()
        q.insert("p_normal", TriageInput(vitals=VitalSigns(pain_score=2)))
        q.insert("p_emergency", TriageInput(vitals=VitalSigns(), symptom_tags=["chest_pain"]))
        q.insert("p_urgent", TriageInput(vitals=VitalSigns(), symptom_tags=["fracture"]))

        assert q.pop().patient_id == "p_emergency"
        assert q.pop().patient_id == "p_urgent"
        assert q.pop().patient_id == "p_normal"

    def test_events_fire_on_insert_and_pop(self):
        events = []
        q = TriageQueue()
        q.on_event(lambda evt, node: events.append(evt))

        q.insert("p1", TriageInput(vitals=VitalSigns()))
        q.pop()

        assert events == ["insert", "pop"]

    def test_age_tick_emits_event(self):
        events = []
        q = TriageQueue()
        q.on_event(lambda evt, node: events.append(evt))
        q.insert("p1", TriageInput(vitals=VitalSigns()))
        q.age_tick()
        assert "age_tick" in events

    def test_age_tick_increases_long_waiting_patient_score(self):
        aging = AgingAlgorithm(points_per_second=5.0)
        q = TriageQueue(aging=aging)

        now = time.time()
        q.insert("old_patient", TriageInput(vitals=VitalSigns(pain_score=1)), arrival_time=now - 120)
        before = q.peek().priority

        q.age_tick(now=now)
        after = q.peek().priority

        assert after > before

    def test_long_waiting_normal_patient_can_overtake_a_fresh_normal_patient(self):
        aging = AgingAlgorithm(points_per_second=5.0)
        q = TriageQueue(aging=aging)
        now = time.time()

        q.insert("waited_long", TriageInput(vitals=VitalSigns(pain_score=1)), arrival_time=now - 300)
        q.insert("just_arrived", TriageInput(vitals=VitalSigns(pain_score=1)), arrival_time=now)

        q.age_tick(now=now)
        assert q.peek().patient_id == "waited_long"

    def test_aging_cannot_overtake_real_emergency(self):
        aging = AgingAlgorithm(points_per_second=50.0, max_level=UrgencyLevel.URGENT)
        q = TriageQueue(aging=aging)
        now = time.time()

        q.insert("emergency", TriageInput(vitals=VitalSigns(), symptom_tags=["chest_pain"]), arrival_time=now)
        q.insert("very_old_normal", TriageInput(vitals=VitalSigns(pain_score=1)), arrival_time=now - 100_000)

        q.age_tick(now=now)
        assert q.peek().patient_id == "emergency"

    def test_remove_patient(self):
        q = TriageQueue()
        q.insert("p1", TriageInput(vitals=VitalSigns()))
        q.insert("p2", TriageInput(vitals=VitalSigns(), symptom_tags=["fracture"]))

        removed = q.remove("p2")
        assert removed.patient_id == "p2"
        assert len(q) == 1

    def test_snapshot_format(self):
        q = TriageQueue()
        q.insert("p1", TriageInput(vitals=VitalSigns()), data={"name": "Test Patient"})
        snap = q.snapshot()

        assert len(snap) == 1
        entry = snap[0]
        assert entry["patient_id"] == "p1"
        assert entry["name"] == "Test Patient"
        assert "urgency_level" in entry
        assert "waited_seconds" in entry
        assert "priority" in entry

    def test_queue_len_and_is_empty(self):
        q = TriageQueue()
        assert q.is_empty()
        q.insert("p1", TriageInput(vitals=VitalSigns()))
        assert len(q) == 1
        assert not q.is_empty()
        q.pop()
        assert q.is_empty()
