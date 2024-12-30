import eventlet
eventlet.monkey_patch()

import time
from io import BytesIO
from PIL import Image
import threading
import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebSocketLogger")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

IMAGES = {
    "front_left": "front_left.jpg",
    "front_right": "front_right.jpg",
    "bottom": "bottom.jpg",
}

current_camera = {"name": "front_left", "lock": threading.Lock()}


def send_video():
    try:
        while True:
            with current_camera["lock"]:
                camera_name = current_camera["name"]
                with Image.open(IMAGES[camera_name]) as image:
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format="JPEG")
                    img_byte_arr.seek(0)
                    socketio.emit(
                        "camera_frame",
                        {"camera_name": camera_name, "frame": img_byte_arr.getvalue()}
                    )
            time.sleep(0.1)
    except Exception as e:
        logger.error(f"Error in camera thread: {e}")


def start_camera_stream():
    logger.info("Starting camera stream thread")
    stream_thread = threading.Thread(target=send_video, daemon=True)
    stream_thread.start()


def telemetry_broadcast():
    while True:
        telemetry_data = {
            "height": 3.5,
            "speed": 1.0,
            "battery": 98,
            "coordinates": {"lat": 50.450079, "lon": 30.4533602},
            "motorsHealth": {"LF": True, "RF": True, "LR": False, "RR": True},
            "sensorsState": {"humidity": 70.1, "brightness": 59.8, "unitsCount": 1},
        }
        socketio.emit("telemetry_data", telemetry_data)
        time.sleep(1)


@socketio.on("connect")
def handle_connect():
    client_ip = request.remote_addr
    logger.info(f"Client connected from IP: {client_ip}")
    emit("connection_status", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    client_ip = request.remote_addr
    logger.info(f"Client disconnected from IP: {client_ip}")


@socketio.on("start_camera")
def handle_start_camera(data):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            emit("camera_status", {"status": "error", "message": "Invalid JSON"})
            logger.error("Received invalid JSON data")
            return

    camera_name = data.get("camera_name")
    logger.info(f"Received 'start_camera' request with data: {data}")
    if camera_name in IMAGES:
        with current_camera["lock"]:
            current_camera["name"] = camera_name
        emit("camera_status", {"camera_name": camera_name, "status": "streaming"})
    else:
        emit("camera_status", {"camera_name": camera_name, "status": "error", "message": "Invalid camera name"})
        logger.warning(f"Invalid camera name: {camera_name}")


@socketio.on("set_task")
def handle_set_task(data):
    logger.info(f"Received 'set_task' request with data: {data}")
    emit("status", {"result": "ok"})


@socketio.on("run_command")
def handle_run_command(data):
    logger.info(f"Received 'run_command' request with data: {data}")
    emit("command_status", {"result": "ok"})


@socketio.on("actuator_command")
def handle_actuator_command(data):
    if isinstance(data, str):
        logger.warning("Received string data, attempting to parse as JSON")
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            emit("actuator_status", {"status": "error", "message": "Invalid JSON format"})
            logger.error("Received invalid JSON data for actuator command")
            return

    actuator_id = data.get("actuator")
    if isinstance(actuator_id, int):
        logger.info(f"Received actuator command: Actuator ID = {actuator_id}")
        emit("actuator_status", {"actuator": actuator_id, "status": "command_received"})
    else:
        emit("actuator_status", {"status": "error", "message": "Invalid actuator ID"})
        logger.warning(f"Invalid actuator ID received: {actuator_id}")


if __name__ == "__main__":
    # Start the camera stream
    start_camera_stream()

    # Start telemetry broadcast
    threading.Thread(target=telemetry_broadcast, daemon=True).start()
    host = "0.0.0.0"
    port = 5000
    logger.info(f"Starting WebSocket server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)
