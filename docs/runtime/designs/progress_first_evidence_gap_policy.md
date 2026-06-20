# Progress-First Evidence Gap Policy

Owner: `MedAutoScience`
Purpose: `progress_first_evidence_gap_policy`
State: `active_contract`
Machine boundary: 本文是人读导航。机器合同归 `contracts/evidence-gap-decision-policy.json`、`contracts/schemas/evidence-gap-decision.schema.json`、`contracts/evidence-gap-decision-examples.json`、`src/med_autoscience/evidence_gap_decision.py`、controller projection 和 tests。

## 目标结论

`missing evidence` 不再默认等于 `typed blocker`。MAS 现在先生成 `EvidenceGapDecision`，把缺口分成：

| Gap class | 当前 action | typed blocker count | 落点 |
| --- | --- | --- | --- |
| `authority_gate` | 阻断 | 是 | MAS/OPL authority、currentness、write/data/privacy 边界。 |
| `human_gate` | 阻断 | 是 | 投稿、不可逆操作、PI/user 决策。 |
| `proceed_with_assumption` | 继续 | 否 | `assumption_ledger`。 |
| `soft_quality_gap` | 继续 | 否 | `soft_gap_ledger`。 |
| `observability_backlog` | 继续 | 否 | `observability_backlog`。 |
| `evidence_tail` | 继续当前 action，阻止 readiness/complete claim | 否 | `evidence_tail_ledger`。 |

这增加了 AI 的主观能动性：AI 可以判断低风险缺口不是当前 hard stop，继续推进当前 owner action，并把缺口记录成 assumption、quality repair、observability backlog 或 evidence tail。这个自主判断不能越过 authority：缺 OPL event/outbox/StageRun readback、owner route currentness、写权限、数据/隐私权限、human/submission authorization 或 stop-loss 时仍 fail closed。

## 外部工程经验折算

- Kubernetes `validationActions` 的 Deny / Warn / Audit 模式对应 MAS 的 hard gate、soft gap 和 backlog/read-model 记账。
- OPA decision logs 的经验对应 MAS 的 `decision_trace`、identity、evidence refs、diagnostic refs 和 claim boundary。
- Temporal Signals / Queries / Updates 的 human-in-the-loop 模式对应 MAS 的 durable human gate；查询/投影只展示状态，不能替代 human owner answer。

这些是本地设计模式来源，不是新增 runtime 依赖。

## 当前落点

- Core API: `med_autoscience.evidence_gap_decision`
- Projection adapter: `med_autoscience.controllers.evidence_gap_projection.attach_evidence_gap_projection`
- Study progress payload: 附加 `evidence_gap_decisions`、summary、ledger surfaces、typed blocker count 和 forbidden claims。
- DHD read-model currentness: `domain_health_diagnostic` runtime scan 从 fresh `study_progress` currentness 携带同一 evidence-gap summary、ledger surfaces、typed blocker count 和 forbidden claims；它只做诊断投影，不从 pending count 推断 hard gate。
- Domain action materializer: action/request/transition projection 携带 evidence gap summary；hard/human gate 变成 blocked dispatch；soft/assumption/backlog/tail 不改变当前 action dispatch。
- Machine contracts: `contracts/evidence-gap-decision-policy.json`、schema、examples。

## Claim Boundary

任何 `EvidenceGapDecision` 都不能声明：

- `paper_progress`
- `owner_receipt_closed`
- `publication_ready`
- `submission_ready`
- `live_runtime_ready`
- `production_ready`
- `provider_running`

Contract landed、docs updated、focused tests passed、projection clean、queue empty、DHD dry-run 或 evidence tail recorded 都不能被解释成以上 claim。

## 非目标

本策略不启动 provider，不运行 DHD apply / hydrate / tick / redrive，不写 study runtime artifacts、`publication_eval/latest.json`、`controller_decisions/latest.json`、paper body、owner receipt、typed blocker 或 human gate。真实 paper progress / readiness 仍只能由 fresh runtime readback、owner receipt、stable typed blocker、human gate、route-back evidence、quality gate receipt 或 canonical paper/gate/artifact semantic delta 证明。
