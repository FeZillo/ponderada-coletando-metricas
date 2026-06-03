from __future__ import annotations

import argparse
import json
import os
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path


def parse_junit(path: Path) -> dict[str, float | int]:
    root = ET.parse(path).getroot()
    suites = list(root) if root.tag == "testsuites" else [root]

    tests = 0
    failures = 0
    errors = 0
    skipped = 0
    duration = 0.0

    for suite in suites:
        tests += int(suite.attrib.get("tests", 0))
        failures += int(suite.attrib.get("failures", 0))
        errors += int(suite.attrib.get("errors", 0))
        skipped += int(suite.attrib.get("skipped", 0))
        duration += float(suite.attrib.get("time", 0.0))

    executed = max(tests - skipped, 0)
    average = duration / executed if executed else 0.0

    return {
        "test_count": tests,
        "test_failures": failures + errors,
        "test_skipped": skipped,
        "test_duration": round(duration, 4),
        "test_avg_time": round(average, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract test metrics from a JUnit XML file.")
    parser.add_argument("--junit", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()

    metrics = parse_junit(args.junit)
    config = json.loads(args.config.read_text(encoding="utf-8"))

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run_id": os.getenv("GITHUB_RUN_ID", ""),
        "run_number": os.getenv("GITHUB_RUN_NUMBER", ""),
        "job": os.getenv("GITHUB_JOB", ""),
        "commit_sha": os.getenv("GITHUB_SHA", ""),
        "ref_name": os.getenv("GITHUB_REF_NAME", ""),
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "experiment": config,
        **metrics,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
