# Plano de observabilidade: extensão de memória do AI-DLC v1 no Grok Build

Fontes: [grok-build](https://github.com/xai-org/grok-build), [Headless & Scripting](https://docs.x.ai/build/cli/headless-scripting), [Monitoring Usage (OTel)](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/24-monitoring-usage.md), [Hooks](https://docs.x.ai/build/features/hooks), [guia de hooks](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/10-hooks.md), [Anthropic, Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), [benchmarks.company](https://benchmarks.company/framework/measure), [anylearn](https://anylearn.cc/lessons/hx-measuring-a-harness).

## 1. O harness
O Grok Build é o CLI `grok` da xAI. NÃO CONFIRMADO: não há executor de evals ou cenários nativo documentado, então os cenários precisam ser montados com scripts que chamam o CLI em modo headless.

## 2. Dados por execução
- Headless: `grok -p "..." --output-format json` ou `streaming-json` (NDJSON). As sessões ficam em `~/.grok/sessions`. NÃO CONFIRMADO: o esquema exato dos campos de tokens.
- OpenTelemetry (alpha, esquema v1), ativado com `GROK_EXTERNAL_OTEL=1` e `OTEL_METRICS_EXPORTER` ou `OTEL_LOGS_EXPORTER` iguais a `otlp` ou `console`.
- Métricas: `grok_code.token.usage` (input, output, reasoning, cache_read), `turn.count`, `turn.ttft`, `tool.usage`, `tool.decision`, `error.count`.
- Eventos: `api_request` (tokens e duration_ms), `tool_result`, `session_end` (duration_secs, turn_count, tool_call_count, compaction_count), `compaction` (tokens_before e tokens_after) e `subagent`.
- Por padrão nada de conteúdo é enviado. `OTEL_LOG_TOOL_DETAILS=1` inclui os caminhos de arquivo e `OTEL_LOG_TOOL_CONTENT=1` inclui o conteúdo. Não há métrica de custo.

## 3. CI e comparação
Comando de base: `grok --no-auto-update -p "..." --always-approve --output-format streaming-json --cwd <repo>`. NÃO CONFIRMADO: não há comparação nativa entre execuções. Sugestão: um wrapper que roda N execuções por braço, cada uma num clone limpo, e grava tudo em `trials.jsonl`.

## 4. Hooks
Ficam em JSON, em `~/.grok/hooks/` ou `.grok/hooks/`, e executam um comando ou chamam HTTP.
- Eventos: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse(Failure), Stop, StopFailure, StopCancelled, SubagentStart e SubagentStop, PreCompact e PostCompact, SessionEnd.
- O PreToolUse pode negar a ação (exit 2) e o Stop pode bloquear o encerramento.
- Sugestão: um hook PostToolUse que grava NDJSON `{event, tool, file, ts, run_id}`.
- Alternativas: um coletor OTel local com exportador de arquivo, ou parsear `~/.grok/sessions` (formato não documentado).

## 5. Práticas de mercado
- A/B com execuções repetidas e intervalo de confiança, comparando em pares por tarefa.
- pass^k para os critérios do tipo "sempre".
- Avaliadores por código e golden tests, além de avaliação da transcrição.
- Leitura manual de 10 a 20 execuções com falha.
- Injeção de falhas e mutação (sugestão).
- Regra de 3/n: com 0 falhas em n execuções, a taxa de falha fica abaixo de ~3/n com 95% de confiança (n=30 dá ~10%, n=60 dá ~5%).

## 6. Critérios de aceite
| # | Critério | Métrica | Coleta | Limiar | Execuções |
|---|---|---|---|---|---|
| 1 | Redução de tokens e tempo no Inception a partir do ciclo 2 | Tokens in, cache_read e out e duração por etapa nos ciclos 2 e 3 | OTel api_request e session_end, com etapas delimitadas pelo audit.md ou por um hook | Mediana de pelo menos X% (ex.: 30%) e IC95% em pares acima de 0 | Pelo menos 5 cenários com 3 a 5 execuções por braço (Wilcoxon ou bootstrap) |
| 2 | Hotfix sempre detectado como stale | Página marcada stale | Script injeta o commit, roda o ciclo e confere handoff, index e audit | 100% (pass^k) | Pelo menos 30 injeções variadas |
| 3 | Nenhum conflito de archive resolvido sem humano | Parada ou aprovação e registro | Specs divergentes injetadas, hooks PreToolUse e Stop, git diff | 0 resoluções automáticas | 20 a 30 conflitos |
| 4 | Decisão skip, delta ou full sempre no audit.md | Cobertura das decisões | Parser do audit.md cruzado com hooks e streaming-json | 100% | Mesma amostra dos critérios 1 a 3, pelo menos 30 decisões |
| 5 | Carga inicial de até ~2k tokens | Tokens lidos antes da primeira ação | Hook PostToolUse com tokenizer, conferido com o input do primeiro api_request | p95 de no máximo 2.000 | Pelo menos 20 |
| 6 | Extensão desligada igual ao upstream | Diferenças estruturais em aidlc-docs e nos estágios | Execuções em pares contra o upstream no mesmo commit | 0 diferenças estruturais | Pelo menos 10 pares |
| 7 | Merge do upstream só conflita nos ganchos | Arquivos em conflito contidos na allowlist | `git merge` das últimas tags e `git diff --name-only --diff-filter=U` | 100% | Determinístico, nas últimas 5 tags e a cada release |
| 8 | Sem texto duplicado entre specs e requirements | Similaridade por 5-gram, MinHash ou embeddings | Script | 0 trechos acima do limiar (ex.: Jaccard > 0,5) | Determinístico, a cada ciclo |

## 7. Execução
1. Fixe o modelo (`-m`), o commit e use `--no-auto-update` com clone limpo.
2. Rode os dois braços (upstream e extensão) nos ciclos 1 a 3, alternando a ordem.
3. Junte OTel, streaming-json e hook num único `trials.jsonl`.
4. Rode os scripts de injeção.
5. Monte o relatório com IC95% em pares, pass^k e 3/n, mais a leitura manual das falhas.

NÃO CONFIRMADO: o executor de evals nativo, o esquema do JSON headless e o formato das sessões. O OTel está em alpha e os limiares marcados "ex." são sugestões.
