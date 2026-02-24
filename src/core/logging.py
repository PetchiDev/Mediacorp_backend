import logging
import sys
from typing import Any

# Rule 11: Centralized logger setup
def setup_logging() -> logging.Logger:
    """Setup centralized logger for the application."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    # Format: Timestamp, Level, Module, Function, Line Number, Message
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s"
    )

    # Stream Handler (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(stream_handler)
    
    return logger

logger = setup_logging()
