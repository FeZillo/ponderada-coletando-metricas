"""Small deterministic workload used by the CI/CD metrics experiment."""

from pipeline_lab.calculator import (
    moving_average,
    normalize_scores,
    rolling_checksum,
    summarize_orders,
)

__all__ = [
    "moving_average",
    "normalize_scores",
    "rolling_checksum",
    "summarize_orders",
]
