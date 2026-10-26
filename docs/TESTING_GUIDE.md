# Testing Guide

Install development dependencies using `python -m pip install -r requirements.txt`, then run `python -m pytest -q` from the project root. Tests use temporary SQLite databases and an in-process local HTTP server, so public API availability is not required.

Test groups:
- `test_monitor.py`: 200, 404, 500, read timeout, connection failure, invalid URL, persistence, concurrent mapping, and delayed sequential/concurrent comparison.
- `test_database.py`: initialization, CRUD, foreign-key enforcement, log insertion, historical query, and empty history.
- `test_analytics.py`: success/failure rates, median, empty data, and all-failed records.
- `test_anomaly_detection.py`: spike detection, normal values, missing data, insufficient observations, and zero-IQR.
- `test_integration.py`: empty monitoring and private-destination blocking.

Expected outcome: all tests pass without internet access. The timing comparison can be sensitive to extreme machine load. Streamlit's full browser UI is not automated in this baseline; manually verify forms, empty states, CSV downloads, and error messages. Test coverage is not claimed to be 100% unless measured separately.
