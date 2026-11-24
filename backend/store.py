import secrets
import threading
import time
from collections import deque


class SessionStore:
    
    def __init__(self, ttl_seconds=3600, max_sessions=200):
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._data = {}
        self._lock = threading.Lock()

    def _purge(self, now):
        expired = [k for k, v in self._data.items() if now - v["last_used"] > self.ttl_seconds]
        for key in expired:
            del self._data[key]

        # Still too many? drop the least recently used ones
        while len(self._data) >= self.max_sessions:
            oldest = min(self._data, key=lambda k: self._data[k]["last_used"])
            del self._data[oldest]

    def create(self, filename, text):
        session_id = secrets.token_urlsafe(16)
        now = time.time()
        with self._lock:
            self._purge(now)
            self._data[session_id] = {"filename": filename, "text": text, "last_used": now}
        return session_id

    def get(self, session_id):
        now = time.time()
        with self._lock:
            item = self._data.get(session_id)
            if not item:
                return None
            if now - item["last_used"] > self.ttl_seconds:
                del self._data[session_id]
                return None
            item["last_used"] = now
            return item

    def count(self):
        with self._lock:
            return len(self._data)


class RateLimiter:
    """Sliding-window limiter: at most `limit` hits per `window` seconds for each key."""

    def __init__(self):
        self._hits = {}
        self._lock = threading.Lock()

    def check(self, key, limit, window):
        """Return 0 if allowed, otherwise the number of seconds to wait."""
        now = time.time()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > window:
                hits.popleft()

            if len(hits) >= limit:
                return max(1, int(window - (now - hits[0])) + 1)

            hits.append(now)

            # keep the dictionary from growing forever
            if len(self._hits) > 5000:
                for stale in [k for k, v in self._hits.items() if not v]:
                    del self._hits[stale]
            return 0
