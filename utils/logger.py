import logging
import os

from utils.config import LOG_FILE, RUNTIME_DIR


def setup_logger(name="TajidoAuto", log_file=LOG_FILE):
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    ch.setFormatter(ch_formatter)

    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger

logger = setup_logger()
