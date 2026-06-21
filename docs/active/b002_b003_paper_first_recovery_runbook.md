# B002 / B003 论文优先恢复运行规则

Status: `active_operating_rule`
Last reviewed: `2026-06-21`
Owner: `MedAutoScience`
Purpose: `paper_first_recovery_runbook`
State: `active_support`
Machine boundary: 本文是人读运行规则和监督口径。机器真相继续归 MAS controller/read-model output、OPL current-control-state、owner receipts、typed blockers、runtime artifacts、publication eval、controller decisions 和真实 workspace evidence。本文不授权手写 `publication_eval/latest.json`、`controller_decisions/latest.json`、runtime-owned study truth、owner receipt、typed blocker 或 human gate。

## 当前判断

B002 / B003 的目标是推进论文，不是用论文测试 MAS / OPL。MAS / OPL 的修复只在它直接解除论文推进阻塞、减少重复返工、或让产物被 owner surface 消费时才是主线工作。

近期停滞暴露的是 mission framing 缺陷：executor 和 supervisor 已经能严谨地区分 owner route、currentness、handoff、typed blocker、absorption 和 forbidden writes，但停止条件容易收敛到“没有越权、状态解释正确、候选已吸收”。这能防止误报，却不能保证稿件、图表、回应材料或 owner decision 往前走。

因此 B002 / B003 采用 paper-first 双轨，并把平台修复作为旁路线治理：

1. `governed MAS / OPL path`：只要 MAS owner callable、domain-handler dispatch、OPL StageRun provider attempt 或 human gate 能合法产出 owner receipt、canonical paper/artifact delta、AI reviewer / publication gate delta、route-back、stable typed blocker 或 human gate，就优先走 governed path。
2. `foreground paper sprint`：当 governed path 被 OPL lease / execution authorization / currentness / handoff 缺口阻塞，且继续修平台不会在本轮产生论文 owner delta 时，立即切到前台论文冲刺，产出可审阅、可接力的手工论文工作品。该工作品必须标记为 manual / foreground output；它不自动更新 MAS truth，也不声明 publication-ready，后续需要由 MAS/OPL owner path 消费、采纳、拒绝或转成 typed blocker。
3. `repair lane`：当论文推进过程中发现 MAS / OPL / control-plane 缺陷，必须先判断它是否直接解除当前论文 work unit 阻断。能小修且不抢论文 executor 写集的 MAS repo 缺陷，可由 supervisor 或独立修复 lane 做最小候选；跨 repo、OPL lifecycle、lease、execution authorization、no live session 或 owner-route authority 缺口，必须作为独立 repair-lane proposal 交主会话，而不是让论文 executor 停下来修平台。

## 论文主线与修复旁路

标准分工如下：

- `paper executor`：持有 B002 / B003 active goal，只负责推进论文工作品、owner handoff、human decision packet、governed owner path 或直接解除当前论文 work unit 的最小 repo/runtime 修复候选。它不能因为平台缺陷调查而长期停在 status readback、precheck、cannot apply 或通用 control-plane 修复。
- `supervisor`：用 heartbeat 做干预型监督。每轮先检查 paper-facing artifact movement，再检查 runtime/currentness。若发现 MAS/OPL 缺陷，必须输出 `repair lane classification`：`absorbed_to_main`、`candidate_ready_for_absorption`、`open_repair_lane_proposal`、`not_actionable_without_owner` 或 `not_blocking_paper_progress`。
- `repair lane`：只处理清晰边界的平台缺陷。它必须有独立 worktree/branch、allowed write set、forbidden write set、root-cause diagnosis、focused verification、fresh readback 和 absorption packet。它不得手写 Yang authority artifacts，也不得把修复进展包装成论文进展。
- `main session`：仍是 repo candidate absorption owner。任何 repair lane 的 repo commit 都必须由主会话独立复核 diff、复跑或采集等价新鲜证据、吸收到 `main`、push 到 `origin/main`，并在安全时清理 worktree/branch。

