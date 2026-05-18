# 当前状态

**更新时间：2026-05-18**

## 当前角色

`Med Auto Science` 是医学研究 domain agent，也是 OPL-compatible package。单一 MAS app skill 是 direct path 的稳定入口；经 OPL 托管时，OPL 只承载 stage-led runtime、attempt、queue、human gate transport、generated surface、projection 和 App/workbench shell。

MAS 持有医学研究 truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body/writeback decision、artifact/package authority、runtime-facing owner receipt/projection、typed blocker 和 safe action refs。OPL 不写 MAS study truth、memory body、publication verdict、artifact authority 或 `current_package`。

`Codex CLI` 是当前第一公民 executor。其他 executor adapter 只能显式接入，并只保证接入、生命周期、回执与审计边界，不承诺行为效果等价。

MDS / DeepScientist 当前只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference，不是 MAS 默认 backend。

## 当前运行与文档事实

- Direct MAS app skill path 与 OPL-hosted path 共享同一 MAS-owned stage、controller、durable truth、quality verdict 和 artifact surface。
- `product-entry-manifest`、sidecar export、contracts、runtime/controller surfaces 和 workspace artifact receipts 是当前机器真相；`docs/**` 只做解释、导航、治理和 provenance。
- MAS 标准 pack / generated-interface source 已在 repo contracts 中声明 domain descriptor、pack compiler input、generated surface handoff、action catalog、stage control plane、memory descriptor、artifact locator contract、owner receipt contract、functional privatization audit 和 private functional surface policy。
- `functional_consumer_boundary` 已完成通用功能面分类与禁回流 guard：`classification_gap_count=0`、`active_private_generic_residue_count=0`。
- 当前仍有 5 项功能/结构 follow-through：`functional_structure_gap_count=5`。尚未关闭的结构 gate 是 `generated_surface_active_caller_cutover`、`refs_only_adapter_thinning`、`legacy_cleanup_physical_retirement`、`opl_app_workbench_drilldown` 和 `lifecycle_locator_retention_restore_ledger_reconciliation`。
- 旧 MDS physical root / monolith binding / legacy provenance 只作为 archive、tombstone 或 refs-only historical fixture 读取；不得回写成 current runtime owner。
- dated closeout、follow-through 和修复流水已经移到 [MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)，不再作为 `docs/status.md` 当前结论展开。

## 当前功能/结构差距

1. `generated_surface_active_caller_cutover`
   MAS 当前仍有 handwritten CLI/MCP/Skill/product-entry/sidecar/status/workbench/projection/test-lane bridge；不能声明 OPL generated/hosted active caller cutover 已完成。

2. `refs_only_adapter_thinning`
   runtime lifecycle SQLite、paper outbox、storage maintenance、publication-route memory transport、artifact lifecycle audit、terminal attach 和 runtime supervisor shell 仍需证明只消费 OPL replacement 或降到 refs-only domain authority。

3. `legacy_cleanup_physical_retirement`
   local LaunchAgent install path、workspace-local wrapper、旧 status/remove cleanup diagnostic、旧 alias/facade/test entry 仍需按 no-active-caller proof 物理删除或 tombstone；不保留兼容别名。

4. `opl_app_workbench_drilldown`
   MAS Progress Portal / workspace cockpit 仍是 active bridge；目标是 OPL App/workbench 承接 operator shell，MAS 只给 refs、owner receipt、typed blocker 和 safe action refs。

5. `lifecycle_locator_retention_restore_ledger_reconciliation`
   OPL-owned lifecycle index / cleanup / restore ledger 还未被 MAS active callers 充分消费；MAS SQLite 只能保留 domain receipt/ref sidecar 与 artifact authority refs。

## 当前测试/证据差距

以下属于证据门，不能替代上面的功能/结构收口：

- 真实 paper-line provider apply。
- publication-route memory receipt scaleout。
- artifact lifecycle receipt scaleout。
- human gate / resume / explicit wakeup owner-chain 运行证明。
- provider SLO long soak。

## 当前完善顺序

1. 用真实 paper-line provider apply 验证 OPL provider -> MAS sidecar -> MAS owner chain 能持续返回 owner receipt、progress delta 或 typed blocker。
2. 扩展 publication-route memory accepted/rejected/blocked writeback receipts。
3. 扩展 artifact lifecycle mutation / cleanup / restore / retention guarded receipts。
4. 验证 human gate、resume、explicit wakeup 与 owner route 不越过 MAS quality gate 或 artifact authority。
5. 关闭结构 gate：generated/hosted active caller cutover、refs-only thinning、legacy physical retirement、OPL workbench drilldown 和 lifecycle index reconciliation 必须逐项拿到 runtime/contract/test proof。

## 当前不能声明

- 不能声明 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能把分类闭合、descriptor ready、local LaunchAgent no-active-caller proof 或 selected proof 写成功能/结构 follow-through 已关闭、真实 paper closure、publication-ready、artifact mutation authorization 或 provider long-soak 已完成。
- 不能在 5 项功能/结构 follow-through 仍存在时声明 `functional_structure_gap_count=0`。
- 不能把 dated specs、dated closeout、修复流水或历史 full record 当成 current truth。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。

## 下一跳

- 目标态：[MAS 理想目标态](./references/positioning/mas_ideal_state.md)
- 差距与顺序：[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)
- 文档治理：[MAS 文档组合治理](./docs_portfolio_consolidation.md)
- 过程归档：[MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)
