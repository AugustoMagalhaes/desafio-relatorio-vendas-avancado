from __future__ import annotations

from decimal import Decimal
from typing import Final

import pytest

from sales_cli.core import Report, Sale, summarize
from sales_cli.output import (
    NO_SALES_MESSAGE,
    format_money,
    format_text,
    quantize_money,
)

QUANTIZE_CASES: Final[list[tuple[str, str]]] = [
    ("10.005", "10.01"),
    ("10.004", "10.00"),
    ("2.675", "2.68"),
    ("0.125", "0.13"),
    ("10", "10.00"),
    ("0", "0.00"),
    ("1E+3", "1000.00"),
]

MONEY_CASES: Final[list[tuple[str, str]]] = [
    ("1234.5", "1234.50"),
    ("0", "0.00"),
    ("2.675", "2.68"),
    ("1E+3", "1000.00"),
    ("99.999", "100.00"),
]

EXPECTED_TEXT: Final[list[str]] = [
    "Product | Units | Revenue",
    "--------+-------+--------",
    "Monitor |     3 | 2700.00",
    "Mouse   |    10 |  100.00",
    "Cabo    |     1 |    5.50",
    "",
    "Grand total: 2805.50",
    "Best seller (units): Mouse (10 sold)",
    "Best seller (revenue): Monitor (2700.00)",
]


def make_sale(product: str, quantity: int, unit_price: str) -> Sale:
    return Sale(
        sale_date=None,
        product=product,
        quantity=quantity,
        unit_price=Decimal(unit_price),
    )


def make_report(sales: list[Sale]) -> Report:
    return summarize(sales)


@pytest.mark.parametrize(("value", "expected"), QUANTIZE_CASES)
def test_quantize_money_rounds_half_up(value: str, expected: str) -> None:
    assert str(quantize_money(Decimal(value))) == expected


@pytest.mark.parametrize(("value", "expected"), MONEY_CASES)
def test_format_money(value: str, expected: str) -> None:
    assert format_money(Decimal(value)) == expected


def test_format_text_without_sales() -> None:
    sales: list[Sale] = []
    report: Report = make_report(sales)
    assert format_text(report) == NO_SALES_MESSAGE


def test_format_text_full_report() -> None:
    sales: list[Sale] = [
        make_sale("Mouse", 10, "10.00"),
        make_sale("Monitor", 3, "900.00"),
        make_sale("Cabo", 1, "5.5"),
    ]
    report: Report = make_report(sales)
    assert format_text(report).splitlines() == EXPECTED_TEXT


def test_format_text_table_lines_have_the_same_width() -> None:
    sales: list[Sale] = [
        make_sale("Teclado Mecânico", 2, "150.00"),
        make_sale("Cabo", 100, "0.50"),
    ]
    report: Report = make_report(sales)
    table_size: int = 2 + len(report.products)
    table_lines: list[str] = format_text(report).splitlines()[:table_size]
    widths: set[int] = {len(line) for line in table_lines}
    assert len(widths) == 1


def test_format_text_rounds_only_on_output() -> None:
    sales: list[Sale] = [make_sale("Bala", 1, "0.005")]
    report: Report = make_report(sales)
    text: str = format_text(report)
    assert "Grand total: 0.01" in text
    assert report.grand_total == Decimal("0.005")


def test_format_text_single_unit_wording() -> None:
    sales: list[Sale] = [make_sale("Mouse", 1, "10.00")]
    report: Report = make_report(sales)
    assert "Best seller (units): Mouse (1 sold)" in format_text(report)
