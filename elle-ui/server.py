from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

from cs50 import SQL

import os
import threading
import time
import serial

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "project.db")

# configure use of SQLite database
db = SQL(f"sqlite:///{DB_PATH}")


DEFAULT_MESSAGES = {
    "cell phone": "Put your phone away and focus.",
    "food": "Finish your task before eating.",
    "bed": "Stay awake and keep working.",
    "wine glass": "Save it for later.",
    "tablewear": "Put the tablewear aside for now."
}


class ArduinoBridge:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._lock = threading.Lock()

    def _ensure_connected(self):
        if self._serial and self._serial.is_open:
            return
        self._serial = serial.Serial(
            self.port,
            baudrate=self.baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=0.1,
        )
        # Allow Arduino auto-reset to finish.
        time.sleep(2)
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()

    def send_line(self, line):
        with self._lock:
            self._ensure_connected()
            payload = f"{line}\n".encode("utf-8")
            self._serial.write(payload)

    def status(self):
        with self._lock:
            connected = bool(self._serial and self._serial.is_open)
            return {"connected": connected, "port": self.port, "baudrate": self.baudrate}


ARDUINO_PORT = os.getenv("ARDUINO_PORT", "COM3")
ARDUINO_BAUD = int(os.getenv("ARDUINO_BAUD", "9600"))
arduino = ArduinoBridge(ARDUINO_PORT, ARDUINO_BAUD)


def normalize_item_name(name):
    key = (name or "").strip().lower()
    aliases = {
        "phone": "cell phone",
        "cellphone": "cell phone",
        "tableware": "tablewear",
        "diningtable": "tablewear",
    }
    return aliases.get(key, key)


def get_messages():
    merged = dict(DEFAULT_MESSAGES)
    rows = db.execute("SELECT name, message FROM objects ORDER BY id ASC")
    for row in rows:
        merged[normalize_item_name(row["name"])] = row["message"]
    return merged

@app.route("/")
def home():
    return render_template("index.html")


@app.get("/messages")
def messages():
    return jsonify(get_messages())


# Frontend can call this to save an updated message into Python
@app.post("/set_message")
def set_message():
    data = request.get_json(force=True)
    item = normalize_item_name(data.get("item"))
    text = (data.get("text") or "").strip()
    print(item, text)

    if not item or not text:
        return jsonify({"ok": False, "error": "Missing item or text"}), 400

    # optional: keep LCD-friendly length
    if len(text) > 64:
        text = text[:64]

    db.execute("INSERT INTO objects (name, message) VALUES (?, ?)", item, text)

    return jsonify({"ok": True, "item": item, "text": text})


@app.get("/arduino/status")
def arduino_status():
    return jsonify({"ok": True, **arduino.status()})


@app.post("/arduino/display")
def arduino_display():
    data = request.get_json(force=True)
    item = normalize_item_name(data.get("item"))
    text = (data.get("text") or "").strip()

    if not text and item:
        text = get_messages().get(item, "")

    if not text:
        return jsonify({"ok": False, "error": "Missing text or resolvable item"}), 400

    if len(text) > 64:
        text = text[:64]

    try:
        arduino.send_line("A")
        arduino.send_line(f"MSG:{text}")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({"ok": True, "item": item, "text": text})


@app.post("/arduino/clear")
def arduino_clear():
    try:
        arduino.send_line("B")
        arduino.send_line("CLR")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({"ok": True})



if __name__ == "__main__":
    app.run(debug=True)
