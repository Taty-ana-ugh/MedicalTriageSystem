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

"""
Single shared instances used across the backend:

- triage_queue : the original flat queue (kept for backward compatibility
                  with the existing WebSocket route and tests)
- departments  : DepartmentRegistry — one TriageQueue per department,
                  per the project brief's Hash Map requirement. Elvis's
                  department-routing endpoint and any future
                  department-aware WebSocket views should use this.
- ws_manager   : shared WebSocket connection manager

Import these wherever you need shared live state:
    from api.state import triage_queue, departments, ws_manager
"""

from core.triage import TriageQueue
from core.department_registry import DepartmentRegistry
from api.websocket_manager import TriageWebSocketManager

triage_queue = TriageQueue()
departments = DepartmentRegistry()
ws_manager = TriageWebSocketManager()