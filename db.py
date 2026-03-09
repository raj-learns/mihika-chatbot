import sqlite3

conn = sqlite3.connect("mihika.db", check_same_thread=False)
cursor = conn.cursor()
conn.row_factory = sqlite3.Row

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT,
    role TEXT,
    content TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

def save_message(thread_id, role, content):
    cursor.execute(
        "INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)",
        (thread_id, role, content)
    )
    conn.commit()
    
def get_last_messages(thread_id, limit=20):
    cursor.execute(
        """
        SELECT role, content FROM messages
        WHERE thread_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (thread_id, limit)
    )

    rows = cursor.fetchall()

    rows.reverse()

    return [{"role": r[0], "content": r[1]} for r in rows]

def get_full_history(thread_id):

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE thread_id = ?
        ORDER BY id
        """,
        (thread_id,)
    )

    rows = cursor.fetchall()

    return [
        {"role": r[0], "content": r[1]}
        for r in rows
    ]