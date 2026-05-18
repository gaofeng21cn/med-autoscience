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
- `functional_consumer_boundary` 已完成分类、cutover、refs-only 收薄、legacy retirement、OPL App drilldown 和 lifecycle ledger 对账证明：`classification_gap_count=0`、`active_private_generic_residue_count=0`、`functional_structure_gap_count=0`。
- 当前 `remaining_gap_classification=live_provider_paper_line_evidence_gates`。剩余缺口只允许是真实 paper-line provider apply、publication-route memory receipt scaleout、artifact lifecycle receipt scaleout、human gate / resume owner-chain 和 provider SLO long soak；不得把这些证据门回写成功能/结构 gap。
- 旧 MDS physical root / monolith binding / legacy provenance 只作为 archive、tombstone 或 refs-only historical fixture 读取；不得回写成 current runtime owner。
- dated closeout、follow-through 和修复流水已经移到 [MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)，不再作为 `docs/status.md` 当前结论展开。

## 当前功能/结构 closure

当前 5 项原功能/结构 gate 已关闭：

1. `generated_surface_active_caller_cutover`
   OPL generated / hosted surface active caller 已切到 OPL generated/hosted surface 或 MAS domain handler target；MAS 不把 generic wrapper 写成长期 owner。

2. `refs_only_adapter_thinning`
   runtime lifecycle SQLite、paper outbox、storage、publication-route memory transport、artifact lifecycle audit、terminal attach 和 projection 只暴露 body-free locator、receipt、blocker、authority refs 或 diagnostic exporter。

3. `legacy_physical_retirement`
   local LaunchAgent install path、workspace-local wrapper、旧 status/remove cleanup diagnostic、旧 alias/facade/test entry 已按 no-active-caller proof 删除、tombstone 或降为 history/provenance。

4. `opl_app_drilldown`
   OPL App / workbench 消费 MAS refs-only payload，按 owner receipt refs、typed blockers、freshness、source/artifact/memory refs 和 safe action refs 做 drilldown；不写 MAS truth、memory body、artifact body 或 publication verdict。

5. `lifecycle_locator_retention_restore_ledger_reconciliation`
   lifecycle locator、retention、restore、cleanup ledger 与 workspace/runtime artifact root locator 完成 OPL-owned lifecycle index / cleanup / restore proof refs 对账；MAS 只保留 artifact authority、receipt refs 和 guarded permission。

## 当前测试/证据差距

以下属于证据门，不再计入功能/结构 gap：

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
5. 做 provider SLO long soak、restart/re-query、retry/dead-letter 和 no-forbidden-write 长窗口验证。

## 当前不能声明

- 不能声明 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能把结构 closure 写成真实 paper closure、publication-ready、artifact mutation authorization 或 provider long-soak 已完成。
- 不能把已关闭的 generated surface cutover、refs-only adapter 收薄、legacy physical retirement、OPL App drilldown 或 lifecycle ledger 对账重新列为 active 功能/结构 gap；若新发现回流，应作为 regression 修复。
- 不能把 dated specs、dated closeout、修复流水或历史 full record 当成 current truth。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。

## 下一跳

- 目标态：[MAS 理想目标态](./references/positioning/mas_ideal_state.md)
- 差距与顺序：[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)
- 文档治理：[MAS 文档组合治理](./docs_portfolio_consolidation.md)
- 过程归档：[MAS standard agent 文档过程归档 2026-05](./history/program/mas-standard-agent-doc-process-history-2026-05.md)
