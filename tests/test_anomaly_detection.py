import numpy as np
from src.anomaly_detection import rolling_median_anomalies, iqr_anomalies

def test_iqr_detects_spike():
    result=iqr_anomalies([10,11,10,12,11,100])
    assert bool(result.iloc[-1]['is_anomaly'])

def test_iqr_normal_and_empty():
    assert not iqr_anomalies([10,10,10,10]).is_anomaly.any()
    assert not iqr_anomalies([None,None]).is_anomaly.any()

def test_rolling_spike():
    result=rolling_median_anomalies([10,11,10,12,11,100],window_size=4,min_observations=3,sensitivity=2)
    assert bool(result.iloc[-1]['is_anomaly'])

def test_rolling_insufficient_and_missing():
    result=rolling_median_anomalies([1,None,2],window_size=5,min_observations=4)
    assert not result.is_anomaly.any()
