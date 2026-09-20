import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Optional


class StructuredJsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured observability across the CAS federation."""
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "contract_id"):
            log_record["contract_id"] = getattr(record, "contract_id")
        if hasattr(record, "society"):
            log_record["society"] = getattr(record, "society")
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = getattr(record, "correlation_id")
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger("CAS")
