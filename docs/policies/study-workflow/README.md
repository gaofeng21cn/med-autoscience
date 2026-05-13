# Study Workflow

Status: `policy index`
Owner: `MedAutoScience`
Purpose: 作为 MAS 研究路线、研究记忆、论文套路、数据资产和工作流规则的总入口。

## 总入口

- [Stage-Led Research Autonomy Policy](./stage_led_research_autonomy.md)
- [Publication Route Memory Policy](./publication_route_memory_policy.md)
- [Publication Route Memory Library](./publication_route_memory_library.md)
- [Domain Memory Markdown-First Policy](../domain_memory_markdown_first_policy.md)
- [Study Archetypes](./study_archetypes.md)
- [Research Route Bias Policy](./research_route_bias_policy.md)
- [Study Route Contract](./study_route_contract.md)
- [Data Asset Management](./data_asset_management.md)
- [Submission Revision Operating Contract](./submission_revision_operating_contract.md)
- [Bounded Analysis Frontier Policy](./bounded_analysis_frontier_policy.md)
- [Workspace Autoscience Rules](./workspace_autoscience_rules.md)

## Memory 分层

MAS 的 memory 现在按统一逻辑管理，不按每一层各自发明一条链路：

| 层 | 记录什么 | 人类/Agent 正文 | 机器面 |
| --- | --- | --- | --- |
| Domain memory | MAS 跨 workspace 的医学经验，例如论文路线、route bias、审稿经验、figure/table 选择经验 | repo Markdown policy/library | seed index、workspace pack、inventory、receipt |
| Workspace memory | 同一 disease workspace 的数据情况、文献调研、可行/不可行方向、期刊邻域、跨 study recall | `portfolio/research_memory/*.md` | `registry.yaml`、literature registry、coverage、workspace packs |
| Study memory | 单篇论文的 selected/rejected line、failed path、reviewer lesson、claim boundary、route-back rationale | study notes / manuscript-facing Markdown where appropriate | `study_charter`、evidence/review ledgers、controller decisions、publication eval、claim/display maps |
| Stage memory | 单个 stage 启动前要读什么、结束后哪些 lesson 可回写 | stage notes can remain prose | `stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt`、`stage_recall_index` |
| OPL/Aion projection | 给平台和 UI 看的 refs、freshness、receipt、status | 不持有 MAS memory 正文 | body-free descriptor / inventory / receipt projection |

统一规则是：给 Codex 理解和判断的自然语言经验用 Markdown 做第一公民；状态、索引、参数、receipt、gate、ledger、runtime truth 用结构化面。Stage executor 不靠全量 prompt stuffing，而是通过 `stage_knowledge_packet` 读小集合 refs、summary 和 required input refs；需要正文时回到对应 Markdown 或 MAS workspace owner surface。

## 现在的读法

MAS 的论文套路经验库已经按 `publication_route_memory` 落地为可检索、可回写的自然语言 memory card。它的设计目标是“给 Codex CLI 提供可参考的经验”，不是把研究过程做成强 schema 的 recipe engine。

当前可用形态是：

- rich natural-language route memory cards
- minimal metadata
- read-only inventory/export
- stage packet retrieval
- typed closeout writeback
- router receipt

OPL 只负责 locator、projection、receipt 和 family-level discovery；publication-route memory 的正文、接受/拒绝、路线判断和质量权威仍归 MAS。

## 论文套路经验库入口

人类用户和维护者现在按三层查阅：

| 层级 | 位置 | 用途 |
| --- | --- | --- |
| 规则入口 | [Publication Route Memory Policy](./publication_route_memory_policy.md) | 解释自然语言 memory card 的维护规则、OPL/MAS 边界、writeback 规则和迁移计划。 |
| 正文入口 | [Publication Route Memory Library](./publication_route_memory_library.md) | 维护者直接查看和编辑的论文套路经验库正文；Markdown 是 canonical body。 |
| 第一代路线种子 | [Study Archetypes](./study_archetypes.md) | 旧 MAS 使用的 route bias / contract input prose；现在也是 overlay 渲染的 Markdown-first 正文源，不是完整经验库。 |
| 第一代路线偏置 | [Research Route Bias Policy](./research_route_bias_policy.md) | 旧 MAS 使用的 route-bias prose；现在是 overlay 渲染的 Markdown-first 正文源，不是 route scorer。 |
| repo seed index | [publication_route_memory_seed_fixture.json](./publication_route_memory_seed_fixture.json) | 9 张 seed card 的机器索引和 Markdown locator；不是 memory 正文，也不是真实 memory store。 |
| workspace memory pack | `portfolio/research_memory/publication_route_memory/memory_pack.json` | 某个 MAS workspace 内应用/回写后的可检索 memory pack；它是生成面，不是维护者第一编辑面。 |
| receipts/proposals | `portfolio/research_memory/publication_route_memory/{migration_receipts,writeback_proposals,writeback_receipts}` | 查看 seed apply、typed closeout proposal 和 MAS router 接受/拒绝记录。 |
| 只读 CLI inventory | `medautosci publication route-memory-inventory --workspace-root <workspace>` | 按 workspace/stage/route family/status 查看 card 元数据、locator 和 receipt summary；默认不输出 memory 正文。维护者显式加 `--include-card-body` 时才输出 rich body sections。 |

