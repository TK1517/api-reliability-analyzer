from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
EXPORT_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "api_monitoring.db"
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_CONCURRENCY_LIMIT = 5
MAX_CONCURRENCY_LIMIT = 20
MAX_ERROR_LENGTH = 300
DEFAULT_ENDPOINTS = [
    {"name": "JSONPlaceholder sample", "url": "https://jsonplaceholder.typicode.com/posts/1", "method": "GET", "timeout_seconds": 5.0, "enabled": True, "expected_status_min": 200, "expected_status_max": 299}
]