修复旁路不得阻断论文主线。若一个缺陷不能在当前轮直接解除 governed owner path，paper executor 必须继续 foreground paper sprint，至少产出更具体的 manuscript/package/review/decision material；supervisor 同时把缺陷登记为 repair-lane proposal。这样论文持续推进，平台问题也不会丢失。

### Repair Lane 分类

每次发现 MAS/OPL 问题时必须按以下分类报告：

| 分类 | 含义 | 必需动作 |
| --- | --- | --- |
| `absorbed_to_main` | 修复已进 `main` 和 `origin/main`，并有 fresh readback 证明目标缺陷消失或被正确投影 | 报告 commit、验证、readback；不再要求同一 absorption |
| `candidate_ready_for_absorption` | 修复 commit 已在独立 worktree/branch，尚未进入 `main` | 停止扩写，提交 absorption packet 给主会话 |
| `open_repair_lane_proposal` | 缺陷真实，但尚未开修复 lane 或跨 repo/owner 需要单独拆分 | 报告 root cause、owner surface、推荐 lane、allowed/forbidden write set、验证方式和停止条件 |
| `not_actionable_without_owner` | 需要 human / OPL / runtime owner 决策、凭据、lease 或权限 | 产出 owner decision packet 或 human gate proposal；paper executor 转 foreground sprint |
| `not_blocking_paper_progress` | 缺陷存在但不阻断当前论文工作品继续产出 | 记录为低优先支线；不得打断 paper executor |

### Repair Lane 开启条件

满足任一条件才开或建议开独立 repair lane：

- 缺陷会重复让 B002/B003 卡在同一 owner route/currentness/handoff/read-model 误判；
- 修复能让当前 foreground paper materials 被 MAS/OPL owner surface 消费、拒绝或转成 typed blocker；
- 缺陷导致系统把 provider completion、queue empty、read-model hygiene、handoff residue 或旧 package authority 误报为论文进展；
- 缺陷导致 main 与 executor worktree 对同一 study 给出不同 progress-first classification；
- 缺陷位于 OPL lifecycle / lease / execution authorization / no live session / cross-repo runtime owner，且不能由当前 paper executor 合法处理。

不应开 repair lane 的情况：

- 只是为了清理状态文案、telemetry 或报告格式；
- 只会让 tests 更绿，但不影响当前论文 work unit；
- 需要直接手写 MAS truth、publication authority、owner receipt、typed blocker 或 human gate；
- root cause 尚未定位，只有“可能哪里不对”的猜测。

## 论文进展计分

每轮执行必须至少推动以下之一：

- canonical manuscript、table、figure、result、submission package、evidence ledger、review ledger 或 response/rebuttal draft 的具体 delta；
- AI reviewer、auditor、publication gate 或 human reviewer 的新判断、问题归纳或 gate delta；
- 可提交给 owner 的 decision packet：包含选项、建议、证据 ref、影响范围、风险和停止条件；
- stable typed blocker / human gate packet，且明确 owner、work unit、缺失输入、不能自动推进原因和恢复条件；
- repo/runtime 修复候选，且该修复直接解除当前论文 work unit 的合法执行阻断。

不计论文进展的内容：

- queue empty、DHD dry-run clean、focused tests 通过、read-model hygiene、projection currentness 修复；
- provider completion、OPL handoff residue、status/card 文案或 telemetry；
- absorption / commit / push 本身；
- 只说明“当前不能越权”但没有给出可执行论文工作品或 owner decision packet。

## Foreground Paper Sprint 输出约束

Foreground sprint 可以在 study workspace 中新增或更新显式标注的 manual work product，例如：

- reviewer issue map / gate-clearing issue map；
- manuscript section patch、abstract / introduction / methods / discussion rewrite；
- figure/table caption revision、figure quality checklist、claim-evidence patch list；
- response letter / rebuttal draft；
- human owner decision packet；
- submission package audit note。

禁止在 foreground sprint 中直接写入：

