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

current_camera = {"name": "front_left", "thread": None, "lock": threading.Lock()}


def send_video(camera_name):
    try:
        with Image.open(IMAGES[camera_name]) as image:
            logger.info(f"Loaded image for camera: {camera_name}, size: {image.size}")
            while True:
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format="JPEG")
                img_byte_arr.seek(0)
                socketio.emit(
                    "camera_frame",
                    {"camera_name": camera_name, "frame": img_byte_arr.getvalue()},
                    to=None,  # Send to all clients
                )
                logger.info(f"Emitting frame for {camera_name}")
                time.sleep(0.1)
    except Exception as e:
        logger.error(f"Error in camera thread for {camera_name}: {e}")


def start_camera_stream(camera_name):
    with current_camera["lock"]:
        if current_camera["thread"] and current_camera["thread"].is_alive():
            logger.info(f"Stopping current camera: {current_camera['name']}")
            current_camera["thread"].do_run = False  # Signal to stop the thread
            current_camera["thread"].join()

        logger.info(f"Starting new stream for camera: {camera_name}")
        new_thread = threading.Thread(target=send_video, args=(camera_name,), daemon=True)
        new_thread.start()
        current_camera.update({"name": camera_name, "thread": new_thread})


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
        logger.info("Broadcasted telemetry data")
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
        start_camera_stream(camera_name)
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


if __name__ == "__main__":
    # Start the default camera
    start_camera_stream("front_left")

    # Start telemetry broadcast
    threading.Thread(target=telemetry_broadcast, daemon=True).start()
    host = "0.0.0.0"
    port = 5000
    logger.info(f"Starting WebSocket server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)
