# Study Workflow

Status: `policy index`
Owner: `MedAutoScience`
Purpose: 作为 MAS 研究路线、研究记忆、论文套路、数据资产和工作流规则的总入口。

## 总入口

- [Stage-Led Research Autonomy Policy](./stage_led_research_autonomy.md)
- [Publication Route Memory Policy](./publication_route_memory_policy.md)
- [Study Archetypes](./study_archetypes.md)
- [Research Route Bias Policy](./research_route_bias_policy.md)
- [Study Route Contract](./study_route_contract.md)
- [Data Asset Management](./data_asset_management.md)
- [Submission Revision Operating Contract](./submission_revision_operating_contract.md)
- [Bounded Analysis Frontier Policy](./bounded_analysis_frontier_policy.md)
- [Workspace Autoscience Rules](./workspace_autoscience_rules.md)

## 现在的读法

MAS 的论文套路经验库已经按 `publication_route_memory` 落地为可检索、可回写的自然语言 memory card。它的设计目标是“给 Codex CLI 提供可参考的经验”，不是把研究过程做成强 schema 的 recipe engine。

当前可用形态是：

- small-set route memory cards
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
| 第一代路线种子 | [Study Archetypes](./study_archetypes.md) | 查看当前高产出论文套路的 prose 入口：`clinical_classifier`、`clinical_subtype_reconstruction`、`external_validation_model_update`、`gray_zone_triage`、`llm_agent_clinical_task`、`mechanistic_sidecar_extension`、`survey_trend_analysis`。 |
| repo seed fixture | [publication_route_memory_seed_fixture.json](./publication_route_memory_seed_fixture.json) | 查看首批可迁移 seed card 示例；它不是真实 memory store。 |
| workspace memory pack | `portfolio/research_memory/publication_route_memory/memory_pack.json` | 查看某个 MAS workspace 内真正可检索的论文套路 memory cards。 |
| receipts/proposals | `portfolio/research_memory/publication_route_memory/{migration_receipts,writeback_proposals,writeback_receipts}` | 查看 seed apply、typed closeout proposal 和 MAS router 接受/拒绝记录。 |
| 只读 CLI inventory | `medautosci publication route-memory-inventory --workspace-root <workspace>` | 按 workspace/stage/route family/status 查看 card 元数据、locator 和 receipt summary；默认不输出 memory 正文。维护者显式加 `--include-card-body` 时才输出 prose / failure modes。 |

当前真实样例在 DM-CVD workspace：

- `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/publication_route_memory/memory_pack.json`
- 当前包含 `3` 张 card：`publication_route_memory_seed__external_validation_rescue`、`publication_route_memory_seed__negative_result_stoploss`、`publication_route_memory_writeback__dm002-route-memory-proof`
- 对应 receipt/proposal 位于同目录下的 `migration_receipts/`、`writeback_proposals/`、`writeback_receipts/`

这些 JSON 现在已经方便维护者阅读和审计，但还不是面向普通用户的编辑 UI。安全管理路径应优先使用 MAS owner CLI/controller surface 生成 pack、proposal 和 receipt；手工编辑 workspace pack 只应作为 maintainer-level 修复，并保持 `memory_id`、stage applicability、source/provenance、status 和 receipt refs 可追溯。

## 现阶段边界

当前已经落地的是 thin but real 的 MAS memory surface。与理想形态的差距主要在：

- OPL 生产级 provider residency
- 真实 paper-line 长时 soak
- human gate / resume 的运行证明
- workspace/runtime memory writeback receipt 在更多真实论文线上的泛化
- 面向普通用户的 OPL/App 分组展示与编辑/审核工作台
- 少量 legacy residue 清理

因此，`publication_route_memory` 现在应按“可用的自然语言经验记忆”理解，不按“完整的自动论文套路引擎”理解。

## 现在适合继续落地

- 继续把真实 paper stage closeout 中的可复用 lesson 写成 natural-language memory card，并通过 `memory_write_router_receipt` 接受或拒绝。
- 给每个活跃 MAS workspace 保持 `publication_route_memory/memory_pack.json`、migration receipt、writeback proposal、writeback receipt 完整可查。
- 使用 `medautosci publication route-memory-inventory --workspace-root <workspace>` 做默认 body-free 的维护者/OPL 只读查看；需要审查正文时再加 `--include-card-body`。
- 在 OPL/Aion 侧只展示 consumed memory refs、writeback receipt refs、rejected reason 和 freshness，不复制 memory 正文、不接受/拒绝 writeback。
- 继续把 OPL/Aion 展示收敛为 ref-only 分组，而不是把 memory body 复制到 OPL。

暂缓的内容：

- 通用 recipe engine；
- 自动 winning-route scorer；
- 把 50 种套路塞进系统提示词；
- 让 OPL 持有 MAS memory body 或 publication route decision。
