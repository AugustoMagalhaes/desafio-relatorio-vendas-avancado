from __future__ import annotations

import logging
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
    parse_sales,
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

TOO_LARGE_ROWS: Final[list[list[str]]] = [
    ["Mouse", "1e30", "10"],
    ["Mouse", "1", "1e30"],
    ["Mouse", "1000000001", "10"],
    ["Mouse", "1", "1000000001"],
]

VALID_CSV: Final[str] = (
    "data;produto;quantidade;preço unitário\n"
    "2025-03-01;Mouse;2;50,00\n"
    "01/03/2025;Teclado;1;150,00\n"
    ";Monitor;1;900,00\n"
)

INVALID_ROWS_CSV: Final[str] = (
    "produto,quantidade,preco\n"
    "Mouse,2,50.00\n"
    ",1,10.00\n"
    "Teclado,abc,150.00\n"
    "Monitor,1,900.00\n"
)

QUOTED_FIELD_CSV: Final[str] = 'produto,quantidade,preco\n"Cabo, USB",2,5.00\n'

BLANK_LINES_CSV: Final[str] = (
    "\nproduto,quantidade,preco\n\nMouse,2,50.00\n,,\nTeclado,1,150.00\n\n"
)

LATIN1_CSV: Final[str] = "produto;quantidade;preço\nTeclado Mecânico;1;150,00\n"

HEADER_ONLY_CSV: Final[str] = "produto,quantidade,preco\n"

ALL_INVALID_CSV: Final[str] = "produto,quantidade,preco\n,1,10\nMouse,x,10\n"

MISSING_COLUMNS_CSV: Final[str] = "a;b\n1;2\n"


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


@pytest.mark.parametrize("row", TOO_LARGE_ROWS)
def test_row_to_sale_rejects_values_above_the_limit(row: list[str]) -> None:
    with pytest.raises(ValueError, match="too large"):
        _ = row_to_sale(row, COLUMNS_WITHOUT_DATE)


def test_row_to_sale_accepts_values_at_the_limit() -> None:
    row: list[str] = ["Mouse", "1000000000", "1000000000"]
    sale: Sale = row_to_sale(row, COLUMNS_WITHOUT_DATE)
    assert sale.total == Decimal(10**18)


def write_csv(directory: Path, content: str, encoding: str = "utf-8") -> Path:
    path: Path = directory / "sales.csv"
    _ = path.write_bytes(content.encode(encoding))
    return path


def test_parse_sales_reads_dates_and_values(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, VALID_CSV)
    sales: list[Sale] = parse_sales(path)
    assert [sale.product for sale in sales] == ["Mouse", "Teclado", "Monitor"]
    assert [sale.sale_date for sale in sales] == [
        date(2025, 3, 1),
        date(2025, 3, 1),
        None,
    ]
    assert sales[0].unit_price == Decimal("50.00")


def test_parse_sales_supports_comma_delimiter(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, INVALID_ROWS_CSV)
    sales: list[Sale] = parse_sales(path)
    assert [sale.product for sale in sales] == ["Mouse", "Monitor"]


def test_parse_sales_supports_quoted_field_with_delimiter(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, QUOTED_FIELD_CSV)
    sales: list[Sale] = parse_sales(path)
    assert sales[0].product == "Cabo, USB"


def test_parse_sales_decodes_latin1_file(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, LATIN1_CSV, encoding="latin-1")
    sales: list[Sale] = parse_sales(path)
    assert sales[0].product == "Teclado Mecânico"


def test_parse_sales_ignores_blank_rows_without_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path: Path = write_csv(tmp_path, BLANK_LINES_CSV)
    with caplog.at_level(logging.DEBUG, logger="sales_cli.parser"):
        sales: list[Sale] = parse_sales(path)
    levels: list[int] = [record.levelno for record in caplog.records]
    assert len(sales) == 2
    assert logging.WARNING not in levels


def test_parse_sales_warns_once_and_details_at_debug(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path: Path = write_csv(tmp_path, INVALID_ROWS_CSV)
    with caplog.at_level(logging.DEBUG, logger="sales_cli.parser"):
        sales: list[Sale] = parse_sales(path)
    warnings: list[str] = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]
    details: list[str] = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.DEBUG and "Skipped row" in record.getMessage()
    ]
    assert len(sales) == 2
    assert len(warnings) == 1
    assert "Skipped 2" in warnings[0]
    assert len(details) == 2
    assert details[0].startswith("Skipped row 3")
    assert details[1].startswith("Skipped row 4")


def test_parse_sales_logs_summary_at_info(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path: Path = write_csv(tmp_path, VALID_CSV)
    with caplog.at_level(logging.INFO, logger="sales_cli.parser"):
        _ = parse_sales(path)
    messages: list[str] = [record.getMessage() for record in caplog.records]
    assert "Read 3 sale(s) from sales.csv" in messages


def test_parse_sales_raises_for_empty_file(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, "")
    with pytest.raises(ParseError, match="no data"):
        _ = parse_sales(path)


def test_parse_sales_raises_for_header_only_file(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, HEADER_ONLY_CSV)
    with pytest.raises(ParseError, match="no valid sales"):
        _ = parse_sales(path)


def test_parse_sales_raises_when_all_rows_are_invalid(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, ALL_INVALID_CSV)
    with pytest.raises(ParseError, match="no valid sales"):
        _ = parse_sales(path)


def test_parse_sales_raises_for_missing_columns(tmp_path: Path) -> None:
    path: Path = write_csv(tmp_path, MISSING_COLUMNS_CSV)
    with pytest.raises(ParseError, match="missing required columns"):
        _ = parse_sales(path)
