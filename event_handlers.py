import json
from flask import request
import logging
from camera import current_camera, IMAGES
from telemetry import telemetry

logger = logging.getLogger("EventHandlers")


def register_event_handlers(socketio):
    @socketio.on("connect")
    def handle_connect():
        client_ip = request.remote_addr
        logger.info(f"Client connected from IP: {client_ip}")
        socketio.emit("connection_status", {"status": "connected"})

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
                socketio.emit("camera_status", {"status": "error", "message": "Invalid JSON"})
                logger.error("Received invalid JSON data")
                return

        camera_name = data.get("camera_name")
        logger.info(f"Received 'start_camera' request with data: {data}")
        if camera_name in IMAGES:
            with current_camera["lock"]:
                current_camera["name"] = camera_name
            socketio.emit("camera_status", {"camera_name": camera_name, "status": "streaming"})
        else:
            socketio.emit("camera_status",
                          {"camera_name": camera_name, "status": "error", "message": "Invalid camera name"})
            logger.warning(f"Invalid camera name: {camera_name}")

    @socketio.on("set_task")
    def handle_set_task(data):
        logger.info(f"Received 'set_task' request with data: {data}")
        socketio.emit("status", {"result": "ok"})

    @socketio.on("run_command")
    def handle_run_command(data):
        logger.info(f"Received 'run_command' request with data: {data}")
        socketio.emit("command_status", {"result": "ok"})

    @socketio.on("actuator_command")
    def handle_actuator_command(data):
        if isinstance(data, str):
            logger.warning("Received string data, attempting to parse as JSON")
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                socketio.emit("actuator_status", {"status": "error", "message": "Invalid JSON format"})
                logger.error("Received invalid JSON data for actuator command")
                return

        actuator_id = data.get("actuator")
        if isinstance(actuator_id, int):
            logger.warning(f"Received actuator command: Actuator ID = {actuator_id}")
            socketio.emit("actuator_status", {"actuator": actuator_id, "status": "command_received"})
        else:
            logger.warning(f"Invalid actuator ID received: {actuator_id}")

    @socketio.on("button_press")
    def handle_button_press(data):
        height = telemetry.get_telemetry()["height"]
        if data == "increase_height":
            telemetry.update_height(height + 0.5)
            logger.info(f"Height increased to {height} meters")
        elif data == "decrease_height":
            telemetry.update_height(max(0.0, height - 0.5))
            logger.info(f"Height decreased to {height} meters")
        else:
            logger.warning(f"Unknown button press command: {data}")

        socketio.emit("telemetry", {"height": height})
