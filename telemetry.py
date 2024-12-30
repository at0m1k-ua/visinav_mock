import time
import logging

logger = logging.getLogger("TelemetryLogger")


def start_telemetry_broadcast(socketio):
    logger.info("Starting telemetry broadcast")
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
