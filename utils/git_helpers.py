"""
utils/git_helpers.py
Git utility wrappers and JSON config loader.
"""

import json
from pathlib import Path
from utils.logger import Logger

log = Logger()


def load_json_config(config_path: str) -> dict:
    """Load and parse the JSON config file. Returns dict or None on failure."""
    path = Path(config_path)
    if not path.exists():
        log.error(f"Config file not found: {config_path}")
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in config file: {e}")
        return None
