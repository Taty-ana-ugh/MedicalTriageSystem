"""
test_patient_api.py
--------------------
Integration tests for Elvis's REST endpoints.

Elvis: import the SHARED state —
    from api.state import triage_queue, departments
— not a fresh TriageQueue()/DepartmentRegistry(), or these tests (and
the live socket feed) won't see your writes.
"""

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_post_patient_registers_and_returns_id():
    response = client.post("/patient", json={
        "name": "Test Patient",
        "department": "ER",
        "vitals": {"heart_rate": 80, "pain_score": 3},
        "symptom_tags": [],
    })
    assert response.status_code == 201
    assert "patient_id" in response.json()


def test_get_queue_reflects_registered_patient():
    client.post("/patient", json={
        "name": "Test", "department": "ER", "vitals": {}, "symptom_tags": ["chest_pain"],
    })
    response = client.get("/queue")
    assert response.status_code == 200
    ids = [p["patient_id"] for p in response.json()]
    assert len(ids) >= 1


def test_get_analytics_returns_metrics_shape():
    response = client.get("/analytics")
    assert response.status_code == 200
    body = response.json()
    assert "average_wait_seconds" in body


def test_put_patient_route_moves_department():
    create = client.post("/patient", json={
        "name": "Test", "department": "ER", "vitals": {}, "symptom_tags": [],
    })
    patient_id = create.json()["patient_id"]
    response = client.put(f"/patient/{patient_id}/route", json={"department": "Radiology"})
    assert response.status_code == 200
    assert response.json()["department"] == "Radiology"