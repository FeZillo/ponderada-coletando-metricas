from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import requests

API_BASE_URL = "https://api.github.com"

METRICS_FIELDS = [
    "run_id",
    "run_number",
    "commit_sha",
    "commit_message",
    "status",
    "workflow_duration",
    "job_name",
    "job_duration",
    "test_count",
    "test_failures",
    "test_average_duration",
    "timestamp",
    "scenario",
    "html_url",
]

RUN_FIELDS = [
    "run_id",
    "run_number",
    "commit_sha",
    "commit_message",
    "status",
    "workflow_duration",
    "test_count",
    "test_failures",
    "test_average_duration",
    "timestamp",
    "scenario",
    "html_url",
]

STEP_FIELDS = [
    "run_id",
    "run_number",
    "job_name",
    "step_name",
    "status",
    "conclusion",
    "step_number",
    "step_duration",
    "started_at",
    "completed_at",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect GitHub Actions metrics.")
    parser.add_argument("--repo", required=True, help="Repository in owner/name format.")
    parser.add_argument("--workflow", default="ci-metrics.yml", help="Workflow file name or ID.")
    parser.add_argument("--limit", type=int, default=12, help="Number of runs to collect.")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN"))
    return parser.parse_args()


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_seconds(start: str | None, end: str | None) -> float:
    start_dt = parse_datetime(start)
    end_dt = parse_datetime(end)
    if start_dt is None or end_dt is None:
        return 0.0
    return round((end_dt - start_dt).total_seconds(), 3)


def github_get(session: requests.Session, path: str, params: dict[str, Any] | None = None) -> Any:
    url = path if path.startswith("https://") else f"{API_BASE_URL}{path}"
    response = session.get(url, params=params, timeout=60)
    response.raise_for_status()
    if response.content:
        return response.json()
    return {}


def fetch_runs(
    session: requests.Session,
    repo: str,
    workflow: str,
    limit: int,
) -> list[dict[str, Any]]:
    path = f"/repos/{repo}/actions/workflows/{workflow}/runs"
    payload = github_get(session, path, {"per_page": min(limit, 100)})
    return payload.get("workflow_runs", [])[:limit]


def fetch_jobs(session: requests.Session, repo: str, run_id: int) -> list[dict[str, Any]]:
    payload = github_get(session, f"/repos/{repo}/actions/runs/{run_id}/jobs", {"per_page": 100})
    return payload.get("jobs", [])


def read_test_metrics_from_artifact(
    session: requests.Session,
    repo: str,
    run_id: int,
) -> dict[str, Any]:
    payload = github_get(session, f"/repos/{repo}/actions/runs/{run_id}/artifacts")
    artifacts = payload.get("artifacts", [])
    matching_artifacts = [
        artifact
        for artifact in artifacts
        if artifact.get("name", "").startswith("pipeline-metrics-") and not artifact.get("expired")
    ]

    for artifact in matching_artifacts:
        response = session.get(artifact["archive_download_url"], timeout=60)
        response.raise_for_status()
        with ZipFile(BytesIO(response.content)) as archive:
            for filename in archive.namelist():
                if filename.endswith("test_metrics.json"):
                    with archive.open(filename) as file:
                        return json.load(file)

    return {
        "test_count": 0,
        "test_failures": 0,
        "test_average_duration": 0.0,
        "scenario": "artifact-not-found",
    }


def commit_message_for(run: dict[str, Any]) -> str:
    head_commit = run.get("head_commit") or {}
    message = head_commit.get("message") or run.get("display_title") or ""
    return message.splitlines()[0]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_rows(
    run: dict[str, Any],
    jobs: list[dict[str, Any]],
    test_metrics: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    status = run.get("conclusion") or run.get("status")
    run_id = run["id"]
    run_number = run.get("run_number")
    commit_sha = run.get("head_sha", "")
    timestamp = run.get("run_started_at") or run.get("created_at")
    workflow_duration = duration_seconds(timestamp, run.get("updated_at"))
    common_run = {
        "run_id": run_id,
        "run_number": run_number,
        "commit_sha": commit_sha,
        "commit_message": commit_message_for(run),
        "status": status,
        "workflow_duration": workflow_duration,
        "test_count": test_metrics.get("test_count", 0),
        "test_failures": test_metrics.get("test_failures", 0),
        "test_average_duration": test_metrics.get("test_average_duration", 0.0),
        "timestamp": timestamp,
        "scenario": test_metrics.get("scenario", "unknown"),
        "html_url": run.get("html_url", ""),
    }

    metric_rows = []
    step_rows = []
    for job in jobs:
        job_duration = duration_seconds(job.get("started_at"), job.get("completed_at"))
        metric_rows.append(
            {
                **common_run,
                "job_name": job.get("name"),
                "job_duration": job_duration,
            }
        )

        for step in job.get("steps", []):
            step_rows.append(
                {
                    "run_id": run_id,
                    "run_number": run_number,
                    "job_name": job.get("name"),
                    "step_name": step.get("name"),
                    "status": step.get("status"),
                    "conclusion": step.get("conclusion"),
                    "step_number": step.get("number"),
                    "step_duration": duration_seconds(
                        step.get("started_at"),
                        step.get("completed_at"),
                    ),
                    "started_at": step.get("started_at"),
                    "completed_at": step.get("completed_at"),
                }
            )

    return metric_rows, common_run, step_rows


def main() -> None:
    args = parse_args()
    session = requests.Session()
    session.headers.update({"Accept": "application/vnd.github+json"})
    if args.token:
        session.headers.update({"Authorization": f"Bearer {args.token}"})

    runs = fetch_runs(session, args.repo, args.workflow, args.limit)
    all_metric_rows: list[dict[str, Any]] = []
    all_run_rows: list[dict[str, Any]] = []
    all_step_rows: list[dict[str, Any]] = []
    raw_runs = []

    for run in runs:
        run_id = run["id"]
        jobs = fetch_jobs(session, args.repo, run_id)
        test_metrics = read_test_metrics_from_artifact(session, args.repo, run_id)
        metric_rows, run_row, step_rows = build_rows(run, jobs, test_metrics)
        all_metric_rows.extend(metric_rows)
        all_run_rows.append(run_row)
        all_step_rows.extend(step_rows)
        raw_runs.append({"run": run, "jobs": jobs, "test_metrics": test_metrics})
        print(f"Collected run {run_id} with {len(jobs)} jobs")

    write_csv(args.output_dir / "metrics.csv", METRICS_FIELDS, all_metric_rows)
    write_csv(args.output_dir / "run_summary.csv", RUN_FIELDS, all_run_rows)
    write_csv(args.output_dir / "steps.csv", STEP_FIELDS, all_step_rows)
    (args.output_dir / "raw_runs.json").write_text(
        json.dumps(raw_runs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote metrics to {args.output_dir}")


if __name__ == "__main__":
    main()

