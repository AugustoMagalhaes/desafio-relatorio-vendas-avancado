from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Final

LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Sale:
    sale_date: date | None
    product: str
    quantity: int
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True, slots=True)
class ProductTotal:
    product: str
    quantity: int
    revenue: Decimal


@dataclass(frozen=True, slots=True)
class Report:
    products: tuple[ProductTotal, ...]
    grand_total: Decimal
    best_by_units: ProductTotal | None
    best_by_revenue: ProductTotal | None


def units_rank(item: ProductTotal) -> tuple[int, Decimal, str]:
    return (-item.quantity, -item.revenue, item.product.casefold())


def revenue_rank(item: ProductTotal) -> tuple[Decimal, str]:
    return (-item.revenue, item.product.casefold())


def summarize(sales: Sequence[Sale]) -> Report:
    totals: dict[str, ProductTotal] = {}

    for sale in sales:
        key: str = sale.product.casefold()
        current: ProductTotal | None = totals.get(key)
        if current is None:
            totals[key] = ProductTotal(
                product=sale.product,
                quantity=sale.quantity,
                revenue=sale.total,
            )
        else:
            totals[key] = ProductTotal(
                product=current.product,
                quantity=current.quantity + sale.quantity,
                revenue=current.revenue + sale.total,
            )

    products: tuple[ProductTotal, ...] = tuple(
        sorted(totals.values(), key=revenue_rank)
    )
    grand_total: Decimal = sum((item.revenue for item in products), Decimal(0))
    best_by_units: ProductTotal | None = min(products, key=units_rank, default=None)
    best_by_revenue: ProductTotal | None = products[0] if products else None

    return Report(
        products=products,
        grand_total=grand_total,
        best_by_units=best_by_units,
        best_by_revenue=best_by_revenue,
    )


def is_within(sale: Sale, start: date | None, end: date | None) -> bool:
    day: date | None = sale.sale_date

    if day is None:
        return False
    if start is not None and day < start:
        return False

    return end is None or day <= end


def filter_by_date(
    sales: Sequence[Sale], start: date | None, end: date | None
) -> list[Sale]:
    if start is None and end is None:
        return list(sales)

    undated: int = sum(1 for sale in sales if sale.sale_date is None)

    if undated == len(sales):
        LOGGER.warning("Date filter ignored: no sale has a recognized date")
        return list(sales)
    if undated:
        LOGGER.warning(
            "Excluded %d sale(s) without a recognized date from the filtered period",
            undated,
        )

    matching: list[Sale] = [sale for sale in sales if is_within(sale, start, end)]

    if not matching:
        LOGGER.warning("No sales match the selected period")

    LOGGER.info("Date filter kept %d of %d sale(s)", len(matching), len(sales))

    return matching
