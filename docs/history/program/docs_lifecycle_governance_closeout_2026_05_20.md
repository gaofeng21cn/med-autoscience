# Docs lifecycle governance closeout 2026-05-20

Owner: `MedAutoScience`
Purpose: `docs_lifecycle_governance_closeout`
State: `history_provenance`
Machine boundary: 本文是人读历史归档。机器真相继续归核心五件套、`agent/`、`contracts/`、source、runtime/controller surfaces、product-entry manifest、sidecar receipt、owner receipts 和真实 workspace evidence。

## 本轮基准

本轮以四类主参考校准 MAS docs：

- OPL family 主参考：`/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md` 与 `current-state-vs-ideal-gap.md`。
- MAS 目标态与 gap 主参考：[MAS 理想目标态](../../references/positioning/mas_ideal_state.md) 与 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)。
- MAS 核心五件套：[项目概览](../../project.md)、[架构](../../architecture.md)、[不可变约束](../../invariants.md)、[关键决策](../../decisions.md)、[当前状态](../../status.md)。
- MAS 机器面：`agent/` pack、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json`、`contracts/production_acceptance/mas-production-acceptance.json`、action catalog、product-entry manifest、sidecar surfaces 和 CLI package entry。

## 当前归档结论

- `docs/status.md` 不再承载 dated follow-up ledger。它只保留当前角色、当前机器事实、功能/结构状态、物理源码形态差距、测试/证据差距、完善顺序和不能误写口径。
- `docs/active/current-development-lines.md` 是唯一执行地图，按 `landed_foundation`、`functional_follow_through_gate`、`production_evidence_gate` 分配后续工作。
- `docs/active/program_portfolio_consolidation.md` 是 program 文档组合治理入口，不再作为第二执行计划或第二 gap matrix。
- `docs/history/program/` 承接 dated proof、full record、旧 phase table、旧 activation package、旧 board、完整命令流水和本轮 closeout 记录。
- 对 Hermes、MDS、DeepScientist、local scheduler、gateway/frontdoor/federation、compat alias、legacy wrapper/facade 等旧语义，active 文档只能用于说明 current boundary、tombstone/provenance 或直接退役规则；history/reference 可以保留来龙去脉，但不能当 current truth。

## 本轮处置

| 文件 | 处置 |
| --- | --- |
| `docs/status.md` | 收敛为 current truth summary，移除长篇 dated process / follow-up 流水。 |
| `docs/active/current-development-lines.md` | 收敛为内容级执行地图，保留当前 lane、owner doc、gate class、下一实施单元和完成证据。 |
| `docs/active/program_portfolio_consolidation.md` | 收敛为 active program 文档唯一职责表、历史归位规则和 direct retirement rule。 |
| `docs/README.md` / `docs/active/README.md` / `docs/docs_portfolio_consolidation.md` / `docs/history/program/README.md` | 同步入口和本轮 closeout 链接。 |

## 后续维护规则

1. 新当前事实先进核心五件套、owner doc 或 machine-readable contract，不堆进 dated history。
2. 新执行计划先判断是否改变 gap plan 或 execution map；否则进入 runtime/policy/reference/history 的对应层。
3. 旧模块、旧接口、旧 CLI alias、旧 wrapper、旧 facade、旧测试入口或旧文档入口满足 no-active-caller、replacement proof、无 fixture/provenance 必需后，直接删除、archive 或 tombstone。
4. 文档和测试不得把 Markdown prose path、章节标题或旧文案当机器接口；需要机器边界时使用 schema、JSON、CLI/API payload、manifest、source path、contract 或 durable semantic ID。
5. MAS 文档只维护 MAS-owned truth、authority、direct/hosted boundary 和上收候选；OPL/MAG/RCA backlog 回各自仓或 OPL family 主参考。
