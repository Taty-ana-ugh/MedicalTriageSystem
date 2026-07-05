# server.py
import asyncio
import json
import time
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.state import triage_queue, departments, ws_manager
from core.triage import TriageAlgorithm, TriageInput, VitalSigns


# ------------------------------------------------------------------ #
# Event Bridge: Binding your Socket Core to the Triage Engine
# ------------------------------------------------------------------ #

# Captured once the app's own event loop starts (see lifespan below).
# Needed because FastAPI runs plain `def` (sync) REST endpoints in a
# worker THREAD with no event loop of its own -- Elvis's sync endpoints
# will land there. Without a reference to the real loop, a broadcast
# triggered from that thread would silently no-op instead of firing.
_main_loop = None


def sync_event_handler(event_name: str, node):
    """
    This callback triggers every single time triage_queue OR any
    department queue mutates (inserts, pops, or removes). It broadcasts
    the change to all connected client terminals.

    triage_queue's/DepartmentRegistry's methods are plain sync methods
    (Tat designed it that way so tests, scripts, and future sync REST
    code can call them without needing async/await), so this handler can
    fire from three different contexts:

    1. Inside the WebSocket route (already on the running loop) ->
       schedule directly with create_task.
    2. Inside a sync FastAPI endpoint, which Starlette runs in a worker
       thread with NO loop of its own -> hand the coroutine to the real
       app loop with run_coroutine_threadsafe.
    3. A plain unit test calling triage_queue.insert() etc. directly,
       with the app never started at all -> no loop exists anywhere;
       there's nothing listening on a socket anyway, so no-op.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast_queue_state(triage_queue, departments))
        return
    except RuntimeError:
        pass

    if _main_loop is not None and not _main_loop.is_closed():
        try:
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast_queue_state(triage_queue, departments), _main_loop
            )
        except RuntimeError:
            # Loop closed between the check above and this call (e.g. app
            # shutting down mid-mutation) -- nothing listening anyway.
            pass


# Hook into the flat queue's event pipeline...
triage_queue.on_event(sync_event_handler)
# ...AND every department queue's, current and future. Without this,
# a department-scoped insert/pop (which is how Elvis's REST API will
# operate once he wires up routing) would mutate silently with nothing
# broadcast over the socket.
departments.on_event(sync_event_handler)


# ------------------------------------------------------------------ #
# Background Worker: The Aging Algorithm Loop
# ------------------------------------------------------------------ #
async def aging_timer_loop():
    """
    Runs continuously in the background. Every 30 seconds, it tells
    triage_queue AND every department queue to recalculate patient
    scores based on wait times.
    """
    while True:
        await asyncio.sleep(30)  # Runs tick evaluations every 30 seconds
        triage_queue.age_tick()
        for dept in departments.departments():
            departments.get_queue(dept).age_tick()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Spins up background workers when the server goes live, captures a
    handle to the running loop (see _main_loop above), and cancels the
    background task on shutdown.
    """
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    task = asyncio.create_task(aging_timer_loop())
    yield
    task.cancel()


# ------------------------------------------------------------------ #
# App setup
# ------------------------------------------------------------------ #
app = FastAPI(title="Real-Time Medical Triage Server", lifespan=lifespan)

# Allow easy communication from local development frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------ #
# WebSocket Router Endpoint
# ------------------------------------------------------------------ #
@app.websocket("/ws/triage")
async def triage_websocket_route(websocket: WebSocket):
    await ws_manager.connect(websocket)

    # Send current snapshot instantly upon connection (flat queue + departments)
    await ws_manager.broadcast_queue_state(triage_queue, departments)

    try:
        while True:
            # Keep line open and listen for socket actions (e.g., admitting/popping patients)
            raw_data = await websocket.receive_text()
            message = json.loads(raw_data)
            action = message.get("action")

            if action == "ADMIT_NEXT":
                # Removes the highest-urgency patient from the flat heap
                triage_queue.pop()

            elif action == "REMOVE_PATIENT":
                patient_id = message.get("patient_id")
                if patient_id:
                    triage_queue.remove(patient_id)

            elif action == "ADMIT_NEXT_IN_DEPARTMENT":
                department = message.get("department")
                if department:
                    departments.get_queue(department).pop()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)