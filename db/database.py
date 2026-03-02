import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "learning.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(user_id, name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            video_id TEXT NOT NULL,
            title TEXT NOT NULL,
            last_position INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(topic_id, video_id),
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()