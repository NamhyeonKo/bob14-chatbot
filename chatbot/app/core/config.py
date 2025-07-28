import json
from pathlib import Path
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent.parent / "conf.json"
    with open(config_path) as f:
        return json.load(f)

conf = get_config()
