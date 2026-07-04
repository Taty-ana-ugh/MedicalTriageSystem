"""
test_department_registry.py
----------------------------
Tests for the department Hash Map layer (core/department_registry.py).
"""

from core.department_registry import DepartmentRegistry
from core.triage import TriageInput, VitalSigns


def test_lazy_department_creation():
    reg = DepartmentRegistry(known_departments=[])
    q = reg.get_queue("Cardiology")
    assert q.is_empty()
    assert "Cardiology" in reg.departments()


def test_departments_are_independent_queues():
    reg = DepartmentRegistry()
    reg.get_queue("ER").insert("p1", TriageInput(vitals=VitalSigns()))
    reg.get_queue("Pediatrics").insert("p2", TriageInput(vitals=VitalSigns()))

    assert len(reg.get_queue("ER")) == 1
    assert len(reg.get_queue("Pediatrics")) == 1
    assert reg.get_queue("ER").peek().patient_id == "p1"


def test_move_patient_between_departments():
    reg = DepartmentRegistry()
    reg.get_queue("ER").insert("p1", TriageInput(vitals=VitalSigns()), data={"name": "Test"})

    moved = reg.move_patient("p1", "ER", "Radiology")
    assert moved is True
    assert len(reg.get_queue("ER")) == 0
    assert len(reg.get_queue("Radiology")) == 1
    assert reg.get_queue("Radiology").peek().data.get("name") == "Test"


def test_move_missing_patient_returns_false():
    reg = DepartmentRegistry()
    moved = reg.move_patient("ghost", "ER", "Radiology")
    assert moved is False


def test_full_snapshot_includes_all_departments():
    reg = DepartmentRegistry(known_departments=["ER", "Pediatrics"])
    reg.get_queue("ER").insert("p1", TriageInput(vitals=VitalSigns()))

    snap = reg.full_snapshot()
    assert set(snap.keys()) == {"ER", "Pediatrics"}
    assert len(snap["ER"]) == 1
    assert len(snap["Pediatrics"]) == 0