
import logging
import sys

def custom_logging(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    # Only add handlers if they haven't been added already.
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        # Prevent log propagation to avoid duplicate logs from the root logger.
        logger.propagate = False
    return logger
