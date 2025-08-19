import json
import os
from pathlib import Path
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent.parent / "conf.json"
    with open(config_path) as f:
        config = json.load(f)
    
    # Override database config with environment variables if available
    if os.getenv('DB_HOST'):
        config['database']['host'] = os.getenv('DB_HOST')
    if os.getenv('DB_PORT'):
        config['database']['port'] = int(os.getenv('DB_PORT'))
    if os.getenv('DB_USER'):
        config['database']['user'] = os.getenv('DB_USER')
    if os.getenv('DB_PASSWORD'):
        config['database']['password'] = os.getenv('DB_PASSWORD')
    if os.getenv('DB_NAME'):
        config['database']['database'] = os.getenv('DB_NAME')
    
    return config

conf = get_config()
