from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    item_count: int
    unit_price: float
    discount: float = 0.0

    @property
    def total(self) -> float:
        gross = self.item_count * self.unit_price
        return round(gross * (1 - self.discount), 2)


def moving_average(values: list[float], window_size: int) -> list[float]:
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    if not values:
        return []
    if window_size > len(values):
        return [round(sum(values) / len(values), 4)]

    averages: list[float] = []
    for index in range(len(values) - window_size + 1):
        window = values[index : index + window_size]
        averages.append(round(sum(window) / window_size, 4))
    return averages


def normalize_scores(values: list[float]) -> list[float]:
    if not values:
        return []

    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        return [1.0 for _ in values]

    return [round((value - minimum) / (maximum - minimum), 4) for value in values]


def rolling_checksum(values: list[int]) -> int:
    checksum = 0
    for index, value in enumerate(values, start=1):
        checksum = (checksum + index * value * 31) % 9973
    return checksum


def summarize_orders(raw_orders: list[dict[str, float]]) -> dict[str, float]:
    orders = [
        Order(
            item_count=int(order["item_count"]),
            unit_price=float(order["unit_price"]),
            discount=float(order.get("discount", 0.0)),
        )
        for order in raw_orders
    ]
    totals = [order.total for order in orders]
    return {
        "count": len(orders),
        "gross_revenue": round(sum(totals), 2),
        "average_ticket": round(sum(totals) / len(totals), 2) if totals else 0.0,
    }
