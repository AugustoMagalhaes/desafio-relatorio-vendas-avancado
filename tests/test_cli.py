from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Final

import pytest

from sales_cli import __version__
from sales_cli.__main__ import (
    Arguments,
    date_argument,
    main,
    parse_arguments,
    resolve_log_level,
)

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

OVERFLOW_CSV_CONTENT: Final[str] = (
    "produto;quantidade;preco\nMouse;2;50,00\nCobre;1;1e30\n"
)


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


CSV_CONTENT: Final[str] = (
    "data;produto;quantidade;preço unitário\n"
    "2025-01-10;Mouse;2;50,00\n"
    "2025-02-15;Teclado;1;150,00\n"
    "2025-03-20;Monitor;1;900,00\n"
)

NO_DATE_CSV_CONTENT: Final[str] = "produto;quantidade;preço\nMouse;2;50,00\n"

HEADER_ONLY_CONTENT: Final[str] = "produto;quantidade;preço\n"

LOG_LEVEL_CASES: Final[list[tuple[list[str], int]]] = [
    (["sales.csv"], logging.INFO),
    (["sales.csv", "-v"], logging.DEBUG),
    (["sales.csv", "-q"], logging.WARNING),
]


def write_csv(directory: Path, content: str) -> Path:
    path: Path = directory / "sales.csv"
    _ = path.write_bytes(content.encode("utf-8"))
    return path


@pytest.mark.parametrize(("argv", "expected"), LOG_LEVEL_CASES)
def test_resolve_log_level(argv: list[str], expected: int) -> None:
    arguments: Arguments = parse_arguments(argv)
    assert resolve_log_level(arguments) == expected


def test_main_prints_text_report_by_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, CSV_CONTENT)
    code: int = main([str(path)])
    out: str = capsys.readouterr().out
    assert code == 0
    assert "Grand total: 1150.00" in out
    assert "Best seller (units): Mouse (2 sold)" in out
    assert "Best seller (revenue): Monitor (900.00)" in out


def test_main_prints_json_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, CSV_CONTENT)
    code: int = main([str(path), "--format", "json"])
    out: str = capsys.readouterr().out
    assert code == 0
    assert out.startswith("{")
    assert '"grand_total": 1150.0' in out


def test_main_applies_date_filter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, CSV_CONTENT)
    code: int = main([str(path), "--start", "2025-02-01", "--end", "2025-03-31"])
    out: str = capsys.readouterr().out
    assert code == 0
    assert "Grand total: 1050.00" in out
    assert "Mouse" not in out


def test_main_keeps_report_on_stdout_and_logs_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, CSV_CONTENT)
    _ = main([str(path)])
    out, err = capsys.readouterr()
    assert "Read 3 sale(s)" not in out
    assert "Read 3 sale(s) from sales.csv" in err


def test_main_quiet_hides_info_messages(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, CSV_CONTENT)
    _ = main([str(path), "-q"])
    assert "Read 3 sale(s)" not in capsys.readouterr().err


def test_main_verbose_shows_debug_messages(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, CSV_CONTENT)
    _ = main([str(path), "-v"])
    assert "Decoded" in capsys.readouterr().err


def test_main_warns_when_date_filter_is_ignored(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, NO_DATE_CSV_CONTENT)
    code: int = main([str(path), "--start", "2025-01-01"])
    out, err = capsys.readouterr()
    assert code == 0
    assert "Date filter ignored" in err
    assert "Mouse" in out


def test_main_returns_error_for_missing_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = tmp_path / "missing.csv"
    code: int = main([str(path)])
    out, err = capsys.readouterr()
    assert code == 1
    assert "File not found" in err
    assert out == ""


def test_main_returns_error_for_unreadable_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code: int = main([str(tmp_path)])
    assert code == 1
    assert "Could not read" in capsys.readouterr().err


def test_main_returns_error_for_file_without_sales(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, HEADER_ONLY_CONTENT)
    code: int = main([str(path)])
    assert code == 1
    assert "no valid sales" in capsys.readouterr().err


def test_main_exits_with_usage_error_for_invalid_arguments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        _ = main(["sales.csv", "--format", "xml"])
    assert exit_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_main_skips_rows_with_values_too_large_to_format(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path: Path = write_csv(tmp_path, OVERFLOW_CSV_CONTENT)
    code: int = main([str(path)])
    out: str
    err: str
    out, err = capsys.readouterr()
    assert code == 0
    assert "Skipped 1" in err
    assert "Grand total: 100.00" in out


def test_module_runs_as_command_and_separates_streams(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, CSV_CONTENT)
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-m", "sales_cli", str(path), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.startswith("{")
    assert "Read 3 sale(s)" in result.stderr


def test_module_returns_error_code_for_missing_file(tmp_path: Path) -> None:
    path: Path = tmp_path / "missing.csv"
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-m", "sales_cli", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "File not found" in result.stderr
