"""
db/models.py
------------
ORM models: patients, departments, queue_history.

Design notes (for Q&A defense):
- No separate "metrics" table. Metrics are derived on-demand from
  queue_history via aggregate queries in GET /analytics. Storing
  pre-computed metrics would mean keeping a second source of truth in
  sync with the event log for no real benefit at this scale -- the
  aggregation queries are cheap and always accurate.
- `patients.department` is a plain string, not a hard FK to
  departments.id. Departments in this system are created lazily
  in-memory (see DepartmentRegistry.get_queue), so enforcing a FK would
  mean the DB and the live heap could disagree about which departments
  exist. `departments` table instead exists for descriptive metadata
  (capacity) that the live in-memory registry doesn't track.
- `queue_history` is an append-only event log (insert/pop/route/remove),
  never updated in place, so it doubles as both the audit trail and the
  analytics data source.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=True)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)  # matches the heap's patient_id (uuid hex)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False, index=True)  # current department
    status = Column(String, nullable=False, default="waiting")  # waiting | seen | removed
    urgency_level = Column(String, nullable=False)
    priority_score = Column(Float, nullable=False)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    history = relationship("QueueHistory", back_populates="patient", cascade="all, delete-orphan")


class QueueHistory(Base):
    """
    Append-only audit log. One row per queue mutation
    (insert / pop / route / remove) so GET /analytics can compute wait
    times and throughput without touching the live in-memory heap.
    """
    __tablename__ = "queue_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # insert | pop | route | remove
    from_department = Column(String, nullable=True)
    to_department = Column(String, nullable=True)
    urgency_level = Column(String, nullable=True)
    priority_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)

    patient = relationship("Patient", back_populates="history")