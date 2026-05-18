# MAS standard agent 文档过程归档 2026-05

Owner: `MedAutoScience`
Purpose: `process_history_provenance`
State: `history_only`
Machine boundary: 本文是人读历史摘要，不是 current truth、contract、runtime surface、owner receipt 或执行队列。
Date: `2026-05-18`

## 归档口径

本文保存 2026-05 中 MAS 向标准 OPL Agent 形态收敛时的过程性摘要。当前定位、当前边界、当前差距和完善顺序以以下文档为准：

- [当前状态](../../status.md)
- [MAS 理想目标态](../../references/positioning/mas_ideal_state.md)
- [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)
- [MAS 文档组合治理](../../docs_portfolio_consolidation.md)

本文不改写 `docs/decisions.md` 的日期日志，也不把 dated specs 当成 current truth。

## 过程摘要

### OPL provider 与 MAS owner receipt 边界

2026-05 中，MAS 文档多次校准 OPL provider proof 与 MAS paper closure 的边界。OPL provider proof、provider attempt availability、guarded apply receipt、source-keyed dispatch 和 `mas_owner_receipt_present` 只能证明框架 attempt 与 MAS owner surface 能连接并返回稳定 receipt / blocker；它们不授权 paper closure、publication-ready、artifact mutation 或 `current_package` 写入。

### Scheduler owner 迁移

默认 supervision scheduler owner 已迁到 OPL replacement。MAS 默认 CLI/status/bootstrap 不再安装或刷新本机 LaunchAgent；显式 local path 只保留 status/remove cleanup diagnostic、provenance 和 drift guard。该过程关闭的是默认 caller / install path 回流风险，不等于 live soak 或 paper-line production closure。

### Workspace / legacy physical cleanup

现有论文 workspace migration 清理了 active binding / snapshot 层的旧 MDS runtime 污染；legacy physical cleanup 将旧 `ops/med-deepscientist` physical root 归入 archive/tombstone/ref-only surface。该过程不写 `current_package`、`publication_eval/latest.json`、`controller_decisions/latest.json`、paper/submission package、runtime SQLite 或 restore archive，也不构成 paper closure。

### Functional consumer boundary 与 privatization 盘点

MAS functional consumer boundary 已把通用 scheduler、daemon、queue、attempt ledger、generic runner、generic transition runner、generic workbench、memory locator、artifact lifecycle 和 observability 归为 OPL-owned / OPL-consumed surface。MAS retained authority surface 被限定为 study truth、publication quality verdict、artifact authority、publication-route memory body、memory writeback decision、domain transition table、owner receipt、typed blocker 和 safe action refs。

后续 functional module inventory 形成 18 项代码路径级清单，分类为 declarative pack / generated surface、refs-only adapter、minimal authority function、legacy cleanup no-active-caller gate。该分类完成第一轮机器面整理，但不是功能/结构完成声明。

### Consumer thinning follow-through

2026-05-17/18 的 consumer thinning closeout 把当前状态拆成两层：

- 第一层：未分类 generic owner 回流关闭，`classification_gap_count=0`、`active_private_generic_residue_count=0`。
- 第二层：follow-through 仍打开，`functional_structure_gap_count=5`。

仍打开的 5 项功能/结构差距是 OPL generated surface active caller cutover、refs-only adapter 收薄、legacy physical retirement、OPL App drilldown、lifecycle locator/retention/restore ledger 对账。

真实 paper apply、memory receipt、artifact receipt、human gate/resume 和 provider SLO 是测试/证据差距，不能替代上述功能/结构收口。

### Transition / receipt / AI reviewer 过程修复

过程中还出现多项控制面修复和 guard：

- publication-route memory writeback receipt 被纳入 transition oracle，但只作为 body-free refs/counts/blocker inspect，不授权 quality、submission 或 generic runner resume。
- completion receipt、delivered package、human gate、stop-loss、fail-closed、owner apply/artifact-delta handoff 开始共同阻断旧 prompt、旧 closeout 和旧 authorization redrive。
- runtime turn closeout 的非 JSON artifact refs 只作为 opaque evidence refs 保留。
- AI reviewer workflow 要求 reviewer-owned record 与 future-facing limitations plan，mechanical projection 不能作为 AI reviewer record。
- explicit wakeup、human takeover resume、managed AI reviewer redrive、clean paper-authority migration 和 publication surface self-stop guard 均按 MAS owner route / quality gate / current authority 边界修复。

这些都是过程性 guard 与 currentness 修复，不应在主文档中展开成流水。

## 当前归档后的文档职责

- `docs/status.md`：只保留最新状态和当前差距。
- `docs/active/mas-ideal-state-gap-plan.md`：只保留当前差距、分类、完善顺序和不能误写口径。
- `docs/references/positioning/mas_ideal_state.md`：只保留 north-star 目标态和长期 owner boundary。
- `docs/docs_portfolio_consolidation.md`：只保留文档生命周期治理规则。
- `docs/active/README.md`：只作为 active 文档索引，不承载过程流水。

后续如果又产生 dated follow-through，应追加到 history/provenance 或对应 history 子目录；主文档只吸收当前结论。
