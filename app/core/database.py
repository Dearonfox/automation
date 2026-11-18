import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class AnalysisRecord:
    analysis_id: str
    created_at: str
    sample_index: int | None
    anomalous: bool
    status: str
    result: dict[str, object]


class AnalysisRepository:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    analysis_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    sample_index INTEGER,
                    anomalous INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS actions (
                    action_id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    note TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (analysis_id)
                );
                """
            )

    def create(
        self, result: dict[str, object], *, sample_index: int | None, anomalous: bool
    ) -> AnalysisRecord:
        record = AnalysisRecord(
            analysis_id=str(uuid4()),
            created_at=datetime.now(UTC).isoformat(),
            sample_index=sample_index,
            anomalous=anomalous,
            status="review_required",
            result=result,
        )
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO analyses VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.analysis_id,
                    record.created_at,
                    record.sample_index,
                    int(record.anomalous),
                    record.status,
                    json.dumps(record.result, ensure_ascii=False),
                ),
            )
        return record

    def get(self, analysis_id: str) -> AnalysisRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM analyses WHERE analysis_id = ?", (analysis_id,)
            ).fetchone()
        if row is None:
            return None
        return AnalysisRecord(
            analysis_id=row["analysis_id"],
            created_at=row["created_at"],
            sample_index=row["sample_index"],
            anomalous=bool(row["anomalous"]),
            status=row["status"],
            result=json.loads(row["result_json"]),
        )

    def add_action(self, analysis_id: str, *, actor: str, action: str, note: str) -> AnalysisRecord:
        record = self.get(analysis_id)
        if record is None:
            raise KeyError(analysis_id)
        allowed = {
            "review_required": {"acknowledged", "rejected"},
            "acknowledged": {"report_prepared", "rejected"},
            "report_prepared": {"confirmed", "rejected"},
            "confirmed": set(),
            "rejected": set(),
        }
        if action not in allowed[record.status]:
            raise ValueError(f"Invalid transition: {record.status} -> {action}")
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO actions VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid4()), analysis_id, now, actor, action, note),
            )
            connection.execute(
                "UPDATE analyses SET status = ? WHERE analysis_id = ?", (action, analysis_id)
            )
        updated = self.get(analysis_id)
        if updated is None:
            raise RuntimeError("Analysis disappeared after action update")
        return updated

    def list_actions(self, analysis_id: str) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT created_at, actor, action, note FROM actions "
                "WHERE analysis_id = ? ORDER BY created_at",
                (analysis_id,),
            ).fetchall()
        return [dict(row) for row in rows]
