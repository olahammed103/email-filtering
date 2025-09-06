import sqlite3, os
def get_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        label TEXT NOT NULL CHECK(label IN ('spam','ham'))
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        api_url TEXT,
        api_token TEXT
    )''')
    cur.execute('SELECT COUNT(*) FROM admin')
    if cur.fetchone()[0]==0:
        cur.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)', ('admin', 'admin123'))
    conn.commit()
    conn.close()
