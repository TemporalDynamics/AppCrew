import logging
import sys
from pathlib import Path


def get_logger(name: str = "talo") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    from core.config import settings
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    fmt = logging.Formatter(
        "[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    return logger
