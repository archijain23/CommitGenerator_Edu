"""
core/validator.py
Validates the JSON config file before execution.

FIX Issue 4: time_override values in each commit are now validated
  for correct datetime format '%Y-%m-%d %H:%M:%S' so the user gets
  a clear error message instead of a raw ValueError crash at runtime.
"""

import pytz
from datetime import datetime

REQUIRED_TOP_KEYS = ["repo_path", "author", "time_window", "commits", "options"]
REQUIRED_AUTHOR_KEYS = ["name", "email"]
REQUIRED_TIME_KEYS = ["start", "end", "timezone"]
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _is_valid_datetime(dt_str: str) -> bool:
    """Return True if dt_str matches the expected datetime format."""
    try:
        datetime.strptime(dt_str, DATETIME_FORMAT)
        return True
    except ValueError:
        return False


def validate_config(cfg: dict) -> list:
    """Validate config dict. Returns list of error strings (empty = valid)."""
    errors = []

    # Check top-level keys
    for key in REQUIRED_TOP_KEYS:
        if key not in cfg:
            errors.append(f"Missing required top-level key: '{key}'")

    if errors:
        return errors

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
        try:
            tz = pytz.timezone(tw["timezone"])
        except pytz.UnknownTimeZoneError:
            errors.append(f"Unknown timezone: '{tw['timezone']}'. Use IANA format e.g. 'Asia/Kolkata'")
            return errors

        try:
            start_dt = datetime.strptime(tw["start"], DATETIME_FORMAT)
        except ValueError:
            errors.append(f"Invalid time_window.start format. Use: YYYY-MM-DD HH:MM:SS")
            start_dt = None

        try:
            end_dt = datetime.strptime(tw["end"], DATETIME_FORMAT)
        except ValueError:
            errors.append(f"Invalid time_window.end format. Use: YYYY-MM-DD HH:MM:SS")
            end_dt = None

        if start_dt and end_dt and start_dt >= end_dt:
            errors.append("time_window.start must be before time_window.end")

    # Validate commits list
    if not isinstance(cfg["commits"], list) or len(cfg["commits"]) == 0:
        errors.append("'commits' must be a non-empty list")
    else:
        for i, commit in enumerate(cfg["commits"]):
            label = f"Commit #{i+1}"

            if "message" not in commit:
                errors.append(f"{label}: missing 'message' field")

            if "files" not in commit or not isinstance(commit["files"], list):
                errors.append(f"{label}: missing or invalid 'files' list")

            # FIX Issue 4: Validate time_override format if present
            if "time_override" in commit:
                if not _is_valid_datetime(commit["time_override"]):
                    errors.append(
                        f"{label}: 'time_override' has invalid format '{commit['time_override']}'. "
                        f"Use: YYYY-MM-DD HH:MM:SS (e.g. '2026-04-25 14:30:00')"
                    )

    # Validate options
    opts = cfg.get("options", {})
    if "num_commits" in opts and not isinstance(opts["num_commits"], int):
        errors.append("options.num_commits must be an integer")
    if "num_commits" in opts and opts["num_commits"] < 1:
        errors.append("options.num_commits must be at least 1")

    return errors
