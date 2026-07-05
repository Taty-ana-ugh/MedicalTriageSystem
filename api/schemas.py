"""
api/schemas.py
---------------
Pydantic request/response models. This is what makes FastAPI's
auto-generated Swagger docs at /docs actually useful -- this file IS
the "Swagger UI API docs" deliverable from the brief.
"""

from typing import Optional
from pydantic import BaseModel, Field


class VitalsIn(BaseModel):
    heart_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    respiratory_rate: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    temperature_c: Optional[float] = None
    pain_score: Optional[int] = None
    consciousness: Optional[str] = None


class PatientCreate(BaseModel):
    name: str
    department: str = Field(..., description="Must be an existing or new department name, e.g. 'ER'")
    vitals: VitalsIn = VitalsIn()
    symptom_tags: list[str] = []
    age: Optional[int] = None


class PatientCreateResponse(BaseModel):
    patient_id: str
    department: str
    urgency_level: str
    priority_score: float


class QueueItem(BaseModel):
    patient_id: str
    department: str
    priority: float
    urgency_level: Optional[str] = None
    waited_seconds: float
    name: Optional[str] = None


class RouteRequest(BaseModel):
    department: str = Field(..., description="Destination department")


class RouteResponse(BaseModel):
    patient_id: str
    department: str


class AnalyticsResponse(BaseModel):
    average_wait_seconds: float
    total_patients_served: int
    department_breakdown: dict[str, int]