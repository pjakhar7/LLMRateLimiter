
import logging
import sys

# Setup logging configuration to direct logs to stdout
def custom_logging():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set the default logging level to INFO

    # Create a stream handler that writes log messages to stdout (console)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)  # Set the level for the handler

    # Create a log format (you can customize this)
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(log_format)

    # Add the handler to the logger
    logger.addHandler(stream_handler)

    return logger
