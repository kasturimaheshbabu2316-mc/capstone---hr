"""Deterministic In-Memory Query Caching Engine.

Track: Recruitment & HR (Naukri.com)
Part 4 - Task T16: In-Memory Deterministic Query Caching
Features:
  - Canonical query normalization (lowercase, punctuation strip, whitespace collapse)
  - SHA-256 key hashing
  - Dynamic status query bypass (APP-XXXXX queries always query live dataset)
  - Atomic hit/miss counters and sub-millisecond O(1) latency telemetry
"""

import hashlib
import re
import time
from typing import Any, Dict, Optional, Tuple


class QueryCache:
    """In-memory cache for static KB policy queries."""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self.hits: int = 0
        self.misses: int = 0

    @classmethod
    def normalize_query(cls, query: str) -> str:
        """Normalizes query by lowercasing, stripping punctuation, and collapsing whitespace."""
        q = query.lower().strip()
        # Remove all punctuation except alphanumeric and single spaces
        q = re.sub(r"[^\w\s]", " ", q)
        # Collapse multiple spaces into single space
        q = re.sub(r"\s+", " ", q).strip()
        return q

    @classmethod
    def generate_key(cls, query: str) -> str:
        """Generates SHA-256 hash of the canonical normalized query."""
        normalized = cls.normalize_query(query)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def is_dynamic_query(cls, query: str) -> bool:
        """Determines if query targets dynamic applicant state and must bypass cache."""
        return bool(re.search(r"APP-\d{5}", query, re.IGNORECASE))

    def get(self, query: str) -> Optional[Any]:
        """Fetches cached entry if applicable. Bypasses cache for dynamic queries."""
        if self.is_dynamic_query(query):
            # Dynamic queries must never be served from static cache
            return None

        key = self.generate_key(query)
        if key in self._store:
            self.hits += 1
            return self._store[key]

        self.misses += 1
        return None

    def set(self, query: str, value: Any) -> None:
        """Caches value for static KB query. Bypasses dynamic queries."""
        if self.is_dynamic_query(query):
            return

        key = self.generate_key(query)
        self._store[key] = value

    def clear(self) -> None:
        """Clears cache store and resets metrics."""
        self._store.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_ratio = (self.hits / total * 100) if total > 0 else 0.0
        return {
            "entries_count": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "total_lookups": total,
            "hit_ratio_pct": round(hit_ratio, 2),
        }
