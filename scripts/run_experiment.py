from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

VARIATIONS = [
    {
        "label": "baseline-rapido",
        "test_cases": 24,
        "slow_ms": 0,
        "force_failure": False,
        "shards": 1,
        "cache_version": "v1",
        "cache_miss_delay_seconds": 6,
        "notes": "Baseline com testes rapidos e execucao sequencial.",
    },
    {
        "label": "cache-aquecido",
        "test_cases": 24,
        "slow_ms": 0,
        "force_failure": False,
        "shards": 1,
        "cache_version": "v1",
        "cache_miss_delay_seconds": 6,
        "notes": "Repeticao do baseline para observar cache hit.",
    },
    {
        "label": "falha-controlada",
        "test_cases": 24,
        "slow_ms": 0,
        "force_failure": True,
        "shards": 1,
        "cache_version": "v1",
        "cache_miss_delay_seconds": 6,
        "notes": "Introducao de uma falha proposital em teste.",
    },
    {
        "label": "recuperacao-verde",
        "test_cases": 24,
        "slow_ms": 0,
        "force_failure": False,
        "shards": 1,
        "cache_version": "v1",
        "cache_miss_delay_seconds": 6,
        "notes": "Correcao da falha controlada.",
    },
    {
        "label": "mais-testes-60",
        "test_cases": 60,
        "slow_ms": 0,
        "force_failure": False,
        "shards": 1,
        "cache_version": "v1",
        "cache_miss_delay_seconds": 6,
        "notes": "Aumento artificial da quantidade de testes.",
    },
    {
        "label": "teste-lento",
        "test_cases": 60,
        "slow_ms": 250,
        "force_failure": False,
        "shards": 1,
        "cache_version": "v1",
        "cache_miss_delay_seconds": 6,
        "notes": "Introducao de testes lentos em parte dos casos.",
    },
    {
        "label": "cache-invalidado",
        "test_cases": 60,
        "slow_ms": 250,
        "force_failure": False,
        "shards": 1,
        "cache_version": "v2",
        "cache_miss_delay_seconds": 6,
        "notes": "Mudanca na chave de cache para provocar cache miss.",
    },
    {
        "label": "cache-v2-aquecido",
        "test_cases": 60,
        "slow_ms": 250,
        "force_failure": False,
        "shards": 1,
        "cache_version": "v2",
        "cache_miss_delay_seconds": 6,
        "notes": "Repeticao com cache v2 aquecido.",
    },
    {
        "label": "paralelo-2-shards",
        "test_cases": 60,
        "slow_ms": 250,
        "force_failure": False,
        "shards": 2,
        "cache_version": "v2",
        "cache_miss_delay_seconds": 6,
        "notes": "Divisao dos testes em dois jobs paralelos.",
    },
    {
        "label": "paralelo-3-shards",
        "test_cases": 90,
        "slow_ms": 250,
        "force_failure": False,
        "shards": 3,
        "cache_version": "v2",
        "cache_miss_delay_seconds": 6,
        "notes": "Carga maior dividida em tres shards paralelos.",
    },
    {
        "label": "falha-em-paralelo",
        "test_cases": 90,
        "slow_ms": 250,
        "force_failure": True,
        "shards": 3,
        "cache_version": "v2",
        "cache_miss_delay_seconds": 6,
        "notes": "Falha controlada em suite paralela.",
    },
    {
        "label": "final-verde",
        "test_cases": 90,
        "slow_ms": 100,
        "force_failure": False,
        "shards": 3,
        "cache_version": "v2",
        "cache_miss_delay_seconds": 6,
        "notes": "Configuracao final verde com paralelismo e lentidao reduzida.",
    },
]


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and push experiment commits.")
    parser.add_argument("--start-at", type=int, default=1, help="1-based variation index to start from.")
    parser.add_argument("--wait", action="store_true", help="Wait a short interval after each push.")
    parser.add_argument("--config", type=Path, default=Path("experiment_config.json"))
    args = parser.parse_args()

    for index, variation in enumerate(VARIATIONS[args.start_at - 1 :], start=args.start_at):
        args.config.write_text(json.dumps(variation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        run(["git", "add", str(args.config)])
        run(["git", "commit", "-m", f"experiment: run {index:02d} {variation['label']}"])
        run(["git", "push", "origin", "main"])
        if args.wait:
            time.sleep(20)


if __name__ == "__main__":
    main()
