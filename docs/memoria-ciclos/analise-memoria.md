# Análise: memória entre ciclos no AI-DLC v1 (somente leitura)

Repo: `tiagoaltomare/aidlc-workflows`, branch `v1`, HEAD `9fd17f197`, `aidlc-rules/VERSION` = 1.0.1. Nada foi alterado: sem código, sem branch e sem PR.

## 1. Estrutura atual da v1

| Peça | Caminho real | Observação |
|---|---|---|
| Regra raiz (entrypoint) | `aidlc-rules/aws-aidlc-rules/core-workflow.md` (539 linhas) | Orquestra todas as fases. Resolve o diretório de detalhes nas linhas 14-18 (`.aidlc/aidlc-rules/aws-aidlc-rule-details/`, `.aidlc-rule-details/`, `.kiro/...`, `.amazonq/...`). |
| Regras comuns | `aidlc-rules/aws-aidlc-rule-details/common/*.md` | São 12 arquivos, entre eles `process-overview.md`, `session-continuity.md`, `workflow-changes.md`, `content-validation.md` e `terminology.md`. |
| Stages, Inception | `aidlc-rules/aws-aidlc-rule-details/inception/` | `workspace-detection.md`, `reverse-engineering.md`, `requirements-analysis.md`, `user-stories.md`, `workflow-planning.md`, `application-design.md`, `units-generation.md`. |
| Stages, Construction | `aidlc-rules/aws-aidlc-rule-details/construction/` | `functional-design.md`, `nfr-requirements.md`, `nfr-design.md`, `infrastructure-design.md`, `code-generation.md`, `build-and-test.md`. |
| Stages, Operations | `aidlc-rules/aws-aidlc-rule-details/operations/operations.md` | Placeholder de 19 linhas. Em `core-workflow.md` aparece nas linhas 425-447. |
| Reverse Engineering | `inception/reverse-engineering.md` (311 linhas) e `core-workflow.md` linhas 112-137 | Gera 8 artefatos em `aidlc-docs/inception/reverse-engineering/` e o arquivo `reverse-engineering-timestamp.md` (Step 10, linhas 258-280). |
| Extensões (opt-in) | `aidlc-rules/aws-aidlc-rule-details/extensions/{security,resiliency,testing}/...` com pares `*.opt-in.md` / `*.md` | O mecanismo está em `core-workflow.md`, linhas 29-50. |
| Templates | **Não existe pasta de templates.** | Os "templates" são blocos markdown dentro das próprias regras: o Step 10 do RE, `session-continuity.md` ("Session Continuity Templates") e a árvore de `aidlc-docs/` em `core-workflow.md` linhas 508-534. |
| Instalador | **Não existe script de instalação.** | (a) Cópia manual pelo `README.md` (seções "Platform-Specific Setup" na linha 58 e seguintes, com `cp -R` para `.kiro/`, `.amazonq/`, `.cursor/rules/*.mdc`, `.clinerules/`, `AGENTS.md`/`CLAUDE.md` e `.aidlc-rule-details/`). (b) "AI-Assisted Setup" no `README.md` linha 921 e seguintes: um prompt que baixa o zip da release para `.aidlc/`. (c) Empacotamento em `.github/workflows/release.yml` linha 57: `zip -r ai-dlc-rules-vX.zip aidlc-rules/`. |
| Ferramental Python | `scripts/aidlc-evaluator/` (uv, pyproject) | É só avaliação/benchmark e não é distribuído ao usuário. |

**Pontos críticos para o design:**
- Só o diretório `aidlc-rules/` é distribuído (release.yml:57). Qualquer script ou template novo precisa morar dentro de `aidlc-rules/`, senão "não vem na instalação".
- O prompt de setup do README (linha 921 e seguintes) baixa a release de `awslabs/aidlc-workflows`, não do fork. Para o fork entregar a memória, o README precisa apontar para `tiagoaltomare/aidlc-workflows`.
- A filosofia declarada no README, linha 815, é "Methodology first… Users shouldn't need to install anything". Um script vira dependência opcional, e por isso precisa de fallback manual na regra.

## 2. Arquivos a criar ou alterar

