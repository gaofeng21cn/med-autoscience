# Docs lifecycle 审计记录 2026-05-17

Owner: `MedAutoScience`
Purpose: `docs_lifecycle_audit_record`
State: `support_reference`
Machine boundary: 本文是人读审计记录，不是执行队列、runtime truth、policy truth 或机器合同。机器真相继续归 contracts、source、runtime/controller surfaces、product-entry manifest、sidecar receipt 和真实 workspace artifact。

## 审计基准

本轮审计以以下当前 owner surface 为准：

- [MAS 理想目标态](../positioning/mas_ideal_state.md)
- [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)
- `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md`
- MAS 核心五件套、[文档组合治理](../../docs_portfolio_consolidation.md) 和各目录 README

固定边界：

- MAS 持有医学研究 truth、quality verdict、publication/artifact authority、publication-route memory body、memory writeback decision、domain transition table、owner receipt、typed blocker 和 safe action refs。
- OPL 持有通用 scheduler、queue、attempt ledger、state-machine runner、workspace/source shell、memory locator/index、artifact lifecycle、workbench shell、observability/SLO 和 provider transport。
- MDS / DeepScientist 只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream intake 或 parity oracle reference。

## 覆盖方式

1. 用 `git ls-files 'docs/**/*.md' 'docs/*.md'` 列出全量 docs，并按 canonical taxonomy 分类：root 7、active 10、delivery 17、history 99、policies 25、product 2、public 1、references 31、runtime 33、source 1、specs 1。
2. 用 `rg` 复扫高风险词面：`Domain Harness OS`、`Open Harness OS`、`outer_loop_wakeup`、`Hermes-first`、`gateway/frontdoor/federation`、`local scheduler`、`LaunchAgent`、`generic runtime/scheduler`、`default MDS`、`DeepScientist`、`program/`、`capabilities/`、`compatibility/shim/facade/wrapper/alias/legacy`。
3. 对非 history 命中文档逐类抽查：core five、active owner docs、runtime control/contracts/display/projection、delivery/medical-display、references/mainline/integration/mds-parity/med-deepscientist/workspace、policies、thin public/product/source/specs index。
4. 对 history 层检查入口是否说明历史读法，确认旧 Domain Harness OS、outer-loop、Hermes-first、gateway/MDS/default path 只能作为 provenance 读取。

## 本轮处置

- `docs/active/ai_first_paper_autonomy_closure_program.md` 改为中文 canonical active target 文档，只保留 P0 paper autonomy 目标、验收合同、gate 分类和 owner 跳转；详细历史回到 full record。
- `docs/active/mas_single_project_mds_absorb_program.md` 改为中文 canonical landed foundation 文档，只保留 P3 当前 owner split、MDS retained-role 分类、禁止用途和验证口径；完整历史回到 full record。
- `docs/active/opl_temporal_mas_runtime_retirement_program.md` 收紧 P2 口径：默认 scheduler owner 已迁到 OPL，local 只做 explicit legacy cleanup；Portal/Live Console/study-progress/cockpit 只读展示，不再表述为 MAS generic runtime/workbench owner。
- `docs/references/README.md` 改为中文 canonical reference index，并补 reference 层保留高风险词面时必须回指当前 MAS/OPL owner 边界的规则。
- `docs/references/positioning/` 只保留 MAS 当前理想目标态；`Research Foundry` positioning、medical phase ladder 和 repo split 三份旧框架定位材料迁入 `docs/history/positioning/`。
- `docs/delivery/medical-display/README.md` 补 owner、purpose、state、machine boundary，并把标题和表头改为中文 canonical。
- `docs/history/README.md` 去掉伪双语切换残留，保持 history-only 读法。

## 剩余命中解释

复扫后仍保留的高风险词面分三类：

- 核心五件套、ideal state、gap plan、program portfolio、current development lines 中的命中用于声明 current boundary、superseded 决策或 direct retirement 规则。
- runtime/control/contracts 中的 `local scheduler`、`LaunchAgent`、`Hermes` 命中用于描述当前显式 diagnostic / cleanup bridge、legacy diagnostic adapter 或 forbidden-write boundary；默认 owner 已写为 OPL replacement。
- history、mds-parity、med-deepscientist reference 中的旧 MDS / DeepScientist / Hermes / Domain Harness OS / Research Foundry / gateway / compatibility 命中只作为 provenance、fixture、archive import、backend audit、upstream intake 或 parity oracle reference。

后续若发现 active/reference/spec 文档把上述词面写成默认 runtime、default dependency、active backlog 或兼容接口，应优先归档到 history 或改写为 current owner boundary；满足 no-active-caller、无 fixture/provenance 必需和 replacement proof 时，旧 alias/wrapper/facade/test entry 直接退役，不新增兼容层。
