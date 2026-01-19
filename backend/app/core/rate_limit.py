from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import DefaultDict


@dataclass
class AttemptWindow:
    last_attempt: datetime
    attempts: int
    blocked_until: datetime | None = None


class InMemoryRateLimiter:
    def __init__(self, attempts: int, window_seconds: int, block_minutes: int):
        self.attempts = attempts
        self.window = timedelta(seconds=window_seconds)
        self.block_duration = timedelta(minutes=block_minutes)
        self.cache: DefaultDict[str, AttemptWindow] = defaultdict(
            lambda: AttemptWindow(last_attempt=datetime.utcnow(), attempts=0)
        )

    def register_failure(self, key: str) -> None:
        now = datetime.utcnow()
        window = self.cache[key]
        if window.blocked_until and window.blocked_until > now:
            return
        if now - window.last_attempt > self.window:
            window.attempts = 0
        window.last_attempt = now
        window.attempts += 1
        if window.attempts >= self.attempts:
            window.blocked_until = now + self.block_duration

    def clear(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]

    def is_blocked(self, key: str) -> bool:
        now = datetime.utcnow()
        window = self.cache.get(key)
        if not window:
            return False
        if window.blocked_until and window.blocked_until > now:
            return True
        if window.blocked_until and window.blocked_until <= now:
            del self.cache[key]
            return False
        return False
