from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Final

import pytest

from sales_cli import __version__
from sales_cli.__main__ import Arguments, date_argument, parse_arguments

ERROR_CASES: Final[list[tuple[list[str], str]]] = [
    ([], "required"),
    (["sales.csv", "--format", "xml"], "invalid choice"),
    (["sales.csv", "--start", "abc"], "invalid date"),
    (["sales.csv", "--end", "31/02/2025"], "invalid date"),
    (
        ["sales.csv", "--start", "2025-02-01", "--end", "2025-01-01"],
        "--start must not be after --end",
    ),
    (["sales.csv", "-v", "-q"], "cannot be used together"),
    (["sales.csv", "--unknown"], "unrecognized arguments"),
]


def test_parse_arguments_defaults() -> None:
    argv: list[str] = ["sales.csv"]
    arguments: Arguments = parse_arguments(argv)
    assert arguments.path == Path("sales.csv")
    assert arguments.output_format == "text"
    assert arguments.start is None
    assert arguments.end is None
    assert arguments.verbose is False
    assert arguments.quiet is False


@pytest.mark.parametrize("flag", ["--format", "-f"])
def test_parse_arguments_accepts_json_format(flag: str) -> None:
    argv: list[str] = ["sales.csv", flag, "json"]
    arguments: Arguments = parse_arguments(argv)
    assert arguments.output_format == "json"


def test_parse_arguments_accepts_dates_in_different_formats() -> None:
    argv: list[str] = ["sales.csv", "--start", "2025-01-01", "--end", "31/03/2025"]
    arguments: Arguments = parse_arguments(argv)
    assert arguments.start == date(2025, 1, 1)
    assert arguments.end == date(2025, 3, 31)


def test_parse_arguments_accepts_only_start() -> None:
    argv: list[str] = ["sales.csv", "--start", "2025-01-01"]
    arguments: Arguments = parse_arguments(argv)
    assert arguments.start == date(2025, 1, 1)
    assert arguments.end is None


def test_parse_arguments_accepts_only_end() -> None:
    argv: list[str] = ["sales.csv", "--end", "2025-03-31"]
    arguments: Arguments = parse_arguments(argv)
    assert arguments.start is None
    assert arguments.end == date(2025, 3, 31)


def test_parse_arguments_accepts_same_start_and_end() -> None:
    argv: list[str] = ["sales.csv", "--start", "2025-01-01", "--end", "2025-01-01"]
    arguments: Arguments = parse_arguments(argv)
    assert arguments.start == arguments.end


def test_parse_arguments_verbose_flag() -> None:
    argv: list[str] = ["sales.csv", "--verbose"]
    arguments: Arguments = parse_arguments(argv)
    assert arguments.verbose is True
    assert arguments.quiet is False


def test_parse_arguments_quiet_flag() -> None:
    argv: list[str] = ["sales.csv", "-q"]
    arguments: Arguments = parse_arguments(argv)
    assert arguments.quiet is True
    assert arguments.verbose is False


@pytest.mark.parametrize(("argv", "message"), ERROR_CASES)
def test_parse_arguments_rejects_invalid_input(
    argv: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        _ = parse_arguments(argv)
    assert exit_info.value.code == 2
    assert message in capsys.readouterr().err


def test_parse_arguments_version(capsys: pytest.CaptureFixture[str]) -> None:
    argv: list[str] = ["--version"]
    with pytest.raises(SystemExit) as exit_info:
        _ = parse_arguments(argv)
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"vendas-cli {__version__}"


def test_date_argument_parses_valid_date() -> None:
    assert date_argument("2025-03-28") == date(2025, 3, 28)


def test_date_argument_rejects_invalid_date() -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="invalid date"):
        _ = date_argument("not a date")
