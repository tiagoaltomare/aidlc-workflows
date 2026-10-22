# Plano: memória entre ciclos no AI-DLC v1
Repo tiagoaltomare/aidlc-workflows, branch v1 (HEAD 9fd17f1, VERSION 1.0.1, idêntica ao upstream).
Status: PLANO, aguardando aprovação do Tiago. Ainda não há código nem PR.
Fontes: parecer do AI-SDLC Expert (parecer-expert.md) e análise do Developer (/workspace/aidlc-analysis/analise-memoria.md).

## Desenho
- Extensão opt-in de memória, empacotada dentro de aidlc-rules/. O release.yml:57 só empacota essa pasta, então tudo o que for novo precisa ficar lá.
- O marcador knowledge/.aidlc-memory liga a extensão.
- Um gancho pequeno no core, na Workspace Detection, decide entre pular o RE, fazer RE delta ou fazer RE completo.
- O estado é calculado por script determinístico. O LLM nunca calcula hash.
- Com a extensão desligada, o v1 se comporta igual ao upstream.

## Fluxo
1. **Início do ciclo** (Workspace Detection, com inception/cycle-start.md):
   - roda `aidlc_memory.py check` (git diff + sha256);
   - lê handoff e index, com no máximo cerca de 2 mil tokens;
   - propõe pular o RE, fazer delta ou fazer completo;
   - essa decisão passa por aprovação humana.
2. **Reverse Engineering:** ganha um modo delta, que re-escaneia só o que está stale ou uncovered. Depois do Step 13 aprovado, regenera o codekb e roda `stamp`.
3. **Requirements e Stories:** leem openspec/specs. Cada intent vira um changes/<id>. O requirements referencia IDs, sem copiar texto.
4. **Units:** cada unit fica ligada a um change-id no aidlc-state.md.
5. **Fechamento de Ciclo** (construction/cycle-close.md, novo estágio entre Build & Test e Operations):
   - openspec archive, com o diff aprovado por humano; conflito sempre bloqueia;
   - ingest sem duplicação;
   - lint;
   - atualização de index e log;
   - handoff no modelo fixo (escopo, changes, stale, dívidas, pendências, commit), aprovado por humano.
   - Tudo registrado no audit.md.

## Forçar RE completo quando qualquer item valer
- source_commit ausente ou fora do histórico.
- Mais de 30% dos hashes divergentes, ou arquivos uncovered.
- Mudança no manifesto de dependências ou build, ou na estrutura de topo.
- 3 ciclos seguidos só com delta.
- Commits sem registro no audit.
- Handoff ausente ou não aprovado.
- Pedido do usuário.

## Arquivos
**Criar (aidlc-rules/):**
- common/memory-protocol.md
- inception/cycle-start.md
- construction/cycle-close.md
- templates/ com handoff, adr, codekb-entry, index, log, openspec-proposal e openspec-spec
- tools/aidlc_memory.py (Python 3 só com a stdlib; comandos check e stamp; gera .stale.json; exit 1 quando há stale; fallback por hash; normaliza fim de linha para LF; inclui procedimento manual se faltar Python)

**Alterar:**
- core-workflow.md:
  - 114-126: a decisão binária de executar ou pular e o "analyze all packages";
  - 536-539: a pasta de docs.
- workspace-detection.md: linha 7 (resume sem noção de ciclo novo) e linhas 38-43 (stale por timestamp).
- reverse-engineering.md: linha 9 (rerun) e Step 10.
- session-continuity.md
- requirements-analysis.md
- workflow-planning.md
- build-and-test.md
- process-overview.md
- terminology.md
- README: a instalação e o prompt de setup precisam apontar para o fork, não para o awslabs.
- docs/GENERATED_DOCS_REFERENCE.md
- VERSION e CHANGELOG, para 1.1.0.

**Frontmatter:**
- type, conforme o OKF v0.2.
- verified, para registrar quem aprovou.
- Chaves próprias: source_commit, sources [{path, sha256}], covers e derived_from.

## Fases e estimativa (dias úteis)
| Fase | Entrega | Dias |
|---|---|---|
| F0 | Spec do protocolo, schema do frontmatter, modelos | 1 a 1,5 |
| F1 | aidlc_memory.py e testes (rebase, shallow clone, renames, CRLF, uncovered) | 1,5 a 2 |
| F2 | Regras: cycle-start, modo delta, cycle-close, gates | 2 a 3 |
| F3 | Integração OpenSpec sem depender da CLI dele | 1 a 1,5 |
| F4 | Instalação, release 1.1.0, README | 1 |
| F5 | Validação em 2 ou 3 ciclos num repo brownfield de exemplo, com métricas | 2 a 3 |
| | **Total** | **cerca de 9 a 12** |

