from __future__ import annotations

import logging
import os
import re
import sys
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import IO, Final

LOGGER_NAME: Final[str] = "sales_cli"
LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-7s | %(message)s"
LOG_DATE_FORMAT: Final[str] = "%H:%M:%S"

RESET: Final[str] = "\033[0m"
DIM: Final[str] = "\033[2m"
RED: Final[str] = "\033[31m"
YELLOW: Final[str] = "\033[33m"

LEVEL_COLORS: Final[dict[int, str]] = {
    logging.DEBUG: DIM,
    logging.WARNING: YELLOW,
    logging.ERROR: RED,
    logging.CRITICAL: RED,
}

DATE_FORMATS: Final[tuple[str, ...]] = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d/%m/%y",
    "%m/%d/%Y",
    "%m-%d-%Y",
)


def is_tty(stream: IO[str] | None = None) -> bool:
    target: IO[str] = stream if stream is not None else sys.stdout
    return target.isatty()


def supports_color(stream: IO[str] | None = None) -> bool:
    return not os.environ.get("NO_COLOR") and is_tty(stream)


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message: str = super().format(record)
        color: str = LEVEL_COLORS.get(record.levelno, "")
        return f"{color}{message}{RESET}" if color else message


def setup_logging(
    level: int = logging.INFO, stream: IO[str] | None = None
) -> logging.Logger:
    target: IO[str] = stream if stream is not None else sys.stderr
    formatter: logging.Formatter = (
        ColorFormatter(LOG_FORMAT, LOG_DATE_FORMAT)
        if supports_color(target)
        else logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    )
    handler: logging.StreamHandler[IO[str]] = logging.StreamHandler(target)
    handler.setFormatter(formatter)
    logger: logging.Logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def strip_accents(value: str) -> str:
    decomposed: str = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", strip_accents(value).lower()).strip("_")


def parse_decimal(text: str) -> Decimal:
    cleaned: str = text.strip().removeprefix("R$").strip()
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        value: Decimal = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"not a number: {text!r}") from None
    if not value.is_finite():
        raise ValueError(f"not a number: {text!r}")
    return value


def parse_date(text: str) -> date | None:
    value: str = text.strip().replace("T", " ").split(" ")[0]
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    return None
