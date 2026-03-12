import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "job_coach", level: int = logging.INFO, log_format: Optional[str] = None
) -> logging.Logger:
    """
    Setup and return a central logger for the application.
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Check if handlers already exist to avoid duplicate logs in some environments
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Prevent logs from propagating to the root logger to avoid duplication
    logger.propagate = False

    return logger


# Create a default instance to be imported across the project
logger = setup_logger()
