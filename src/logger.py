import sys
import os
from loguru import logger

logger.remove()

# File handler only — console keeps Werkzeug HTTP logs, app logs go to file
_log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
try:
    os.makedirs(_log_dir, exist_ok=True)
    logger.add(
        os.path.join(_log_dir, "ygam.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
    )
except Exception as e:
    # Fallback: stderr only for critical startup errors
    logger.add(sys.stderr, level="WARNING")
    logger.warning("Could not set up file logging ({}), using stderr only", e)
