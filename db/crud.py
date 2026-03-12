import sqlite3
from db.database import get_connection


# ========================
# TOPICS
# ========================

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


# ========================
# VIDEOS
# ========================

def get_video_by_video_id(video_id: str):
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


# ========================
# PLAYLISTS
# ========================

def get_playlist_by_playlist_id(playlist_id: str):
    """Look up a tracked playlist by its YouTube playlist_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.*, t.name as topic_name
        FROM playlists p
        JOIN topics t ON p.topic_id = t.id
        WHERE p.playlist_id = ?
        """,
        (playlist_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_playlist_by_db_id(db_id: int):
    """Look up a tracked playlist by its internal DB id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.*, t.name as topic_name
        FROM playlists p
        JOIN topics t ON p.topic_id = t.id
        WHERE p.id = ?
        """,
        (db_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def add_playlist(
    topic_id: int,
    playlist_id: str,
    title: str,
    channel: str,
    total_videos: int,
    current_video_id: str,
    current_index: int,
    current_position: int,
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO playlists (
                topic_id, playlist_id, title, channel,
                total_videos, current_video_id, current_index, current_position
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic_id, playlist_id, title, channel,
                total_videos, current_video_id, current_index, current_position,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def update_playlist_position(db_id: int, video_id: str, index: int, position: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE playlists
        SET current_video_id = ?,
            current_index = ?,
            current_position = ?,
            status = 'active',
            last_accessed = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (video_id, index, position, db_id),
    )
    conn.commit()
    conn.close()


def get_active_playlists(topic_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM playlists
        WHERE topic_id = ? AND status = 'active'
        ORDER BY last_accessed DESC
        """,
        (topic_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_latest_active_playlist(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.*, t.name as topic_name
        FROM playlists p
        JOIN topics t ON p.topic_id = t.id
        WHERE t.user_id = ? AND p.status = 'active'
        ORDER BY p.last_accessed DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def mark_playlist_completed(db_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE playlists SET status = 'completed' WHERE id = ?",
        (db_id,),
    )
    conn.commit()
    conn.close()


def delete_playlist(db_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    # Also clean up playlist_videos for this playlist
    cursor.execute(
        "SELECT playlist_id FROM playlists WHERE id = ?", (db_id,)
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "DELETE FROM playlist_videos WHERE playlist_id = ?",
            (row["playlist_id"],),
        )
    cursor.execute("DELETE FROM playlists WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()


# ========================
# PLAYLIST VIDEOS
# ========================

def add_playlist_videos(playlist_id: str, videos: list):
    """
    videos: list of dicts with keys: video_id, title, index_in_playlist
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(
            """
            INSERT OR IGNORE INTO playlist_videos (playlist_id, video_id, title, index_in_playlist)
            VALUES (?, ?, ?, ?)
            """,
            [(playlist_id, v["video_id"], v["title"], v["index_in_playlist"]) for v in videos],
        )
        conn.commit()
    finally:
        conn.close()


def find_video_in_playlists(video_id: str):
    """
    Check if a video_id exists in any tracked playlist.
    Returns the playlist row (with topic_name) if found, else None.
    Used for Android reverse lookup.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.*, t.name as topic_name, pv.index_in_playlist
        FROM playlist_videos pv
        JOIN playlists p ON pv.playlist_id = p.playlist_id
        JOIN topics t ON p.topic_id = t.id
        WHERE pv.video_id = ?
        AND p.status = 'active'
        LIMIT 1
        """,
        (video_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_playlist_video_index(playlist_id: str, video_id: str) -> int:
    """Get the index of a video within a playlist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT index_in_playlist FROM playlist_videos
        WHERE playlist_id = ? AND video_id = ?
        """,
        (playlist_id, video_id),
    )
    row = cursor.fetchone()
    conn.close()
    return row["index_in_playlist"] if row else 0


# ========================
# SETTINGS
# ========================

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
    cursor.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )
    conn.commit()
    conn.close()

def delete_topic(topic_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    conn.commit()
    conn.close()