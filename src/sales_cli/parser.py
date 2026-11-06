from __future__ import annotations

import csv
import io
import logging
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Final

from sales_cli.core import Sale
from sales_cli.utils import normalize_text, parse_date, parse_decimal

LOGGER: Final[logging.Logger] = logging.getLogger(__name__)

ENCODINGS: Final[tuple[str, ...]] = ("utf-8-sig", "cp1252")
FALLBACK_ENCODING: Final[str] = "latin-1"
DELIMITERS: Final[tuple[str, ...]] = (";", ",", "\t")
DEFAULT_DELIMITER: Final[str] = ","

HEADER_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "date": ("data", "date", "data_venda", "data_da_venda", "sale_date"),
    "product": ("produto", "product", "item", "nome_produto"),
    "quantity": ("quantidade", "quantity", "qtd", "qtde", "qty"),
    "unit_price": (
        "preco_unitario",
        "unit_price",
        "preco",
        "price",
        "valor_unitario",
    ),
}
REQUIRED_FIELDS: Final[tuple[str, ...]] = ("product", "quantity", "unit_price")
MAX_AMOUNT: Final[Decimal] = Decimal(10**9)


class ParseError(Exception):
    pass


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


def map_columns(header: Sequence[str]) -> dict[str, int]:
    indexes: dict[str, int] = {
        normalize_text(name): index for index, name in enumerate(header)
    }
    columns: dict[str, int] = {}
    for field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias in indexes:
                columns[field] = indexes[alias]
                break
    missing: list[str] = [name for name in REQUIRED_FIELDS if name not in columns]
    if missing:
        raise ParseError(f"missing required columns: {', '.join(missing)}")
    return columns


def get_cell(row: Sequence[str], columns: Mapping[str, int], field: str) -> str:
    index: int | None = columns.get(field)
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def check_amount(value: Decimal, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} is negative: {value}")
    if value > MAX_AMOUNT:
        raise ValueError(f"{name} is too large: {value}")


def parse_quantity(text: str) -> int:
    value: Decimal = parse_decimal(text)
    if value != value.to_integral_value():
        raise ValueError(f"quantity is not a whole number: {text!r}")
    check_amount(value, "quantity")
    return int(value)


def row_to_sale(row: Sequence[str], columns: Mapping[str, int]) -> Sale:
    product: str = get_cell(row, columns, "product")
    if not product:
        raise ValueError("missing product")
    quantity: int = parse_quantity(get_cell(row, columns, "quantity"))
    unit_price: Decimal = parse_decimal(get_cell(row, columns, "unit_price"))

    check_amount(unit_price, "unit price")

    date_text: str = get_cell(row, columns, "date")
    sale_date: date | None = parse_date(date_text) if date_text else None
    if date_text and sale_date is None:
        LOGGER.debug("Unrecognized date %r", date_text)
    return Sale(
        sale_date=sale_date,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
    )


def parse_sales(path: Path) -> list[Sale]:
    text: str = read_text(path)
    delimiter: str = detect_delimiter(text)
    rows: list[list[str]] = list(
        csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    )
    numbered_rows: list[tuple[int, list[str]]] = [
        (number, row)
        for number, row in enumerate(rows, start=1)
        if any(cell.strip() for cell in row)
    ]
    if not numbered_rows:
        raise ParseError(f"no data found in {path.name}")
    columns: dict[str, int] = map_columns(numbered_rows[0][1])
    LOGGER.debug("Delimiter %r, columns %s", delimiter, columns)
    sales: list[Sale] = []
    skipped: int = 0
    for number, row in numbered_rows[1:]:
        try:
            sales.append(row_to_sale(row, columns))
        except ValueError as error:
            skipped += 1
            LOGGER.debug("Skipped row %d: %s", number, error)
    if skipped:
        LOGGER.warning(
            "Skipped %d invalid row(s) in %s (use -v for details)",
            skipped,
            path.name,
        )
    if not sales:
        raise ParseError(f"no valid sales found in {path.name}")
    LOGGER.info("Read %d sale(s) from %s", len(sales), path.name)
    return sales
