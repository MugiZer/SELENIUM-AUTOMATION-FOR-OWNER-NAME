import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


class Cache:
    """SQLite-backed cache for previously scraped payloads."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.execute("SELECT data FROM cache WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, key: str, data: Dict[str, Any], timestamp: str) -> None:
        payload = json.dumps(data, ensure_ascii=False)
        self._conn.execute(
            "REPLACE INTO cache (key, data, updated_at) VALUES (?, ?, ?)",
            (key, payload, timestamp),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def normalize_key(*parts: str) -> str:
    return "|".join(part.strip().lower() for part in parts if part)
