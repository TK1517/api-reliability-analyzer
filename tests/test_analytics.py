from src.analytics import calculate_metrics

def test_metrics_mixed():
    rows=[{'success':True,'response_time_ms':10,'failure_category':None},{'success':False,'response_time_ms':20,'failure_category':'http_error'}, {'success':False,'response_time_ms':None,'failure_category':'read_timeout'}]
    m=calculate_metrics(rows)
    assert m['total_attempts']==3 and m['successful_requests']==1 and m['failed_requests']==2
    assert round(m['success_rate_pct'],2)==33.33 and round(m['failure_rate_pct'],2)==66.67
    assert m['median_latency_ms']==15 and m['timeout_count']==1 and m['http_error_count']==1

def test_empty_metrics():
    m=calculate_metrics([]); assert m['total_attempts']==0 and m['success_rate_pct'] is None

def test_all_failed():
    m=calculate_metrics([{'success':False,'response_time_ms':None,'failure_category':'connection_error'}])
    assert m['success_rate_pct']==0 and m['failure_rate_pct']==100 and m['median_latency_ms'] is None
