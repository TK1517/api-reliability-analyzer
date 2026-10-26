"""Pandas/NumPy-based monitoring analytics."""
import numpy as np
import pandas as pd
from src.database import query_logs

def records_frame(records: list[dict]) -> pd.DataFrame:
    df=pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=['timestamp','endpoint_id','endpoint_name','response_time_ms','status_code','success','failure_category'])
    if 'timestamp' in df: df['timestamp']=pd.to_datetime(df['timestamp'],utc=True,errors='coerce')
    if 'success' in df: df['success']=df['success'].astype(bool)
    for col in ('response_time_ms','status_code','response_size_bytes'):
        if col in df: df[col]=pd.to_numeric(df[col],errors='coerce')
    return df

def calculate_metrics(records: list[dict] | pd.DataFrame) -> dict:
    df=records.copy() if isinstance(records,pd.DataFrame) else records_frame(records)
    if df.empty:
        return {"total_attempts":0,"successful_requests":0,"failed_requests":0,"success_rate_pct":None,"failure_rate_pct":None,
                "min_latency_ms":None,"max_latency_ms":None,"mean_latency_ms":None,"median_latency_ms":None,"p95_latency_ms":None,
                "latency_stddev_ms":None,"timeout_count":0,"http_error_count":0,"connection_error_count":0}
    success=df['success'].fillna(False).astype(bool) if 'success' in df else pd.Series(False,index=df.index)
    total=len(df); successful=int(success.sum()); failed=total-successful
    latency=pd.to_numeric(df.get('response_time_ms',pd.Series(index=df.index,dtype=float)),errors='coerce').dropna()
    cats=df.get('failure_category',pd.Series(index=df.index,dtype=object)).fillna('').astype(str)
    return {"total_attempts":total,"successful_requests":successful,"failed_requests":failed,
            "success_rate_pct":successful/total*100,"failure_rate_pct":failed/total*100,
            "min_latency_ms":float(latency.min()) if len(latency) else None,"max_latency_ms":float(latency.max()) if len(latency) else None,
            "mean_latency_ms":float(latency.mean()) if len(latency) else None,"median_latency_ms":float(latency.median()) if len(latency) else None,
            "p95_latency_ms":float(np.percentile(latency,95,method='linear')) if len(latency) else None,
            "latency_stddev_ms":float(latency.std(ddof=1)) if len(latency)>1 else (0.0 if len(latency)==1 else None),
            "timeout_count":int(cats.isin(['connect_timeout','read_timeout','timeout']).sum()),
            "http_error_count":int((cats=='http_error').sum()),"connection_error_count":int((cats=='connection_error').sum())}

def endpoint_metrics(records: list[dict] | pd.DataFrame) -> pd.DataFrame:
    df=records.copy() if isinstance(records,pd.DataFrame) else records_frame(records)
    if df.empty: return pd.DataFrame(columns=['endpoint_id','endpoint_name','total_attempts','success_rate_pct','median_latency_ms','p95_latency_ms','failed_requests','timeout_count'])
    rows=[]
    for endpoint_id, group in df.groupby('endpoint_id',dropna=False):
        m=calculate_metrics(group); endpoint_name = group['endpoint_name'].iloc[0] if 'endpoint_name' in group.columns and len(group) else 'Endpoint'
        rows.append({"endpoint_id":endpoint_id,"endpoint_name":endpoint_name,
          "total_attempts":m['total_attempts'],"success_rate_pct":m['success_rate_pct'],"median_latency_ms":m['median_latency_ms'],"p95_latency_ms":m['p95_latency_ms'],
          "failed_requests":m['failed_requests'],"timeout_count":m['timeout_count']})
    return pd.DataFrame(rows)

def load_analytics(db_path, endpoint_id=None, start_time=None, end_time=None) -> pd.DataFrame:
    return records_frame(query_logs(db_path,endpoint_id,start_time,end_time))
