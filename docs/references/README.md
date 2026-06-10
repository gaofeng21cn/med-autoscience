# 参考材料

Owner: `MedAutoScience`
Purpose: `support_reference_index`
State: `active_support`
Machine boundary: 人读参考索引。机器真相继续归 contracts、schemas、source、runtime/controller surfaces、product-entry manifest、owner receipt 和真实 workspace artifact。

本目录保存支撑材料。References 解释背景、集成形态、parity 证据、定位、workspace 语境和 mainline assessment；它们不拥有执行 gate、runtime truth、publication authority、artifact authority 或 dated verification ledger。dated proof、real-study verification note 和过程性 audit 归 `docs/history/**`。

External-learning reference 的统一读法见 [External Learning Adoption Closure Runbook](../runtime/control/external_learning_adoption_closure.md)。本目录下的外部框架 intake 只记录 clean-room provenance、pattern classification 和 MAS-native target shape；`adopt_contract`、reference intake 或 design doc 不等于 functional landing。只有进入 owner surface、generated/read-model projection、worker/sidecar slot、callable/action catalog、quality pack consumer、controller-authorized soak 或等价 repo-native surface，并有验证证明 allowed writes、forbidden authority 和 nonblocking / fail-open 边界，才能在 status、decision 或 read-model 中写成对应层级的 landed。

| 目录 | 用途 |
| --- | --- |
| [governance](./governance/) | OPL series 文档治理与跨仓一致性巡检参考。 |
| [mainline](./mainline/) | 当前 MAS 质量、自治、模块化、修复优先级和文档治理参考。 |
| [integration](./integration/) | Codex/plugin、OPL handoff、product-entry、family integration 和 Stage-Led Autonomy family inventory 参考。 |
| [mds-parity](./mds-parity/) | MDS 行为/能力 parity、WebUI cleanroom 行为和用户体验差距评估。 |
| [positioning](./positioning/) | MAS 当前理想目标态定位。旧 Domain/Harness OS、Open Harness OS 与 Research Foundry 梯子材料已归入 `docs/history/positioning/`。 |
| [workspace](./workspace/) | Workspace 架构和 quickstart 参考。 |
| [med-deepscientist](./med-deepscientist/README.md) | 上游学习、provenance、method 和 deconstruction 参考。 |

## 生命周期规则

Reference 如果变成当前执行队列，应迁入 `docs/active/`；如果变成稳定规则，应迁入 `docs/policies/`；如果变成完成快照或退役 board，应归档到 `docs/history/`。

## 定位参考

- [MAS 理想目标态](./positioning/mas_ideal_state.md)：MAS 作为医学研究 domain agent 的 north-star 目标边界，以及它与 OPL、workspace、runtime artifact、quality gate、memory 和 workbench 的理想分工；当前差距和完善计划读 [MAS 理想目标态差距与完善计划](../active/mas-ideal-state-gap-plan.md)。
- [Docs lifecycle 审计记录 2026-05-17](../history/program/docs_lifecycle_audit_2026_05_17.md)：本轮逐类审计覆盖方式、处置摘要和剩余历史词面读法；只作 history provenance。
- [项目修补优先级图](./mainline/project_repair_priority_map.md)：旧 runtime truth / workspace knowledge / cutover tranche 的历史支撑参考。它不再承担 current execution queue 或 runtime owner truth；当前 owner 边界回到核心五件套、MAS 理想目标态、MAS 理想目标态差距计划和 runtime contracts。
- [Life Science Research Learning Intake](./mainline/life_science_research_learning_intake.md)：OpenAI Life Science Research 插件的 clean-room source discovery / evidence helper pattern 吸收记录；只作为 MAS-native source refs、typed blocker、review input 和 descriptor locator 的参考，不是外部 runtime、默认 skill source 或 authority。
- [AutoSci Learning Intake](./mainline/autosci_learning_intake.md)：`skyllwt/AutoSci` / `OmegaWiki` 的 clean-room research lifecycle pattern 吸收记录；只作为 typed graph、proposal/action discovery、negative memory、experiment lifecycle receipt、reviewer verdict mapping 和 artifact render QA contract 的参考，不是外部 runtime、slash skill、permission model 或 authority。
- [Co-Scientist Hypothesis Portfolio Intake](./mainline/co_scientist_hypothesis_portfolio_intake.md)：Google / Nature Co-Scientist 论文启发的 MAS-native hypothesis portfolio / evidence pack adoption narrative；只吸收生成、反思、ranking、proximity、evolution、meta-review 的 contract shape，ranking/Elo/proximity 只能作为 advisory signal，不能替代 MAS quality gate、human/expert gate 或 owner receipt。
- [ARK Research Workflow Intake](./mainline/ark_learning_intake.md)：`kaust-ark/ARK` 的 clean-room research workflow pattern 吸收记录；只吸收 review loop、goal anchor、issue repair validation、API-first citation、figure manifest、page adjustment、human-intervention UX、micro-study canary、operator preview、real-run closeout、compiled visual QA、semantic no-progress evidence 和 citation lifecycle queue 的 contract shape，不引入 ARK runtime、SQLite authority、conda project model、Telegram/webapp service、代码或依赖。
- [External Learning Adoption Closure Runbook](../runtime/control/external_learning_adoption_closure.md)：跨框架 landing-status 口径；用于判断 reference / contract / projection / worker / sidecar / owner surface 到底落到哪一层，以及哪些 `contract_only_gap`、`projection_only_gap`、`history_only_gap` 或 `not_landed_gap` 不能写成 landed。

旧 `Domain Harness OS`、`Open Harness OS`、`Research Foundry` 梯子和 Hermes/MDS 默认链路相关材料只作为历史定位读取，入口见 [Positioning 历史归档](../history/positioning/README.md)。任何 reference 文档若需要保留这些词面，必须同时写清当前 owner：MAS 持有医学 truth/quality/artifact/memory body/owner receipt，OPL 持有通用 runtime/queue/attempt ledger/state-machine runner/workspace-source shell/memory locator/artifact lifecycle/workbench/observability。
