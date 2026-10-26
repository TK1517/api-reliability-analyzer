"""Explainable latency anomaly detectors."""
import numpy as np
import pandas as pd

def rolling_median_anomalies(values, window_size: int = 10, min_observations: int = 5, sensitivity: float = 3.0) -> pd.DataFrame:
    series=pd.to_numeric(pd.Series(values),errors='coerce')
    prior=series.shift(1)
    baseline=prior.rolling(window=max(1,int(window_size)),min_periods=max(1,int(min_observations))).median()
    deviation=(prior-baseline).abs().rolling(window=max(1,int(window_size)),min_periods=max(1,int(min_observations))).median()
    threshold=baseline + float(sensitivity)*deviation
    # When historical MAD is zero, require a strict increase above baseline.
    anomalous=(series>threshold) & baseline.notna()
    anomalous=anomalous | ((series>baseline) & baseline.notna() & (deviation.fillna(0)==0))
    return pd.DataFrame({"value":series,"baseline":baseline,"threshold":threshold,"is_anomaly":anomalous.fillna(False)})

def iqr_anomalies(values, k: float = 1.5, high_only: bool = True) -> pd.DataFrame:
    series=pd.to_numeric(pd.Series(values),errors='coerce')
    valid=series.dropna()
    if valid.empty:
        q1=q3=iqr=lower=upper=np.nan
    else:
        q1=float(valid.quantile(.25,interpolation='linear')); q3=float(valid.quantile(.75,interpolation='linear')); iqr=q3-q1
        lower=q1-float(k)*iqr; upper=q3+float(k)*iqr
    anomaly=(series>upper) if high_only else ((series<lower)|(series>upper))
    return pd.DataFrame({"value":series,"q1":q1,"q3":q3,"iqr":iqr,"lower_bound":lower,"upper_bound":upper,"is_anomaly":anomaly.fillna(False)})

def annotate_anomalies(records: pd.DataFrame, method: str = 'rolling_median', **kwargs) -> pd.DataFrame:
    if records.empty: return records.assign(is_anomaly=pd.Series(dtype=bool),detection_method=pd.Series(dtype=str))
    df=records.copy().sort_values('timestamp')
    values=df['response_time_ms']
    result=rolling_median_anomalies(values,**kwargs) if method=='rolling_median' else iqr_anomalies(values,**kwargs)
    for col in result.columns:
        if col not in df: df[col]=result[col].values
    df['is_anomaly']=result['is_anomaly'].values; df['detection_method']=method
    return df
