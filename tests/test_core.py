from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from sales_cli.core import ProductTotal, Report, Sale, summarize


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


def test_summarize_empty_sales() -> None:
    sales: list[Sale] = []
    report: Report = summarize(sales)
    assert report.products == ()
    assert report.grand_total == Decimal(0)
    assert report.best_by_units is None
    assert report.best_by_revenue is None


def test_summarize_single_sale() -> None:
    sales: list[Sale] = [make_sale(product="Mouse", quantity=2, unit_price="10.00")]
    expected: ProductTotal = ProductTotal(
        product="Mouse", quantity=2, revenue=Decimal("20.00")
    )
    report: Report = summarize(sales)
    assert report.products == (expected,)
    assert report.grand_total == Decimal("20.00")
    assert report.best_by_units == expected
    assert report.best_by_revenue == expected


def test_summarize_adds_sales_of_the_same_product() -> None:
    sales: list[Sale] = [
        make_sale(product="Mouse", quantity=2, unit_price="10.00"),
        make_sale(product="Mouse", quantity=3, unit_price="10.00"),
    ]
    report: Report = summarize(sales)
    assert report.products == (
        ProductTotal(product="Mouse", quantity=5, revenue=Decimal("50.00")),
    )


def test_summarize_groups_products_ignoring_case() -> None:
    sales: list[Sale] = [
        make_sale(product="Mouse", quantity=1),
        make_sale(product="mouse", quantity=1),
        make_sale(product="MOUSE", quantity=1),
    ]
    report: Report = summarize(sales)
    assert len(report.products) == 1
    assert report.products[0].product == "Mouse"
    assert report.products[0].quantity == 3


def test_summarize_grand_total_adds_all_products() -> None:
    sales: list[Sale] = [
        make_sale(product="Mouse", quantity=2, unit_price="10.00"),
        make_sale(product="Teclado", quantity=1, unit_price="150.00"),
    ]
    report: Report = summarize(sales)
    assert report.grand_total == Decimal("170.00")


def test_summarize_has_no_floating_point_error() -> None:
    sales: list[Sale] = [make_sale(quantity=1, unit_price="0.10") for _ in range(3)]
    report: Report = summarize(sales)
    assert report.grand_total == Decimal("0.30")


def test_summarize_orders_products_by_revenue_then_name() -> None:
    sales: list[Sale] = [
        make_sale(product="Zeta", quantity=1, unit_price="50.00"),
        make_sale(product="Alfa", quantity=1, unit_price="50.00"),
        make_sale(product="Beta", quantity=1, unit_price="100.00"),
    ]
    report: Report = summarize(sales)
    names: list[str] = [item.product for item in report.products]
    assert names == ["Beta", "Alfa", "Zeta"]


def test_best_by_units_can_differ_from_best_by_revenue() -> None:
    sales: list[Sale] = [
        make_sale(product="Cabo", quantity=10, unit_price="1.00"),
        make_sale(product="Monitor", quantity=1, unit_price="100.00"),
    ]
    report: Report = summarize(sales)
    assert report.best_by_units is not None
    assert report.best_by_revenue is not None
    assert report.best_by_units.product == "Cabo"
    assert report.best_by_revenue.product == "Monitor"


def test_best_by_units_tie_is_broken_by_revenue() -> None:
    sales: list[Sale] = [
        make_sale(product="Barato", quantity=2, unit_price="1.00"),
        make_sale(product="Caro", quantity=2, unit_price="5.00"),
    ]
    report: Report = summarize(sales)
    assert report.best_by_units is not None
    assert report.best_by_units.product == "Caro"


def test_best_by_units_full_tie_is_broken_by_name() -> None:
    sales: list[Sale] = [
        make_sale(product="Beta", quantity=2, unit_price="5.00"),
        make_sale(product="alfa", quantity=2, unit_price="5.00"),
    ]
    report: Report = summarize(sales)
    assert report.best_by_units is not None
    assert report.best_by_units.product == "alfa"
