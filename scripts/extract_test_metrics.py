from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract test metrics from a JUnit XML file.")
    parser.add_argument("junit_xml", type=Path)
    parser.add_argument("output_json", type=Path)
    return parser.parse_args()


def load_experiment_config(project_root: Path) -> dict[str, object]:
    config_path = project_root / "experiment_config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def build_empty_metrics(project_root: Path, reason: str) -> dict[str, object]:
    config = load_experiment_config(project_root)
    return {
        "status": "missing",
        "reason": reason,
        "test_count": 0,
        "test_failures": 0,
        "test_errors": 0,
        "test_skipped": 0,
        "test_total_duration": 0.0,
        "test_average_duration": 0.0,
        "scenario": config.get("scenario", "unknown"),
        "variant_note": config.get("variant_note", ""),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def extract_metrics(junit_xml: Path, project_root: Path) -> dict[str, object]:
    if not junit_xml.exists():
        return build_empty_metrics(project_root, "JUnit XML file not found")

    root = ElementTree.parse(junit_xml).getroot()
    cases = list(root.iter("testcase"))
    case_times = [float(case.attrib.get("time", 0.0)) for case in cases]
    failures = sum(1 for case in cases if case.find("failure") is not None)
    errors = sum(1 for case in cases if case.find("error") is not None)
    skipped = sum(1 for case in cases if case.find("skipped") is not None)
    total_duration = round(sum(case_times), 4)
    test_count = len(cases)
    average_duration = round(total_duration / test_count, 4) if test_count else 0.0
    config = load_experiment_config(project_root)

    return {
        "status": "collected",
        "test_count": test_count,
        "test_failures": failures + errors,
        "test_errors": errors,
        "test_skipped": skipped,
        "test_total_duration": total_duration,
        "test_average_duration": average_duration,
        "scenario": config.get("scenario", "unknown"),
        "variant_note": config.get("variant_note", ""),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    args = parse_args()
    project_root = Path.cwd()
    metrics = extract_metrics(args.junit_xml, project_root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

