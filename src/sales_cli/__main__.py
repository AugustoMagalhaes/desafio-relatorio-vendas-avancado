from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Final

from sales_cli import __version__
from sales_cli.utils import parse_date

PROG: Final[str] = "vendas-cli"
FORMATS: Final[tuple[str, ...]] = ("text", "json")
DEFAULT_FORMAT: Final[str] = "text"


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
