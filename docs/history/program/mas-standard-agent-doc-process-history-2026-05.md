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

### 2026-05-30 owner-chain refs-only refresh 与 DM003 current-owner foldback

同日 owner-chain latest refresh 继续把 OPL domain-dispatch workorder 回查到 MAS owner surface，并记录 success refs path 或 typed-blocker refs path。过程性 receipt IDs、per-attempt counters、record / verify preflight 和具体 no-forbidden-write refs 属于 OPL runtime ledger / action receipt history；active docs 只保留 latest current readout。

本轮 latest post-verify readout 为 `open_worklist_item_count=0`、`open_safe_action_payload_required_item_count=0`、`open_safe_action_payload_free_item_count=0`、`closed_refs_only_item_count=430`、`domain_dispatch_evidence_receipt_item_count=388`、`domain_dispatch_evidence_workorder_count=0`、`stage_receipt_freshness_open_workorder_count=0`。本轮新增 success owner-receipt refs-only receipt `opl://external-evidence/medautoscience/domain_dispatch:medautoscience:sat_d9a709c902ff095f3573ccab`，receipt refs 为 `studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_execution/sat_d9a709c902ff095f3573ccab.closeout.json`，owner-chain refs 为 `studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/publication_eval/ai_reviewer_responses/20260530T094529Z_publication_eval_record.json` 与 `studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller_decisions/latest.json`，`receipt_semantics=domain_owned_receipt_ref`。Framework readiness 仍是 `framework_control_plane_available_with_blocked_refs_only_attention`，`evidence_envelope_blocked_count=1290`、`domain_dispatch_attention_count=11`；zero-open worklist 仍显式不等于 completion、domain-ready 或 production-ready。App/operator drilldown 显示 `domain_dispatch_evidence_current_default_actionable_attempt_count=0`、`domain_dispatch_evidence_receipt_action_route_count=0`、`app_operator_production_evidence_tail_open_item_count=0`，但 App release/user path 与 Codex App runtime evidence action route 仍为 0，不能写成 App release closeout 或 production long-soak。

本轮追加 provenance：`sat_e751c4fc044fa19dcef294f9` 由 MAS owner surface 生成 success refs path，OPL verify receipt 为 `opl://external-evidence/medautoscience/domain_dispatch:medautoscience:sat_e751c4fc044fa19dcef294f9`；`sat_692da0876d18ea13f46396f7` 由 MAS owner surface 生成 `dispatch_superseded_by_current_owner_route` typed-blocker path，OPL verify receipt 为 `opl://external-evidence/medautoscience/domain_dispatch:medautoscience:sat_692da0876d18ea13f46396f7`。两条 receipt 都是 refs-only ledger closure，不授权 MAS truth、paper body、artifact body、memory body、quality/export verdict、domain-ready 或 production-ready。

同轮还把 DM003 `study_progress` current-owner read-model 从 stale `external_supervisor` repair lifecycle 折回当前 OPL terminal handoff：repo-local clean-runner projection 显示 `ai_repair_lifecycle=null`，并把 next owner/action 指向最新 terminal handoff 的 MAS owner action。具体 owner/action 是 volatile live projection，不作为历史归档的稳定事实；该 foldback 是 status/currentness 修复和 owner-chain 接力显示修复，不写真实 paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、memory body 或 artifact body，也不声明 paper closure、publication-ready、domain-ready、production-ready 或 global completion。

## 当前归档后的文档职责

- `docs/status.md`：只保留最新状态和当前差距。
- `docs/active/mas-ideal-state-gap-plan.md`：只保留当前差距、分类、完善顺序和不能误写口径。
- `docs/references/positioning/mas_ideal_state.md`：只保留 north-star 目标态和长期 owner boundary。
- `docs/docs_portfolio_consolidation.md`：只保留文档生命周期治理规则。
- `docs/active/README.md`：只作为 active 文档索引，不承载过程流水。

后续如果又产生 dated follow-through，应追加到 history/provenance 或对应 history 子目录；主文档只吸收当前结论。
