# Workspace Knowledge And Literature Contract

## 1. 目标

本文件冻结当前已经落地的 workspace-first knowledge / literature truth：

- 同一 disease workspace 的研究记忆与文献资产统一在 workspace 管理
- study 只持有本研究线的 reference context
- quest 只持有 runtime local materialization

这不是未来目标，而是当前 `P1` 的正式完成态。

## 2. Authority Boundary

### 2.1 Workspace 层

workspace 持有可跨 study 复用的 canonical knowledge / literature truth。

稳定表面：

- `portfolio/research_memory/topic_landscape.md`
- `portfolio/research_memory/dataset_question_map.md`
- `portfolio/research_memory/venue_intelligence.md`
- `portfolio/research_memory/literature/registry.jsonl`
- `portfolio/research_memory/literature/references.bib`
- `portfolio/research_memory/literature/coverage/latest.json`

这层回答的是：

- 同一病种 workspace 当前有哪些高信号方向
- 哪些文献与证据 bucket 值得跨 study 复用
- 哪些 venue / literature 结论已经达到 workspace 复用级别

### 2.2 Study 层

study 持有本研究线特有的 reference context。

稳定表面：

- `studies/<study_id>/artifacts/reference_context/latest.json`
- `study_charter`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`

这层回答的是：

- workspace canonical literature 中哪些 record 被当前 study 选中
- 它们承担什么角色：`framing_anchor`、`claim_support`、`journal_fit_neighbor`、`adjacent_inspiration`
- 哪些是本研究线的 mandatory anchor，哪些只是 optional neighbor

### 2.3 Quest 层

quest 只持有 runtime local materialization。

稳定表面：

- `quest_root/literature/*`
- `quest_root/paper/references.bib`
- `quest_root/paper/reference_coverage_report.json`

这层的角色固定为：

- materialized working copy

而不是：

- canonical literature truth

## 3. 当前实现口径

当前主线已经按下面顺序工作：

1. startup ingress 进入 `study_reference_context`
2. `study_reference_context` 同步 / 提升到 workspace canonical literature registry
3. `build_hydration_payload(...)` 向 quest hydration 提供：
   - `workspace_literature`
   - `study_reference_context`
   - `literature_records`
4. quest hydration / literature hydration 只把选中的 records materialize 到 quest local surface

因此，同一病种 workspace 下的研究记忆与文献资产已经是统一管理，而不是继续在每个 quest 各自持有一份 authority truth。

## 4. Fail-Closed 规则

这条 contract 必须继续 fail-closed：

- 缺 workspace canonical literature registry 时，不得把 quest-local cache 静默升格成 authority root
- `study_reference_context.workspace_registry_path` 与 `workspace_literature.registry_path` 不一致时，必须报错
- study reference context 缺失时，不得把当前 quest working set 误报成 study-approved anchor set
- external research 报告只能沉淀回 workspace canonical layer，不能直接替代 workspace / study authority
- `quest_root/literature/*` 可以为空，但它为空时表示“当前 materialization 为空”，不表示 workspace canonical literature 不存在

## 5. 当前完成状态

当前正式状态如下：

- `P1 workspace canonical literature / knowledge truth` 已完成
- 研究记忆与文献资产已经按 workspace-first 统一管理
- 当前剩余工作不在 knowledge plane owner 本身，而在 `P2 controlled cutover -> physical monorepo migration`

所以，这条 contract 当前的重点不是“继续上提 literature”，而是：

- 不让 workspace canonical literature 回退
- 不让 study reference context 与 quest materialization 重新混叠
