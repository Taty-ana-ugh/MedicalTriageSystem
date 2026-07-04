# server.py
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Pull in your manager and your team's code structures
from api.websocket_manager import TriageWebSocketManager

app = FastAPI(title="Real-Time Medical Triage Server")

# Allow easy communication from local development frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core initialization — shared instances, importable by Elvis's REST routes too
from api.state import triage_queue, ws_manager

# ------------------------------------------------------------------ #
# Event Bridge: Binding your Socket Core to the Triage Engine
# ------------------------------------------------------------------ #
def sync_event_handler(event_name: str, node):
    """
    This callback triggers every single time triage_queue mutates 
    (inserts, pops, or removes). It spawns an async task to broadcast 
    the change to all client terminals.
    """
    asyncio.create_task(ws_manager.broadcast_queue_state(triage_queue))

# Hooking into the event pipeline your teammate built for you
triage_queue.on_event(sync_event_handler)


# ------------------------------------------------------------------ #
# Background Worker: The Aging Algorithm Loop
# ------------------------------------------------------------------ #
@app.on_event("startup")
async def startup_event():
    """Spins up background workers when the server goes live."""
    asyncio.create_task(aging_timer_loop())

async def aging_timer_loop():
    """
    Runs continuously in the background. Every 30 seconds, it tells 
    triage_queue to recalculate patient scores based on wait times.
    """
    while True:
        await asyncio.sleep(30)  # Runs tick evaluations every 30 seconds
        triage_queue.age_tick()   # Recalculates; internally fires 'age_tick' event -> triggers broadcast


# ------------------------------------------------------------------ #
# WebSocket Router Endpoint
# ------------------------------------------------------------------ #
@app.websocket("/ws/triage")
async def triage_websocket_route(websocket: WebSocket):
    await ws_manager.connect(websocket)
    
    # Send current snapshot instantly upon connection
    await ws_manager.broadcast_queue_state(triage_queue)
    
    try:
        while True:
            # Keep line open and listen for socket actions (e.g., admitting/popping patients)
            raw_data = await websocket.receive_text()
            message = json.loads(raw_data)
            action = message.get("action")
            
            if action == "ADMIT_NEXT":
                # Removes the highest-urgency patient from the heap
                triage_queue.pop() 
                
            elif action == "REMOVE_PATIENT":
                patient_id = message.get("patient_id")
                if patient_id:
                    triage_queue.remove(patient_id)
                    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)