"""
core/time_distributor.py
Distributes commits evenly or randomly across a user-defined time window.
Converts local timezone times to UTC ISO 8601 for GitPython author_date/commit_date.

FIXES APPLIED:
  - Round 2 Issue 1: ISO 8601 'T' separator in _to_utc_str
  - B8 [Round 3]: Document that total_seconds=0 edge case is safely caught
    by validator.py (start >= end check). Do NOT remove validator dependency.
"""

import pytz
import random
from datetime import datetime, timedelta

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
# ISO 8601 with T separator — strictly required by GitPython index.commit(author_date=...)
# IMPORTANT: Space-separated format works in some Git versions but is unreliable.
# Do NOT change this format string.
GIT_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class TimeDistributor:
    def __init__(self, time_window: dict):
        self.tz = pytz.timezone(time_window["timezone"])
        self.start = self._localize(time_window["start"])
        self.end = self._localize(time_window["end"])
        # B8 NOTE: total_seconds=0 when start==end. This edge case is caught
        # upstream by validator.py (start >= end raises error). If you ever
        # remove the validator call in main.py, add a guard here too.
        self.total_seconds = int((self.end - self.start).total_seconds())

    def _localize(self, dt_str: str) -> datetime:
        """Parse datetime string and localize to configured timezone."""
        dt_naive = datetime.strptime(dt_str, DATETIME_FORMAT)
        return self.tz.localize(dt_naive)

    def distribute_evenly(self, n: int) -> list:
        """
        Spread n commits evenly across the time window.
        Returns list of UTC ISO 8601 strings for GitPython.
        """
        if n <= 1:
            return [self._to_utc_str(self.start)]

        interval = self.total_seconds / (n - 1)
        timestamps = []
        for i in range(n):
            offset = int(interval * i)
            dt = self.start + timedelta(seconds=offset)
            timestamps.append(self._to_utc_str(dt))
        return timestamps

    def distribute_random(self, n: int) -> list:
        """
        Place n commits at random points within the time window.
        Returns sorted list of UTC ISO 8601 strings.
        """
        offsets = sorted(random.randint(0, self.total_seconds) for _ in range(n))
        timestamps = []
        for offset in offsets:
            dt = self.start + timedelta(seconds=offset)
            timestamps.append(self._to_utc_str(dt))
        return timestamps

    def override_time(self, dt_str: str) -> str:
        """Convert a user-supplied override time to UTC ISO 8601 string."""
        dt_local = self._localize(dt_str)
        return self._to_utc_str(dt_local)

    def _to_utc_str(self, dt: datetime) -> str:
        """Convert timezone-aware datetime to UTC ISO 8601 string for GitPython."""
        dt_utc = dt.astimezone(pytz.utc)
        return dt_utc.strftime(GIT_DATETIME_FORMAT)
