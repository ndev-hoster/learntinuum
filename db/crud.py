import sqlite3
from db.database import get_connection


def create_topic(user_id: int, name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO topics (user_id, name) VALUES (?, ?)",
            (user_id, name.strip()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_topics(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name FROM topics WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_topic_by_id(topic_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM topics WHERE id = ?", (topic_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_video_by_video_id(video_id: str):
    """Look up by YouTube video_id. Returns row with topic_name joined."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT v.*, t.name as topic_name
        FROM videos v
        JOIN topics t ON v.topic_id = t.id
        WHERE v.video_id = ?
        """,
        (video_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_video_by_db_id(db_id: int):
    """Look up by internal DB id. Returns row with topic_name joined."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT v.*, t.name as topic_name
        FROM videos v
        JOIN topics t ON v.topic_id = t.id
        WHERE v.id = ?
        """,
        (db_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def add_video(topic_id: int, video_id: str, title: str, position: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO videos (topic_id, video_id, title, last_position)
            VALUES (?, ?, ?, ?)
            """,
            (topic_id, video_id, title, position),
        )
        conn.commit()
    finally:
        conn.close()


def update_video_position(db_id: int, position: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE videos
        SET last_position = ?, status = 'active', last_accessed = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (position, db_id),
    )
    conn.commit()
    conn.close()


def get_active_videos(topic_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM videos
        WHERE topic_id = ? AND status = 'active'
        ORDER BY last_accessed DESC
        """,
        (topic_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_latest_active_video(user_id: int):
    """Most recently accessed active video across all topics for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT v.*, t.name as topic_name
        FROM videos v
        JOIN topics t ON v.topic_id = t.id
        WHERE t.user_id = ? AND v.status = 'active'
        ORDER BY v.last_accessed DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def mark_video_completed(db_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE videos SET status = 'completed' WHERE id = ?",
        (db_id,),
    )
    conn.commit()
    conn.close()


def delete_video(db_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()

def get_setting(key: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else None

def set_setting(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()