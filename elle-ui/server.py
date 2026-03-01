from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

from cs50 import SQL

import os

# configure use of SQLite database
db = SQL("sqlite:///project.db")


# In-memory store (resets if server restarts)
messages = {
    "cell phone": "Put your phone away and focus.",
    "food": "Finish your task before eating.",
    "bed": "Stay awake and keep working.",
    "wine glass": "Save it for later.",
    "tablewear": "Put the tablewear aside for now."
}

@app.route("/")
def home():
    return render_template("index.html")

# Frontend can call this to save an updated message into Python
@app.post("/set_message")
def set_message():
    data = request.get_json(force=True)
    item = (data.get("item") or "").strip()
    text = (data.get("text") or "").strip()
    print(item, text)

    if not item or not text:
        return jsonify({"ok": False, "error": "Missing item or text"}), 400

    # optional: keep LCD-friendly length
    if len(text) > 64:
        text = text[:64]

    messages[item] = text

    db.execute("INSERT INTO objects (name, message) VALUES (?, ?)", item, text)

    return jsonify({"ok": True, "item": item, "text": text})



if __name__ == "__main__":
    app.run(debug=True)