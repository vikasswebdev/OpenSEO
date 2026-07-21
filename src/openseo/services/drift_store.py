"""
SQLite service to store and manage SEO drift baselines and comparisons.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from openseo.constants import CONFIG_DIR

DRIFT_DIR = CONFIG_DIR / "drift"
DRIFT_DB = DRIFT_DIR / "drift.db"

UTM_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


def normalize_url(url: str) -> str:
    """
    Normalize a URL for consistent baseline matching.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()

    port = parsed.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None

    netloc = hostname
    if port:
        netloc = f"{hostname}:{port}"

    query_params = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in sorted(query_params.items()) if k not in UTM_PARAMS}
    query = urlencode(filtered, doseq=True)

    path = parsed.path.rstrip("/") or "/"

    return urlunparse((scheme, netloc, path, "", query, ""))


def url_hash(url: str) -> str:
    """SHA-256 hash of normalized URL, truncated to 16 hex chars."""
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


class DriftStore:
    """
    SQLite-backed repository for SEO baselines and comparisons.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DRIFT_DB
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._initialize_schema()
        return self._conn

    def _initialize_schema(self) -> None:
        conn = self._conn
        assert conn is not None
        conn.execute("""
            CREATE TABLE IF NOT EXISTS baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                url_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                title TEXT,
                meta_description TEXT,
                canonical TEXT,
                robots TEXT,
                h1 TEXT,
                h2_json TEXT,
                h3_json TEXT,
                schema_json TEXT,
                og_json TEXT,
                cwv_json TEXT,
                html_hash TEXT,
                schema_hash TEXT,
                status_code INTEGER
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_url_hash ON baselines(url_hash)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                url_hash TEXT NOT NULL,
                baseline_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                results_json TEXT NOT NULL,
                critical_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                info_count INTEGER DEFAULT 0,
                FOREIGN KEY (baseline_id) REFERENCES baselines(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_comp_url_hash ON comparisons(url_hash)
        """)
        conn.commit()

    def save_baseline(self, baseline_data: dict) -> int:
        """
        Save a new baseline entry and return its ID.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            INSERT INTO baselines (
                url, url_hash, timestamp, title, meta_description, canonical,
                robots, h1, h2_json, h3_json, schema_json, og_json, cwv_json,
                html_hash, schema_hash, status_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                baseline_data["url"],
                baseline_data["url_hash"],
                baseline_data["timestamp"],
                baseline_data["title"],
                baseline_data["meta_description"],
                baseline_data["canonical"],
                baseline_data["robots"],
                baseline_data["h1"],
                baseline_data["h2_json"],
                baseline_data["h3_json"],
                baseline_data["schema_json"],
                baseline_data["og_json"],
                baseline_data["cwv_json"],
                baseline_data["html_hash"],
                baseline_data["schema_hash"],
                baseline_data["status_code"],
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def load_baseline(self, url: str, baseline_id: int | None = None) -> dict | None:
        """
        Load the most recent baseline or a specific baseline by ID.
        """
        conn = self._get_conn()
        uhash = url_hash(url)
        if baseline_id is not None:
            row = conn.execute(
                "SELECT * FROM baselines WHERE id = ? AND url_hash = ?",
                (baseline_id, uhash),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM baselines WHERE url_hash = ? ORDER BY id DESC LIMIT 1",
                (uhash,),
            ).fetchone()

        if not row:
            return None
        return dict(row)

    def save_comparison(self, comparison_data: dict, baseline_id: int) -> int:
        """
        Save a new comparison record.
        """
        conn = self._get_conn()
        url = comparison_data["url"]
        uhash = url_hash(url)
        now = datetime.now(timezone.utc).isoformat()
        summary = comparison_data.get("summary", {})
        critical_count = summary.get("critical", 0)
        warning_count = summary.get("warning", 0)
        info_count = summary.get("info", 0)

        cursor = conn.execute(
            """
            INSERT INTO comparisons (
                url, url_hash, baseline_id, timestamp, results_json,
                critical_count, warning_count, info_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalize_url(url),
                uhash,
                baseline_id,
                now,
                json.dumps(comparison_data),
                critical_count,
                warning_count,
                info_count,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_history(self, url: str, limit: int = 20) -> dict:
        """
        Retrieve history of baselines and comparisons for a URL.
        """
        conn = self._get_conn()
        norm_url = normalize_url(url)
        uhash = url_hash(url)

        rows = conn.execute(
            """
            SELECT id, url, timestamp, title, canonical, robots, h1,
                   status_code, html_hash, schema_hash,
                   CASE WHEN cwv_json IS NOT NULL THEN 1 ELSE 0 END as has_cwv
            FROM baselines
            WHERE url_hash = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (uhash, limit),
        ).fetchall()

        baselines = []
        for row in rows:
            baselines.append({
                "id": row["id"],
                "url": row["url"],
                "timestamp": row["timestamp"],
                "title": row["title"],
                "canonical": row["canonical"],
                "robots": row["robots"],
                "h1": row["h1"],
                "status_code": row["status_code"],
                "html_hash": row["html_hash"][:12] + "..." if row["html_hash"] else None,
                "schema_hash": row["schema_hash"][:12] + "..." if row["schema_hash"] else None,
                "has_cwv": bool(row["has_cwv"]),
            })

        comp_rows = conn.execute(
            """
            SELECT id, baseline_id, timestamp, critical_count, warning_count, info_count
            FROM comparisons
            WHERE url_hash = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (uhash, limit),
        ).fetchall()

        comparisons = []
        for row in comp_rows:
            comparisons.append({
                "id": row["id"],
                "baseline_id": row["baseline_id"],
                "timestamp": row["timestamp"],
                "critical": row["critical_count"],
                "warning": row["warning_count"],
                "info": row["info_count"],
            })

        return {
            "url": norm_url,
            "baselines": baselines,
            "comparisons": comparisons,
        }

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
