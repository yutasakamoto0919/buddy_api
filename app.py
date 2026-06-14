from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():

    message = request.json["message"]

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

    return jsonify(response.json())