# API Monitoring Guide

1. Start the dashboard with `python -m streamlit run app.py`.
2. Open **Endpoint Management** and add a friendly name, HTTP/HTTPS URL, method, timeout, and expected status interval.
3. For normal public endpoints, leave the local/private destination checkbox unchecked. For the project's own local test API, explicitly opt in only when the local server is running.
4. Open **Run Monitoring**, select endpoints, choose sequential or concurrent mode, set a bounded concurrency limit, and click **Run monitoring now**. There is no automatic polling.
5. Read the results: status code means an HTTP response arrived; `http_error` means its status fell outside the expected range. A timeout or connection failure has no status code. Latency is elapsed wall time measured with a monotonic clock.
6. Use **Historical Analytics** to filter and chart the saved observations. Use **Anomaly Detection** to inspect rolling-median or IQR flags; flags are statistical signals, not proof of an outage.
7. Use **Endpoint Comparison** with sample counts and observation ranges in mind. Use **Data Export** to download CSV files.

Do not monitor services without authorization, do not add secrets to URLs, and do not use this tool as a load tester.
