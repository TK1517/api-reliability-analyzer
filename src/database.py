"""SQLite persistence layer. Database access is intentionally separate from the UI."""
import sqlite3
from pathlib import Path
from typing import Any
from config.settings import DB_PATH
from src.utils import utc_now_iso

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS endpoints (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 url TEXT NOT NULL,
 method TEXT NOT NULL DEFAULT 'GET' CHECK(method IN ('GET','HEAD')),
 timeout_seconds REAL NOT NULL DEFAULT 5.0 CHECK(timeout_seconds >= 0.1 AND timeout_seconds <= 60),
 enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
 expected_status_min INTEGER NOT NULL DEFAULT 200,
 expected_status_max INTEGER NOT NULL DEFAULT 299,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL,
 CHECK(expected_status_min BETWEEN 100 AND 599),
 CHECK(expected_status_max BETWEEN expected_status_min AND 599)
);
CREATE TABLE IF NOT EXISTS monitoring_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 started_at TEXT NOT NULL,
 completed_at TEXT,
 execution_mode TEXT NOT NULL CHECK(execution_mode IN ('sequential','concurrent')),
 endpoint_count INTEGER NOT NULL DEFAULT 0,
 concurrency_limit INTEGER NOT NULL DEFAULT 1,
 run_status TEXT NOT NULL DEFAULT 'running' CHECK(run_status IN ('running','completed','partial','failed'))
);
CREATE TABLE IF NOT EXISTS api_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 run_id INTEGER NOT NULL REFERENCES monitoring_runs(id) ON DELETE CASCADE,
 endpoint_id INTEGER NOT NULL REFERENCES endpoints(id) ON DELETE RESTRICT,
 timestamp TEXT NOT NULL,
 method TEXT NOT NULL,
 response_time_ms REAL,
 status_code INTEGER,
 success INTEGER NOT NULL CHECK(success IN (0,1)),
 failure_category TEXT,
 error_message TEXT,
 response_size_bytes INTEGER,
 execution_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint_timestamp ON api_logs(endpoint_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_api_logs_run ON api_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_success ON api_logs(success);
"""

def connect(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn

def initialize_database(db_path: str | Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)

def create_endpoint(config: dict, db_path: str | Path = DB_PATH) -> int:
    now = utc_now_iso()
    with connect(db_path) as conn:
        cur = conn.execute("INSERT INTO endpoints(name,url,method,timeout_seconds,enabled,expected_status_min,expected_status_max,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
          (config['name'],config['url'],config.get('method','GET'),config.get('timeout_seconds',5.0),int(config.get('enabled',True)),config.get('expected_status_min',200),config.get('expected_status_max',299),now,now))
        return int(cur.lastrowid)

def list_endpoints(db_path: str | Path = DB_PATH, enabled_only: bool = False) -> list[dict]:
    with connect(db_path) as conn:
        query = "SELECT * FROM endpoints" + (" WHERE enabled=1" if enabled_only else "") + " ORDER BY id"
        return [dict(row) for row in conn.execute(query).fetchall()]

def update_endpoint(endpoint_id: int, config: dict, db_path: str | Path = DB_PATH) -> bool:
    with connect(db_path) as conn:
        cur = conn.execute("UPDATE endpoints SET name=?,url=?,method=?,timeout_seconds=?,enabled=?,expected_status_min=?,expected_status_max=?,updated_at=? WHERE id=?",
          (config['name'],config['url'],config.get('method','GET'),config.get('timeout_seconds',5.0),int(config.get('enabled',True)),config.get('expected_status_min',200),config.get('expected_status_max',299),utc_now_iso(),endpoint_id))
        return cur.rowcount > 0

def set_endpoint_enabled(endpoint_id: int, enabled: bool, db_path: str | Path = DB_PATH) -> bool:
    with connect(db_path) as conn:
        cur = conn.execute("UPDATE endpoints SET enabled=?,updated_at=? WHERE id=?", (int(enabled),utc_now_iso(),endpoint_id))
        return cur.rowcount > 0

def delete_endpoint(endpoint_id: int, db_path: str | Path = DB_PATH) -> bool:
    with connect(db_path) as conn:
        cur = conn.execute("DELETE FROM endpoints WHERE id=?", (endpoint_id,))
        return cur.rowcount > 0

def create_run(execution_mode: str, endpoint_count: int, concurrency_limit: int, db_path: str | Path = DB_PATH) -> int:
    with connect(db_path) as conn:
        cur = conn.execute("INSERT INTO monitoring_runs(started_at,execution_mode,endpoint_count,concurrency_limit,run_status) VALUES(?,?,?,?, 'running')",
          (utc_now_iso(),execution_mode,endpoint_count,concurrency_limit))
        return int(cur.lastrowid)

def finish_run(run_id: int, run_status: str = 'completed', db_path: str | Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute("UPDATE monitoring_runs SET completed_at=?,run_status=? WHERE id=?", (utc_now_iso(),run_status,run_id))

def insert_logs(run_id: int, records: list[dict], db_path: str | Path = DB_PATH) -> None:
    rows = [(run_id,r['endpoint_id'],r['timestamp'],r['method'],r.get('response_time_ms'),r.get('status_code'),int(r['success']),r.get('failure_category'),r.get('error_message'),r.get('response_size_bytes'),r['execution_id']) for r in records]
    with connect(db_path) as conn:
        conn.executemany("INSERT INTO api_logs(run_id,endpoint_id,timestamp,method,response_time_ms,status_code,success,failure_category,error_message,response_size_bytes,execution_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)", rows)

def query_logs(db_path: str | Path = DB_PATH, endpoint_id: int | None = None, start_time: str | None = None, end_time: str | None = None, limit: int | None = None) -> list[dict]:
    sql = "SELECT l.*, e.name AS endpoint_name, e.url AS endpoint_url, r.execution_mode FROM api_logs l JOIN endpoints e ON e.id=l.endpoint_id JOIN monitoring_runs r ON r.id=l.run_id WHERE 1=1"
    args: list[Any] = []
    if endpoint_id is not None: sql += " AND l.endpoint_id=?"; args.append(endpoint_id)
    if start_time: sql += " AND l.timestamp>=?"; args.append(start_time)
    if end_time: sql += " AND l.timestamp<=?"; args.append(end_time)
    sql += " ORDER BY l.timestamp DESC"
    if limit is not None: sql += " LIMIT ?"; args.append(int(limit))
    with connect(db_path) as conn:
        return [dict(row) for row in conn.execute(sql,args).fetchall()]

def query_runs(db_path: str | Path = DB_PATH, limit: int = 50) -> list[dict]:
    with connect(db_path) as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM monitoring_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

def maintain_database(db_path: str | Path = DB_PATH, keep_days: int | None = None) -> None:
    """Optional maintenance: optimize SQLite; if keep_days is set, prune old logs/runs."""
    with connect(db_path) as conn:
        if keep_days is not None and keep_days > 0:
            conn.execute("DELETE FROM api_logs WHERE timestamp < datetime('now', ?)", (f'-{int(keep_days)} days',))
            conn.execute("DELETE FROM monitoring_runs WHERE id NOT IN (SELECT DISTINCT run_id FROM api_logs) AND started_at < datetime('now', ?)", (f'-{int(keep_days)} days',))
        conn.execute("PRAGMA optimize")
