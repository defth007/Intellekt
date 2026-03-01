import math
import os
import time

import cv2
import serial
from cs50 import SQL
from ultralytics import YOLO


SerialObj = serial.Serial("COM3", baudrate=9600, bytesize=8, parity="N", stopbits=1, timeout=0.1)
time.sleep(2)
SerialObj.reset_input_buffer()
SerialObj.reset_output_buffer()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "project.db")
MODEL_PATH = os.path.join(BASE_DIR, "yolo-Weights", "yolov8n.pt")

db = SQL(f"sqlite:///{DB_PATH}")

DEFAULT_MESSAGES = {
    "cell phone": "Put your phone away and focus.",
    "food": "Finish your task before eating.",
    "bed": "Stay awake and keep working.",
    "wine glass": "Save it for later.",
    "tablewear": "Put the tablewear aside for now.",
}


FOOD_CLASSES = {
    "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
    "hot dog", "pizza", "donut", "cake", "bowl",
}


def normalize_item_name(name):
    key = (name or "").strip().lower()
    aliases = {
        "phone": "cell phone",
        "cellphone": "cell phone",
        "tableware": "tablewear",
        "diningtable": "tablewear",
    }
    return aliases.get(key, key)


def detection_to_item_key(class_name):
    key = normalize_item_name(class_name)
    if key in FOOD_CLASSES:
        return "food"
    return key


def load_message_map():
    message_map = dict(DEFAULT_MESSAGES)
    rows = db.execute("SELECT name, message FROM objects ORDER BY id ASC")
    for row in rows:
        key = normalize_item_name(row["name"])
        if key:
            message_map[key] = row["message"]
    return message_map


# start webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# model
model = YOLO(MODEL_PATH)

# object classes
classNames = [
    "person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
    "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
    "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
    "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
    "teddy bear", "hair drier", "toothbrush",
]


message_map = load_message_map()
last_db_refresh = time.monotonic()
last_lcd_message = None
last_alert_state = None
active_item = None
last_resend = 0.0
RESEND_SECONDS = 1.0

try:
    while True:
        success, img = cap.read()
        if not success:
            continue

        now = time.monotonic()
        if now - last_db_refresh >= 2:
            message_map = load_message_map()
            last_db_refresh = now

        results = model(img, stream=True)

        detected_items = {}

        for r in results:
            for box in r.boxes:
                # bounding box
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                confidence = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = classNames[cls]

                print("Confidence --->", math.ceil(confidence * 100) / 100)
                print("Class name -->", class_name)

                cv2.putText(
                    img,
                    class_name,
                    (x1, y1),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 0, 0),
                    2,
                )

                key = detection_to_item_key(class_name)
                if key in message_map:
                    previous = detected_items.get(key, 0.0)
                    if confidence > previous:
                        detected_items[key] = confidence

        # Keep showing the same item's message as long as that item remains in frame.
        if active_item and active_item in detected_items:
            selected_item = active_item
        elif detected_items:
            selected_item = max(detected_items, key=detected_items.get)
        else:
            selected_item = None

        best_message = message_map.get(selected_item) if selected_item else None
        active_item = selected_item

        alert_state = active_item is not None
        if alert_state != last_alert_state:
            if alert_state:
                SerialObj.write(b"A\n")
            else:
                SerialObj.write(b"B\n")
            last_alert_state = alert_state

        if best_message != last_lcd_message:
            if best_message:
                payload = f"MSG:{best_message}\n".encode("utf-8")
                SerialObj.write(payload)
            else:
                SerialObj.write(b"CLR\n")
            last_lcd_message = best_message
            last_resend = now
        elif best_message and (now - last_resend) >= RESEND_SECONDS:
            payload = f"MSG:{best_message}\n".encode("utf-8")
            SerialObj.write(payload)
            last_resend = now

        cv2.imshow("Webcam", img)
        if cv2.waitKey(1) == ord("q"):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    SerialObj.close()
