from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


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
