"""HTTP monitoring engine with bounded concurrency and explicit failure categories."""
import time, uuid, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError, InvalidURL, MissingSchema, InvalidSchema, RequestException
from config.settings import DB_PATH, DEFAULT_CONCURRENCY_LIMIT, MAX_CONCURRENCY_LIMIT
from src import database
from src.utils import utc_now_iso, shorten_error
from src.validation import validate_endpoint_url

logger = logging.getLogger(__name__)

def monitor_endpoint(endpoint: dict, execution_id: str | None = None, allow_local: bool = False) -> dict:
    execution_id = execution_id or str(uuid.uuid4())
    record = {"endpoint_id": int(endpoint['id']), "endpoint_name": endpoint['name'], "timestamp": utc_now_iso(),
              "method": endpoint.get('method','GET'), "response_time_ms": None, "status_code": None, "success": False,
              "failure_category": None, "error_message": None, "response_size_bytes": None, "execution_id": execution_id}
    start = time.monotonic()
    try:
        validate_endpoint_url(endpoint['url'], allow_local=allow_local)
        response = requests.request(endpoint.get('method','GET'), endpoint['url'], timeout=float(endpoint.get('timeout_seconds',5.0)),
                                    allow_redirects=False, headers={"User-Agent":"API-Reliability-Analyzer/1.0"})
        try:
            record['response_time_ms'] = (time.monotonic()-start)*1000
            record['status_code'] = int(response.status_code)
            record['response_size_bytes'] = len(response.content)
            low, high = int(endpoint.get('expected_status_min',200)), int(endpoint.get('expected_status_max',299))
            record['success'] = low <= response.status_code <= high
            if not record['success']:
                record['failure_category'] = 'http_error'
                record['error_message'] = f"HTTP status {response.status_code} outside expected range {low}-{high}"
        finally:
            response.close()
    except ConnectTimeout as exc:
        record['response_time_ms'] = (time.monotonic()-start)*1000
        record['failure_category'] = 'connect_timeout'; record['error_message'] = shorten_error(exc or 'Connection timed out')
    except ReadTimeout as exc:
        record['response_time_ms'] = (time.monotonic()-start)*1000
        record['failure_category'] = 'read_timeout'; record['error_message'] = shorten_error(exc or 'Response read timed out')
    except (InvalidURL, MissingSchema, InvalidSchema, ValueError) as exc:
        record['failure_category'] = 'invalid_url'; record['error_message'] = shorten_error(exc)
    except ConnectionError as exc:
        record['response_time_ms'] = (time.monotonic()-start)*1000
        record['failure_category'] = 'connection_error'; record['error_message'] = shorten_error(exc)
    except RequestException as exc:
        record['response_time_ms'] = (time.monotonic()-start)*1000
        record['failure_category'] = 'request_error'; record['error_message'] = shorten_error(exc)
    except Exception as exc:
        logger.exception('Unexpected monitoring error for endpoint id=%s', endpoint.get('id'))
        record['response_time_ms'] = (time.monotonic()-start)*1000
        record['failure_category'] = 'unexpected_error'; record['error_message'] = shorten_error(type(exc).__name__ + ': ' + str(exc))
    return record

def run_monitoring(endpoints: list[dict], execution_mode: str = 'concurrent', concurrency_limit: int = DEFAULT_CONCURRENCY_LIMIT,
                   db_path=DB_PATH, allow_local: bool = False, persist: bool = True) -> dict:
    if execution_mode not in {'sequential','concurrent'}: raise ValueError('execution_mode must be sequential or concurrent')
    if not endpoints: return {"run_id": None, "records": [], "elapsed_seconds": 0.0, "run_status": "completed"}
    limit = max(1,min(int(concurrency_limit),MAX_CONCURRENCY_LIMIT,len(endpoints))) if execution_mode == 'concurrent' else 1
    execution_id = str(uuid.uuid4())
    run_id = database.create_run(execution_mode,len(endpoints),limit,db_path) if persist else None
    start = time.monotonic(); records=[]; errors=0
    if execution_mode == 'sequential':
        for endpoint in endpoints:
            result=monitor_endpoint(endpoint,execution_id,allow_local); records.append(result)
    else:
        with ThreadPoolExecutor(max_workers=limit,thread_name_prefix='api-monitor') as pool:
            future_map={pool.submit(monitor_endpoint,e,execution_id,allow_local):e for e in endpoints}
            for future in as_completed(future_map):
                endpoint=future_map[future]
                try: records.append(future.result())
                except Exception as exc:
                    errors += 1
                    records.append({"endpoint_id":int(endpoint['id']),"endpoint_name":endpoint['name'],"timestamp":utc_now_iso(),"method":endpoint.get('method','GET'),"response_time_ms":None,"status_code":None,"success":False,"failure_category":"worker_error","error_message":shorten_error(exc),"response_size_bytes":None,"execution_id":execution_id})
    elapsed=time.monotonic()-start
    records.sort(key=lambda r: r['endpoint_id'])
    status='failed' if errors == len(endpoints) else ('partial' if errors else 'completed')
    if persist and run_id is not None:
        try:
            database.insert_logs(run_id,records,db_path); database.finish_run(run_id,status,db_path)
        except Exception:
            database.finish_run(run_id,'failed',db_path)
            raise
    return {"run_id":run_id,"records":records,"elapsed_seconds":elapsed,"run_status":status,"execution_id":execution_id}
