"""Logging configuration for the data pipeline."""

import logging
import sys
from datetime import datetime


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers = []
    logger.addHandler(handler)
    
    return logger
