"""
utils/git_helpers.py
Git utility wrappers and JSON config loader.

FIX B9 (Round 3): Explicit encoding='utf-8' on JSON file open.
  - Prevents UnicodeDecodeError on Windows when config contains
    emoji or non-ASCII characters in commit messages/author names.
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
        # FIX B9: Explicit UTF-8 encoding — prevents failure on Windows
        # when config contains emoji or non-ASCII in commit messages
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in config file: {e}")
        return None
    except UnicodeDecodeError as e:
        log.error(f"Encoding error reading config (ensure file is saved as UTF-8): {e}")
        return None
