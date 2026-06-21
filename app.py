from flask import Flask, request
import requests
import os
import sqlite3

app = Flask(__name__)
DB_FILE = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route("/chat", methods=["POST"])
def chat():
    message = request.json["message"]
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (role, content) VALUES (?, ?)",
        ("user", message)
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
            "INSERT INTO history (role, content) VALUES (?, ?)",
            ("user", ai_response_text)
        )
        conn.commit()
        conn.close()
        return ai_response_text
    except (KeyError, IndexError):
        return "エラーが発生しました", 500


@app.route("/history", methods=["GET"])
def send():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM history")

    rows = cursor.fetchall()
    conn.close()
    return(rows)