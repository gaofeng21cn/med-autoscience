# 参考材料

Owner: `MedAutoScience`
Purpose: `support_reference_index`
State: `active_support`
Machine boundary: 人读参考索引。机器真相继续归 contracts、schemas、source、runtime/controller surfaces、product-entry manifest、sidecar receipt 和真实 workspace artifact。

本目录保存支撑材料。References 解释背景、集成形态、parity 证据、定位、workspace 语境和验证历史；它们不拥有执行 gate、runtime truth、publication authority 或 artifact authority。

| 目录 | 用途 |
| --- | --- |
| [mainline](./mainline/) | 当前 MAS 质量、自治、模块化、修复优先级和文档治理参考。 |
| [integration](./integration/) | Codex/plugin、OPL handoff、product-entry、family integration 和 Stage-Led Autonomy family inventory 参考。 |
| [mds-parity](./mds-parity/) | MDS 行为/能力 parity、WebUI cleanroom 行为和用户体验差距评估。 |
| [positioning](./positioning/) | MAS 当前理想目标态定位。旧 Domain/Harness OS、Open Harness OS 与 Research Foundry 梯子材料已归入 `docs/history/positioning/`。 |
| [verification](./verification/) | 完成 ledger 和真实 study 验证记录。 |
| [workspace](./workspace/) | Workspace 架构和 quickstart 参考。 |
| [med-deepscientist](./med-deepscientist/README.md) | 上游学习、provenance、method 和 deconstruction 参考。 |

## 生命周期规则

Reference 如果变成当前执行队列，应迁入 `docs/active/`；如果变成稳定规则，应迁入 `docs/policies/`；如果变成完成快照或退役 board，应归档到 `docs/history/`。

## 定位参考

- [MAS 理想目标态](./positioning/mas_ideal_state.md)：MAS 作为医学研究 domain agent 的 north-star 目标边界，以及它与 OPL、workspace、runtime artifact、quality gate、memory 和 workbench 的理想分工；当前差距和完善计划读 [MAS 理想目标态差距与完善计划](../active/mas-ideal-state-gap-plan.md)。
- [Docs lifecycle 审计记录 2026-05-17](./mainline/docs_lifecycle_audit_2026_05_17.md)：本轮逐类审计覆盖方式、处置摘要和剩余历史词面读法。

旧 `Domain Harness OS`、`Open Harness OS`、`Research Foundry` 梯子和 Hermes/MDS 默认链路相关材料只作为历史定位读取，入口见 [Positioning 历史归档](../history/positioning/README.md)。任何 reference 文档若需要保留这些词面，必须同时写清当前 owner：MAS 持有医学 truth/quality/artifact/memory body/owner receipt，OPL 持有通用 runtime/queue/attempt ledger/state-machine runner/workspace-source shell/memory locator/artifact lifecycle/workbench/observability。
