"""
test_websocket_manager.py
--------------------------
Integration tests for the /ws/triage route and TriageWebSocketManager,
using the SAME shared triage_queue instance the real app uses (api.state).

Run with:
    pytest tests/test_websocket_manager.py -v
"""

import json
import pytest
from fastapi.testclient import TestClient

from api.server import app
from api.state import triage_queue
from core.triage import TriageInput, VitalSigns


@pytest.fixture(autouse=True)
def clean_queue():
    """Make sure the shared queue starts empty for every test."""
    while not triage_queue.is_empty():
        triage_queue.pop()
    yield
    while not triage_queue.is_empty():
        triage_queue.pop()


def test_new_connection_receives_initial_snapshot():
    triage_queue.insert("p1", TriageInput(vitals=VitalSigns()), data={"name": "Test Patient"})
    client = TestClient(app)

    with client.websocket_connect("/ws/triage") as ws:
        data = ws.receive_json()
        assert data["event"] == "QUEUE_UPDATE"
        assert any(p["patient_id"] == "p1" for p in data["snapshot"])


def test_admit_next_pops_highest_priority_patient():
    triage_queue.insert("p_normal", TriageInput(vitals=VitalSigns(pain_score=1)))
    triage_queue.insert("p_emergency", TriageInput(vitals=VitalSigns(), symptom_tags=["chest_pain"]))
    client = TestClient(app)

    with client.websocket_connect("/ws/triage") as ws:
        ws.receive_json()  # initial snapshot on connect
        ws.send_text(json.dumps({"action": "ADMIT_NEXT"}))
        update = ws.receive_json()
        ids = {p["patient_id"] for p in update["snapshot"]}
        assert "p_emergency" not in ids
        assert "p_normal" in ids


def test_remove_patient_action_removes_specific_patient():
    triage_queue.insert("p1", TriageInput(vitals=VitalSigns()))
    triage_queue.insert("p2", TriageInput(vitals=VitalSigns(), symptom_tags=["fracture"]))
    client = TestClient(app)

    with client.websocket_connect("/ws/triage") as ws:
        ws.receive_json()
        ws.send_text(json.dumps({"action": "REMOVE_PATIENT", "patient_id": "p1"}))
        update = ws.receive_json()
        ids = {p["patient_id"] for p in update["snapshot"]}
        assert "p1" not in ids
        assert "p2" in ids