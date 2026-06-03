from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import requests
from requests import HTTPError as RequestsHTTPError

API_ROOT = "https://api.github.com"


@dataclass(frozen=True)
class GitHubClient:
    token: str | None

    def request_json(self, url: str) -> Any:
        with urlopen(self._request(url)) as response:
            return json.loads(response.read().decode("utf-8"))

    def request_bytes(self, url: str) -> bytes:
        response = requests.get(url, headers=self._headers(), allow_redirects=False, timeout=30)
        response.raise_for_status()

        redirect_url = response.headers.get("Location")
        if redirect_url:
            response = requests.get(redirect_url, timeout=60)
            response.raise_for_status()

        return response.content

    def _request(self, url: str) -> Request:
        return Request(url, headers=self._headers())

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ci-metrics-experiment",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


def iso_to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_seconds(start: str | None, end: str | None) -> float:
    start_dt = iso_to_datetime(start)
    end_dt = iso_to_datetime(end)
    if not start_dt or not end_dt:
        return 0.0
    return round((end_dt - start_dt).total_seconds(), 3)


def discover_repo() -> str:
    remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", remote)
    if not match:
        raise SystemExit("Unable to infer GitHub repository. Pass --repo OWNER/REPO.")
    return f"{match.group('owner')}/{match.group('repo')}"


def list_runs(client: GitHubClient, repo: str, workflow: str, limit: int) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    page = 1
    while len(runs) < limit:
        url = (
            f"{API_ROOT}/repos/{repo}/actions/workflows/{workflow}/runs"
            f"?branch=main&per_page=100&page={page}"
        )
        payload = client.request_json(url)
        batch = payload.get("workflow_runs", [])
        if not batch:
            break
        runs.extend(batch)
        page += 1
    return runs[:limit]


def list_jobs(client: GitHubClient, repo: str, run_id: int) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    page = 1
    while True:
        url = f"{API_ROOT}/repos/{repo}/actions/runs/{run_id}/jobs?filter=all&per_page=100&page={page}"
        payload = client.request_json(url)
        batch = payload.get("jobs", [])
        if not batch:
            break
        jobs.extend(batch)
        page += 1
    return jobs


def download_test_artifacts(client: GitHubClient, repo: str, run_id: int) -> list[dict[str, Any]]:
    url = f"{API_ROOT}/repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100"
    artifacts = client.request_json(url).get("artifacts", [])
    metrics: list[dict[str, Any]] = []

    for artifact in artifacts:
        if not artifact.get("name", "").startswith("pipeline-metrics-"):
            continue
        try:
            archive = client.request_bytes(artifact["archive_download_url"])
        except (HTTPError, RequestsHTTPError):
            continue
        with zipfile.ZipFile(BytesIO(archive)) as zipped:
            for member in zipped.namelist():
                if member.endswith("pipeline-metrics.json"):
                    with zipped.open(member) as handle:
                        metrics.append(json.loads(handle.read().decode("utf-8")))
    return metrics


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def first_line(message: str | None) -> str:
    return (message or "").splitlines()[0]


