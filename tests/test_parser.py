from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest

from sales_cli.core import Sale
from sales_cli.parser import (
    ParseError,
    detect_delimiter,
    map_columns,
    read_text,
    row_to_sale,
)

SAMPLE_TEXT: Final[str] = "produto;preço unitário;ação"

COLUMNS: Final[dict[str, int]] = {
    "date": 0,
    "product": 1,
    "quantity": 2,
    "unit_price": 3,
}
COLUMNS_WITHOUT_DATE: Final[dict[str, int]] = {
    "product": 0,
    "quantity": 1,
    "unit_price": 2,
}

ENCODINGS_UNDER_TEST: Final[list[str]] = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]

DELIMITER_CASES: Final[list[tuple[str, str]]] = [
    ("a;b;c", ";"),
    ("a,b,c", ","),
    ("a\tb\tc", "\t"),
    ("abc", ","),
    ("", ","),
    ("\n\nproduto;quantidade", ";"),
    ("a;b,c;d", ";"),
    ("a,b;c,d", ","),
]

UNUSABLE_DATES: Final[list[str]] = ["", "   ", "28 de março de 2025", "abc"]

PRICE_CASES: Final[list[tuple[str, str]]] = [
    ("10,5", "10.5"),
    ("1.234,50", "1234.50"),
    ("1234.50", "1234.50"),
]

INVALID_ROWS: Final[list[list[str]]] = [
    ["", "1", "10"],
    ["Mouse", "abc", "10"],
    ["Mouse", "1.5", "10"],
    ["Mouse", "-1", "10"],
    ["Mouse", "1", "abc"],
    ["Mouse", "1", "-10"],
    ["Mouse", "1"],
    [],
]


@pytest.mark.parametrize("encoding", ENCODINGS_UNDER_TEST)
def test_read_text_decodes_supported_encodings(tmp_path: Path, encoding: str) -> None:
    path: Path = tmp_path / "sales.csv"
    content: bytes = SAMPLE_TEXT.encode(encoding)
    _ = path.write_bytes(content)
    assert read_text(path) == SAMPLE_TEXT


def test_read_text_removes_utf8_bom(tmp_path: Path) -> None:
    path: Path = tmp_path / "sales.csv"
    content: bytes = SAMPLE_TEXT.encode("utf-8-sig")
    _ = path.write_bytes(content)
    assert not read_text(path).startswith("\ufeff")


def test_read_text_falls_back_to_latin1_for_undefined_cp1252_bytes(
    tmp_path: Path,
) -> None:
    path: Path = tmp_path / "sales.csv"
    content: bytes = b"abc\x81"
    _ = path.write_bytes(content)
    assert read_text(path) == "abc\x81"


def test_read_text_raises_for_missing_file(tmp_path: Path) -> None:
    path: Path = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError):
        _ = read_text(path)


@pytest.mark.parametrize(("text", "expected"), DELIMITER_CASES)
def test_detect_delimiter(text: str, expected: str) -> None:
    assert detect_delimiter(text) == expected


def test_map_columns_with_portuguese_header() -> None:
    header: list[str] = ["Data", "Produto", "Quantidade", "Preço Unitário"]
    assert map_columns(header) == COLUMNS


def test_map_columns_with_english_header() -> None:
    header: list[str] = ["date", "product", "quantity", "price"]
    assert map_columns(header) == COLUMNS


def test_map_columns_ignores_case_accents_and_spacing() -> None:
    header: list[str] = [" PRODUTO ", "QTD", "PREÇO  UNITÁRIO"]
    assert map_columns(header) == COLUMNS_WITHOUT_DATE


def test_map_columns_is_independent_of_column_order() -> None:
    header: list[str] = ["preco_unitario", "quantidade", "produto"]
    expected: dict[str, int] = {"unit_price": 0, "quantity": 1, "product": 2}
    assert map_columns(header) == expected


def test_map_columns_ignores_extra_columns() -> None:
    header: list[str] = ["id", "produto", "obs", "qtd", "preco"]
    expected: dict[str, int] = {"product": 1, "quantity": 3, "unit_price": 4}
    assert map_columns(header) == expected


def test_map_columns_date_is_optional() -> None:
    header: list[str] = ["produto", "quantidade", "preco"]
    columns: dict[str, int] = map_columns(header)
    assert "date" not in columns


def test_map_columns_reports_missing_required_columns() -> None:
    header: list[str] = ["data", "produto"]
    with pytest.raises(ParseError, match="quantity, unit_price"):
        _ = map_columns(header)


def test_row_to_sale_with_all_fields() -> None:
    row: list[str] = ["2025-03-28", "Mouse", "2", "10.50"]
    expected: Sale = Sale(
        sale_date=date(2025, 3, 28),
        product="Mouse",
        quantity=2,
        unit_price=Decimal("10.50"),
    )
    assert row_to_sale(row, COLUMNS) == expected


def test_row_to_sale_without_date_column() -> None:
    row: list[str] = ["Mouse", "2", "10.50"]
    sale: Sale = row_to_sale(row, COLUMNS_WITHOUT_DATE)
    assert sale.sale_date is None


@pytest.mark.parametrize("date_text", UNUSABLE_DATES)
def test_row_to_sale_without_usable_date(date_text: str) -> None:
    row: list[str] = [date_text, "Mouse", "2", "10.50"]
    sale: Sale = row_to_sale(row, COLUMNS)
    assert sale.sale_date is None


@pytest.mark.parametrize(("price_text", "expected"), PRICE_CASES)
def test_row_to_sale_parses_price_formats(price_text: str, expected: str) -> None:
    row: list[str] = ["Mouse", "1", price_text]
    sale: Sale = row_to_sale(row, COLUMNS_WITHOUT_DATE)
    assert sale.unit_price == Decimal(expected)


def test_row_to_sale_accepts_integer_quantity_written_as_decimal() -> None:
    row: list[str] = ["Mouse", "3.0", "10"]
    sale: Sale = row_to_sale(row, COLUMNS_WITHOUT_DATE)
    assert sale.quantity == 3


def test_row_to_sale_strips_whitespace() -> None:
    row: list[str] = ["  Mouse  ", " 2 ", " 10 "]
    sale: Sale = row_to_sale(row, COLUMNS_WITHOUT_DATE)
    assert sale.product == "Mouse"


@pytest.mark.parametrize("row", INVALID_ROWS)
def test_row_to_sale_rejects_invalid_rows(row: list[str]) -> None:
    with pytest.raises(ValueError):
        _ = row_to_sale(row, COLUMNS_WITHOUT_DATE)
