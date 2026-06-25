# websocket_manager.py
import asyncio
import json
from typing import List
from fastapi import WebSocket

class TriageWebSocketManager:
    def __init__(self):
        # Keeps track of all actively connected UI clients
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts an incoming client connection and registers it."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Removes a client from the tracking list upon disconnection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_queue_state(self, triage_queue):
        """
        Takes a real-time snapshot of your teammate's TriageQueue,
        serializes it, and sends it out to all connected terminals concurrently.
        """
        if not self.active_connections:
            return

        # Matches Elvis's REST payload format perfectly
        payload = {
            "event": "QUEUE_UPDATE",
            "snapshot": triage_queue.snapshot()
        }
        message = json.dumps(payload)

        # Fire transmission tasks to all connected screens in parallel
        await asyncio.gather(
            *[connection.send_text(message) for connection in self.active_connections],
            return_exceptions=True
        )