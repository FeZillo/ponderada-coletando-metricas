# Leitura Lab - experimento de metricas CI/CD

Projeto simples para instrumentar um pipeline no GitHub Actions, coletar metricas reais
de execucao, gerar graficos e apoiar um relatorio tecnico.

O tema escolhido e uma lista de leitura. A API possui somente tres endpoints REST:

| Metodo | Rota | Descricao |
| --- | --- | --- |
| GET | `/api/books` | Lista os livros cadastrados em memoria. |
| POST | `/api/books/{book_id}/toggle` | Avanca o status do livro. |
| GET | `/api/stats` | Retorna resumo da lista e percentual concluido. |

## Como rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
uvicorn leitura_lab.app:app --reload
```

Em outro terminal, suba o front:

```bash
python -m http.server 5500 -d frontend
```

Acesse `http://127.0.0.1:5500`.

No Windows PowerShell, a ativacao da venv e:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Testes e lint

```bash
ruff check .
pytest --junitxml=reports/junit.xml
python scripts/extract_test_metrics.py reports/junit.xml data/current/test_metrics.json
```

## Pipeline

O workflow esta em `.github/workflows/ci-metrics.yml` e executa:

- instalacao de dependencias;
- analise estatica com Ruff;
- testes automatizados com Pytest;
- geracao de JUnit XML;
- extracao de metricas de teste;
- upload do artefato `pipeline-metrics-<run_id>`.

Os jobs `lint` e `tests` estao paralelos por padrao. Para uma variacao sequencial,
adicione `needs: lint` no job `tests`, faca commit e rode novamente o pipeline.

## Variacoes sugeridas para 12 execucoes

Use o arquivo `experiment_config.json` para controlar quantidade de testes, teste lento
e falha controlada. O script abaixo ajuda a trocar o cenario:

```bash
python scripts/run_experiment.py --list
python scripts/run_experiment.py --scenario more-tests
```

Plano sugerido:

| Execucoes | Variacao |
| --- | --- |
| 1-3 | `baseline`, sem alteracoes. |
| 4-5 | `more-tests`, com mais testes parametrizados. |
| 6-7 | `slow-tests`, com atraso artificial. |
| 8 | `failing-test`, para registrar falha real. |
| 9 | Voltar para `baseline`, pipeline verde novamente. |
| 10 | Alterar chave de cache no YAML ou dependencia para medir cache frio. |
| 11 | Adicionar `needs: lint` em `tests` para testar execucao sequencial. |
| 12 | Remover `needs: lint` para voltar ao paralelismo. |

Cada alteracao deve virar commit e push para gerar uma execucao real no GitHub Actions.

## Coleta das metricas

Depois das execucoes reais, crie um token com permissao de leitura do repositorio e rode:

```bash
export GITHUB_TOKEN="seu_token"
python scripts/collect_github_metrics.py --repo SEU_USUARIO/ponderada-coletando-metricas --workflow ci-metrics.yml --limit 12
```

No PowerShell:

```powershell
$env:GITHUB_TOKEN="seu_token"
python scripts/collect_github_metrics.py --repo SEU_USUARIO/ponderada-coletando-metricas --workflow ci-metrics.yml --limit 12
```

Arquivos gerados:

- `data/metrics.csv`: uma linha por job de cada execucao;
- `data/run_summary.csv`: uma linha por execucao;
- `data/steps.csv`: uma linha por etapa;
- `data/raw_runs.json`: resposta bruta usada na analise.

## Graficos

```bash
python scripts/generate_charts.py
```

Graficos gerados em `charts/`:

- `pipeline_duration_by_run.png`;
- `average_duration_by_job.png`;
- `success_failure_rate.png`;
- `tests_vs_pipeline_duration.png`;
- `slowest_steps.png`.

## Relatorio

Use `docs/relatorio.md` como base. O relatorio final precisa conter os links das
execucoes reais, IDs dos workflows, commits usados, graficos gerados e analise critica.

