# Workspace Knowledge And Literature Contract

## 1. 背景

当前仓库已经明确存在一层 workspace 级显式研究记忆：

- `portfolio/research_memory/topic_landscape.md`
- `portfolio/research_memory/dataset_question_map.md`
- `portfolio/research_memory/venue_intelligence.md`

这说明平台已经承认：

- 同一 disease workspace 会跨多个 study 复用研究判断；
- quest/global memory 不能替代 workspace 级研究资产。

但文献层还没有完成同样的上提。

今天文献主线仍主要沿着下面这条路径工作：

- `startup_contract.paper_urls`
- `reference_papers`
- `startup_literature.resolve_startup_literature_records(...)`
- `quest_hydration`
- `quest_root/literature/*`
- `quest_root/paper/references.bib`

这意味着：

- workspace memory 已经是 explicit layer；
- workspace literature 还不是 canonical layer；
- study / quest 仍在分担本应属于 workspace 的文献 truth。

## 2. 目标

这条合同要完成四件事：

1. 把 workspace 级 research memory 与 literature registry 收成同一知识平面。
2. 让 study 只持有当前研究线的 reference context 与 framing anchor。
3. 让 quest 只持有 runtime local materialization，不再持有 literature truth。
4. 让后续 monorepo 吸收时，knowledge plane 与 runtime plane 一样具备清晰的 authority boundary。

## 3. 非目标

本 tranche 不做：

- 让 workspace memory 取代 quest/global memory；
- 让 workspace literature registry 取代 study 的 framing / shortlist / paper-specific decision；
- 把外部调研自动总结成最终结论；
- 把文献 registry 直接做成 startup hard gate；
- 继续允许 quest-local literature cache 充当长期 authority root。

## 4. 三层 authority 边界

### 4.1 Workspace 层

workspace 层持有跨 study 复用的 canonical 知识与文献资产。

至少包括：

- `portfolio/research_memory/*`
- future `portfolio/research_memory/literature/*`
- optional `external_reports/*`

它回答的是：

- 这个 disease workspace 当前高信号方向是什么；
- 同一批核心数据还能分叉出哪些 study；
- 哪些 reference / literature bucket 值得跨 study 复用；
- 哪些 venue / topic / evidence 判断可以在多个 study 之间继承。

### 4.2 Study 层

study 层只持有当前研究线特有的 decision 与 reference context。

至少应包括：

- `study_charter`
- `startup_contract` 中的 framing / endpoint / evidence package
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- future `studies/<study_id>/artifacts/reference_context/latest.json`

它回答的是：

- 当前 study 选择了 workspace 文献资产中的哪一部分；
- 哪些 anchor 进入这条研究线；
- 哪些 papers 是本研究线的强制 framing / claim-support / journal-fit evidence。

### 4.3 Quest 层

quest 层只持有 runtime local materialization。

例如：

- `quest_root/literature/*`
- `quest_root/paper/references.bib`
- 运行时当前需要消费的 local working set

这层可以存在，但它的角色必须改成：

- materialized working copy

而不是：

- canonical literature truth

## 5. 当前剩余漏洞

### 5.1 Workspace knowledge 已上提，workspace literature 还没上提

现在 `portfolio_memory` 已经明确是 workspace-first。
但 literature hydration 仍然是 quest-first。

这会导致：

- 同一 disease workspace 的 anchor papers 与 related work 在不同 quest 中反复 materialize；
- workspace 无法形成统一去重、统一 coverage、统一 provenance；
- 后续 study 很难明确继承前一条 study 已经验证过的 literature bucket。

### 5.2 Study reference context 没有被显式冻结

现在有：

- `paper_urls`
- `reference_papers`

但还没有一个独立的 study-owned reference context artifact 去回答：

- workspace registry 中哪些文献被当前 study 选中；
- 它们是 `framing anchor`、`claim support`、`journal fit neighbor` 还是 `adjacent inspiration`；
- 哪些只属于 quest working set，哪些已经进入 study authority。

