"""
api/patients.py
----------------
Elvis's REST endpoints: POST /patient, GET /queue, GET /analytics,
PUT /patient/{id}/route.

Integration rules this file follows:
- Import the SHARED `departments` from api.state -- never instantiate a
  fresh DepartmentRegistry() here, or writes made through this router
  would be invisible to Joe's WebSocket feed and to the tests.
- PUT /patient/{id}/route calls departments.move_patient() directly and
  does NOT touch heap internals -- it already handles removal,
  reinsertion, and priority preservation.
- This router only does DB reads/writes and thin calls into the shared
  in-memory queue objects. It is NOT one of the project's two required
  algorithms -- the Triage Algorithm and Aging Algorithm (Tat's module)
  are. This router is integration/persistence glue.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.database import get_db
from db.models import Patient, QueueHistory
from api.schemas import (
    PatientCreate, PatientCreateResponse, QueueItem,
    RouteRequest, RouteResponse, AnalyticsResponse,
)
from api.state import departments
from core.triage import VitalSigns, TriageInput

router = APIRouter()


@router.post("/patient", response_model=PatientCreateResponse, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    """
    Register a new patient: run the Triage Algorithm (via TriageQueue.insert,
    which wraps it), push them onto their department's heap, and persist a
    DB row + an "insert" audit event.
    """
    patient_id = uuid.uuid4().hex

    vitals = VitalSigns(**payload.vitals.model_dump())
    intake = TriageInput(vitals=vitals, symptom_tags=payload.symptom_tags, age=payload.age)

    queue = departments.get_queue(payload.department)
    node = queue.insert(patient_id, intake, data={"name": payload.name})
    urgency_level = node.data.get("urgency_level", "NORMAL")

    db_patient = Patient(
        id=patient_id,
        name=payload.name,
        department=payload.department,
        status="waiting",
        urgency_level=urgency_level,
        priority_score=node.priority,
        age=payload.age,
    )
    db.add(db_patient)
    db.add(QueueHistory(
        patient_id=patient_id,
        event_type="insert",
        to_department=payload.department,
        urgency_level=urgency_level,
        priority_score=node.priority,
    ))
    db.commit()

    return PatientCreateResponse(
        patient_id=patient_id,
        department=payload.department,
        urgency_level=urgency_level,
        priority_score=node.priority,
    )


@router.get("/queue", response_model=list[QueueItem])
def get_queue():
    """
    Live queue snapshot across ALL departments, flattened into one
    priority-sorted list. Reads straight from the in-memory heaps (via
    DepartmentRegistry.full_snapshot) -- NOT the database -- because the
    heap, not the DB, is the source of truth for "who's waiting right now".
    """
    snapshot = departments.full_snapshot()
    items: list[QueueItem] = []
    for dept, patients in snapshot.items():
        for p in patients:
            items.append(QueueItem(
                patient_id=p["patient_id"],
                department=dept,
                priority=p["priority"],
                urgency_level=p.get("urgency_level"),
                waited_seconds=p["waited_seconds"],
                name=p.get("name"),
            ))
    items.sort(key=lambda i: i.priority, reverse=True)
    return items


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    """
    Historical metrics, computed on-demand from queue_history. No
    separate metrics table -- see db/models.py docstring for why.
    """
    inserts = {h.patient_id: h.created_at for h in
               db.query(QueueHistory).filter(QueueHistory.event_type == "insert").all()}
    pops = {h.patient_id: h.created_at for h in
            db.query(QueueHistory).filter(QueueHistory.event_type == "pop").all()}

    wait_times = [
        (pops[pid] - inserts[pid]).total_seconds()
        for pid in pops if pid in inserts
    ]
    average_wait = sum(wait_times) / len(wait_times) if wait_times else 0.0

    total_served = len(pops)

    breakdown_rows = (
        db.query(Patient.department, func.count(Patient.id))
        .group_by(Patient.department)
        .all()
    )
    breakdown = {dept: count for dept, count in breakdown_rows}

    return AnalyticsResponse(
        average_wait_seconds=round(average_wait, 2),
        total_patients_served=total_served,
        department_breakdown=breakdown,
    )


@router.put("/patient/{patient_id}/route", response_model=RouteResponse)
def route_patient(patient_id: str, payload: RouteRequest, db: Session = Depends(get_db)):
    """
    Move a patient to a different department's queue.

    Per the team's explicit instruction: call departments.move_patient()
    directly. It already handles heap removal/reinsertion and priority
    preservation -- this endpoint does NOT reimplement any of that.
    """
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    from_dept = db_patient.department
    to_dept = payload.department

    moved = departments.move_patient(patient_id, from_dept, to_dept)
    if not moved:
        raise HTTPException(
            status_code=409,
            detail=f"Patient not found in department '{from_dept}' queue (may have already been seen or removed)",
        )

    db_patient.department = to_dept
    db.add(QueueHistory(
        patient_id=patient_id,
        event_type="route",
        from_department=from_dept,
        to_department=to_dept,
    ))
    db.commit()

    return RouteResponse(patient_id=patient_id, department=to_dept)