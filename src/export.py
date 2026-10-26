"""CSV export helpers."""
from pathlib import Path
import pandas as pd
from src.database import query_logs
from src.analytics import records_frame, endpoint_metrics
from src.anomaly_detection import annotate_anomalies

def export_logs_csv(db_path, output_path) -> Path:
    path=Path(output_path); path.parent.mkdir(parents=True,exist_ok=True)
    records=query_logs(db_path)
    records_frame(records).to_csv(path,index=False)
    return path

def export_metrics_csv(db_path, output_path) -> Path:
    path=Path(output_path); path.parent.mkdir(parents=True,exist_ok=True)
    df=records_frame(query_logs(db_path)); endpoint_metrics(df).to_csv(path,index=False)
    return path

def export_anomalies_csv(db_path, output_path, method='iqr', **kwargs) -> Path:
    path=Path(output_path); path.parent.mkdir(parents=True,exist_ok=True)
    df=records_frame(query_logs(db_path))
    if not df.empty:
        df['timestamp']=pd.to_datetime(df['timestamp'],utc=True,errors='coerce')
        pieces=[]
        for _, group in df.groupby('endpoint_id'):
            pieces.append(annotate_anomalies(group,method,**kwargs))
        df=pd.concat(pieces,ignore_index=True)
        df=df[df['is_anomaly']]
    else: df['is_anomaly']=pd.Series(dtype=bool)
    df.to_csv(path,index=False)
    return path
