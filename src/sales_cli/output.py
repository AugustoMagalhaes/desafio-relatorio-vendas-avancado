from __future__ import annotations

import json
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal
from typing import Final, TypeAlias

from sales_cli.core import ProductTotal, Report

Row: TypeAlias = tuple[str, str, str]

CENTS: Final[Decimal] = Decimal("0.01")
HEADER: Final[Row] = ("Product", "Units", "Revenue")
NO_SALES_MESSAGE: Final[str] = "No sales to report."


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def format_money(value: Decimal) -> str:
    return f"{quantize_money(value):.2f}"


def to_row(item: ProductTotal) -> Row:
    return (item.product, str(item.quantity), format_money(item.revenue))


def column_widths(rows: Sequence[Row]) -> tuple[int, int, int]:
    return (
        max(len(row[0]) for row in rows),
        max(len(row[1]) for row in rows),
        max(len(row[2]) for row in rows),
    )


def format_row(row: Row, widths: tuple[int, int, int]) -> str:
    product, units, revenue = row
    product_width, units_width, revenue_width = widths
    cells: list[str] = [
        f"{product:<{product_width}}",
        f"{units:>{units_width}}",
        f"{revenue:>{revenue_width}}",
    ]

    return " | ".join(cells)


def format_table(products: Sequence[ProductTotal]) -> list[str]:
    rows: list[Row] = [HEADER, *(to_row(item) for item in products)]
    widths: tuple[int, int, int] = column_widths(rows)
    separator: str = "-+-".join("-" * width for width in widths)
    lines: list[str] = [format_row(HEADER, widths), separator]
    lines.extend(format_row(row, widths) for row in rows[1:])

    return lines


def format_text(report: Report) -> str:
    best_units: ProductTotal | None = report.best_by_units
    best_revenue: ProductTotal | None = report.best_by_revenue

    if best_units is None or best_revenue is None:
        return NO_SALES_MESSAGE

    revenue_text: str = format_money(best_revenue.revenue)
    lines: list[str] = format_table(report.products)
    lines.extend(
        [
            "",
            f"Grand total: {format_money(report.grand_total)}",
            f"Best seller (units): {best_units.product} ({best_units.quantity} sold)",
            f"Best seller (revenue): {best_revenue.product} ({revenue_text})",
        ]
    )

    return "\n".join(lines)


def money_number(value: Decimal) -> float:
    return float(quantize_money(value))


def product_to_dict(item: ProductTotal) -> dict[str, object]:
    return {
        "product": item.product,
        "quantity": item.quantity,
        "revenue": money_number(item.revenue),
    }


def optional_product(item: ProductTotal | None) -> dict[str, object] | None:
    return None if item is None else product_to_dict(item)


def format_json(report: Report) -> str:
    payload: dict[str, object] = {
        "products": [product_to_dict(item) for item in report.products],
        "grand_total": money_number(report.grand_total),
        "best_seller_by_units": optional_product(report.best_by_units),
        "best_seller_by_revenue": optional_product(report.best_by_revenue),
    }

    return json.dumps(payload, indent=2, ensure_ascii=False)
