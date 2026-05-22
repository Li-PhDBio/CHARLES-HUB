"""SQLite + FTS5 storage for messages, agent state, and meeting records."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone


class Storage:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                msg_id TEXT UNIQUE NOT NULL,
                chat_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                mentioned_bots TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_state (
                agent_name TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'offline',
                last_seen TEXT,
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_type TEXT NOT NULL,
                topic TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                started_at TEXT NOT NULL,
                closed_at TEXT,
                summary TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
                USING fts5(content, sender, msg_id UNINDEXED,
                           tokenize='unicode61');
            CREATE TRIGGER IF NOT EXISTS messages_ai
                AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(content, sender, msg_id)
                VALUES (new.content, new.sender, new.msg_id);
            END;
        """)
        self.conn.commit()

    def save_message(self, msg_id: str, chat_id: str, sender: str,
                     content: str, mentioned_bots: list[str] | None = None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO messages(msg_id, chat_id, sender, content, mentioned_bots, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, chat_id, sender, content,
             json.dumps(mentioned_bots or []), now),
        )
        self.conn.commit()
        return cur.lastrowid

    def search_messages(self, query: str, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(
            "SELECT m.* FROM messages m "
            "JOIN messages_fts f ON f.msg_id = m.msg_id "
            "WHERE messages_fts MATCH ? ORDER BY rank LIMIT ?",
            (query, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_messages_since(self, since: str, chat_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? AND created_at > ? "
            "ORDER BY created_at ASC",
            (chat_id, since),
        ).fetchall()
        return [dict(r) for r in rows]

    def set_agent_status(self, agent_name: str, status: str, metadata: dict | None = None):
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT OR REPLACE INTO agent_state(agent_name, status, last_seen, metadata) "
            "VALUES (?, ?, ?, ?)",
            (agent_name, status, now, json.dumps(metadata or {})),
        )
        self.conn.commit()

    def get_all_agent_statuses(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM agent_state").fetchall()
        return [dict(r) for r in rows]

    def create_meeting(self, meeting_type: str, topic: str | None = None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            "INSERT INTO meetings(meeting_type, topic, status, started_at) "
            "VALUES (?, ?, 'open', ?)",
            (meeting_type, topic, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def close_meeting(self, meeting_id: int, summary: str):
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE meetings SET status='closed', closed_at=?, summary=? WHERE id=?",
            (now, summary, meeting_id),
        )
        self.conn.commit()

    def get_pending_messages_for_agent(self, agent_name: str, since: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE created_at > ? "
            "AND mentioned_bots LIKE ? "
            "ORDER BY created_at ASC",
            (since, f'%"{agent_name}"%'),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self.conn.close()
