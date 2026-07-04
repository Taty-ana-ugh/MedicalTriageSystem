# Medical Triage System

Real-time hospital queue management: patients are prioritized by medical
urgency (Emergency > Urgent > Normal), not arrival order, with an aging
mechanism so no one waits forever.

## Architecture

- `core/heap.py` — custom max-heap priority queue (Tat)
- `core/triage.py` — Triage + Aging algorithms, `TriageQueue` facade (Tat)
- `api/websocket_manager.py` — WebSocket connection/broadcast handling (Joe)
- `api/server.py` — FastAPI app, `/ws/triage` route, aging timer loop (Joe)
- `api/state.py` — the **shared** `triage_queue` / `ws_manager` instances.
  **Any new REST route (Elvis) must import from here**, not create its own
  `TriageQueue()`, or writes won't sync with the live socket feed.
- `main.py` — app entrypoint (`uvicorn main:app`)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn main:app --reload
```

WebSocket clients connect at `ws://localhost:8000/ws/triage`.

## Run with Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest -v
```

## WebSocket protocol

On connect, the server immediately sends the current queue snapshot:

```json
{ "event": "QUEUE_UPDATE", "snapshot": [ { "patient_id": "...", "priority": 1234.5, "urgency_level": "EMERGENCY", "waited_seconds": 12.3 } ] }
```

Client → server actions:

```json
{ "action": "ADMIT_NEXT" }
{ "action": "REMOVE_PATIENT", "patient_id": "p1" }
```

## For Elvis (REST/DB)

Import the shared queue instead of creating a new one:

```python
from api.state import triage_queue
```

Register your router in `api/server.py` with `app.include_router(...)`.