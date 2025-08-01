from utils.logger_setup import get_logger
logger = get_logger("signal")
for i in range(100):
    logger.info(f"Flooding the log with message number {i}")