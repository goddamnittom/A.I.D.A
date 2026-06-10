"""
Simple but robust memory system for Termux Agentic AI.
Uses SQLite for goals, reflections, logs, and key-value store.
No heavy vector database for starter version (easy on storage/battery).
"""

import sqlite3
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path.home() / "termux-agentic-ai" / "data" / "memory.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class Memory:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        
        # Goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                priority INTEGER DEFAULT 3,
                status TEXT DEFAULT 'active',  -- active, completed, paused, failed
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                metadata TEXT  -- JSON for extra data
            )
        """)
        
        # Reflections / self-improvement notes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle INTEGER,
                summary TEXT,
                insights TEXT,           -- JSON array of insights
                suggested_improvements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Action / tool call log (for debugging and reflection)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                thought TEXT,
                action TEXT,
                args TEXT,               -- JSON
                result TEXT,
                success BOOLEAN,
                cycle INTEGER
            )
        """)
        
        # Simple key-value store for config/state
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()

    # ==================== Goals ====================
    def create_goal(self, description: str, priority: int = 3, metadata: dict = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO goals (description, priority, metadata)
            VALUES (?, ?, ?)
        """)
        self.conn.commit()
        return cursor.lastrowid

    def get_active_goals(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM goals 
            WHERE status = 'active' 
            ORDER BY priority ASC, created_at ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def update_goal(self, goal_id: int, **kwargs):
        allowed = {'description', 'priority', 'status', 'metadata'}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        
        if 'status' in updates and updates['status'] == 'completed':
            updates['completed_at'] = datetime.datetime.now().isoformat()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates])
        values = list(updates.values()) + [goal_id]
        
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE goals SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
        self.conn.commit()

    def complete_goal(self, goal_id: int):
        self.update_goal(goal_id, status='completed')

    # ==================== Logging & Reflection ====================
    def log_action(self, thought: str, action: str, args: dict, result: str, success: bool, cycle: int = 0):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO action_log (thought, action, args, result, success, cycle)
            VALUES (?, ?, ?, ?, ?, ?)
        """)
        self.conn.commit()

    def add_reflection(self, cycle: int, summary: str, insights: list, suggested_improvements: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reflections (cycle, summary, insights, suggested_improvements)
            VALUES (?, ?, ?, ?)
        """)
        self.conn.commit()

    def get_recent_reflections(self, limit: int = 5) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM reflections ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_recent_actions(self, limit: int = 20) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM action_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # ==================== KV Store ====================
    def set_value(self, key: str, value: Any):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO kv_store (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """)
        self.conn.commit()

    def get_value(self, key: str, default: Any = None) -> Any:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM kv_store WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row['value'])
            except:
                return row['value']
        return default

    def close(self):
        self.conn.close()