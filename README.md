# Ponderada: coletando metricas de CI/CD

Experimento pratico para instrumentar um pipeline no GitHub Actions, coletar metricas reais de execucao, gerar graficos e produzir uma analise tecnica sobre desempenho, estabilidade e gargalos.

## Projeto

O repositorio contem um pequeno pacote Python (`pipeline_lab`) com testes automatizados. O arquivo `experiment_config.json` controla as variacoes do experimento:

- quantidade de testes executados;
- atraso artificial em parte dos testes;
- falha controlada;
- quantidade de shards de teste em paralelo;
- versao da chave de cache.

## Pipeline

Workflow: [`.github/workflows/ci-metrics.yml`](.github/workflows/ci-metrics.yml)

O pipeline executa:

1. leitura da configuracao do experimento;
2. instalacao de dependencias;
3. lint com Ruff;
4. testes automatizados com Pytest;
5. upload de artefatos com JUnit XML e metricas dos testes;
6. coleta posterior via API do GitHub Actions.

## Como reproduzir

Instale as dependencias locais:

```bash
python -m pip install -r requirements-dev.txt
```

Execute validacoes locais:

```bash
ruff check .
pytest
```

Depois de executar o workflow no GitHub Actions pelo menos 12 vezes, colete os dados:

```bash
python scripts/collect_github_metrics.py --repo FeZillo/ponderada-coletando-metricas --workflow ci-metrics.yml --limit 30
```

Gere os graficos:

```bash
python scripts/generate_charts.py --input data/run_summary.csv --jobs data/metrics.csv --steps data/steps.csv --output-dir charts
```

Atualize o relatorio:

```bash
python scripts/render_report.py --repo FeZillo/ponderada-coletando-metricas
```

## Entregaveis

- workflow YAML: `.github/workflows/ci-metrics.yml`
- script de coleta: `scripts/collect_github_metrics.py`
- base de dados: `data/*.csv`
- graficos: `charts/*.png`
- relatorio tecnico: `docs/relatorio.md`
