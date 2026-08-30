"""Utility functions for logging within the Poussins project."""
import logging
import os
import sys


def getLogger(name: str) -> logging.Logger:
    """Get a logger."""
    logger = logging.getLogger(name)
    level = getattr(
        logging,
        os.getenv("POUSSINS_LOG_LEVEL", "INFO").upper(),
        logging.INFO
    )

    if not logger.handlers:
        # Configure the logger only if it hasn't been configured yet
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
