"""
Centralized Structured Logging Configuration
============================================
Purpose: Provides structured logging for both human-readable (dev)
and machine-parsable (prod/JSON) formats using structlog.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import structlog

from job_coach.app.core.config import settings


def setup_logging() -> None:
    """
    Configures structlog to output JSON in production and
    colored text in development.
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.DEBUG:
        # Human-friendly logging for local development
        processors = shared_processors + [structlog.dev.ConsoleRenderer()]
    else:
        # JSON logging for production (ELK, Grafana Loki, etc.)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,  # type: ignore[attr-defined]
        cache_logger_on_first_use=True,
    )

    # Standard library logging integration
    # Prevent duplicate handlers if setup_logging is called multiple times
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        root_logger.addHandler(console_handler)

        # File handler (only in non-debug mode)
        if not settings.DEBUG:
            log_file_path = Path(settings.LOG_FILE_PATH)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=settings.LOG_FILE_MAX_SIZE,
                backupCount=settings.LOG_FILE_BACKUP_COUNT,
            )
            # For file logging, we want a machine-readable format (JSON)
            # The JSONRenderer is already in the processor chain for non-debug
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            root_logger.addHandler(file_handler)

        root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)


setup_logging()
logger: structlog.stdlib.BoundLogger = structlog.get_logger("job_coach")
audit_logger: structlog.stdlib.BoundLogger = structlog.get_logger("audit")
