from src.endpoint_manager import add_endpoint
from src.database import list_endpoints, query_logs
from src.monitor import run_monitoring

def test_empty_monitoring_is_safe(db_path):
    result=run_monitoring([],db_path=db_path)
    assert result['records']==[] and result['run_id'] is None

def test_url_validation_blocks_private_by_default(db_path):
    import pytest
    from src.validation import EndpointValidationError
    with pytest.raises(EndpointValidationError): add_endpoint('unsafe','http://127.0.0.1:8000',db_path=db_path)
