from __future__ import annotations

import os


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def pytest_generate_tests(metafunc):
    if "case_index" not in metafunc.fixturenames:
        return

    test_cases = max(_int_env("EXPERIMENT_TEST_CASES", 24), 1)
    shard_count = max(_int_env("EXPERIMENT_SHARD_COUNT", 1), 1)
    shard_index = _int_env("EXPERIMENT_SHARD_INDEX", 0)
    selected_cases = [
        case_index for case_index in range(test_cases) if case_index % shard_count == shard_index
    ]

    metafunc.parametrize("case_index", selected_cases)
