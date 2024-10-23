# models/user.py
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

def create_user_table():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        date_of_birth DATE NOT NULL,
        height REAL NOT NULL,
        weight REAL NOT NULL
    )''')
    conn.commit()
    conn.close()

# Kullanıcıyı veri tabanından alma
def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

# Kullanıcıyı veritabanına kaydetme
def add_user(first_name, last_name, username, password, date_of_birth, height, weight):
    conn = get_db_connection()
    conn.execute('INSERT INTO users (first_name, last_name, username, password, date_of_birth, height, weight) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (first_name, last_name, username, password, date_of_birth, height, weight))
    conn.commit()
    conn.close()
