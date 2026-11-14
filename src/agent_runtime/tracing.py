from datetime import datetime, timezone
import uuid
import math

def _serialize_value(value):
    
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Value must be finite.")
        return value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        serialized = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Key is not a string")

            serialized[key] = _serialize_value(item)

        return serialized

    if isinstance(value, list):
        return [_serialize_value(item) for item in value]

    if value is None:
        return value
    
    if isinstance(value, (str, bool, int)):
        return value
    
    raise TypeError("Invalid value type cannot be serialized")

def _deserialize_value(value):

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, str, type(None))):
        return value

    if isinstance(value, float):

        if not math.isfinite(value):
            raise ValueError("float must be finite")

        return value

    if isinstance(value, dict):
        deserialized = {}
        for key, item in value.items():

            if not isinstance(key, str):
                raise TypeError("dictionary key must be a string")

            deserialized[key] = _deserialize_value(item)

        return deserialized
            

    if isinstance(value, list):

        return [_deserialize_value(item) for item in value]

    raise TypeError("unsupported value type")

    

def _validate_string(value, field_name):
    if not isinstance(value, str):
        raise TypeError(f"{field_name} value should be a string")

def _validate_optional_integer(value, field_name):
    if isinstance(value, bool):
        raise TypeError(f"{field_name} cannot be a bool")
    
    if not isinstance(value, (int, type(None))):
        raise TypeError(f"{field_name} optional value must be an integer")

def _validate_optional_number(value, field_name):
    if isinstance(value, bool):
        raise TypeError(f"{field_name} cannot be a bool")
    
    if not isinstance(value, (int, float, type(None))):
        raise TypeError(f"{field_name} optional value must be an integer or float")

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("float value must be finite")

def _deserialize_datetime(value):

    _validate_string(value, "timestamp")    
    
    return datetime.fromisoformat(value)
    

class TraceEvent:

    def __init__(self, event_id: str, event_type: str, timestamp: datetime, iteration: int | None = None, duration_ms: float | None = None, status: str = "info", event_details: dict | None = None):
        
        self.event_id = event_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.iteration = iteration
        self.duration_ms = duration_ms
        self.status = status
        self.event_details = event_details if event_details is not None else {}

    def to_dict(self):
        
        return{
            "event_id": _serialize_value(self.event_id),
            "event_type": _serialize_value(self.event_type),
            "timestamp": _serialize_value(self.timestamp),
            "iteration": _serialize_value(self.iteration),
            "duration_ms": _serialize_value(self.duration_ms),
            "status": _serialize_value(self.status),
            "event_details": _serialize_value(self.event_details)
        }

    @classmethod
    def from_dict(cls, data):

        if not isinstance(data, dict):
            raise TypeError("data is not a dictionary")

        if set(("event_id", "event_type", "timestamp", "iteration", "duration_ms", "status", "event_details")) != set(data.keys()):
            raise ValueError("data is missing entries or contains unexpected entries")

        _validate_string(data["event_id"], "event_id")

        _validate_string(data["event_type"], "event_type")

        _validate_optional_integer(data["iteration"], "iteration")
        
        _validate_optional_number(data["duration_ms"], "duration_ms")
        
        _validate_string(data["status"], "status")

        timestamp = _deserialize_datetime(data["timestamp"])

        if not isinstance(data["event_details"], dict):
            raise TypeError("event_details must be a dictionary")
        
        event_details = _deserialize_value(data["event_details"])
       
        return cls(data["event_id"], data["event_type"], timestamp, data["iteration"], data["duration_ms"], data["status"], event_details)

        
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
            raise RuntimeError("Cannot add events to a finalized trace")
        self.events.append(event)

    def get_events(self, event_type: str | None = None) -> list[TraceEvent]:
        if event_type is None:
            return self.events.copy()
        return [event for event in self.events if event.event_type == event_type]

    def finish(self, final_status: str ):

        if self.status in ["completed", "failed"]:
            raise RuntimeError("Trace is already finalized")
        
        if final_status not in ["completed", "failed"]:
            raise ValueError("final_status must be either 'completed' or 'failed'")

        self.status = final_status
        self.completed_at = datetime.now(timezone.utc)

    def record_event(self, event_type: str, iteration: int | None = None, duration_ms: float | None = None, status: str = "info", event_details: dict | None = None):
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)

        event = TraceEvent(event_id, event_type, timestamp, iteration, duration_ms, status, event_details)
        self.add_event(event)
        return event

    def to_dict(self):
        return {
            "schema_version": 1,
            "run_id": _serialize_value(self.run_id),
            "started_at": _serialize_value(self.started_at),
            "completed_at": _serialize_value(self.completed_at),
            "status": _serialize_value(self.status),
            "events": [event.to_dict() for event in self.events]
        }
        