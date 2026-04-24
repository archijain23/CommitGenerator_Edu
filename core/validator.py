"""
core/validator.py
Validates the JSON config file before execution.
"""

import pytz
from datetime import datetime

REQUIRED_TOP_KEYS = ["repo_path", "author", "time_window", "commits", "options"]
REQUIRED_AUTHOR_KEYS = ["name", "email"]
REQUIRED_TIME_KEYS = ["start", "end", "timezone"]
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def validate_config(cfg: dict) -> list:
    """Validate config dict. Returns list of error strings (empty = valid)."""
    errors = []

    # Check top-level keys
    for key in REQUIRED_TOP_KEYS:
        if key not in cfg:
            errors.append(f"Missing required top-level key: '{key}'")

    if errors:
        return errors  # Can't continue without structure

    # Validate author
    for key in REQUIRED_AUTHOR_KEYS:
        if key not in cfg["author"]:
            errors.append(f"Missing author field: '{key}'")

    # Validate time_window
    tw = cfg["time_window"]
    for key in REQUIRED_TIME_KEYS:
        if key not in tw:
            errors.append(f"Missing time_window field: '{key}'")

    if not errors:
        # Validate timezone
        try:
            tz = pytz.timezone(tw["timezone"])
        except pytz.UnknownTimeZoneError:
            errors.append(f"Unknown timezone: '{tw['timezone']}'")
            return errors

        # Validate datetime strings
        try:
            start_dt = datetime.strptime(tw["start"], DATETIME_FORMAT)
        except ValueError:
            errors.append(f"Invalid start datetime format. Use: YYYY-MM-DD HH:MM:SS")
            start_dt = None

        try:
            end_dt = datetime.strptime(tw["end"], DATETIME_FORMAT)
        except ValueError:
            errors.append(f"Invalid end datetime format. Use: YYYY-MM-DD HH:MM:SS")
            end_dt = None

        if start_dt and end_dt:
            if start_dt >= end_dt:
                errors.append("time_window.start must be before time_window.end")

    # Validate commits list
    if not isinstance(cfg["commits"], list) or len(cfg["commits"]) == 0:
        errors.append("'commits' must be a non-empty list")
    else:
        for i, commit in enumerate(cfg["commits"]):
            if "message" not in commit:
                errors.append(f"Commit #{i+1} is missing 'message' field")
            if "files" not in commit or not isinstance(commit["files"], list):
                errors.append(f"Commit #{i+1} is missing 'files' list")

    # Validate options
    opts = cfg["options"]
    if "num_commits" in opts and not isinstance(opts["num_commits"], int):
        errors.append("options.num_commits must be an integer")

    return errors
