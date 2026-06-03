from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

STATUS_COLORS = {
    "success": "#2f7d6d",
    "failure": "#b44d4d",
    "cancelled": "#7a8496",
    "skipped": "#b28b2e",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CI/CD metrics charts.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--charts-dir", type=Path, default=Path("charts"))
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def save_figure(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    print(f"Saved {path}")


def plot_pipeline_duration(run_summary: pd.DataFrame, charts_dir: Path) -> None:
    if run_summary.empty:
        return

    df = run_summary.sort_values("timestamp")
    labels = df["run_number"].astype(str)
    colors = [STATUS_COLORS.get(status, "#4f6f9f") for status in df["status"]]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, df["workflow_duration"], color=colors)
    plt.title("Pipeline duration by run")
    plt.xlabel("Workflow run number")
    plt.ylabel("Duration (seconds)")
    plt.xticks(rotation=45, ha="right")
    save_figure(charts_dir / "pipeline_duration_by_run.png")


def plot_job_duration(metrics: pd.DataFrame, charts_dir: Path) -> None:
    if metrics.empty:
        return

    df = metrics.groupby("job_name", as_index=False)["job_duration"].mean()
    df = df.sort_values("job_duration", ascending=False)

    plt.figure(figsize=(9, 5))
    plt.barh(df["job_name"], df["job_duration"], color="#2f7d6d")
    plt.title("Average duration by job")
    plt.xlabel("Duration (seconds)")
    plt.gca().invert_yaxis()
    save_figure(charts_dir / "average_duration_by_job.png")


def plot_success_failure_rate(run_summary: pd.DataFrame, charts_dir: Path) -> None:
    if run_summary.empty:
        return

    counts = run_summary["status"].value_counts().sort_index()
    colors = [STATUS_COLORS.get(status, "#4f6f9f") for status in counts.index]

    plt.figure(figsize=(7, 5))
    plt.bar(counts.index, counts.values, color=colors)
    plt.title("Success and failure rate")
    plt.xlabel("Status")
    plt.ylabel("Runs")
    save_figure(charts_dir / "success_failure_rate.png")


def plot_tests_vs_duration(run_summary: pd.DataFrame, charts_dir: Path) -> None:
    if run_summary.empty:
        return

    plt.figure(figsize=(8, 5))
    colors = [STATUS_COLORS.get(status, "#4f6f9f") for status in run_summary["status"]]
    plt.scatter(run_summary["test_count"], run_summary["workflow_duration"], c=colors, s=90)
    plt.title("Tests count vs pipeline duration")
    plt.xlabel("Tests executed")
    plt.ylabel("Pipeline duration (seconds)")
    save_figure(charts_dir / "tests_vs_pipeline_duration.png")


def plot_slowest_steps(steps: pd.DataFrame, charts_dir: Path) -> None:
    if steps.empty:
        return

    df = steps.sort_values("step_duration", ascending=False).head(10)
    labels = df["job_name"].astype(str) + " / " + df["step_name"].astype(str)

    plt.figure(figsize=(10, 6))
    plt.barh(labels, df["step_duration"], color="#6b5dd3")
    plt.title("Slowest workflow steps")
    plt.xlabel("Duration (seconds)")
    plt.gca().invert_yaxis()
    save_figure(charts_dir / "slowest_steps.png")


def main() -> None:
    args = parse_args()
    metrics = read_csv(args.data_dir / "metrics.csv")
    run_summary = read_csv(args.data_dir / "run_summary.csv")
    steps = read_csv(args.data_dir / "steps.csv")

    if metrics.empty and run_summary.empty and steps.empty:
        raise SystemExit("No data found. Run collect_github_metrics.py first.")

    plot_pipeline_duration(run_summary, args.charts_dir)
    plot_job_duration(metrics, args.charts_dir)
    plot_success_failure_rate(run_summary, args.charts_dir)
    plot_tests_vs_duration(run_summary, args.charts_dir)
    plot_slowest_steps(steps, args.charts_dir)


if __name__ == "__main__":
    main()

