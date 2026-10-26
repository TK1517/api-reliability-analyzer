"""Manual one-shot monitoring helper; no background loop is started automatically."""
from src.database import list_endpoints
from src.monitor import run_monitoring

def monitor_enabled_endpoints(execution_mode='concurrent', concurrency_limit=5, db_path=None, allow_local=False):
    endpoints=list_endpoints(db_path,enabled_only=True) if db_path is not None else list_endpoints(enabled_only=True)
    kwargs={'execution_mode':execution_mode,'concurrency_limit':concurrency_limit,'allow_local':allow_local}
    if db_path is not None: kwargs['db_path']=db_path
    return run_monitoring(endpoints,**kwargs)
