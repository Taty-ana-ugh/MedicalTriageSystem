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
        Takes a real-time snapshot of the TriageQueue, serializes it, and
        sends it to all connected terminals concurrently. Any connection
        that fails to receive (e.g. client closed without a clean
        disconnect) is dropped from the active list.
        """
        if not self.active_connections:
            return

        payload = {
            "event": "QUEUE_UPDATE",
            "snapshot": triage_queue.snapshot()
        }
        message = json.dumps(payload)

        results = await asyncio.gather(
            *[connection.send_text(message) for connection in self.active_connections],
            return_exceptions=True
        )

        dead_connections = [
            conn for conn, result in zip(self.active_connections, results)
            if isinstance(result, Exception)
        ]
        for conn in dead_connections:
            self.disconnect(conn)