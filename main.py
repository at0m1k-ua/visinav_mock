import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
import threading
from camera import start_camera_stream
from telemetry import start_telemetry_broadcast
from event_handlers import register_event_handlers

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

if __name__ == "__main__":
    # Start background threads
    start_camera_stream(socketio)
    threading.Thread(target=start_telemetry_broadcast, args=(socketio,), daemon=True).start()

    # Register event handlers
    register_event_handlers(socketio)

    host = "0.0.0.0"
    port = 5000
    socketio.run(app, host=host, port=port, debug=True)
