"""Run controlled local reliability and concurrency experiments; results are measured at runtime."""
import json, time, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from src.database import initialize_database, create_endpoint, list_endpoints, query_logs
from src.monitor import run_monitoring
from config.settings import PROJECT_ROOT

def main():
    db=PROJECT_ROOT/'data'/'experiments.db'; initialize_database(db)
    base='http://127.0.0.1:8765'
    specs=[('fast',base+'/fast'),('delayed',base+'/slow'),('not found',base+'/404'),('variable',base+'/variable'),('timeout',base+'/timeout')]
    existing={x['name'] for x in list_endpoints(db)}
    for name,url in specs:
        if name not in existing: create_endpoint({'name':name,'url':url,'method':'GET','timeout_seconds':0.7 if name=='timeout' else 2,'enabled':True,'expected_status_min':200,'expected_status_max':299},db)
    endpoints=list_endpoints(db,enabled_only=True)
    output=[]
    for mode,limit in [('sequential',1),('concurrent',4)]:
        result=run_monitoring(endpoints,mode,limit,db_path=db,allow_local=True)
        row={'experiment':'local endpoint comparison','mode':mode,'endpoint_count':len(endpoints),'concurrency_limit':limit,'elapsed_seconds':round(result['elapsed_seconds'],4),'success_count':sum(x['success'] for x in result['records']),'failure_count':sum(not x['success'] for x in result['records'])}
        output.append(row); print(json.dumps(row,indent=2))
    path=PROJECT_ROOT/'outputs'/'experiment_results.json'; path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(output,indent=2)); print(f'Results saved to {path}')
    print('These values are runtime measurements from the local test server, not public API benchmarks.')
if __name__=='__main__': main()