### 5.3 Quest hydration 还在扮演过多 owner 角色

`quest_hydration` 今天同时负责：

- display / paper stub 物化
- literature hydration
- bibliography 生成

这使得 quest-local runtime root 仍容易被误读为 literature truth root。

### 5.4 `refs/` 与 venue intelligence promotion 仍缺正式合同

workspace 架构里已经存在：

- `refs/`

但它目前更像目录约定，而不是 machine-readable canonical registry。

同时：

- `journal_shortlist_evidence`
  - 仍应保持 study-owned
- `venue_intelligence`
  - 仍应保持 workspace-owned

这两者之间还缺正式的 promotion contract。

## 6. 目标 end-state

### 6.1 Workspace canonical knowledge root

workspace 继续保留：

- `portfolio/research_memory/README.md`
- `portfolio/research_memory/registry.yaml`
- `topic_landscape.md`
- `dataset_question_map.md`
- `venue_intelligence.md`

并新增 canonical literature layer，例如：

- `portfolio/research_memory/literature/registry.jsonl`
- `portfolio/research_memory/literature/references.bib`
- `portfolio/research_memory/literature/coverage/latest.json`

这里的重点不是具体文件名本身，而是 authority 语义：

- workspace literature registry 是跨 study 复用的 canonical 文献层。
- `refs/`、external reports、study reference context 若要被长期复用，也必须先被受控吸收到这层 canonical registry 或其正式索引里。

### 6.2 Study reference context artifact

study 层需要一个正式 artifact 去表达：

- 本 study 选择了哪些 workspace literature records；
- 每条 record 在本 study 中承担什么角色；
- 当前 study 的 mandatory anchors 与 optional neighbors 是什么。

建议固定为：

- `studies/<study_id>/artifacts/reference_context/latest.json`

### 6.3 Quest materialization contract

quest hydration 继续可以写：

- `quest_root/literature/*`
- `quest_root/paper/references.bib`

但这些输出必须被定义为：

- 从 workspace canonical literature + study reference context materialize 出来的 runtime local surfaces

而不是 quest 自己长期持有的 authority truth。

## 7. Fail-Closed 规则

这条知识/文献合同也必须 fail-closed：

- workspace canonical literature registry 缺失时，不得把 quest-local cache 静默当成长期 authority。
- study reference context 缺失时，不得把当前 quest working set 误报成 study-approved anchor set。
- external research 报告只能作为 enrichment surface，不得直接替代 workspace canonical literature。
- `paper_urls` 与 `reference_papers` 若仍作为启动输入存在，它们必须被受控吸收到 workspace / study layer，而不是永远停在 quest ingress。
- `journal_shortlist_evidence` 若形成跨 study 可复用的 venue 结论，必须经受控 promotion 写回 workspace `venue_intelligence`，不能只停在单篇 study。

## 8. 推荐阶段

### P0: Contract 冻结

- 冻结 workspace / study / quest 三层知识与文献 owner 边界。
- 冻结 workspace canonical literature registry 与 study reference context 的目标表面。

### P1: Canonical Layer 落地

- 引入 workspace literature registry controller 与 status surface。
- 引入 study reference context artifact。
- 让 quest hydration 从 canonical sources materialize，而不是继续独占 owner 语义。

### P2: Runtime/Knowledge 双平面收敛

- 在 runtime plane 与 knowledge plane 都完成 authority 收敛后，再做 monorepo 级模块吸收。
- 让 knowledge plane 成为与 runtime / eval 对称的 harness OS 内部模块，而不是继续散落在 startup glue 中。

## 9. 结论

当前最合理的总结构不是：

- 所有 memory 和 literature 都继续停在 quest；

也不是：

- 所有东西都直接上提到 workspace。

正确结构是：

- workspace 持有可复用 canonical knowledge / literature；
- study 持有本研究线的 reference context；
- quest 持有 runtime local materialization。

这样同一 disease workspace 才真正像一个长期研究资产层，而不是若干 quest 的松散集合。
