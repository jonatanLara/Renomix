import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "renomix.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._init_schema()

    def _init_schema(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                old_path TEXT NOT NULL,
                new_path TEXT NOT NULL,
                operation TEXT NOT NULL,   -- 'rename' | 'copy'
                note TEXT,
                timestamp TEXT NOT NULL    -- ISO-8601
            )
            """
        )
        self.conn.commit()

    # ===== escritura =====
    def insert_many(self, rows: List[Dict[str, Any]]):
        now = datetime.now().isoformat(timespec='seconds')
        payload = []
        for r in rows:
            payload.append({
                "batch_id": r["batch_id"],
                "old_path": r["old_path"],
                "new_path": r["new_path"],
                "operation": r["operation"],
                "note": r.get("note", ""),
                "timestamp": r.get("timestamp", now),
            })
        self.conn.executemany(
            """
            INSERT INTO history (batch_id, old_path, new_path, operation, note, timestamp)
            VALUES (:batch_id, :old_path, :new_path, :operation, :note, :timestamp)
            """,
            payload,
        )
        self.conn.commit()

    # ===== lectura utilitaria =====
    def count_rows(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM history")
        return int(cur.fetchone()[0] or 0)

    def get_last_batch_id(self) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT batch_id FROM history ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None

    def get_rows_by_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT batch_id, old_path, new_path, operation, note, timestamp
            FROM history
            WHERE batch_id = ?
            ORDER BY id ASC
            """,
            (batch_id,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    def delete_by_batch(self, batch_id: str) -> int:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM history WHERE batch_id = ?", (batch_id,))
        self.conn.commit()
        return cur.rowcount

    def get_recent_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT batch_id, operation, old_path, new_path, timestamp
            FROM history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    def get_batches_summary(self, limit: int = 50) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                batch_id,
                MIN(timestamp) AS started_at,
                MAX(timestamp) AS ended_at,
                COUNT(*) AS items,
                SUM(CASE WHEN operation='copy' THEN 1 ELSE 0 END) AS copies,
                SUM(CASE WHEN operation='rename' THEN 1 ELSE 0 END) AS renames
            FROM history
            GROUP BY batch_id
            ORDER BY MAX(id) DESC
            LIMIT ?
            """,
            (limit,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    def get_operations_breakdown(self) -> Dict[str, int]:
        cur = self.conn.cursor()
        cur.execute("SELECT operation, COUNT(*) FROM history GROUP BY operation")
        out = {op: cnt for (op, cnt) in cur.fetchall()}
        return {"copy": out.get("copy", 0), "rename": out.get("rename", 0)}

    def get_top_extensions(self, limit: int = 15):
        # Se calcula en Python para evitar hacks SQL con 'último punto'
        cur = self.conn.cursor()
        cur.execute("SELECT old_path, new_path FROM history")
        rows = cur.fetchall()
        counts = {}
        for old_p, new_p in rows:
            p = new_p or old_p
            base = os.path.basename(p)
            _, ext = os.path.splitext(base)
            ext = ext.lower()
            counts[ext] = counts.get(ext, 0) + 1
        # Ordenar y limitar
        items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return [{"extension": k, "count": v} for k, v in items]

    def vacuum(self):
        self.conn.execute("VACUUM")
        self.conn.commit()

    def close(self):
        self.conn.close()
