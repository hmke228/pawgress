"""SQLite support for one saved profile and immutable, complete dog reports."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path


class ReportStore:
    """Keep Epic 2 records separate from the standalone comparison demo table."""

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS dog_profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS dog_reports (
                    report_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )

    def load_profile(self) -> dict | None:
        """Return the single dog's profile, if collected previously."""
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute("SELECT payload FROM dog_profile WHERE id = 1")
            result = row.fetchone()
        return json.loads(result[0]) if result else None

    def save_profile(self, profile: dict) -> None:
        """Save once; never silently replace the dog associated with this history."""
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "INSERT INTO dog_profile (id, payload) VALUES (1, ?)",
                (json.dumps(profile, ensure_ascii=False),),
            )

    def previous_reports(self, current_id: str = "") -> list[dict]:
        """Read all candidates newest first; Comparison filters before limiting."""
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute(
                "SELECT payload FROM dog_reports WHERE report_id != ? "
                "ORDER BY created_at DESC, report_id DESC",
                (current_id,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def save_report(self, report: dict) -> None:
        """Insert the final report without overwriting any previous report."""
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "INSERT INTO dog_reports (report_id, created_at, payload) "
                "VALUES (?, ?, ?)",
                (
                    report["report_id"],
                    report["created_at"],
                    json.dumps(report, ensure_ascii=False),
                ),
            )
