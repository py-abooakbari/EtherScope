"""Structured logging configuration for EtherScope."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from .config import Config


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "wallet_address"):
            log_data["wallet_address"] = record.wallet_address
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class SimpleFormatter(logging.Formatter):
    """Simple formatter for non-JSON output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as simple text."""
        return (
            f"[{record.levelname}] {record.name} - "
            f"{record.funcName}:{record.lineno} - {record.getMessage()}"
        )


def setup_logging(
    log_level: Optional[str] = None, log_format: Optional[str] = None
) -> logging.Logger:
    """Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format type ('structured' for JSON, 'simple' for text)

    Returns:
        Configured logger instance

    """
    log_level = log_level or Config.LOG_LEVEL
    log_format = log_format or Config.LOG_FORMAT

    logger = logging.getLogger("EtherScope")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Set formatter based on format type
    if log_format == "structured":
        formatter = StructuredFormatter()
    else:
        formatter = SimpleFormatter()

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    """
    return logging.getLogger(name)