## Critérios de aceite
- Redução medida de tokens e tempo na Inception do ciclo 2 em diante, comparada ao baseline.
- Um hotfix injetado fora do AI-DLC é sempre detectado como stale.
- Nenhum conflito de archive é resolvido sem humano.
- Toda decisão de pular, delta ou completo fica no audit.md.
- O carregamento inicial fica dentro do limite.
- Com a extensão desligada, o comportamento é igual ao upstream.
- O merge do upstream só dá conflito nos ganchos.
- Não há texto duplicado entre specs e requirements.

## Riscos
- O LLM pode ignorar o modo delta. Mitigação: gates MANDATORY e um cenário no evaluator.
- Resumo de resumo: mitigado pelo RE completo forçado.
- Duas fontes de verdade.
- Granularidade de artefatos agregados como architecture.md. Mitigação: um limite de % de fontes alteradas.
- Divergência com o upstream, porque a v1 está em manutenção.

## Decisões para o Tiago
1. **DECIDIDO:** knowledge/ e openspec/ ficam dentro de aidlc-docs/.
   - na raiz, relaxando a regra "aidlc-docs only";
   - ou dentro de aidlc-docs/, que diverge menos do upstream. Recomendo dentro de aidlc-docs/.
2. **DECIDIDO:** v1, com protocolo independente de versão.
3. **Aprovar o plano** para o Developer começar pela F0, em branch separada.

## Observabilidade e validação com dados (harness Grok Build)
Pesquisa completa do Pesquisador em /workspace/pesquisador/observabilidade-grok-build.md.

### Coleta
- O CLI `grok` roda em modo headless (`-p`, `--output-format streaming-json`, `--always-approve`, `--no-auto-update`) com modelo e commit fixos, sempre em clone limpo.
- O OpenTelemetry (alpha) é ligado com `GROK_EXTERNAL_OTEL=1`. Ele exporta os tokens (input, output, cache_read e reasoning) e os eventos api_request, session_end, tool_result e compaction. `OTEL_LOG_TOOL_DETAILS=1` acrescenta os caminhos dos arquivos lidos.
- Os hooks ficam em `.grok/hooks`. O PostToolUse grava NDJSON com {run_id, ciclo, etapa, tool, arquivo, ts}. O PreToolUse e o Stop servem para barrar a resolução automática de conflitos.
- O script `aidlc_memory.py` emite eventos próprios: decisão de RE, stale detectado, archive e handoff.
- Tudo é consolidado num único `trials.jsonl` por execução.

### Fase F-OBS (nova, paralela a F1 e F2, de 1,5 a 2 dias)
- `eval/run_trials.py`: roda N execuções por braço (upstream e extensão), nos ciclos 1 a 3, alternando a ordem.
- `eval/inject_hotfix.py`: commits fora do AI-DLC, com variações de arquivo, rename e CRLF.
- `eval/inject_conflict.py`: specs divergentes.
- `eval/parse_audit.py`, `eval/dup_check.py` (5-gram/Jaccard) e `eval/merge_check.sh`.
- `eval/report.py`: gera mediana, IC95% em pares, pass^k e o cálculo 3/n, além de separar as falhas para leitura manual.

### Critérios com dados
| # | Evidência | Limiar | Amostra |
|---|---|---|---|
| 1 | Tokens e duração do Inception, ciclos 2 e 3, extensão contra baseline | Redução mediana ≥ 30% e IC95% > 0 | ≥ 5 cenários × 3 a 5 execuções por braço |
| 2 | Hotfix injetado aparece como stale no .stale.json, no handoff e no audit | 100% | ≥ 30 injeções (falha < 10% com 95% de confiança) |
| 3 | Conflito injetado gera parada e aprovação registrada | 0 automáticas | 20 a 30 |
| 4 | Cada decisão de RE tem registro no audit.md, cruzado com os eventos | 100% | ≥ 30 decisões |
| 5 | Tokens carregados antes da primeira ação | p95 ≤ 2.000 | ≥ 20 |
| 6 | Diff estrutural de aidlc-docs com a extensão desligada contra o upstream | 0 diferenças | ≥ 10 pares |
| 7 | Merge das últimas 5 tags, conflitos contidos na allowlist dos ganchos | 100% | Determinístico, a cada release |
| 8 | Similaridade entre specs e requirements | 0 trechos com Jaccard > 0,5 | A cada ciclo |

### A confirmar no primeiro uso
- O esquema do JSON do modo headless e o formato de ~/.grok/sessions.
- A estabilidade do OTel, que está em alpha.
- A calibração dos limiares, feita no baseline.

### Estimativa revista
Cerca de 10,5 a 14 dias úteis com a F-OBS. A F5 passa a ser a execução da bateria de testes.

## Status (22/10/2026, 13:53 BRT)
- O Tiago aprovou o plano, e o Developer foi acionado pelo próprio Tiago para implementar.
- Os casos de teste ficam pendentes. O repo será um clone enxuto do ai-control-center, preparado com o Developer-x. Os cenários previstos são uma feature básica e um refactor complexo, cada um em 3 ciclos e com um hotfix injetado.
