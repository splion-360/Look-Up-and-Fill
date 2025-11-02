import asyncio
import logging
import os
from functools import wraps
from typing import Literal

from dotenv import load_dotenv
from fastapi import HTTPException


load_dotenv()

#######################################################
############# GLOBAL CONSTANTS ########################
#######################################################

ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
CONCURRENCY_LIMIT = 5
BUCKET_CLEANUP_FREQ = 3600  # s Every hour
PORT = 8000
MAX_RETRIES = 3
MAX_WORKERS = 6
REQUEST_PER_MINUTE = 30
LOG_COLORS = {
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    "BRIGHT_RED": "\033[91m",
    "BRIGHT_GREEN": "\033[92m",
    "BRIGHT_YELLOW": "\033[93m",
    "RESET": "\033[0m",
}


#######################################################
############ LOGGING UTILITIES ########################
#######################################################

ColorType = Literal[
    "RED",
    "GREEN",
    "YELLOW",
    "BLUE",
    "MAGENTA",
    "CYAN",
    "WHITE",
    "BRIGHT_RED",
    "BRIGHT_GREEN",
    "BRIGHT_YELLOW",
]


class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt: str):
        super().__init__(fmt)
        self.colors = {
            logging.DEBUG: "BRIGHT_YELLOW",
            logging.INFO: "GREEN",
            logging.WARNING: "YELLOW",
            logging.ERROR: "RED",
            logging.CRITICAL: "BRIGHT_RED",
        }

    def format(self, record):
        message = super().format(record)
        if hasattr(record, "custom_color") and record.custom_color:
            color = record.custom_color
        else:
            color = self.colors.get(record.levelno, "WHITE")
        return f"{LOG_COLORS[color]}{message}{LOG_COLORS['RESET']}"


class ColoredLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def info(self, message: str, color: ColorType = None):
        record = self._logger.makeRecord(
            self._logger.name, logging.INFO, "", 0, message, (), None
        )
        if color:
            record.custom_color = color
        self._logger.handle(record)

    def debug(self, message: str, color: ColorType = None):
        record = self._logger.makeRecord(
            self._logger.name, logging.DEBUG, "", 0, message, (), None
        )
        if color:
            record.custom_color = color
        self._logger.handle(record)

    def warning(self, message: str, color: ColorType = None):
        record = self._logger.makeRecord(
            self._logger.name, logging.WARNING, "", 0, message, (), None
        )
        if color:
            record.custom_color = color
        self._logger.handle(record)

    def error(self, message: str, color: ColorType = None):
        record = self._logger.makeRecord(
            self._logger.name, logging.ERROR, "", 0, message, (), None
        )
        if color:
            record.custom_color = color
        self._logger.handle(record)

    def __getattr__(self, name):
        return getattr(self._logger, name)


def setup_logger(name: str = __name__) -> ColoredLogger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return ColoredLogger(logger)

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return ColoredLogger(logger)


logger = setup_logger(__name__)

#######################################################
############ DOCUMENT SERVICE UTILITIES ###############
#######################################################


def get_header() -> dict[any]:
    if not FINNHUB_API_KEY:
        raise ValueError("Invalid API Key")

    headers = {}
    headers["X-Finnhub-Token"] = FINNHUB_API_KEY

    return headers


def retry_handler(max_retries: int = MAX_RETRIES):

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attepmt in range(max_retries + 1):
                try:
                    response = await func(*args, **kwargs)
                    return response

                except HTTPException as e:
                    if e.status_code == 429:
                        if attepmt < max_retries:
                            wait_time = (2**attepmt) + 0.5
                            logger.warning(
                                f"Rate limit hit, retrying in {wait_time}s (attempt {attepmt + 1}/{max_retries + 1})"
                            )
                            await asyncio.sleep(wait_time)
                            continue

                        else:
                            raise HTTPException(
                                500,
                                detail="Max retry limit reached. Unable to fetch data",
                            ) from e
                except Exception as e:
                    raise HTTPException(500, detail="Retry failed") from e
            return

        return wrapper

    return decorator


def is_valid(text: str):
    """
    Check whether the given text is a valid ticker
    """
    if len(text) < 10 and text.isupper():
        return True

    return False


def hamming_distance(s1: str, s2: str) -> int:
    if len(s1) != len(s2):
        return max(len(s1), len(s2))
    return sum(c1 != c2 for c1, c2 in zip(s1, s2, strict=False))
