"""
test_patient_api.py
--------------------
Skeleton integration tests for Elvis's REST endpoints. SKIPPED until his
router exists — once he adds it (e.g. api/patients.py, included into
api/server.py's `app`), remove the skip markers and fill in real
assertions against his response schema.

Elvis: import the SHARED state —
    from api.state import triage_queue, departments
— not a fresh TriageQueue()/DepartmentRegistry(), or these tests (and
the live socket feed) won't see your writes.
"""

import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


@pytest.mark.skip(reason="Elvis's POST /patient endpoint not implemented yet")
def test_post_patient_registers_and_returns_id():
    response = client.post("/patient", json={
        "name": "Test Patient",
        "department": "ER",
        "vitals": {"heart_rate": 80, "pain_score": 3},
        "symptom_tags": [],
    })
    assert response.status_code == 201
    assert "patient_id" in response.json()


@pytest.mark.skip(reason="Elvis's GET /queue endpoint not implemented yet")
def test_get_queue_reflects_registered_patient():
    client.post("/patient", json={
        "name": "Test", "department": "ER", "vitals": {}, "symptom_tags": ["chest_pain"],
    })
    response = client.get("/queue")
    assert response.status_code == 200
    ids = [p["patient_id"] for p in response.json()]
    assert len(ids) >= 1


@pytest.mark.skip(reason="Elvis's GET /analytics endpoint not implemented yet")
def test_get_analytics_returns_metrics_shape():
    response = client.get("/analytics")
    assert response.status_code == 200
    body = response.json()
    assert "average_wait_seconds" in body


@pytest.mark.skip(reason="Elvis's PUT /patient/:id/route endpoint not implemented yet")
def test_put_patient_route_moves_department():
    client.post("/patient", json={
        "name": "Test", "department": "ER", "vitals": {}, "symptom_tags": [],
    })
    response = client.put("/patient/some-id/route", json={"department": "Radiology"})
    assert response.status_code == 200
    assert response.json()["department"] == "Radiology"