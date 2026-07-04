"""
state.py
--------
Single shared instance of the TriageQueue and the WebSocket manager.

Why this file exists:
Both the WebSocket layer (api/server.py) and the future REST endpoints
(Elvis's api/patients.py or similar) need to mutate/read the SAME queue.
If each module instantiates its own TriageQueue(), a patient registered
via POST /patient will never show up on the live socket feed, and vice
versa. Import the objects below wherever you need the live queue:

    from api.state import triage_queue, ws_manager
"""

from core.triage import TriageQueue
from api.websocket_manager import TriageWebSocketManager

triage_queue = TriageQueue()
ws_manager = TriageWebSocketManager()