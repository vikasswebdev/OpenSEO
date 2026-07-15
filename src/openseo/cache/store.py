"""
SQLite-backed cache store.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

from openseo.constants import CACHE_DB, DEFAULT_CACHE_TTL
from openseo.exceptions import CacheError

logger = logging.getLogger(__name__)


class CacheStore:
    """
    SQLite-backed key-value cache with TTL support.

    Thread-safe for single-process use.
    The database is lazily initialized on first use.
    """

    def __init__(self, db_path: Path | None = None, default_ttl: int = DEFAULT_CACHE_TTL) -> None:
        self._db_path = db_path or CACHE_DB
        self._default_ttl = default_ttl
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        """Lazily initialize the SQLite connection."""
        if self._conn is not None:
            return self._conn

        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._initialize_schema()
            logger.debug("Cache DB opened at %s", self._db_path)
        except sqlite3.Error as e:
            raise CacheError(f"Failed to open cache database: {e}") from e

        return self._conn

    def _initialize_schema(self) -> None:
        """Create the cache table if it doesn't exist."""
        conn = self._conn
        assert conn is not None
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
        conn.commit()

    def get(self, key: str) -> Any | None:
        """
        Retrieve a cached value.

        Returns None if not found or expired.
        """
        try:
            conn = self._get_conn()
            now = time.time()
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()

            if row is None:
                return None

            if row["expires_at"] < now:
                self.delete(key)
                return None

            return json.loads(row["value"])
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.warning("Cache get failed for key '%s': %s", key, e)
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: JSON-serializable value
            ttl: Time-to-live in seconds (uses default_ttl if None)
        """
        try:
            conn = self._get_conn()
            now = time.time()
            effective_ttl = ttl if ttl is not None else self._default_ttl
            expires_at = now + effective_ttl
            serialized = json.dumps(value, default=str)
            conn.execute(
                """
                INSERT INTO cache (key, value, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    expires_at = excluded.expires_at,
                    created_at = excluded.created_at
                """,
                (key, serialized, expires_at, now),
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.warning("Cache set failed for key '%s': %s", key, e)

    def delete(self, key: str) -> None:
        """Remove a specific key from the cache."""
        try:
            conn = self._get_conn()
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
        except sqlite3.Error as e:
            logger.warning("Cache delete failed for key '%s': %s", key, e)

    def clear(self) -> int:
        """Remove all entries. Returns the number deleted."""
        try:
            conn = self._get_conn()
            cursor = conn.execute("DELETE FROM cache")
            conn.commit()
            count = cursor.rowcount
            logger.info("Cache cleared: %d entries removed", count)
            return count
        except sqlite3.Error as e:
            raise CacheError(f"Cache clear failed: {e}") from e

    def purge_expired(self) -> int:
        """Remove expired entries. Returns count of purged entries."""
        try:
            conn = self._get_conn()
            cursor = conn.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
            conn.commit()
            count = cursor.rowcount
            logger.debug("Purged %d expired cache entries", count)
            return count
        except sqlite3.Error as e:
            logger.warning("Cache purge failed: %s", e)
            return 0

    def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        try:
            conn = self._get_conn()
            now = time.time()
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE expires_at >= ?", (now,)
            ).fetchone()[0]
            return {"total": total, "active": active, "expired": total - active}
        except sqlite3.Error:
            return {"total": 0, "active": 0, "expired": 0}

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


__all__ = ["CacheStore"]