### Ponto que força o RE completo (a sobrescrever)
1. **`aidlc-rules/aws-aidlc-rules/core-workflow.md`, linhas 114-121.** O RE executa se "No previous reverse engineering artifacts found" e é pulado se "Previous reverse engineering artifacts exist". É binário e contradiz o `workspace-detection.md`. **Linhas 125-126** ("Execute reverse engineering: Analyze all packages and components"): é aqui que se força a varredura total, e é este trecho que precisa ganhar um modo incremental.
2. **`aidlc-rules/aws-aidlc-rule-details/inception/workspace-detection.md`, linhas 38-43.** A detecção de stale usa "compare artifact timestamps against codebase's last significant modification" (linha 39). Se stale, o RE é reexecutado inteiro (linha 41). Esta é a regra a trocar por "consultar o manifesto codekb e reescanear só as entradas stale".
3. **`aidlc-rules/aws-aidlc-rule-details/inception/reverse-engineering.md`, linha 9** ("Rerun behavior… reverse engineering executes again"). Também o Step 1 (linhas 11 e seguintes), que analisa tudo, e o Step 10 (linhas 258-280), cujo timestamp é só de data, sem commit nem hash.
4. Secundário: `workspace-detection.md`, linha 7. Se `aidlc-state.md` existe, faz "Resume from last phase", e não há noção de "novo ciclo". É preciso distinguir ciclo concluído (handoff existe) de ciclo em andamento.

### Alterar
- `aidlc-rules/aws-aidlc-rules/core-workflow.md`
  - Linhas 22-27: carregar `common/memory-protocol.md`.
  - Linhas 98-137: Workspace Detection e RE incrementais, mais a leitura do handoff.
  - Depois da linha 420 (Build and Test): novo stage "Cycle Close". A pergunta da linha 420 passa a levar ao fechamento antes de Operations.
  - Linhas 508-534: árvore de diretórios com `knowledge/` e `openspec/`.
- `inception/workspace-detection.md`: Step 1 (detectar `knowledge/handoff/cycle-NN.md` mais recente), Step 3 (stale por manifesto) e Step 4 (registrar o número do ciclo em `aidlc-state.md`).
- `inception/reverse-engineering.md`: modo incremental com as entradas `knowledge/code/*.md` e frontmatter OKF (`source_commit` e `sha256` por arquivo-fonte coberto). O Step 10 passa a gravar `source_commit`.
- `common/session-continuity.md`: ler o handoff e o `knowledge/index.md` ao retomar.
- `inception/requirements-analysis.md` e `inception/workflow-planning.md`: criar `openspec/changes/<id>/` (proposal, tasks, spec deltas) para o ciclo.
- `construction/build-and-test.md`: o fim aponta para o Cycle Close.
- `common/process-overview.md` e `common/terminology.md`: definir ciclo, handoff, codekb, stale e OKF.
- `README.md`: a instalação passa a criar `knowledge/` e `openspec/` (ou deixa isso para o 1º ciclo) e copia o script. O AI-Assisted Setup aponta para o fork.
- `docs/GENERATED_DOCS_REFERENCE.md`: documentar os novos artefatos.
- `aidlc-rules/VERSION` e `CHANGELOG.md`: subir a versão (1.1.0).
- `scripts/aidlc-evaluator/`: opcionalmente, um cenário brownfield de 2 ciclos para validar.

### Criar (todos dentro de `aidlc-rules/` para entrar no zip)
- `aidlc-rules/aws-aidlc-rule-details/common/memory-protocol.md`: layout de `knowledge/`, schema OKF de frontmatter, regras de stale e de append em `log.md`.
- `aidlc-rules/aws-aidlc-rule-details/construction/cycle-close.md`: arquivar `openspec/changes/<id>` em `openspec/changes/archive/` e fundir os deltas em `openspec/specs/`, atualizar o codekb (commit e hash), criar ADRs e `knowledge/handoff/cycle-NN.md`, append em `knowledge/log.md`, atualizar `knowledge/index.md`.
- `aidlc-rules/aws-aidlc-rule-details/inception/cycle-start.md`, ou isso fica dentro de `workspace-detection.md`: ler o handoff e rodar o check de stale.
- `aidlc-rules/aws-aidlc-rule-details/templates/` (pasta nova) com `handoff.md`, `adr.md`, `codekb-entry.md`, `index.md`, `log.md`, `openspec-proposal.md`, `openspec-spec.md`.
- `aidlc-rules/tools/aidlc_memory.py`: script stale/refresh, ver a seção 3. Caminho sugerido; ele não existe hoje.

Observação de compatibilidade: os novos artefatos devem ficar **fora** de `aidlc-docs/`? A regra em core-workflow:536-539 diz "Documentation: aidlc-docs/ only". Ou se ajusta essa regra para permitir `knowledge/` e `openspec/` na raiz (é o que se pede), ou se aninha em `aidlc-docs/knowledge/`. É uma decisão para o PM ou o Tiago.

## 3. Script git diff + sha256 (marcar stale)

