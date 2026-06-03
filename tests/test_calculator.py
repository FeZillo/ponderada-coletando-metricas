from __future__ import annotations

import os
import time

import pytest

from pipeline_lab import moving_average, normalize_scores, rolling_checksum, summarize_orders


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def test_moving_average_handles_windowed_values():
    assert moving_average([10, 20, 30, 40], window_size=2) == [15, 25, 35]


def test_normalize_scores_handles_equal_values():
    assert normalize_scores([7, 7, 7]) == [1.0, 1.0, 1.0]


def test_summarize_orders_returns_business_metrics():
    orders = [
        {"item_count": 2, "unit_price": 10.0},
        {"item_count": 1, "unit_price": 50.0, "discount": 0.1},
    ]

    assert summarize_orders(orders) == {
        "count": 2,
        "gross_revenue": 65.0,
        "average_ticket": 32.5,
    }


def test_workload_case(case_index: int):
    slow_ms = _int_env("EXPERIMENT_SLOW_MS", 0)
    test_cases = max(_int_env("EXPERIMENT_TEST_CASES", 24), 1)
    force_failure = os.getenv("EXPERIMENT_FORCE_FAILURE", "false").lower() == "true"

    slow_interval = max(test_cases // 4, 1)
    if slow_ms > 0 and case_index % slow_interval == 0:
        time.sleep(slow_ms / 1000)

    values = [case_index, case_index + 3, case_index * 2 + 1, 42]
    checksum = rolling_checksum(values)

    assert 0 <= checksum < 9973

    if force_failure and case_index == test_cases - 1:
        pytest.fail("Falha controlada para medir comportamento do pipeline vermelho.")
