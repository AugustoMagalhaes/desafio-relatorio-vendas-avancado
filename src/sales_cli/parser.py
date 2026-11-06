from __future__ import annotations

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


def parse_quantity(text: str) -> int:
    value: Decimal = parse_decimal(text)
    if value != value.to_integral_value():
        raise ValueError(f"quantity is not a whole number: {text!r}")
    if value < 0:
        raise ValueError(f"quantity is negative: {text!r}")
    return int(value)


def row_to_sale(row: Sequence[str], columns: Mapping[str, int]) -> Sale:
    product: str = get_cell(row, columns, "product")
    if not product:
        raise ValueError("missing product")
    quantity: int = parse_quantity(get_cell(row, columns, "quantity"))
    unit_price: Decimal = parse_decimal(get_cell(row, columns, "unit_price"))
    if unit_price < 0:
        raise ValueError("unit price is negative")
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
