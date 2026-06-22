import os
import sqlite3

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'chat_history.db'))

def init_db():
    """Initializes the SQLite database and ensures the chat table exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_message(user_id: str, role: str, content: str):
    """Saves a single chat message to the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_messages (user_id, role, content)
        VALUES (?, ?, ?)
    ''', (user_id.strip(), role, content))
    conn.commit()
    conn.close()


def get_messages(user_id: str) -> list[dict[str, str]]:
    """Retrieves all chat messages for a specific user ID in chronological order."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM chat_messages
        WHERE user_id = ?
        ORDER BY id ASC
    ''', (user_id.strip(),))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in rows]


def clear_messages(user_id: str):
    """Clears all stored chat messages for a specific user ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM chat_messages
        WHERE user_id = ?
    ''', (user_id.strip(),))
    conn.commit()
    conn.close()
