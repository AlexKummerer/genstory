from datetime import datetime, timezone
from uuid import uuid4

def generate_uuid() -> str:
    """Generate a UUID as a string."""
    return str(uuid4())

def get_current_utc_time() -> datetime:
    """Get the current UTC time."""
    return datetime.now(timezone.utc)

def serialize_json_field(json_field):
    """Safely serialize a JSON field from a database."""
    try:
        return json_field if json_field else {}
    except Exception as e:
        raise ValueError(f"Error serializing JSON field: {e}")