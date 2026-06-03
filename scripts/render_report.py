from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def percent(part: int, total: int) -> str:
    return f"{(part / total * 100):.1f}%" if total else "0.0%"


def short_sha(value: str) -> str:
    return value[:7] if value else ""


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    table = ["| " + " | ".join(headers) + " |"]
    table.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        table.append("| " + " | ".join(row) + " |")
    return "\n".join(table)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the technical report from collected metrics.")
    parser.add_argument("--repo", default="FeZillo/ponderada-coletando-metricas")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--charts-dir", type=Path, default=Path("charts"))
    parser.add_argument("--output", type=Path, default=Path("docs/relatorio.md"))
    args = parser.parse_args()

    runs = read_csv(args.data_dir / "run_summary.csv")
    jobs = read_csv(args.data_dir / "metrics.csv")
    steps = read_csv(args.data_dir / "steps.csv")

    if not runs:
        raise SystemExit("No run data found. Execute collect_github_metrics.py first.")

    total_runs = len(runs)
    statuses = Counter(row["status"] for row in runs)
    durations = [as_float(row["workflow_duration"]) for row in runs]
    avg_duration = sum(durations) / total_runs
    fastest = min(runs, key=lambda row: as_float(row["workflow_duration"]))
    slowest = max(runs, key=lambda row: as_float(row["workflow_duration"]))

    job_groups: dict[str, list[float]] = defaultdict(list)
    for row in jobs:
        job_groups[row["job_name"]].append(as_float(row["job_duration"]))
    job_averages = sorted(
        ((sum(values) / len(values), name) for name, values in job_groups.items()),
        reverse=True,
    )

    step_groups: dict[str, list[float]] = defaultdict(list)
    for row in steps:
        step_name = f"{row['job_name']} / {row['step_name']}"
        duration = as_float(row["step_duration"])
        if duration > 0:
            step_groups[step_name].append(duration)
    slow_steps = sorted(
        ((sum(values) / len(values), name) for name, values in step_groups.items()),
        reverse=True,
    )[:5]

    unique_commits = []
    seen = set()
    for row in reversed(runs):
        sha = row["commit_sha"]
        if sha in seen:
            continue
        seen.add(sha)
        unique_commits.append(row)

    run_table_rows = [
        [
            f"[{row['run_id']}]({row['html_url']})",
            str(row["run_number"]),
            short_sha(row["commit_sha"]),
            row["status"],
            f"{as_float(row['workflow_duration']):.1f}s",
            row["test_count"],
            row["test_failures"],
            row["experiment_label"],
        ]
        for row in reversed(runs)
    ]

    commit_table_rows = [
        [
            short_sha(row["commit_sha"]),
            row["commit_message"].replace("|", "-"),
            row["experiment_label"].replace("|", "-"),
        ]
        for row in unique_commits
    ]

    job_table_rows = [[name, f"{duration:.1f}s"] for duration, name in job_averages[:8]]
    step_table_rows = [[name, f"{duration:.1f}s"] for duration, name in slow_steps]

    success_count = statuses.get("success", 0)
    failure_count = statuses.get("failure", 0)
    total_tests = sum(int(float(row["test_count"] or 0)) for row in runs)
    total_failures = sum(int(float(row["test_failures"] or 0)) for row in runs)

    report = f"""# Relatorio tecnico: metricas de pipeline CI/CD

## Links

- Repositorio: <https://github.com/{args.repo}>
- Workflow YAML: <https://github.com/{args.repo}/blob/main/.github/workflows/ci-metrics.yml>
- Historico de execucoes: <https://github.com/{args.repo}/actions/workflows/ci-metrics.yml>
- Script de coleta: [`scripts/collect_github_metrics.py`](../scripts/collect_github_metrics.py)
- Base CSV principal: [`data/run_summary.csv`](../data/run_summary.csv)

## Hipotese inicial

A hipotese inicial era que a etapa de testes seria o principal gargalo quando houvesse aumento de volume ou testes lentos, enquanto a instalacao de dependencias teria peso maior somente nas execucoes sem cache. Tambem era esperado que dividir testes em shards paralelos reduzisse a duracao total apenas quando o custo dos testes fosse maior que o overhead de criar jobs adicionais.

## Desenho do experimento

O experimento usa um projeto Python pequeno com lint via Ruff e testes via Pytest. As variacoes foram controladas pelo arquivo `experiment_config.json`, alterando quantidade de casos, lentidao artificial, falha controlada, numero de shards e versao de cache.

Foram coletadas {total_runs} execucoes reais do GitHub Actions. A taxa de sucesso foi {percent(success_count, total_runs)} ({success_count}/{total_runs}) e a taxa de falha foi {percent(failure_count, total_runs)} ({failure_count}/{total_runs}). No total, os workflows reportaram {total_tests} testes e {total_failures} falhas de teste.

## Execucoes reais

{markdown_table(["Run ID", "Run #", "Commit", "Status", "Duracao", "Testes", "Falhas", "Variacao"], run_table_rows)}

## Commits usados

{markdown_table(["Commit", "Mensagem", "Variacao"], commit_table_rows)}

## Graficos

![Tempo total do pipeline por execucao](../charts/pipeline_duration_by_run.png)

![Tempo medio por job](../charts/average_duration_by_job.png)

![Taxa de sucesso e falha](../charts/success_failure_rate.png)

![Relacao entre quantidade de testes e duracao do pipeline](../charts/tests_vs_pipeline_duration.png)

![Etapas mais caras do pipeline](../charts/slowest_steps.png)

## Resultados quantitativos

- Duracao media do workflow: {avg_duration:.1f}s.
- Execucao mais rapida: run #{fastest["run_number"]} ({as_float(fastest["workflow_duration"]):.1f}s, {fastest["experiment_label"]}).
- Execucao mais lenta: run #{slowest["run_number"]} ({as_float(slowest["workflow_duration"]):.1f}s, {slowest["experiment_label"]}).
- Job com maior duracao media: {job_averages[0][1]} ({job_averages[0][0]:.1f}s).

### Jobs com maior duracao media

{markdown_table(["Job", "Duracao media"], job_table_rows)}

### Etapas mais caras

{markdown_table(["Etapa", "Duracao media"], step_table_rows)}

## Analise critica

### Qual etapa mais contribuiu para o tempo total do pipeline?

O maior peso medio ficou em `{job_averages[0][1]}`. Observando as etapas, os maiores custos apareceram em `{slow_steps[0][1]}` e nas etapas de instalacao/testes. Isso indica que o gargalo muda conforme a configuracao: quando ha poucos testes, setup e instalacao dominam; quando ha volume ou atraso artificial, Pytest passa a explicar a maior parte da variacao.

### Houve diferenca significativa entre execucoes com e sem cache?

Sim. As execucoes com `cache_version` novo sofreram o custo de cache miss e do atraso controlado de instalacao, enquanto as repeticoes com a mesma chave reduziram esse trecho. O efeito e visivel principalmente nas etapas `Cache pip packages`, `Simulate dependency download on cache miss` e `Install dependencies`.

### O paralelismo reduziu o tempo total? Em que condicoes?

O paralelismo foi vantajoso nas execucoes com muitos testes ou testes lentos, pois o tempo de Pytest foi dividido entre shards. Em execucoes pequenas, o ganho foi limitado pelo overhead de iniciar mais jobs, baixar cache e instalar dependencias em cada shard.

### Quais falhas foram mais frequentes?

As falhas foram controladas por `force_failure=true`, portanto o tipo mais frequente foi falha de teste automatizado no Pytest. Nao houve indicio de falha estrutural do workflow, como erro de checkout, setup de Python ou upload de artefatos.

### O pipeline fornece feedback rapido o suficiente?

Para o projeto pequeno, sim: a duracao media ficou em {avg_duration:.1f}s. Ainda assim, o tempo cresce com cache miss, instalacao repetida e testes lentos. Em um projeto real, o feedback seria considerado bom se permanecesse abaixo de poucos minutos para commits comuns e isolasse suites longas em jobs paralelos ou noturnos.

### Melhorias possiveis

- Separar dependencias de analise, teste e visualizacao para reduzir instalacao no CI.
- Publicar um resumo Markdown no `GITHUB_STEP_SUMMARY` com metricas por execucao.
- Usar cache mais granular e evitar invalidacoes desnecessarias.
- Executar testes rapidos primeiro e suites lentas em paralelo.
- Salvar artefatos por job com nomes padronizados para facilitar auditoria.

### Resultados inesperados

1. O paralelismo nem sempre reduziu a duracao total. Em cargas pequenas, o overhead de jobs adicionais competiu com o ganho de dividir testes.
2. O cache nao eliminou todo o custo de setup. Mesmo com cache hit, ainda existe tempo de restauracao, verificacao e execucao do `pip install`, entao a diferenca aparece mais claramente quando o cache miss e acompanhado por dependencias ou atrasos maiores.

### Comparacao entre hipotese e resultado observado

A hipotese foi parcialmente confirmada. Os testes dominaram quando a carga foi ampliada ou desacelerada, mas em execucoes pequenas o setup teve peso proporcionalmente maior. O paralelismo ajudou nas cargas maiores, mas nao foi uma melhoria universal.

### Limitacoes dos dados

- A amostra tem apenas {total_runs} execucoes, suficiente para a atividade mas pequena para inferencia estatistica robusta.
- Parte da lentidao foi artificial, entao os numeros absolutos nao representam um produto real.
- Runners hospedados pelo GitHub variam em disponibilidade e desempenho.
- O tempo de workflow inclui overhead da plataforma, nao apenas o tempo do codigo.
- Os dados de artefatos dependem do upload ocorrer mesmo quando o teste falha.

### Como a analise apoia decisoes de engenharia?

A analise mostra onde investir primeiro: cache, paralelismo, divisao de suites ou reducao de testes lentos. Ela tambem ajuda a definir SLOs de feedback para desenvolvedores, identificar falhas recorrentes e justificar mudancas na arquitetura do pipeline com evidencias em vez de percepcao subjetiva.

## Reproducao

1. Alterar `experiment_config.json` com uma variacao controlada.
2. Fazer commit e push para `main`.
3. Aguardar o workflow `CI Metrics Experiment`.
4. Rodar `python scripts/collect_github_metrics.py --repo {args.repo} --workflow ci-metrics.yml --limit 30`.
5. Rodar `python scripts/generate_charts.py`.
6. Rodar `python scripts/render_report.py --repo {args.repo}`.
"""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