`study_archetypes.md` 不是论文套路 domain memory 的完整存储位置。它是第一代入口，旧 MAS 通过 profile / study payload 的 `preferred_study_archetypes`、`study_archetype` 或 `preferred_study_archetype` 选择分析和报告合同；真正的人类维护入口现在是 `publication_route_memory_library.md`。`publication_route_memory_seed_fixture.json` 只做索引和 locator，workspace `memory_pack.json`、`stage_knowledge_packet.publication_route_memory_refs`、`stage-memory-closeout-route` 和 `route-memory-inventory` 是应用、检索、回写与审计面。

`stage_route_contract.yaml` 不归类为 memory。它位于 `agent/stages/stage_route_contract.yaml`，是 MAS route/stage contract 的 canonical structured source：`show-stage-route-contract`、stage surface contract、product-entry/family descriptors、OPL projection 和 tests 都从它读取 route ids、entry mode、success gate、durable outputs、human gate、route-back triggers 与 knowledge/closeout obligations。`show-agent-entry-modes` 只是兼容别名。它可以继续生成 Markdown guide 和 Codex/OpenClaw entry prompt，但它本身承担 contract authority；publication-route memory 和其他自然语言经验继续由 Markdown-first memory body 管理。

当前真实样例在 DM-CVD workspace：

- `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/publication_route_memory/memory_pack.json`
- 当前包含 `3` 张 card：`publication_route_memory_seed__external_validation_rescue`、`publication_route_memory_seed__negative_result_stoploss`、`publication_route_memory_writeback__dm002-route-memory-proof`
- 对应 receipt/proposal 位于同目录下的 `migration_receipts/`、`writeback_proposals/`、`writeback_receipts/`

这些 JSON 现在已经方便维护者阅读和审计，但还不是面向普通用户的编辑 UI。安全管理路径应优先使用 MAS owner CLI/controller surface 生成 pack、proposal 和 receipt；手工编辑 workspace pack 只应作为 maintainer-level 修复，并保持 `memory_id`、stage applicability、source/provenance、status、rich body 和 receipt refs 可追溯。

当前推荐查看方式：

```bash
medautosci publication route-memory-inventory --workspace-root /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk
medautosci publication route-memory-inventory --workspace-root /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk --stage decision
```

2026-05-12 fresh output 显示 DM-CVD workspace 的旧 pack 共有 `3` 张 card；`--stage decision` 过滤后有 `2` 张，分别是 `publication_route_memory_seed__negative_result_stoploss` 和 `publication_route_memory_writeback__dm002-route-memory-proof`。当前 repo Markdown library 已扩展为 `9` 张富文本 seed cards，seed fixture 只做索引；新 workspace 或重新应用 seed 后会得到完整 seed library。默认输出不含 memory 正文，适合 OPL/Aion 和维护者快速查 inventory；审查正文时才使用 `--include-card-body`。

## 现阶段边界

当前已经落地的是 MAS-owned rich natural-language memory surface。OPL 平台也已经从 descriptor-only 往前推进：family agent / stage / domain-memory 三个索引都能解析 MAS/MAG/RCA，Temporal provider core、attempt start/query/signal、residency proof 和 Codex runner harness 已进入 OPL 仓。与理想形态的差距主要在：

- 外部 production Temporal provider residency 和 managed worker 长驻
- 真实 paper-line 长时 soak
- human gate / resume 的运行证明
- workspace/runtime memory writeback receipt 在更多真实论文线上的泛化
- 面向普通用户的 OPL/App ref-only 分组展示
- 带 receipt generation / provenance / deprecation / stale review 的编辑审核工作台
- 少量 legacy residue 清理

因此，`publication_route_memory` 现在应按“可用的自然语言经验记忆”理解，不按“完整的自动论文套路引擎”理解。

## 现在适合继续落地

- 继续把真实 paper stage closeout 中的可复用 lesson 写成 natural-language memory card，并通过 `memory_write_router_receipt` 接受或拒绝。
- 给每个活跃 MAS workspace 保持 `publication_route_memory/memory_pack.json`、migration receipt、writeback proposal、writeback receipt 完整可查。
- 使用 `medautosci publication route-memory-inventory --workspace-root <workspace>` 做默认 body-free 的维护者/OPL 只读查看；需要审查正文时再加 `--include-card-body`。
- 把 DM002 之外的真实 paper closeout 继续通过 MAS router 生成 accepted/rejected writeback receipt，优先补足负结果/止损、外部验证/模型更新、审稿返修路线三类高频经验。
- 在 OPL/Aion 侧先做按 workspace、stage、route family、status、receipt freshness 的 ref-only 分组展示。
- 给 memory card 补 maintainer-level `status` 纪律，例如 active、draft_seed、deprecated、stale_review_needed；状态仍由 MAS workspace owner surface 和 receipt 支撑。
- 在 OPL/Aion 侧只展示 consumed memory refs、writeback receipt refs、rejected reason 和 freshness，不复制 memory 正文、不接受/拒绝 writeback。
- 继续把 OPL/Aion 展示收敛为 ref-only 分组，而不是把 memory body 复制到 OPL。

暂缓的内容：

- 通用 recipe engine；
- 自动 winning-route scorer；
- 把 50 种套路塞进系统提示词；
- 让 OPL 持有 MAS memory body 或 publication route decision。
