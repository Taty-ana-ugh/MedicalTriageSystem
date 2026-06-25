"""
demo.py
-------
A runnable demonstration of the module, mainly so Joe and Elvis can see
exactly how to plug into TriageQueue without reading all of triage.py.

Run with:
    python3 demo.py
"""

import time
from core.triage import TriageQueue, TriageInput, VitalSigns


def websocket_style_broadcaster(event: str, node):
    """
    Stand-in for what Joe's real WebSocket handler will do.
    In the real app this would push `queue.snapshot()` to all connected
    clients whenever this fires.
    """
    if node:
        print(f"  [EVENT: {event:>6}] -> patient_id={node.patient_id}  priority={node.priority:.1f}")
    else:
        print(f"  [EVENT: {event:>6}]")


def main():
    queue = TriageQueue()
    queue.on_event(websocket_style_broadcaster)  # <-- Joe hooks in exactly like this

    print("=== Registering patients ===")
    queue.insert(
        "PT-001",
        TriageInput(vitals=VitalSigns(pain_score=2, heart_rate=72)),
        data={"name": "Joe Migwi", "department": "General"},
    )
    queue.insert(
        "PT-002",
        TriageInput(vitals=VitalSigns(), symptom_tags=["chest_pain"]),
        data={"name": "Elvis Koech", "department": "Cardiology"},
    )
    queue.insert(
        "PT-003",
        TriageInput(vitals=VitalSigns(temperature_c=39.5), symptom_tags=["high_fever"]),
        data={"name": "Tat Kamau", "department": "General"},
    )

    print("\n=== Current queue snapshot (what Elvis's GET /queue would return) ===")
    for entry in queue.snapshot():
        print(f"  {entry}")

    print("\n=== Simulating an aging tick (e.g. Joe's timer firing after a while) ===")
    queue.age_tick(now=time.time() + 600)  # pretend 10 minutes passed

    print("\n=== Snapshot after aging ===")
    for entry in queue.snapshot():
        print(f"  {entry}")

    print("\n=== Popping patients in priority order ===")
    while not queue.is_empty():
        seen = queue.pop()
        print(f"  Now seeing: {seen.data.get('name')} (was {seen.data.get('urgency_level')})")


if __name__ == "__main__":
    main()
