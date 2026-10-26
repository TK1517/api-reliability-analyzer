# API Reliability and Latency Analyzer

A local-first academic project for measuring HTTP API response time and reliability, storing observations in SQLite, analyzing them with Pandas/NumPy, detecting latency outliers, and presenting results in Streamlit.

## Problem statement and objectives
API consumers need a simple way to observe availability and latency without paid monitoring products. This project supports explicit one-shot checks, historical analysis, endpoint comparison, CSV export, controlled local experiments, and reproducible notebook analysis.

## Features
- Endpoint CRUD and expected HTTP status range configuration.
- UTC timestamps, monotonic elapsed-time measurement, HTTP/transport failure classification, response-size measurement, and bounded concurrent monitoring.
- SQLite persistence with foreign keys, transactions, indexes, and historical queries.
- Reliability and latency metrics, rolling-median and IQR anomaly detectors.
- Streamlit dashboard with overview, endpoint management, monitoring, historical charts, anomaly review, comparisons, and CSV exports.
- Local mock API, repeatable experiments, pytest tests, and Jupyter notebook.
- Safety defaults: HTTP/HTTPS only, private destinations blocked by default, redirects disabled, no credential storage, no automatic polling.

## Architecture
`app.py` is the Streamlit presentation layer. `src/endpoint_manager.py` and `src/validation.py` manage safe configuration. `src/monitor.py` performs one-shot requests and concurrency. `src/database.py` owns SQLite operations. `src/analytics.py`, `src/anomaly_detection.py`, and `src/export.py` provide data processing. The local server and experiment scripts live under `scripts/`.

## Requirements
- Python 3.11 recommended (3.10+ should work with compatible package versions).
- Internet is not needed for tests or local experiments after dependencies are installed.
- No API keys, cloud account, or paid service required.

## Windows PowerShell installation
```powershell
cd api-reliability-analyzer
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -c "from src.database import initialize_database; initialize_database(); print('SQLite initialized')"
python -m streamlit run app.py
```
If PowerShell blocks activation, use a process-scoped setting: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. This does not change the machine-wide policy. Alternatively run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe -m streamlit run app.py` without activation.

## Linux/macOS
```bash
cd api-reliability-analyzer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -c "from src.database import initialize_database; initialize_database(); print('SQLite initialized')"
python -m streamlit run app.py
```

## Local test API (offline experiments)
Open a second terminal from the project root and run:
```bash
python scripts/run_local_test_server.py
```
It listens on `127.0.0.1:8765`. Routes include `/fast`, `/slow`, `/variable`, `/404`, `/500`, `/timeout`, `/small`, and `/large`. In the dashboard, explicitly enable the local/private testing checkbox when adding and monitoring these endpoints. Stop the server with Ctrl+C.

## Experiments and notebook
With the local server running:
```bash
python scripts/run_experiments.py
```
The script writes runtime measurements to `outputs/experiment_results.json` and stores its run data in `data/experiments.db`. Results depend on the machine and current load; do not present them as universal benchmarks.

Start Jupyter:
```bash
jupyter notebook notebooks/api_reliability_analysis.ipynb
```
The notebook loads real local SQLite observations if present and otherwise uses explicitly labelled synthetic data. Run cells top-to-bottom.

## Automated tests
```bash
python -m pytest -q
```
Tests use a local in-process HTTP server and temporary SQLite files. They do not call public APIs. The concurrency timing assertion is based on artificial delays and may vary on heavily loaded machines.

## Database and exports
The dashboard initializes `data/api_monitoring.db` automatically. Tables: `endpoints`, `monitoring_runs`, `api_logs`. Export CSVs from the Data Export page; generated files are placed in `data/exports/`. You can also call the functions in `src/export.py`.

## Configuration
Defaults are in `config/settings.py`. `.env.example` documents a possible DB path override, but environment loading is not required by the core implementation. To use the trusted local test server, use the UI's explicit local-testing option or call the monitor with `allow_local=True` in a controlled experiment.

## Metrics and interpretation
Success means the HTTP status code falls inside the configured expected range (200–299 by default). An HTTP 404/500 is a received response but an unsuccessful API check. Connection failures and timeouts have no HTTP status. Reliability rates include all attempts. Latency summaries include requests for which elapsed time could be measured, including many failed requests; failures that occur before elapsed time is recorded are absent from latency statistics. P95 uses NumPy's linear interpolation convention. A short sample is not a long-term uptime guarantee.

## Security limitations
URL validation blocks non-global IP destinations by default and validates again immediately before requests; redirects are disabled. This is useful defense-in-depth, not a complete SSRF boundary: DNS rebinding, proxies, unusual network routing, and changes between validation and connection can require network-level egress restrictions. Only monitor endpoints you own or are authorized to test. Do not place secrets in URLs. The project deliberately limits methods to GET/HEAD and does not persist response bodies or request credentials.

## Troubleshooting
See [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md). Common fixes: activate the virtual environment, install requirements, check that port 8765 is free, explicitly allow localhost for the test server, and run commands from the repository root so `src` imports resolve.

## Known limitations and future work
This is a manually triggered monitor, not a daemon or production SLA platform. It has no authentication or multi-user access control and is intended for local use. Potential extensions include a scheduled background worker, alerting, richer request templates, retention policies, authentication profiles stored securely, and more robust network-level SSRF controls.

## Academic-use disclaimer
This implementation is intended for educational demonstration. Explain the code and experiment choices in your own words and follow your institution's rules for AI-assisted work. Never report unrun experiments or unmeasured performance as fact.
