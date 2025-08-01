from utils.logger_setup import get_logger

signal_logger = get_logger("signal")
signal_logger.info("Test from standalone script", extra={"extra_data": {"source": "test_log"}})
print("Logged a test message.")
