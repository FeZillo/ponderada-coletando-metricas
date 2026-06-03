from __future__ import annotations

import argparse
import json
from pathlib import Path

CONFIG_PATH = Path("experiment_config.json")

SCENARIOS: dict[str, dict[str, object]] = {
    "baseline": {
        "extra_case_count": 3,
        "slow_test_delay_seconds": 0.0,
        "force_failure": False,
        "variant_note": "Execucao base com cache habilitado e testes rapidos.",
    },
    "more-tests": {
        "extra_case_count": 25,
        "slow_test_delay_seconds": 0.0,
        "force_failure": False,
        "variant_note": "Aumento artificial da quantidade de testes parametrizados.",
    },
    "slow-tests": {
        "extra_case_count": 8,
        "slow_test_delay_seconds": 2.0,
        "force_failure": False,
        "variant_note": "Introducao de teste lento controlado.",
    },
    "failing-test": {
        "extra_case_count": 5,
        "slow_test_delay_seconds": 0.0,
        "force_failure": True,
        "variant_note": "Falha controlada para medir estabilidade do pipeline.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update experiment_config.json.")
    parser.add_argument("--list", action="store_true", help="List available scenarios.")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), help="Scenario to write.")
    parser.add_argument("--extra-case-count", type=int)
    parser.add_argument("--slow-test-delay-seconds", type=float)
    parser.add_argument("--force-failure", action="store_true")
    parser.add_argument("--no-force-failure", action="store_true")
    parser.add_argument("--variant-note")
    return parser.parse_args()


def load_current_config() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    if args.list:
        for name, values in SCENARIOS.items():
            print(f"{name}: {values['variant_note']}")
        return

    config = load_current_config()
    if args.scenario:
        config = {"scenario": args.scenario, **SCENARIOS[args.scenario]}

    if args.extra_case_count is not None:
        config["extra_case_count"] = args.extra_case_count
    if args.slow_test_delay_seconds is not None:
        config["slow_test_delay_seconds"] = args.slow_test_delay_seconds
    if args.force_failure:
        config["force_failure"] = True
    if args.no_force_failure:
        config["force_failure"] = False
    if args.variant_note:
        config["variant_note"] = args.variant_note

    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()

