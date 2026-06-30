# MAS executor-first 重构目标与迁移计划

Owner: `MedAutoScience`
Purpose: `executor_first_rearchitecture_program`
State: `active_support`
Machine boundary: 本文是人读目标架构、根因归类和迁移计划。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、OPL current-control / provider attempt ledger、MAS controller durable surfaces、真实 workspace artifact、owner receipt、typed blocker、human gate 和 publication gate。本文不授权手写 `publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker、human gate、runtime queue/provider attempt 或 `current_package`。

## SSOT 读法

- 本文只保留 executor-first 的目标形态、owner split、迁移路线和禁止误写口径。
- 当前 active gap / completion owner 是 [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)。若本文与 active gap plan 冲突，以 active gap plan 为准。
- Next action 控制面 SSOT 是 [Next Action Control Plane](../runtime/control/next_action_control_plane.md)。`StageOutcome -> NextActionEnvelope -> OPL TransitionReceipt -> MAS owner consumption` 是当前默认读法。
- 2026-06-22 到 2026-06-30 的 DM002/DM003 命令流水、readback 表、candidate package、consume ledger、completion audit 和旧残留审计已经压缩为 [Program 历史归档](../history/program/README.md) 的 `NextAction / PaperMission / typed-blocker structural closeouts` 主题；需要精确追溯时读 git history、runtime/workspace receipts 或对应 machine surface。

## 当前判断

MAS 的主要问题不是单篇论文执行者能力不足，而是旧系统把论文推进拆成多个 owner-route、domain diagnostic、paper recovery、provider admission、OPL readback、typed blocker、gate replay 和 projection surface。任何一环 current identity 不一致，论文主线都会回到等待或稳定阻塞。

目标形态是从 `PaperMissionRun` candidate / readback 继续升级为 `PaperMissionTransaction + StageTerminalDecision` 主路径：医学论文 executor 在 MAS stage 内持有粗粒度 transaction，先产出论文工作品，再由 MAS terminalizer 在同一 stage 内给出 `StageTerminalDecision`。只有 terminal decision 已把 artifact delta、owner answer、typed blocker、human interrupt、route-back 或 exit-handler 归一化后，OPL 才消费派生出的 route command。OPL 负责 session、attempt、queue、retry、resume 和 transport，不消费 MAS 内部 domain diagnostic、owner-route、default dispatch 或 PaperRecovery 作为论文主线。

根因归类：

| Layer | Diagnosis |
| --- | --- |
| L0 symptom | 论文线长时间停在 queued / repair / quality / domain_blocked，active run 为空，用户看不到实质完成。 |
| L1 failing boundary | owner action 到 provider attempt 到 MAS owner receipt / typed blocker 的闭环不是一个粗粒度 deliverable transaction，而是多个 projection / handoff / dispatch / gate surface 串联。 |
| L2 cross-surface evidence | DM002/DM003 历史读面曾同时暴露 progress owner action、domain diagnostic typed blocker、runtime missing live session、authority lifecycle readback 或 OPL transition request，互相指向不同 owner。 |
| L3 owner repair path | OPL 持有 session / attempt / queue / outbox / StageRun；MAS 只持有 medical paper mission policy、artifact authority、quality verdict、owner receipt / typed blocker 和 human gate。 |
| L4 prevention | 以 paper-facing artifact delta、accepted owner answer、stable blocker 或 owner decision packet 作为 primary progress metric；currentness / read-model / domain diagnostic / storage / admission 修复进入 sidecar repair lane。 |

## 设计理念

1. 从 `status-first` 改为 `artifact-first`：每轮必须产生 canonical manuscript / figure / table / evidence ledger / reviewer response / owner decision packet / stable blocker 中至少一种。
2. 从 `controller-first` 改为 `executor-first`：MAS 入口默认启动或恢复 paper mission executor，让它在粗粒度任务包内连续完成写作、修订、证据对齐、review response 和 gate clearing。
3. 从 `many current identities` 改为 `single transaction identity`：一个 `PaperMissionTransaction` 只有一个 transaction id、一个 current objective、一个 artifact delta ledger 和一个 terminal decision。
4. 从 `gate blocks progress` 改为 `gate shapes repair`：review / publication / data gate 发现问题后应生成 repair brief、required artifact delta 和 owner handoff；只有权限、不可逆写入、human decision 或 forbidden authority write 才阻断 mission run。
5. 从 `platform repair on critical path` 改为 `platform repair sidecar`：OPL lease、provider admission、currentness、domain diagnostic scope、projection drift、storage/index/read-model 问题默认是 repair lane。
6. 从 `MAS owns runtime-like behavior` 改为 `MAS owns minimal medical authority`：MAS 保留医学 truth、source readiness、publication quality、artifact authority、memory accept/reject、owner receipt / typed blocker / human gate；attempt、queue、resume、retry、dead-letter、session shell、workbench 和 provider lifecycle 归 OPL。

## Target Architecture

| Layer | Owner | Responsibility |
| --- | --- | --- |
| `medical-paper product entry` | MAS generated/direct entry + OPL hosted shell | `paper-mission start|resume|inspect|consume`。用户只面对“推进这篇论文到下一个可审阅/可投稿 milestone”的产品入口。 |
| `PaperMissionTransaction` | MAS stage domain owner | 同一 transaction identity 下的 objective、mission input、candidate artifact delta、decision constraints、forbidden-write guard、terminalizer input 和 owner-answer boundary。 |
| `StageTerminalDecision` | MAS terminalizer | 在 MAS stage 内把 transaction outcome terminalize 为 artifact delta、owner receipt candidate、route-back、stable typed blocker、human interrupt、retry catch 或 exit handler。 |
| `OPL route command` | OPL runtime substrate | 只消费 `StageTerminalDecision` 派生的 route command，负责 attempt、queue、resume、retry/dead-letter、provider lifecycle、stdout/log 和 current-control readback。 |
| `Mission workspace` | MAS study workspace | mission-scoped candidate artifacts、draft patches、reviewer issue map、gate-clearing plan、submission candidate、source refs、artifact delta ledger。 |
| `MAS Authority Kernel` | MAS | source/data readiness、forbidden-write guard、publication policy、quality verdict acceptance、artifact/package authority、owner receipt、typed blocker、human gate。 |
| `Review / Gate Kernel` | MAS | 独立 AI reviewer / auditor / publication gate 只消费 mission artifacts，输出 repair brief、route-back、quality gate receipt、stable blocker 或 publication handoff。 |
| `Progress Workbench` | MAS projection + OPL workbench | 首屏只显示 paper-facing delta、current mission objective、next forced delta、owner/human decision、artifact pickup；platform currentness 放 diagnostics。 |
| `Platform repair sidecar` | OPL / MAS repo repair lane | domain diagnostic/currentness/dispatch/storage/read-model 修复，必须带 owner、allowed writes、verification 和 absorption path；不计论文进度。 |

最小命令语义：

```text
medautosci paper-mission start --profile <profile> --study-id <study> --objective <objective>
medautosci paper-mission resume --profile <profile> --study-id <study> --mission-id <mission>
medautosci paper-mission inspect --profile <profile> --study-id <study> --format json
medautosci paper-mission consume-candidate --profile <profile> --study-id <study> --candidate <path>
```

这些命令表达目标语义和当前 no-authority readback 入口。任何 publication-ready、submission-ready、runtime-ready、owner receipt、typed blocker authority file、human gate、paper body patch、current package 或 provider-running claim 必须回到对应 owner surface fresh 读取。

## 功能不降级映射

| Existing MAS capability | New design preservation |
| --- | --- |
| study truth / source readiness | 保留在 MAS Authority Kernel；mission 只能引用和请求消费，不能自行改 truth。 |
| publication eval / AI reviewer quality | 保留独立 reviewer/auditor invocation；executor 不能自审关闭 gate。 |
| controller decisions | 缩小为 mission admission、policy decision、gate decision 和 owner receipt materialization；不再作为 generic next-action queue。 |
| owner receipt / typed blocker | 保留为 terminal owner answer。blocker 必须绑定 mission objective 和 next recoverable path，不能只是状态解释。 |
| human gate | 保留，但必须携带最小 decision packet、options、risk、resume condition 和 artifact refs。 |
| evidence / review ledger | mission run 必须更新或提出 candidate patch；MAS consume path 决定接收、拒绝或 route-back。 |
| artifact authority / current package | 仍由 MAS gate 授权；mission candidate 不自动成为 current package。 |
| OPL current-control / provider lifecycle | 上收 OPL；MAS 只发 terminal decision 派生的 route command 并消费 OPL readback，不生成或手写 provider authority。 |
| progress portal / workbench | 改为 artifact-first IA：论文进展、下一 owner、人类决策、可拾取文件优先；platform repair 折叠。 |
| external learning / sidecars | 只能作为 mission helper / advisory refs；不能成为 hard gate 或 completion claim。 |

## 迁移路线

| Phase | Goal | Current state | Remaining work |
| --- | --- | --- | --- |
| Phase 0: Freeze old critical path | 停止继续在旧 domain diagnostic / owner-route / provider-admission 链上补 guard 作为主线。 | 旧 truth / blocker 已可作为 migration input、decision constraint 和 provenance 读取。 | 不得把旧 blocker 或 diagnostic 重新写成默认 executor 主状态。 |
| Phase 1: Build mission entry beside old system | 先造 no-authority mission readback，不动旧 truth。 | `PaperMissionRun` / `PaperMissionTransaction` candidate/readback shape、CLI inspect/start/resume/consume、product-entry 和 domain-handler 默认入口已切到 paper mission 语义。 | 长期主路径仍应继续收敛到 `PaperMissionTransaction + StageTerminalDecision`，而不是让 `PaperMissionRun` 承担 runtime envelope。 |
| Phase 2: Migrate DM002 / DM003 as canaries | 用新 mission loop 推进旧项目，证明功能不降级。 | DM002/DM003 历史状态已能冻结为 non-authority mission candidate、owner decision packet 和 consume/readback。 | 真正论文推进必须消费或继续修订 candidate，而不是停在 typed blocker / waiting readback 解释层。 |
| Phase 3: Cut over default execution | 新任务默认走 mission loop。 | 默认 product/domain-handler/MCP/skill/action-catalog surface 不再把旧链路暴露为 paper mission mainline；study progress 首屏优先 mission summary。 | read-model / workbench 继续只显示唯一 mission objective、paper delta、next owner 和 forbidden claims。 |
| Phase 4: Retire old way | 彻底退役旧控制面，而不是长期双轨。 | 旧 domain diagnostic / owner-route / dispatch / PaperRecovery 默认主路径已 tombstone；仍有 diagnostic / migration / provenance references。 | 若要物理删除旧 diagnostic / ABI / fixture / provenance refs，必须逐项证明 replacement parity、no-active-caller、no-forbidden-write 和 tombstone/provenance。 |

## 当前状态与边界

| Area | Current read | Forbidden interpretation |
| --- | --- | --- |
| PaperMissionTransaction / StageTerminalDecision | Repo contract、validator、CLI/read-model shape 已转向 transaction / terminal decision / route command split。 | 不是 OPL hosted run、live provider run、paper body delta、owner receipt、typed blocker authority file、publication-ready 或 current package proof。 |
| Paper mission default entry | CLI、product-entry、domain-handler 默认任务已转向 `paper_mission/start_or_resume` 和 no-authority readback。 | 不是 live mission execution、paper artifact completion、owner receipt 或 provider running proof。 |
| Candidate package / consume ledger | Candidate package 和 consume ledger 可作为 owner-consumption-first 输入与 route handoff evidence。 | 不是 authority truth、runtime truth、paper body patch、owner receipt、typed blocker、human gate、publication eval、controller decision 或 current package。 |
| Old path retirement | 默认入口污染口已关闭，旧 path 只允许 diagnostics、migration input 或 provenance。 | 不等于旧 physical caller / ABI / fixture 全部删除；不能把 default-surface retirement 写成全物理删除。 |
| OPL runtime handoff | MAS route command 能表达给 OPL 的 transition intent 和 handoff boundary。 | OPL queue、StageAttempt、provider completion、queue empty 或 transition clean 不能直接变成 paper progress、runtime-ready、publication-ready 或 submission-ready。 |
| Capability / ScholarSkills support | Capability registry 和 refs-only package consumption 支撑 mission helper。 | 不是 OPL Capability Runtime live invocation、hosted provider run、owner gate 接受、paper truth 或 production-ready。 |

## Immediate Next Work

1. 在 OPL hosted run 和 MAS authority materialization 接入前，继续把 `paper-mission` CLI / domain-handler 输出标为 no-authority candidate/readback；不得声明 runtime-ready、provider-running、submission-ready、publication-ready、DM002 complete 或 DM003 complete。
2. 下一轮真正论文推进必须优先消费或继续修订 DM002/DM003 已生成的 `submission_milestone_candidate`：MAS authority 应接受、拒绝、route-back、human-gate 或 typed-blocker；OPL owner path 应为 DM003 提供 missing live readback 或可消费 owner answer。
3. 若要物理删除旧 diagnostic / ABI / fixture / provenance refs，必须先逐项证明 replacement parity 与 no-forbidden-write；不能把 default-surface retirement 等同于全物理删除。
4. Capability 文档闭环维护在三份本体：`docs/runtime/designs/mas_opl_capability_module_operating_model.md`、`docs/runtime/projections/runtime_capability_matrix.md`、`docs/runtime/control/external_learning_adoption_closure.md`；后续只在 live owner / runtime evidence 到位时更新 readiness 行。
