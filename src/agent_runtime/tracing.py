from datetime import datetime, timezone


class TraceEvent:

    def __init__(self, event_id: str, event_type: str, timestamp: datetime, iteration: int | None = None, duration_ms: float | None = None, status: str = "info", event_details: dict | None = None):
        
        self.event_id = event_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.iteration = iteration
        self.duration_ms = duration_ms
        self.status = status
        self.event_details = event_details if event_details is not None else {}


class ExecutionTrace:

    def __init__(self, run_id: str, started_at: datetime, events: list[TraceEvent] | None = None):
        self.run_id = run_id
        self.started_at = started_at
        self.completed_at = None
        self.status = "running"
        self.events = events.copy() if events is not None else []

    def add_event(self, event: TraceEvent):
        if not isinstance(event, TraceEvent):
            raise TypeError("event must be an instance of TraceEvent")

        if self.status != "running":
            raise RuntimeError("Cannot add events to a finalized trace.")
        self.events.append(event)

    def get_events(self, event_type: str | None = None) -> list[TraceEvent]:
        if event_type is None:
            return self.events.copy()
        return [event for event in self.events if event.event_type == event_type]

    def finish(self, final_status: str ):

        if self.status in ["completed", "failed"]:
            raise RuntimeError("Trace is already finalized.")
        
        if final_status not in ["completed", "failed"]:
            raise ValueError("final_status must be either 'completed' or 'failed'")

        self.status = final_status
        self.completed_at = datetime.now(timezone.utc)
        
            