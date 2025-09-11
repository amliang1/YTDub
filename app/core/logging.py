import logging
import logging.config
from .settings import settings

def setup_logging():
    """Configure logging for the application"""
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG" if settings.app_debug else "INFO",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "ytdub.log",
                "formatter": "default",
                "level": "INFO",
            },
        },
        "root": {
            "level": "DEBUG" if settings.app_debug else "INFO",
            "handlers": ["console", "file"],
        },
    }
    
    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name"""
    return logging.getLogger(name)

# Initialize logging
setup_logging()