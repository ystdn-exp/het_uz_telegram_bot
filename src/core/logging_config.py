import os
import logging

from logging.handlers import RotatingFileHandler

from src.core.config import settings


def _create_log_dir():
    """
    Helper function to create the log dir if not exists.
    """

    log_dir = settings.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)


def _init_root_logger():
    """
    Helper function to initialize root logger.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    return root_logger


def _init_console_logger(root_logger):
    """
    Helper function to initialize console logger with rotation.
    """
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelName)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # rotation configuration
    rotating_file = RotatingFileHandler(
        filename=os.path.join(settings.LOG_DIR, "app.log"),
        maxBytes=settings.ROTATING_LOG_FILE_SIZE,
        backupCount=settings.ROATING_LOG_FILE_BACKUPS,
        encoding="utf-8",
    )
    rotating_file.setFormatter(formatter)
    root_logger.addHandler(rotating_file)


def setup_logging():
    """
    Initialize logging with log files.
    """
    _create_log_dir()

    root_logger = _init_root_logger()

    _init_console_logger(root_logger)

    logging.info("Logging configured successfully.")
