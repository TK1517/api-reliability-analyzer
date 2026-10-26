# Troubleshooting

- **Python not found:** install Python 3.11 and verify `py -3.11 --version` on Windows or `python3 --version` on Linux/macOS.
- **Virtual environment activation blocked:** in PowerShell use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for the current shell only, or call `.venv\Scripts\python.exe` directly.
- **Missing packages:** activate `.venv` and run `python -m pip install -r requirements.txt`.
- **Port 8765 already in use:** stop the other process or change the port in `scripts/run_local_test_server.py` and update endpoint URLs.
- **External API unavailable:** expected behavior; use the local mock server and opt into local testing.
- **Local endpoint rejected:** the private/loopback block is intentional. Explicitly enable local-testing mode only for the trusted local server.
- **SQLite database locked:** close other app instances, ensure no process is holding a long transaction, and retry. Connections use a 10-second timeout and busy timeout.
- **Empty dashboard:** monitoring records appear only after a run. Check that endpoints are enabled and selected.
- **Streamlit reruns:** Streamlit reruns on widget interaction; monitoring is only called by the button handler and does not start automatically.
- **Notebook import errors:** launch Jupyter from the project root or add the root to `sys.path` as the notebook does.
- **Test failures:** run one file with `python -m pytest tests/test_monitor.py -vv`; inspect the traceback. The timing test can vary under heavy load.
- **Endpoint deletion blocked:** historical records reference the endpoint. Disable it to stop future checks while preserving history.
