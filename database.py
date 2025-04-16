import sqlite3
import hashlib

DB_NAME = "users.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

def create_user_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK (role IN ('admin', 'user'))
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, role):
    try:
        conn = get_conn()
        cur = conn.cursor()
        hashed_pw = hash_password(password)
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, hashed_pw, role))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        pass

def authenticate_user(username, password):
    conn = get_conn()
    cur = conn.cursor()
    hashed_pw = hash_password(password)
    cur.execute("SELECT role FROM users WHERE username=? AND password=?", (username, hashed_pw))
    data = cur.fetchone()
    conn.close()
    return data

def init_dummy_users():
    add_user("admin", "admin123", "admin")
    add_user("user01", "user01123", "user")
