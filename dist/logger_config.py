# logger_config.py
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Set up file handler
file_handler = logging.FileHandler('output.log', mode='a')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Set up stream handler for console output in Linux
if os.name == 'posix':
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

def setup_logging():
    if os.name == 'nt':
        print("Windows OS detected. Logging to console.")
    elif os.name == 'posix':
        logger.info("Linux OS detected. Logging to file and console.")
    else:
        logger.info("Unknown OS detected. Logging to file.")