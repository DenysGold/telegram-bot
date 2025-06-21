import sqlite3
from openpyxl import Workbook

# Создание базы данных, если её ещё нет
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    join_date TEXT
)
''')
conn.commit()

def add_user(user_id, username, first_name, join_date):
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO users (id, username, first_name, join_date) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, join_date))
        conn.commit()
    except Exception as e:
        print(f"Ошибка добавления пользователя: {e}")

def get_all_users():
    cursor.execute("SELECT id FROM users")
    rows = cursor.fetchall()
    return [row[0] for row in rows]

def export_users_to_excel():
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Users"

    ws.append(["ID", "Username", "First Name", "Join Date"])

    for row in rows:
        ws.append(row)

    filename = "users_export.xlsx"
    wb.save(filename)
    return filename