def build_rows(
    client: GitHubClient,
    repo: str,
    runs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    job_rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []
    run_rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []

    for run in runs:
        run_id = run["id"]
        jobs = list_jobs(client, repo, run_id)
        artifacts = download_test_artifacts(client, repo, run_id)
        raw_rows.append({"run": run, "jobs": jobs, "artifacts": artifacts})

        test_count = sum(int(item.get("test_count", 0)) for item in artifacts)
        test_failures = sum(int(item.get("test_failures", 0)) for item in artifacts)
        test_duration = sum(float(item.get("test_duration", 0.0)) for item in artifacts)
        test_avg_time = round(test_duration / test_count, 6) if test_count else 0.0
        experiment_labels = sorted(
            {item.get("experiment", {}).get("label", "") for item in artifacts if item.get("experiment")}
        )
        experiment_label = ", ".join(label for label in experiment_labels if label)

        head_commit = run.get("head_commit") or {}
        commit_message = first_line(head_commit.get("message") or run.get("display_title"))
        workflow_duration = duration_seconds(run.get("run_started_at"), run.get("updated_at"))
        status = run.get("conclusion") or run.get("status")

        run_row = {
            "run_id": run_id,
            "run_number": run.get("run_number"),
            "commit_sha": run.get("head_sha"),
            "commit_message": commit_message,
            "status": status,
            "workflow_duration": workflow_duration,
            "test_count": test_count,
            "test_failures": test_failures,
            "test_avg_time": test_avg_time,
            "timestamp": run.get("run_started_at") or run.get("created_at"),
            "html_url": run.get("html_url"),
            "experiment_label": experiment_label,
        }
        run_rows.append(run_row)

        for job in jobs:
            job_duration = duration_seconds(job.get("started_at"), job.get("completed_at"))
            job_row = {
                **run_row,
                "job_name": job.get("name"),
                "job_status": job.get("conclusion") or job.get("status"),
                "job_duration": job_duration,
                "job_started_at": job.get("started_at"),
                "job_completed_at": job.get("completed_at"),
            }
            job_rows.append(job_row)

            for step in job.get("steps", []):
                step_rows.append(
                    {
                        "run_id": run_id,
                        "run_number": run.get("run_number"),
                        "commit_sha": run.get("head_sha"),
                        "commit_message": commit_message,
                        "status": status,
                        "workflow_duration": workflow_duration,
                        "job_name": job.get("name"),
                        "step_name": step.get("name"),
                        "step_status": step.get("conclusion") or step.get("status"),
                        "step_duration": duration_seconds(
                            step.get("started_at"), step.get("completed_at")
                        ),
                        "timestamp": step.get("started_at"),
                        "html_url": run.get("html_url"),
                        "experiment_label": experiment_label,
                    }
                )

    return run_rows, job_rows, step_rows, raw_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect CI metrics from GitHub Actions.")
    parser.add_argument("--repo", default=None, help="GitHub repository in OWNER/REPO format.")
    parser.add_argument("--workflow", default="ci-metrics.yml", help="Workflow file name or id.")
    parser.add_argument("--limit", type=int, default=30, help="Maximum number of recent runs to collect.")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN"))
    args = parser.parse_args()

    repo = args.repo or discover_repo()
    token = args.token
    if not token:
        token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()

    client = GitHubClient(token=token)
    runs = list_runs(client, repo, args.workflow, args.limit)
    if not runs:
        raise SystemExit("No workflow runs found.")

    run_rows, job_rows, step_rows, raw_rows = build_rows(client, repo, runs)

    write_csv(
        args.output_dir / "run_summary.csv",
        run_rows,
        [
            "run_id",
            "run_number",
            "commit_sha",
            "commit_message",
            "status",
            "workflow_duration",
            "test_count",
            "test_failures",
            "test_avg_time",
            "timestamp",
            "html_url",
            "experiment_label",
        ],
    )
    write_csv(
        args.output_dir / "metrics.csv",
        job_rows,
        [
            "run_id",
            "run_number",
            "commit_sha",
            "commit_message",
            "status",
            "workflow_duration",
            "job_name",
            "job_status",
            "job_duration",
            "test_count",
            "test_failures",
            "test_avg_time",
            "timestamp",
            "html_url",
            "experiment_label",
            "job_started_at",
            "job_completed_at",
        ],
    )
    write_csv(
        args.output_dir / "steps.csv",
        step_rows,
        [
            "run_id",
            "run_number",
            "commit_sha",
            "commit_message",
            "status",
            "workflow_duration",
            "job_name",
            "step_name",
            "step_status",
            "step_duration",
            "timestamp",
            "html_url",
            "experiment_label",
        ],
    )
    (args.output_dir / "raw_runs.json").write_text(
        json.dumps(raw_rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Collected {len(run_rows)} runs, {len(job_rows)} jobs and {len(step_rows)} steps.")


if __name__ == "__main__":
    main()
