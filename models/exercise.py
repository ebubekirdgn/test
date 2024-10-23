# models/exercise.py
import sqlite3
from datetime import datetime

def create_exercises_table():
    conn = sqlite3.connect('db.sqlite3')
    conn.execute('''CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        biceps_curl INTEGER NOT NULL DEFAULT 0,
        triceps_extension INTEGER NOT NULL DEFAULT 0,
        lateral_raise INTEGER NOT NULL DEFAULT 0,
        squat INTEGER NOT NULL DEFAULT 0,
        shoulder_press INTEGER NOT NULL DEFAULT 0,
        crunch INTEGER NOT NULL DEFAULT 0,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user) REFERENCES users (username)
    )''')
    conn.commit()
    conn.close()

def add_exercise(user, biceps_curl, triceps_extension, lateral_raise, squat, shoulder_press, crunch):
    conn = sqlite3.connect('db.sqlite3')
    conn.execute('INSERT INTO exercises (user, biceps_curl, triceps_extension, lateral_raise, squat, shoulder_press, crunch, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                 (user, biceps_curl, triceps_extension, lateral_raise, squat, shoulder_press, crunch, datetime.now()))
    conn.commit()
    conn.close()

def get_exercises_by_user(user):
    conn = sqlite3.connect('db.sqlite3')
    exercises = conn.execute('SELECT * FROM exercises WHERE user = ?', (user,)).fetchall()
    conn.close()
    return exercises
