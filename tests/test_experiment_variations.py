from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "experiment_config.json"


def load_experiment_config() -> dict[str, object]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


CONFIG = load_experiment_config()
EXTRA_CASE_COUNT = int(CONFIG.get("extra_case_count", 0))


@pytest.mark.parametrize("case_index", range(EXTRA_CASE_COUNT))
def test_dynamic_book_shape_cases(client, case_index):
    books = client.get("/api/books").json()
    book = books[case_index % len(books)]

    assert isinstance(book["id"], int)
    assert book["title"]
    assert book["author"]
    assert book["status"] in {"to_read", "reading", "done"}


def test_optional_slow_case():
    delay_seconds = float(CONFIG.get("slow_test_delay_seconds", 0.0))

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    assert delay_seconds >= 0


def test_controlled_failure_flag_is_disabled():
    force_failure = bool(CONFIG.get("force_failure", False))

    assert not force_failure, "Controlled failure enabled in experiment_config.json"

