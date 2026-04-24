"""
core/time_distributor.py
Distributes commits evenly or randomly across a user-defined time window.
Converts local timezone times to UTC for Git environment variables.
"""

import pytz
import random
from datetime import datetime, timedelta

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class TimeDistributor:
    def __init__(self, time_window: dict):
        self.tz = pytz.timezone(time_window["timezone"])
        self.start = self._localize(time_window["start"])
        self.end = self._localize(time_window["end"])
        self.total_seconds = int((self.end - self.start).total_seconds())

    def _localize(self, dt_str: str) -> datetime:
        """Parse datetime string and localize to configured timezone."""
        dt_naive = datetime.strptime(dt_str, DATETIME_FORMAT)
        return self.tz.localize(dt_naive)

    def distribute_evenly(self, n: int) -> list:
        """
        Spread n commits evenly across the time window.
        Returns list of UTC datetime strings for Git env vars.
        """
        if n <= 1:
            return [self._to_utc_str(self.start)]

        interval = self.total_seconds / (n - 1) if n > 1 else 0
        timestamps = []
        for i in range(n):
            offset = int(interval * i)
            dt = self.start + timedelta(seconds=offset)
            timestamps.append(self._to_utc_str(dt))
        return timestamps

    def distribute_random(self, n: int) -> list:
        """
        Place n commits at random points within the time window.
        Returns sorted list of UTC datetime strings.
        """
        offsets = sorted(random.randint(0, self.total_seconds) for _ in range(n))
        timestamps = []
        for offset in offsets:
            dt = self.start + timedelta(seconds=offset)
            timestamps.append(self._to_utc_str(dt))
        return timestamps

    def override_time(self, dt_str: str) -> str:
        """
        Convert a user-supplied override time (in configured timezone) to UTC string.
        """
        dt_local = self._localize(dt_str)
        return self._to_utc_str(dt_local)

    def _to_utc_str(self, dt: datetime) -> str:
        """Convert timezone-aware datetime to UTC string for Git."""
        dt_utc = dt.astimezone(pytz.utc)
        return dt_utc.strftime(DATETIME_FORMAT)
