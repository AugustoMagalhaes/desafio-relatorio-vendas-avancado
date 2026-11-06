from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Final

from sales_cli import __version__
from sales_cli.core import Report, Sale, filter_by_date, summarize
from sales_cli.output import format_json, format_text
from sales_cli.parser import ParseError, parse_sales
from sales_cli.utils import LOGGER_NAME, parse_date, setup_logging

PROG: Final[str] = "vendas-cli"
FORMATS: Final[tuple[str, ...]] = ("text", "json")
DEFAULT_FORMAT: Final[str] = "text"
LOGGER: Final[logging.Logger] = logging.getLogger(f"{LOGGER_NAME}.cli")
EXIT_OK: Final[int] = 0
EXIT_ERROR: Final[int] = 1


class Arguments(argparse.Namespace):
    def __init__(self) -> None:
        super().__init__()
        self.path: Path = Path()
        self.output_format: str = DEFAULT_FORMAT
        self.start: date | None = None
        self.end: date | None = None
        self.verbose: bool = False
        self.quiet: bool = False


def date_argument(value: str) -> date:
    parsed: date | None = parse_date(value)
    if parsed is None:
        raise argparse.ArgumentTypeError(f"invalid date: {value!r}")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=PROG,
        description="Generate a sales report from a CSV file.",
    )
    _ = parser.add_argument("path", type=Path, help="path to the sales CSV file")
    _ = parser.add_argument(
        "-f",
        "--format",
        dest="output_format",
        choices=FORMATS,
        default=DEFAULT_FORMAT,
        help="output format (default: %(default)s)",
    )
    _ = parser.add_argument(
        "--start",
        type=date_argument,
        metavar="DATE",
        help="only include sales on or after this date (YYYY-MM-DD or DD/MM/YYYY)",
    )
    _ = parser.add_argument(
        "--end",
        type=date_argument,
        metavar="DATE",
        help="only include sales on or before this date (YYYY-MM-DD or DD/MM/YYYY)",
    )
    _ = parser.add_argument(
        "-v", "--verbose", action="store_true", help="show debug messages"
    )
    _ = parser.add_argument(
        "-q", "--quiet", action="store_true", help="show only warnings and errors"
    )
    _ = parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def parse_arguments(argv: Sequence[str] | None = None) -> Arguments:
    parser: argparse.ArgumentParser = build_parser()
    arguments: Arguments = parser.parse_args(argv, namespace=Arguments())
    if (
        arguments.start is not None
        and arguments.end is not None
        and arguments.start > arguments.end
    ):
        parser.error("--start must not be after --end")
    if arguments.verbose and arguments.quiet:
        parser.error("--verbose and --quiet cannot be used together")
    return arguments


def resolve_log_level(arguments: Arguments) -> int:
    if arguments.verbose:
        return logging.DEBUG
    if arguments.quiet:
        return logging.WARNING
    return logging.INFO


def render(report: Report, output_format: str) -> str:
    if output_format == "json":
        return format_json(report)
    return format_text(report)


def main(argv: Sequence[str] | None = None) -> int:
    arguments: Arguments = parse_arguments(argv)
    _ = setup_logging(resolve_log_level(arguments))
    try:
        sales: list[Sale] = parse_sales(arguments.path)
    except FileNotFoundError:
        LOGGER.error("File not found: %s", arguments.path)
        return EXIT_ERROR
    except OSError as error:
        LOGGER.error("Could not read %s: %s", arguments.path, error.strerror)
        return EXIT_ERROR
    except ParseError as error:
        LOGGER.error("%s", error)
        return EXIT_ERROR
    filtered: list[Sale] = filter_by_date(sales, arguments.start, arguments.end)
    report: Report = summarize(filtered)
    print(render(report, arguments.output_format))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
