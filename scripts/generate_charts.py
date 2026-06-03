from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def short_sha(value: str) -> str:
    return value[:7] if value else ""


def save_pipeline_duration(rows: list[dict[str, str]], output_dir: Path) -> None:
    ordered = list(reversed(rows))
    labels = [f"#{row['run_number']}\n{short_sha(row['commit_sha'])}" for row in ordered]
    values = [as_float(row["workflow_duration"]) for row in ordered]
    colors = ["#2a9d8f" if row["status"] == "success" else "#e76f51" for row in ordered]

    plt.figure(figsize=(13, 6))
    plt.bar(labels, values, color=colors)
    plt.ylabel("Duracao total (s)")
    plt.xlabel("Execucao")
    plt.title("Tempo total do pipeline por execucao")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_dir / "pipeline_duration_by_run.png", dpi=160)
    plt.close()


def save_job_duration(rows: list[dict[str, str]], output_dir: Path) -> None:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[row["job_name"]].append(as_float(row["job_duration"]))

    names = sorted(grouped)
    averages = [sum(grouped[name]) / len(grouped[name]) for name in names]

    plt.figure(figsize=(12, 6))
    plt.barh(names, averages, color="#457b9d")
    plt.xlabel("Duracao media (s)")
    plt.title("Tempo medio por job")
    plt.tight_layout()
    plt.savefig(output_dir / "average_duration_by_job.png", dpi=160)
    plt.close()


def save_status_rate(rows: list[dict[str, str]], output_dir: Path) -> None:
    counts = Counter(row["status"] for row in rows)
    labels = list(counts)
    values = [counts[label] for label in labels]
    colors = ["#2a9d8f" if label == "success" else "#e76f51" for label in labels]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, values, color=colors)
    plt.ylabel("Quantidade de execucoes")
    plt.title("Taxa de sucesso e falha")
    for index, value in enumerate(values):
        plt.text(index, value + 0.05, str(value), ha="center")
    plt.tight_layout()
    plt.savefig(output_dir / "success_failure_rate.png", dpi=160)
    plt.close()


def save_tests_vs_duration(rows: list[dict[str, str]], output_dir: Path) -> None:
    test_counts = [as_float(row["test_count"]) for row in rows]
    durations = [as_float(row["workflow_duration"]) for row in rows]
    colors = ["#2a9d8f" if row["status"] == "success" else "#e76f51" for row in rows]

    plt.figure(figsize=(10, 6))
    plt.scatter(test_counts, durations, c=colors, s=90, alpha=0.85, edgecolors="#1d1d1d")
    plt.xlabel("Quantidade de testes")
    plt.ylabel("Duracao total do pipeline (s)")
    plt.title("Relacao entre quantidade de testes e duracao do pipeline")
    for row, x_value, y_value in zip(rows, test_counts, durations, strict=False):
        plt.annotate(f"#{row['run_number']}", (x_value, y_value), textcoords="offset points", xytext=(6, 6))
    plt.tight_layout()
    plt.savefig(output_dir / "tests_vs_pipeline_duration.png", dpi=160)
    plt.close()


def save_step_duration(rows: list[dict[str, str]], output_dir: Path) -> None:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        name = f"{row['job_name']} / {row['step_name']}"
        duration = as_float(row["step_duration"])
        if duration > 0:
            grouped[name].append(duration)

    averages = sorted(
        ((sum(values) / len(values), name) for name, values in grouped.items()),
        reverse=True,
    )[:12]

    plt.figure(figsize=(12, 7))
    plt.barh([name for _, name in averages], [value for value, _ in averages], color="#8d99ae")
    plt.xlabel("Duracao media (s)")
    plt.title("Etapas mais caras do pipeline")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_dir / "slowest_steps.png", dpi=160)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate charts for CI/CD metrics.")
    parser.add_argument("--input", type=Path, default=Path("data/run_summary.csv"))
    parser.add_argument("--jobs", type=Path, default=Path("data/metrics.csv"))
    parser.add_argument("--steps", type=Path, default=Path("data/steps.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("charts"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_rows = read_csv(args.input)
    job_rows = read_csv(args.jobs)
    step_rows = read_csv(args.steps)

    save_pipeline_duration(run_rows, args.output_dir)
    save_job_duration(job_rows, args.output_dir)
    save_status_rate(run_rows, args.output_dir)
    save_tests_vs_duration(run_rows, args.output_dir)
    save_step_duration(step_rows, args.output_dir)
    print(f"Charts written to {args.output_dir}")


if __name__ == "__main__":
    main()
