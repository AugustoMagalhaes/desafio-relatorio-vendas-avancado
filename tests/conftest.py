from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from sales_cli.utils import LOGGER_NAME


@pytest.fixture(autouse=True)
def _reset_package_logger() -> Iterator[None]:
    yield
    logger: logging.Logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    logger.setLevel(logging.NOTSET)
    logger.propagate = True
