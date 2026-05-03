"""Lightweight SQLite memory for past research topics (Milestone C)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DB_PATH = Path.home() / ".shadow_writer" / "memory.sqlite3"


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            artifact_path TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    conn.commit()


def record_run(topic: str, artifact_path: str) -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    try:
        _ensure_schema(conn)
        conn.execute(
            "INSERT INTO runs (topic, artifact_path, created_at) VALUES (?, ?, ?)",
            (
                topic,
                artifact_path,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def recent_topics(limit: int = 20) -> list[tuple[str, str, str]]:
    if not _DB_PATH.is_file():
        return []
    conn = sqlite3.connect(_DB_PATH)
    try:
        _ensure_schema(conn)
        cur = conn.execute(
            "SELECT topic, artifact_path, created_at FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return list(cur.fetchall())
    finally:
        conn.close()