- `publication_eval/latest.json`；
- `controller_decisions/latest.json`；
- runtime-owned study truth、OPL queue、provider attempt、owner receipt、typed blocker、human gate；
- masquerading outputs，例如把 manual draft 写成 governed MAS receipt、publication readiness 或 current package authority。

Foreground sprint 的验收是“可被人或后续 owner path 采纳/拒绝/消费”。它必须报告：

- modified or created paper-facing files；
- source evidence refs；
- what changed in the manuscript/package/reviewer response；
- what remains unconsumed by MAS/OPL；
- next owner path that should consume or reject it。

## B002 当前运行口径

Fresh 读法以 `study progress` / DHD 为准。2026-06-21 main 状态下，B002 已有 AI reviewer record 被投影为 successor action：

- current owner/action: `gate_clearing_batch/run_gate_clearing_batch`
- work unit: `ai_reviewer_record_gate_consumption`
- fingerprint: `sha256:c82b52d55725eb89ed014ff1f805c07d6a6c2ee25a47c5e5713367a54fd88917`
- source record: `artifacts/publication_eval/ai_reviewer_responses/20260621T015831Z_publication_eval_record.json`
- governed blocker: OPL handoff / execution authorization / no live session

B002 executor 的下一步不能继续只解释 handoff blocker。若 OPL 授权路径本轮不能合法执行，必须切 foreground sprint：把 AI reviewer record 消费成 gate-clearing issue map、manuscript patch plan、必要的 section/caption/table revision 和 owner decision packet。该结果是 paper-facing manual work product，后续由 MAS owner path 消费。

## B003 当前运行口径

Fresh 读法以 `study progress` / DHD 为准。2026-06-21 main 状态下，B003 的 owner gate decision 已被 current projection 消费为 domain blocker：

- `paper_recovery_state.phase=domain_blocked`
- condition: `accepted_owner_gate_decision`
- next safe action: `honor_stable_typed_blocker`
- refs: `owner-gate-decision:d6d895635654560a85573c04`, `human_gate:owner-gate-decision:d6d895635654560a85573c04`, `stable_typed_blocker:owner-gate-decision:d6d895635654560a85573c04`

B003 executor 的下一步不能 redrive provider 绕过 blocker。若 human / authority decision 尚未给出，必须切 foreground sprint：产出 human decision packet、blocked revision alternatives、可安全采纳的 manuscript/package patch proposal，或明确建议保持 blocker 的理由。该结果不自动解除 MAS blocker；它为 owner 决策提供可读工作品。

## Executor / Supervisor 分工

Executor 持有 goal，负责产出论文工作品或直接阻断论文推进的 repo/runtime 修复候选。每轮报告必须先列 paper-facing delta，再列 platform repair。

Supervisor 用 heartbeat 做干预型监督。每轮必须检查真实 paper artifact movement，包括 manuscript、delivery package、figure/table、review/gate、decision packet 的变化。若 executor 只停在 owner packet、precheck、readback、tests 或 absorption 状态，supervisor 必须立即 steering：要求本轮转入 governed owner path 或 foreground paper sprint。

Main session 仍是 repo candidate 的 absorption owner。Foreground paper sprint 输出进入 Yang study workspace 时，不等于 repo absorption；repo 代码修复才需要 main absorption、commit、push 和 worktree cleanup。

## 停止条件

单轮可以停止在以下任一状态：

- paper-facing manual work product 已生成，并有 source refs、改动摘要、剩余 MAS/OPL consumption gap；
- governed owner path 产出 owner receipt、paper/artifact delta、reviewer/gate delta、route-back、stable typed blocker 或 human gate；
- repo/runtime 修复候选已准备 absorption，并证明它直接解除当前论文 work unit 阻断；
- human / authority decision packet 已完整，且继续自动推进会越权。

不能停止在：

- “当前状态如此”；
- “DHD/readback 已解释”；
- “不能合法 apply”但没有 paper work product 或 owner decision packet；
- “tests passed / candidate absorbed”但没有映射到论文推进。
