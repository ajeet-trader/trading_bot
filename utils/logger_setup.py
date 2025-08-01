import logging
import logging.handlers
import json
from pathlib import Path
from typing import Dict
from datetime import datetime
import pandas as pd

# Import the global config object from our config loader
from utils.config_loader import config

def setup_logging() -> Dict[str, logging.Logger]:
    """
    Configures and returns structured loggers for the application.

    Returns:
        Dict[str, logging.Logger]: A dictionary of configured loggers:
            - 'signal_logger': For trading signals
            - 'trade_logger': For trade executions
            - 'error_logger': For errors and warnings
    """
    # Ensure logs directory exists
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Load logging config from our central configuration
    log_config = config.get("logging", {
        "max_bytes": 20 * 1024 * 1024,  # Default 20MB
        "backup_count": 5
    })

    # Custom formatter that outputs JSON
    class StructuredMessageFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": self.formatTime(record, self.datefmt),
                "module": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
            }

            if hasattr(record, 'extra_data'):
                def serialize(obj):
                    if isinstance(obj, (datetime, pd.Timestamp)):
                        return obj.isoformat()
                    if isinstance(obj, dict):
                        return {k: serialize(v) for k, v in obj.items()}
                    if isinstance(obj, list):
                        return [serialize(i) for i in obj]
                    return obj

                log_data["extra_data"] = serialize(record.extra_data)

            if record.exc_info:
                log_data['exc_info'] = self.formatException(record.exc_info)

            return json.dumps(log_data)

    # Configure log handlers
    def make_handler(log_name: str) -> logging.Handler:
        handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / f"{log_name}.log",
            maxBytes=log_config["max_bytes"],
            backupCount=log_config["backup_count"]
        )
        handler.setFormatter(StructuredMessageFormatter(datefmt='%Y-%m-%dT%H:%M:%S%z'))
        return handler

    # Create and configure loggers
    loggers = {
        "signal_logger": logging.getLogger("signals"),
        "trade_logger": logging.getLogger("trades"),
        "error_logger": logging.getLogger("errors")
    }

    for name, logger in loggers.items():
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler_name = name.replace('_logger', '')
            logger.addHandler(make_handler(handler_name))
            logger.propagate = False

    return loggers

# Initialize loggers once when this module is imported
_loggers = setup_logging()

def get_logger(log_type: str) -> logging.Logger:
    """
    Public interface to get a pre-configured logger.

    Args:
        log_type (str): One of 'signal', 'trade', or 'error'

    Returns:
        logging.Logger: The requested logger instance
    """
    logger_name = f"{log_type}_logger"
    if logger_name not in _loggers:
        raise ValueError(f"Invalid log type '{log_type}'. Must be one of 'signal', 'trade', or 'error'")
    return _loggers[logger_name]

# Example usage for direct execution and testing
if __name__ == "__main__":
    print("Testing logging system...")

    signal_log = get_logger("signal")
    trade_log = get_logger("trade")
    error_log = get_logger("error")

    # Structured logging with serializable fields
    signal_log.info("EMA crossover signal generated", extra={
        "extra_data": {
            "symbol": "BTC/USDT",
            "strategy": "ema_crossover",
            "signal": "BUY",
            "confidence": 0.82
        }
    })

    trade_log.info("Trade executed", extra={
        "extra_data": {
            "action": "BUY",
            "symbol": "BTC/USDT",
            "quantity": 0.5,
            "price": 42350.20
        }
    })

    try:
        1 / 0
    except ZeroDivisionError:
        error_log.exception("An unexpected error occurred", extra={
            "extra_data": {
                "api": "InternalMath",
                "details": "Division by zero"
            }
        })

    print("Log tests complete. Check the 'logs' directory for output files.")
