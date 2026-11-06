from __future__ import annotations

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
    return f"{product:<{widths[0]}} | {units:>{widths[1]}} | {revenue:>{widths[2]}}"


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
