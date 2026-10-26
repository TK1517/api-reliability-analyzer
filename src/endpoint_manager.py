"""Validated endpoint configuration operations."""
from config.settings import DB_PATH
from src import database
from src.validation import validate_endpoint_config

def add_endpoint(name: str, url: str, method: str = 'GET', timeout_seconds: float = 5.0, enabled: bool = True,
                 expected_status_min: int = 200, expected_status_max: int = 299, allow_local: bool = False, db_path=DB_PATH) -> int:
    config = validate_endpoint_config(name,url,method,timeout_seconds,expected_status_min,expected_status_max,allow_local)
    config['enabled'] = enabled
    return database.create_endpoint(config,db_path)

def edit_endpoint(endpoint_id: int, name: str, url: str, method: str = 'GET', timeout_seconds: float = 5.0, enabled: bool = True,
                  expected_status_min: int = 200, expected_status_max: int = 299, allow_local: bool = False, db_path=DB_PATH) -> bool:
    config = validate_endpoint_config(name,url,method,timeout_seconds,expected_status_min,expected_status_max,allow_local)
    config['enabled'] = enabled
    return database.update_endpoint(endpoint_id,config,db_path)
