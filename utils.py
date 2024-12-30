import json
import logging

logger = logging.getLogger("Utils")


def safe_json_parse(data):
    try:
        return json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError:
        logger.error("Invalid JSON received")
        return None
