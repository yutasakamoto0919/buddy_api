from flask import Flask, request, jsonify
import requests
import os
import sqlite3

app = Flask(__name__)
DB_FILE = "chat_history.db"
# usersがありますが使いません！！！！！！

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


init_db()

@app.route("/create-chat", methods=["POST"])
def create_chat():
    #本来ならここでユーザーを取得しますがusersは仮なので使いません。
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chats (user_id, title) VALUES (?, ?)",
        (1, "無題のチャット")
    )
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": chat_id, "title": "無題のチャット"})

@app.route("/rename-chat", methods=["POST"])
def rename_chat():
    chat_id = request.json["chat_id"]
    newname = request.json["new_name"]
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE chats
    SET title = ?
    WHERE id = ?
    """, (newname, chat_id))
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()


@app.route("/send", methods=["POST"])
def send():
    message = request.json["message"]
    chat_id = request.json["chat_id"]
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (role, content, chat_id) VALUES (?, ?, ?)",
        ("user", message, chat_id)
    )
    api_key = os.environ["GEMINI_API_KEY"]

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": message}
                ]
            }
        ]
    }

    response = requests.post(url, json=payload)
    
    try:
        response_data = response.json()
        ai_response_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        cursor.execute(
            "INSERT INTO history (role, content, chat_id) VALUES (?, ?, ?)",
            ("assistant", ai_response_text, chat_id)
        )
        conn.commit()
        conn.close()
        return ai_response_text
    except (KeyError, IndexError):
        return "エラーが発生しました", 500


@app.route("/history", methods=["GET"])
def history():
    chat_id = request.args.get("chat_id")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, role, content
        FROM history
        WHERE chat_id = ?
        ORDER BY id ASC
        """,
        (chat_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    history = [
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
        }
        for row in rows
    ]

    return jsonify(history)

@app.route("/chats", methods=["GET"])
def chats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, title
        FROM chats
        ORDER BY id ASC
        """,
    )
    rows = cursor.fetchall()
    conn.close()

    chats = [
        {
            "id": row[0],
            "user_id": row[1],
            "title": row[2],
        }
        for row in rows
    ]

    return jsonify(chats)