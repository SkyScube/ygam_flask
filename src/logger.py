import sys
import os
from loguru import logger

logger.remove()

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

# File handler — create logs dir if needed, skip silently if not writable
_log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
try:
    os.makedirs(_log_dir, exist_ok=True)
    logger.add(
        os.path.join(_log_dir, "ygam.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
    )
except Exception as e:
    logger.warning("Could not set up file logging ({}), using stdout only", e)