**Linguagem: Python 3, somente stdlib** (`hashlib`, `subprocess`, `pathlib`, `re`/frontmatter simples, sem PyYAML).
- O repo já é Python no ferramental (`scripts/aidlc-evaluator/`, uv, pyproject, bandit e semgrep na CI), então lint e testes já existem.
- Portável em macOS, Linux e Windows. Bash quebraria no Windows, e o README documenta PowerShell e CMD (linhas 217-247). Node não é garantido em projetos Java, Go etc.
- Sem dependências, então não fere o "não instalar nada". A regra deve ter fallback: se não houver Python, o agente executa os mesmos passos manualmente (`git diff --name-only`, `git hash-object` / `shasum -a 256`).

**Algoritmo** (`aidlc_memory.py check|stamp`):
1. Ler todas as `knowledge/code/*.md`. O frontmatter OKF traz `source_commit`, `sources: [{path, sha256}]` e `status`.
2. `git rev-parse HEAD`. Para cada `source_commit` distinto, `git diff --name-only --no-renames <source_commit> HEAD`, mais `git status --porcelain` para arquivos sujos e não rastreados. Se `source_commit` não existir (rebase, shallow clone), cair para a comparação por hash.
3. Para cada fonte candidata, calcular o sha256 do conteúdo, com EOL normalizado para LF para não marcar stale por CRLF. Se diverge ou o arquivo sumiu, a entrada fica `stale`. Arquivos novos que nenhuma entrada cobre e que casam com os globs de código entram como `uncovered`.
4. Saída em JSON (`knowledge/code/.stale.json`) e resumo em markdown para o agente. Exit code 0 = limpo, 1 = há stale.
5. `stamp <entrada>`: após o RE parcial, regrava `source_commit=HEAD` e os hashes.
- A base ideal é o `source_commit` gravado no handoff anterior. O sha256 é a verdade final; o git diff é só filtro rápido.
- Sem git (workspace não versionado), usar só sha256.

## 4. Riscos técnicos

- **Aderência do LLM:** as regras são prompts, não código. O agente pode ignorar o modo incremental e refazer tudo, ou pular o Cycle Close. Mitigação: gates explícitos com "MANDATORY" e checklist em `aidlc-state.md`, mais um cenário no evaluator.
- **Conflito com regras existentes:** "aidlc-docs/ only" (core-workflow:536-539), RE binário (114-121) e "Resume from last phase" (workspace-detection:7). É preciso editar de forma consistente para não deixar instruções contraditórias.
- **Contexto e tokens:** mais regras carregadas sempre. Usar carregamento sob demanda no estilo das extensões e manter `memory-protocol.md` curto.
- **Granularidade do codekb:** mapear entradas para arquivos-fonte. Entrada larga demais faz tudo ficar stale; estreita demais faz o RE parcial perder a visão de arquitetura. Os artefatos agregados (`architecture.md`, `business-overview.md`) precisam de regra própria (stale se >N% das fontes mudaram).
- **Git edge cases:** shallow clone, rebase/squash que faz o commit sumir, renames, monorepo, submódulos, CRLF.
- **Python ausente ou Windows:** são necessários fallback e path handling.
- **OpenSpec:** é uma convenção externa (Fission-AI). Fixar o formato usado (proposal, tasks, specs/deltas, archive) sem depender da CLI dele.
- **Distribuição:** o fork precisa de release própria (release.yml já serve com tag `v*`), e o README precisa apontar para o fork. Fazer merge da upstream `awslabs` v1 gera conflitos nos mesmos arquivos.
- **Upstream:** o README diz que `main` é o multi-harness atual e `v1` está em manutenção. A divergência vai crescer.

## Estimativa por fase (1 dev com agente; dias úteis)

| Fase | Escopo | Estimativa |
|---|---|---|
| F0 | Especificar o schema OKF, o layout de `knowledge/`/`openspec/` e os templates; decidir raiz vs `aidlc-docs/` | 1-1,5 d |
| F1 | Script `aidlc_memory.py` (check/stamp), testes pytest, CI (bandit/semgrep já existem) | 1,5-2 d |
| F2 | Regras: `memory-protocol.md`, `cycle-close.md`, cycle start; editar core-workflow, workspace-detection, RE, session-continuity, B&T | 2-3 d |
| F3 | Integração OpenSpec (requirements/workflow-planning, archive no close) | 1-1,5 d |
| F4 | Instalação: README (7 plataformas, bash/PowerShell/CMD), AI-assisted setup para o fork, release/VERSION/CHANGELOG | 1 d |
| F5 | Validação: greenfield e brownfield em 2 ciclos reais (Cursor/Claude Code) e/ou cenário no evaluator; ajustes de prompt | 2-3 d |
| **Total** | | **~9-12 d** |
