import sqlite3
from werkzeug.security import generate_password_hash

def add_user(username, password):
    conn = sqlite3.connect("data.db")
    hashed_password = generate_password_hash(password)
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print(f"User {username} added successfully.")
    except sqlite3.IntegrityError:
        print(f"User {username} already exists.")
    finally:
        conn.close()

add_user('admin3', 'allo')
add_user('user3', 'azer')
