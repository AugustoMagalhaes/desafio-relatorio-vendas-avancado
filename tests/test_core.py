from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from sales_cli.core import Sale


def make_sale(
    product: str = "Mouse",
    quantity: int = 1,
    unit_price: str = "10.00",
    sale_date: date | None = None,
) -> Sale:
    return Sale(
        sale_date=sale_date,
        product=product,
        quantity=quantity,
        unit_price=Decimal(unit_price),
    )


@pytest.mark.parametrize(
    ("quantity", "unit_price", "expected"),
    [
        (1, "10.00", "10.00"),
        (3, "10.00", "30.00"),
        (3, "0.10", "0.30"),
        (0, "99.99", "0.00"),
        (2, "1234.50", "2469.00"),
    ],
)
def test_total_multiplies_price_by_quantity(
    quantity: int, unit_price: str, expected: str
) -> None:
    sale: Sale = make_sale(quantity=quantity, unit_price=unit_price)
    assert sale.total == Decimal(expected)


def test_total_has_no_floating_point_error() -> None:
    sale: Sale = make_sale(quantity=3, unit_price="0.10")
    assert sale.total == Decimal("0.30")


def test_sale_allows_missing_date() -> None:
    sale: Sale = make_sale(sale_date=None)
    assert sale.sale_date is None


def test_sale_keeps_given_date() -> None:
    expected: date = date(2025, 3, 28)
    sale: Sale = make_sale(sale_date=expected)
    assert sale.sale_date == expected


def test_sales_with_same_values_are_equal() -> None:
    first: Sale = make_sale(product="Teclado", quantity=2, unit_price="50.00")
    second: Sale = make_sale(product="Teclado", quantity=2, unit_price="50.00")
    assert first == second


def test_sales_with_different_values_are_not_equal() -> None:
    first: Sale = make_sale(quantity=1)
    second: Sale = make_sale(quantity=2)
    assert first != second
