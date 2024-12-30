import threading
import time
from io import BytesIO
from PIL import Image
import logging

IMAGES = {
    "front_left": "static/front_left.jpg",
    "front_right": "static/front_right.jpg",
    "bottom": "static/bottom.jpg",
}

current_camera = {"name": "front_left", "lock": threading.Lock()}
logger = logging.getLogger("CameraLogger")


def send_video(socketio):
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


def start_camera_stream(socketio):
    logger.info("Starting camera stream thread")
    threading.Thread(target=send_video, args=(socketio,), daemon=True).start()
