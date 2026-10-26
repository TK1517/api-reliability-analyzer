import pytest, sqlite3
from src.database import *
from src.endpoint_manager import add_endpoint

def sample(db_path):
    return add_endpoint('local test','http://127.0.0.1:8000/ok',allow_local=True,db_path=db_path)

def test_initialization_and_endpoint_crud(db_path):
    eid=sample(db_path); assert list_endpoints(db_path)[0]['id']==eid
    assert update_endpoint(eid,{'name':'changed','url':'http://127.0.0.1:8000/ok','method':'GET','timeout_seconds':2,'enabled':False,'expected_status_min':200,'expected_status_max':299},db_path)
    assert list_endpoints(db_path)[0]['name']=='changed'
    assert set_endpoint_enabled(eid,True,db_path)
    assert delete_endpoint(eid,db_path)

def test_foreign_key_enforcement(db_path):
    with pytest.raises(sqlite3.IntegrityError):
        insert_logs(1,[{'endpoint_id':99,'timestamp':'2026-01-01T00:00:00Z','method':'GET','response_time_ms':1,'status_code':200,'success':True,'failure_category':None,'error_message':None,'response_size_bytes':2,'execution_id':'x'}],db_path)

def test_log_insert_and_history(db_path):
    eid=sample(db_path); rid=create_run('sequential',1,1,db_path)
    rec={'endpoint_id':eid,'timestamp':'2026-01-01T00:00:00Z','method':'GET','response_time_ms':12.3,'status_code':200,'success':True,'failure_category':None,'error_message':None,'response_size_bytes':4,'execution_id':'abc'}
    insert_logs(rid,[rec],db_path); finish_run(rid,db_path=db_path)
    assert len(query_logs(db_path,endpoint_id=eid))==1
    assert query_runs(db_path)[0]['run_status']=='completed'

def test_empty_history(db_path): assert query_logs(db_path)==[]
