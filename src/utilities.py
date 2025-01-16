from typing import Any
from pathlib import Path
from enum import Enum
import json
from datetime import datetime

class EnumJSONEncoder(json.JSONEncoder):
    """JSON encoder with support for Enum and other types"""
    def default(self, obj: Any) -> Any:
        try:
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, (datetime, Path)):
                return str(obj)
            elif hasattr(obj, 'to_dict'):
                return obj.to_dict()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        except Exception as e:
            return str(obj)

def serialize_config(config: Any) -> dict:
    """Safely serialize any configuration object"""
    try:
        return json.loads(
            json.dumps(config, cls=EnumJSONEncoder, sort_keys=True)
        )
    except Exception:
        return str(config)