from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

LOGGER: Final[logging.Logger] = logging.getLogger(__name__)

ENCODINGS: Final[tuple[str, ...]] = ("utf-8-sig", "cp1252")
FALLBACK_ENCODING: Final[str] = "latin-1"
DELIMITERS: Final[tuple[str, ...]] = (";", ",", "\t")
DEFAULT_DELIMITER: Final[str] = ","


def read_text(path: Path) -> str:
    raw: bytes = path.read_bytes()
    for encoding in ENCODINGS:
        try:
            text: str = raw.decode(encoding)
        except UnicodeDecodeError:
            LOGGER.debug("Could not decode %s as %s", path, encoding)
        else:
            LOGGER.debug("Decoded %s as %s", path, encoding)
            return text
    LOGGER.debug("Decoded %s as %s (fallback)", path, FALLBACK_ENCODING)
    return raw.decode(FALLBACK_ENCODING)


def detect_delimiter(text: str) -> str:
    header: str = next((line for line in text.splitlines() if line.strip()), "")
    best: str = DEFAULT_DELIMITER
    best_count: int = 0
    for delimiter in DELIMITERS:
        count: int = header.count(delimiter)
        if count > best_count:
            best = delimiter
            best_count = count
    return best
