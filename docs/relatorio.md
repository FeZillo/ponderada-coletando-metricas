# Relatorio tecnico - metricas de CI/CD

## Identificacao

- Repositorio: preencher com o link do GitHub
- Workflow YAML: preencher com o link para `.github/workflows/ci-metrics.yml`
- Periodo do experimento: preencher datas

## Hipotese inicial

Preencher antes da analise. Exemplo: esperava-se que cache e paralelismo reduzissem
significativamente a duracao total do pipeline, enquanto testes lentos aumentariam a
duracao do job de testes.

## Evidencias reais das execucoes

| Run ID | Link GitHub Actions | Commit | Mensagem | Variacao | Status |
| --- | --- | --- | --- | --- | --- |
| preencher | preencher | preencher | preencher | preencher | preencher |

## Variacoes realizadas

Descrever as mudancas feitas entre as execucoes: baseline, mais testes, teste lento,
falha controlada, cache frio/quente, jobs sequenciais e jobs paralelos.

## Base de dados

- CSV principal: `data/metrics.csv`
- Resumo por execucao: `data/run_summary.csv`
- Etapas: `data/steps.csv`
- JSON bruto: `data/raw_runs.json`

## Graficos

Inserir os graficos gerados:

```markdown
![Tempo total por execucao](../charts/pipeline_duration_by_run.png)
![Tempo medio por job](../charts/average_duration_by_job.png)
![Taxa de sucesso e falha](../charts/success_failure_rate.png)
![Quantidade de testes vs duracao](../charts/tests_vs_pipeline_duration.png)
```

## Analise

### Qual etapa mais contribuiu para o tempo total do pipeline?

Preencher com base em `data/steps.csv` e no grafico de etapas mais lentas.

### Houve diferenca significativa entre execucoes com e sem cache?

Comparar execucoes com cache quente e cache frio usando duracao do step
`Install dependencies` e o tempo total do workflow.

### O paralelismo reduziu o tempo total? Em que condicoes?

Comparar execucoes com jobs `lint` e `tests` paralelos contra execucoes com
`needs: lint` no job `tests`.

### Quais falhas foram mais frequentes?

Preencher usando runs com status `failure` e os logs/artefatos correspondentes.

### O pipeline fornece feedback rapido o suficiente?

Avaliar se a duracao total atende a expectativa do desenvolvedor.

### Que melhorias poderiam ser feitas?

Listar melhorias como cache mais especifico, separar testes lentos, usar matriz,
reduzir instalacao duplicada ou melhorar criterios de falha.

### Quais limitacoes existem nos dados coletados?

Discutir numero pequeno de execucoes, variacao de carga do GitHub Actions, artefatos
expiraveis e mudancas controladas mas nao perfeitamente isoladas.

### Como essa analise poderia apoiar decisoes de engenharia?

Explicar como os dados ajudam a priorizar otimizacoes, reduzir tempo de feedback e
melhorar confiabilidade.

## Resultados inesperados

1. Resultado inesperado 1: preencher com evidencia.
2. Resultado inesperado 2: preencher com evidencia.

## Comparacao entre hipotese e resultado observado

Preencher apos gerar os graficos e analisar os dados reais.

## Como reproduzir

1. Instalar dependencias com `python -m pip install -r requirements-dev.txt`.
2. Fazer commits alterando `experiment_config.json` ou o YAML do workflow.
3. Executar pelo menos 12 pipelines reais no GitHub Actions.
4. Rodar `scripts/collect_github_metrics.py`.
5. Rodar `scripts/generate_charts.py`.
6. Preencher este relatorio com links, IDs reais e analise.

