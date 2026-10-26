"""Run a local deterministic test API. Use only for trusted local experiments."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json, time
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        routes={'/fast':(200,{'message':'fast response'}),'/404':(404,{'error':'not found'}),'/500':(500,{'error':'simulated server error'}),'/small':(200,{'x':'ok'}),'/large':(200,{'payload':'x'*8192})}
        if self.path=='/slow': time.sleep(0.4); status,data=200,{'message':'delayed response'}
        elif self.path=='/variable': time.sleep((int(time.time()*1000)%250)/1000); status,data=200,{'message':'variable delay'}
        elif self.path=='/timeout': time.sleep(3); status,data=200,{'message':'long delay'}
        else: status,data=routes.get(self.path,(200,{'message':'default success'}))
        body=json.dumps(data).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers()
        try: self.wfile.write(body)
        except BrokenPipeError: pass
    def log_message(self,*args): print('%s - %s' % (self.address_string(),args[0] % args[1:]))
if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',8765),Handler); print('Local test API: http://127.0.0.1:8765 (Ctrl+C to stop)');
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
