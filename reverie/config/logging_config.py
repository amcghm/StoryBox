import sys
import os
from loguru import logger
from reverie.config.config import Config

# Ensure the log directory exists
os.makedirs(Config.log_dir, exist_ok=True)

# Log file path
LOG_FILE_PATH = os.path.join(Config.log_dir, "system.log")

# Configure loguru
logger.remove()  # Remove the default configuration

log_format = "{time:YYYY-MM-DD HH:mm:ss} | <level>{level:<8}</level> | {file:<24} | {message}"

# Add log file handler
logger.add(
    LOG_FILE_PATH,
    mode="w",
    rotation="10 MB",
    retention=None,
    level="DEBUG",
    encoding="utf-8",
    format=log_format
)

# Add console log handler
logger.add(
    sys.stdout,
    level="DEBUG",
    format=log_format
)
