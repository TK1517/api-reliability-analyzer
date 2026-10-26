"""Shared utilities for timestamps and safe error messages."""
from datetime import datetime, timezone
from config.settings import MAX_ERROR_LENGTH

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def shorten_error(message: object, limit: int = MAX_ERROR_LENGTH) -> str:
    text = " ".join(str(message).split())
    return text[:limit] if len(text) > limit else text
