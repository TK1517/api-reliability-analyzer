# Database Schema

SQLite is initialized by `initialize_database()`. Foreign-key enforcement is enabled on every connection.

## `endpoints`
- `id`: integer primary key.
- `name`, `url`: required friendly name and endpoint URL.
- `method`: GET or HEAD only.
- `timeout_seconds`: 0.1–60 seconds.
- `enabled`: 0/1 switch for whether the endpoint is eligible for a run.
- `expected_status_min`, `expected_status_max`: inclusive success interval, default 200–299.
- `created_at`, `updated_at`: UTC ISO-8601 strings.

## `monitoring_runs`
- `id`: primary key.
- `started_at`, `completed_at`: UTC timestamps.
- `execution_mode`: sequential/concurrent.
- `endpoint_count`, `concurrency_limit`: run configuration.
- `run_status`: running/completed/partial/failed.

## `api_logs`
- `id`: primary key.
- `run_id`: FK to `monitoring_runs`, cascade-delete if the run is deleted.
- `endpoint_id`: FK to `endpoints`, restricts endpoint deletion when history exists.
- `timestamp`: UTC timestamp of the attempt.
- `method`, `response_time_ms`, `status_code`, `success`, `failure_category`, `error_message`, `response_size_bytes`, `execution_id`: per-attempt observations.

Indexes support time-range queries, endpoint history, run lookup, and success filtering. SQL statements use placeholders. Writes are grouped in transactions. Keep endpoint records with history; disable rather than delete them to preserve historical joins. Optional `maintain_database(keep_days=...)` can prune old logs and orphaned run records; back up the database before retention cleanup.

## Example queries
```sql
SELECT e.name, COUNT(*) AS attempts, AVG(l.success) * 100 AS success_pct
FROM api_logs l JOIN endpoints e ON e.id=l.endpoint_id
GROUP BY e.id, e.name;

SELECT endpoint_id, timestamp, response_time_ms, status_code, failure_category
FROM api_logs WHERE endpoint_id=? AND timestamp>=? AND timestamp<=?
ORDER BY timestamp;

SELECT failure_category, COUNT(*) AS failures
FROM api_logs WHERE success=0 GROUP BY failure_category ORDER BY failures DESC;
```
