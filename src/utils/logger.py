"""Logging configuration for HA-Calendar."""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(config):
    """
    Set up logging with file and console handlers.

    Args:
        config: Configuration dictionary with logging settings

    Returns:
        logging.Logger: Configured logger instance
    """
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('file', 'logs/calendar.log')
    max_bytes = log_config.get('max_bytes', 1048576)  # 1MB default
    backup_count = log_config.get('backup_count', 3)

    # Create logger
    logger = logging.getLogger('ha_calendar')
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (rotating)
    try:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to set up file logging: {e}")

    return logger


def get_logger():
    """
    Get the existing logger instance.

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger('ha_calendar')
