from __future__ import annotations

import io
import logging
import sys
from datetime import date
from decimal import Decimal

import pytest

from sales_cli.utils import (
    DIM,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    LOGGER_NAME,
    RED,
    RESET,
    YELLOW,
    ColorFormatter,
    is_tty,
    normalize_text,
    parse_date,
    parse_decimal,
    setup_logging,
    strip_accents,
    supports_color,
)


class FakeStream(io.StringIO):
    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty: bool = tty

    def isatty(self) -> bool:
        return self._tty


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.delenv("NO_COLOR", raising=False)
    return monkeypatch


def make_record(level: int) -> logging.LogRecord:
    return logging.LogRecord("sales_cli.test", level, __file__, 1, "hello", None, None)


def test_is_tty_true_and_false() -> None:
    assert is_tty(FakeStream(True)) is True
    assert is_tty(FakeStream(False)) is False


def test_is_tty_defaults_to_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", FakeStream(True))
    assert is_tty() is True


@pytest.mark.usefixtures("clean_env")
def test_supports_color_on_tty() -> None:
    assert supports_color(FakeStream(True)) is True


@pytest.mark.usefixtures("clean_env")
def test_supports_color_off_when_not_tty() -> None:
    assert supports_color(FakeStream(False)) is False


def test_supports_color_respects_no_color(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("NO_COLOR", "1")
    assert supports_color(FakeStream(True)) is False


@pytest.mark.parametrize(
    ("level", "color"),
    [
        (logging.DEBUG, DIM),
        (logging.WARNING, YELLOW),
        (logging.ERROR, RED),
        (logging.CRITICAL, RED),
    ],
)
def test_formatter_colours_by_level(level: int, color: str) -> None:
    out: str = ColorFormatter(LOG_FORMAT, LOG_DATE_FORMAT).format(make_record(level))
    assert out.startswith(color)
    assert out.endswith(RESET)
    assert "hello" in out


def test_formatter_leaves_info_uncoloured() -> None:
    out: str = ColorFormatter(LOG_FORMAT, LOG_DATE_FORMAT).format(
        make_record(logging.INFO)
    )
    assert "hello" in out
    assert "\033[" not in out


@pytest.mark.usefixtures("clean_env")
def test_setup_logging_writes_to_given_stream_and_respects_level() -> None:
    stream: FakeStream = FakeStream(False)
    logger: logging.Logger = setup_logging(logging.INFO, stream)
    logger.debug("hidden")
    logger.info("visible")
    output: str = stream.getvalue()
    assert "visible" in output
    assert "INFO" in output
    assert "hidden" not in output
    assert "\033[" not in output


def test_setup_logging_is_idempotent() -> None:
    _ = setup_logging(logging.INFO, FakeStream(False))
    logger: logging.Logger = setup_logging(logging.INFO, FakeStream(False))
    assert len(logger.handlers) == 1
    assert logger.propagate is False


def test_setup_logging_child_loggers_reach_the_handler() -> None:
    stream: FakeStream = FakeStream(False)
    _ = setup_logging(logging.INFO, stream)
    logging.getLogger("sales_cli.core").info("from child")
    assert "from child" in stream.getvalue()


@pytest.mark.usefixtures("clean_env")
def test_setup_logging_uses_colour_on_tty() -> None:
    stream: FakeStream = FakeStream(True)
    setup_logging(logging.INFO, stream).warning("careful")
    assert YELLOW in stream.getvalue()


def test_setup_logging_defaults_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    _ = setup_logging()
    logging.getLogger(LOGGER_NAME).info("to stderr")
    out: str
    err: str
    out, err = capsys.readouterr()
    assert "to stderr" in err
    assert out == ""


def test_strip_accents() -> None:
    assert strip_accents("Preço Unitário") == "Preco Unitario"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Preço Unitário", "preco_unitario"),
        ("  Data da Venda ", "data_da_venda"),
        ("Preço Unitário (R$)", "preco_unitario_r"),
        ("QTD", "qtd"),
    ],
)
def test_normalize_text(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("49.9", Decimal("49.9")),
        ("49,9", Decimal("49.9")),
        ("1.234,56", Decimal("1234.56")),
        ("1,234.56", Decimal("1234.56")),
        ("R$ 49,90", Decimal("49.90")),
        ("R$49,90", Decimal("49.90")),
        ("  7 ", Decimal(7)),
        ("-3", Decimal(-3)),
        (".5", Decimal("0.5")),
        ("5.", Decimal(5)),
        ("0", Decimal(0)),
    ],
)
def test_parse_decimal_valid(raw: str, expected: Decimal) -> None:
    assert parse_decimal(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "abc",
        "12abc",
        "--5",
        "5-",
        "R$",
        ".",
        ",",
        "USD 5",
        "NaN",
        "Infinity",
        "1.234.567",
    ],
)
def test_parse_decimal_invalid(raw: str) -> None:
    with pytest.raises(ValueError, match="not a number"):
        _ = parse_decimal(raw)


def test_parse_decimal_avoids_float_error() -> None:
    assert parse_decimal("49.9") * 3 == Decimal("149.7")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2025-01-31", date(2025, 1, 31)),
        ("2025/01/31", date(2025, 1, 31)),
        ("2025.01.31", date(2025, 1, 31)),
        ("2025-1-5", date(2025, 1, 5)),
        ("31/01/2025", date(2025, 1, 31)),
        ("31-01-2025", date(2025, 1, 31)),
        ("31.01.2025", date(2025, 1, 31)),
        ("05/01/25", date(2025, 1, 5)),
        ("03/04/2025", date(2025, 4, 3)),
        ("01/31/2025", date(2025, 1, 31)),
        ("2025-01-31 23:59:59", date(2025, 1, 31)),
        ("2025-01-31T10:30:00Z", date(2025, 1, 31)),
        ("31/01/2025 10:30", date(2025, 1, 31)),
        ("  2025-01-31  ", date(2025, 1, 31)),
    ],
)
def test_parse_date_valid(raw: str, expected: date) -> None:
    assert parse_date(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "not a date",
        "31/13/2025",
        "29/02/2025",
        "2025-13-01",
        "2025-02-30",
        "12345678",
        "28 de março de 2025",
        "Jan 31, 2025",
    ],
)
def test_parse_date_invalid(raw: str) -> None:
    assert parse_date(raw) is None
