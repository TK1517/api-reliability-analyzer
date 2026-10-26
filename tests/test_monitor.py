from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time
from src.monitor import monitor_endpoint, run_monitoring

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/slow': time.sleep(.25)
        code=404 if self.path=='/404' else (500 if self.path=='/500' else 200)
        body=b'ok' if code==200 else b'error'
        self.send_response(code); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass

class Server:
    def __enter__(self):
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler); self.thread=Thread(target=self.server.serve_forever,daemon=True); self.thread.start(); self.base=f'http://127.0.0.1:{self.server.server_port}'; return self
    def __exit__(self,*args): self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)

def endpoint(url, eid=1, timeout=1): return {'id':eid,'name':f'test-{eid}','url':url,'method':'GET','timeout_seconds':timeout,'expected_status_min':200,'expected_status_max':299}

def test_http_statuses():
    with Server() as s:
        assert monitor_endpoint(endpoint(s.base+'/ok'),allow_local=True)['success']
        r=monitor_endpoint(endpoint(s.base+'/404'),allow_local=True); assert not r['success'] and r['failure_category']=='http_error' and r['status_code']==404
        assert monitor_endpoint(endpoint(s.base+'/500'),allow_local=True)['failure_category']=='http_error'

def test_timeout_connection_and_invalid_url():
    with Server() as s:
        r=monitor_endpoint(endpoint(s.base+'/slow',timeout=.05),allow_local=True); assert r['failure_category']=='read_timeout'
    r=monitor_endpoint(endpoint('http://127.0.0.1:1/no',timeout=.2),allow_local=True); assert r['failure_category']=='connection_error'
    r=monitor_endpoint(endpoint('not a url'),allow_local=True); assert r['failure_category']=='invalid_url'

def test_concurrent_mapping_and_persistence(db_path):
    from src.endpoint_manager import add_endpoint
    with Server() as s:
        ids=[]
        for i,path in enumerate(['/ok','/slow','/404'],1): ids.append(add_endpoint(f'e{i}',s.base+path,allow_local=True,db_path=db_path))
        eps=__import__('src.database',fromlist=['list_endpoints']).list_endpoints(db_path)
        result=run_monitoring(eps,'concurrent',3,db_path,allow_local=True)
        assert len(result['records'])==3 and {x['endpoint_id'] for x in result['records']}==set(ids)
        assert len(__import__('src.database',fromlist=['query_logs']).query_logs(db_path))==3

def test_sequential_vs_concurrent_timing():
    with Server() as s:
        eps=[endpoint(s.base+'/slow',i,timeout=2) for i in range(1,4)]
        seq=run_monitoring(eps,'sequential',1,persist=False,allow_local=True)
        con=run_monitoring(eps,'concurrent',3,persist=False,allow_local=True)
        assert con['elapsed_seconds'] < seq['elapsed_seconds']
