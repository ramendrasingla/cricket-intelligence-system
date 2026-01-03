"""
Logging Configuration

Centralized logging setup for the entire application.
"""

import logging
import logging.config
import yaml
from pathlib import Path
from typing import Optional


def setup_logging(
    config_path: Optional[Path] = None,
    default_level: int = logging.INFO
) -> None:
    """
    Setup logging configuration

    Args:
        config_path: Path to logging YAML config file
        default_level: Default logging level if config file not found
    """
    if config_path is None:
        # Use config path from settings
        from cricket_intelligence.config import settings
        config_path = settings.logging_config

    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        # Fallback to basic config if YAML not found
        logging.basicConfig(
            level=default_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
