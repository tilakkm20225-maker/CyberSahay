import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "cybersahay.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_type TEXT NOT NULL,
            category TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

def save_analysis(input_type: str, category: str, risk_score: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO analyses (input_type, category, risk_score) VALUES (?, ?, ?)",
            (input_type, category, risk_score)
        )

def recent_analyses(limit: int = 20):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, input_type, category, risk_score, created_at FROM analyses ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(id=r[0], input_type=r[1], category=r[2], risk_score=r[3], created_at=r[4]) for r in rows]
