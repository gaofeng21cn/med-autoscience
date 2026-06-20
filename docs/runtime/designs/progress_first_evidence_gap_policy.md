# Progress-First Evidence Gap Policy 目标设计

Owner: `MedAutoScience`
Purpose: `progress_first_evidence_gap_policy_target_design`
State: `active_target_design`
Machine boundary: 本文是人读目标设计和合同导航。机器真相归 `contracts/evidence-gap-decision-policy.json`、`contracts/schemas/evidence-gap-decision.schema.json`、`contracts/evidence-gap-decision-examples.json`、源码、测试、runtime/controller durable surfaces、owner receipt、typed blocker、human gate、route-back evidence 和 fresh runtime readback。
Date: `2026-06-20`

## 目标结论

MAS progress-first 路径需要把“缺证据”拆成可执行的机器决策，而不是把所有缺口都升格为 blocker，也不能把软缺口、observability、open evidence tail 包装成 ready 或 paper progress。

`EvidenceGapDecision` 是本轮落地的机器合同。它的作用是：

- 让 hard gate fail closed；
- 让 bounded assumption、soft quality follow-up 和 observability backlog 不阻断当前 owner action；
- 让 evidence tail 阻止 completion / readiness claim，但不自动进入 typed blocker count；
- 固定 forbidden claim 边界，避免把 docs、contract、focused tests、queue empty、projection clean 或 evidence-tail record 写成 live runtime ready / paper progress。

本设计是目标态和合同落地，不声明 live runtime readiness、DM002/DM003 paper progress、publication-ready、submission-ready、provider running、owner receipt closure 或 production-ready。

## 机器落点

| Surface | 角色 |
| --- | --- |
| `contracts/evidence-gap-decision-policy.json` | gap class、typed blocker materialization、claim boundary 和 forbidden interpretations 的 canonical policy。 |
| `contracts/schemas/evidence-gap-decision.schema.json` | 单条 `mas_evidence_gap_decision` 记录的 schema。 |
| `contracts/evidence-gap-decision-examples.json` | 六类 gap 的最小可消费 examples。 |
| `tests/test_evidence_gap_contract.py` | 合同测试：schema/policy link、六类 gap、hard/soft 边界、forbidden claims。 |

Markdown 只解释和导航；后续 controller、doctor、rollup 或 work-order 消费方必须读 JSON contract，不得解析本文章节。

## Gap Class Taxonomy

| `gap_class` | 当前 action 是否阻断 | 是否进入 typed blocker count | 正确处理 |
| --- | --- | --- | --- |
| `authority_gate` | 是 | 是 | 当前 owner / MAS authority / OPL runtime authority 缺失时 fail closed，可 materialize typed blocker。 |
| `human_gate` | 是 | 是 | 需要 human/operator/owner answer 时打开 human gate 或 materialize typed blocker。 |
| `proceed_with_assumption` | 否 | 否 | 记录 bounded assumption、scope boundary 和 revisit trigger 后继续当前 owner action。 |
| `soft_quality_gap` | 否 | 否 | 生成 reviewer / quality follow-up work order；不阻断非终局推进。 |
| `observability_backlog` | 否 | 否 | 生成 diagnostic / monitoring follow-up；不升级为 runtime readiness 或 typed blocker。 |
| `evidence_tail` | 否 | 否 | 阻止 completion / readiness claim，记录 next owner、accepted evidence family 和 forbidden substitutes。 |

## Typed Blocker 边界

Typed blocker count 只允许来自四类原因：

1. `authority_gate`
2. `human_gate`
3. `forbidden_write_boundary`
4. `stop_loss_materialized`

以下 gap class 不能进入 typed blocker count：

- `proceed_with_assumption`
- `soft_quality_gap`
- `observability_backlog`
- `evidence_tail`

`evidence_tail` 可以阻止 “all complete / live ready / production ready” 这类 claim，但它不是 current owner action blocker。缺 live evidence 时，应记录 evidence tail 或 owner work order；只有同一 current identity 命中 authority gate、human gate、forbidden write 或 stop-loss materialization，才进入 typed blocker materialization。

## Claim Boundary

`EvidenceGapDecision` 默认禁止以下 claim：

- `live_runtime_ready`
- `paper_progress`
- `publication_ready`
- `submission_ready`
- `production_ready`
- `provider_running`
- `owner_receipt_closed`
- `quality_verdict`
- `domain_ready`
- `current_package_fresh`

禁止把以下事实解释为完成或 ready：

- docs updated；
- contract landed；
- focused tests passed；
- evidence gap policy landed；
- evidence tail recorded；
- queue empty；
- projection clean；
- read-model currentness；
- provider completion；
- DHD dry-run / observe-only。

这些事实可以证明对应合同、测试或投影规则成立；它们不能替代 fresh live readback、owner receipt、stable typed blocker、human gate、route-back evidence、quality gate receipt 或 canonical paper/gate/artifact semantic delta。

## 设计原则

1. Soft gaps 不反进度。质量 polish、diagnostic 和 bounded assumption 应进入 follow-up / assumption / backlog，而不是无差别阻断 owner action。
2. Hard gates 不被软化。source/data/evidence authority、owner route identity、forbidden write、irreversible mutation、publication gate、human gate 和 MAS hard gate 缺失时必须 fail closed。
3. Evidence tail 是 claim gate，不是 action gate。它阻止 completion/readiness 口径，但不自动重复 redrive 或增加 typed blocker count。
4. Claim boundary 随记录携带。每条 decision 都必须显式带 `completion_claim_allowed=false` 与 readiness/progress forbidden claim flags，避免下游只读 gap class 后误报。
5. 当前身份优先。decision 必须绑定 `current_owner_delta_ref` 与 study / work-unit / fingerprint identity；需要 route/attempt 语义时携带 `route_identity_key` 和 `attempt_idempotency_key`。

## 非目标

- 不启动 provider。
- 不运行 DHD apply、hydrate、tick 或 redrive。
- 不写 Yang study/runtime artifacts。
- 不写 paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker 或 human gate。
- 不关闭 live evidence tails。
- 不声明 DM002/DM003 live paper-line 前进、publication-ready、runtime-ready 或 production-ready。

## 后续消费方式

短期消费方应先从 JSON 合同读取：

```text
EvidenceGapDecision -> gap_class -> typed_blocker_policy -> claim_boundary
```

推荐消费规则：

- status / doctor / rollup 展示 typed blocker count 时，只累计 `typed_blocker_policy.typed_blocker_countable=true` 的记录；
- completion audit 展示 evidence tail 时，使用 `gap_class=evidence_tail` 与 `blocks_completion_claim=true`；
- owner action admission 只把 `authority_gate`、`human_gate`、`forbidden_write_boundary` 和 `stop_loss_materialized` 当成 current action hard stop；
- soft gap 只生成 follow-up work order 或 assumption ref，不能成为 provider admission、owner receipt、quality verdict 或 paper progress。
