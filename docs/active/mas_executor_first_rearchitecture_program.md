# MAS executor-first 重构目标与迁移计划

Owner: `MedAutoScience`
Purpose: `executor_first_rearchitecture_program`
State: `active_plan`
Machine boundary: 本文是人读目标架构、根因归类和迁移计划。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、OPL current-control / provider attempt ledger、MAS controller durable surfaces、真实 workspace artifact、owner receipt、typed blocker、human gate 和 publication gate。本文不授权手写 `publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker、human gate、runtime queue/provider attempt 或 `current_package`。

## 当前判断

MAS 当前问题不是单篇论文执行者能力不足，而是系统形态把主要能量放在 currentness、handoff、read-model、authorization 和 false-claim 防护上，导致论文主线经常被平台控制链吞没。DM002 / DM003 在 30 多小时后仍未形成目标态完成，说明这是架构问题，不是继续给旧链路补一个 projection guard 就能解决。

RCA 和 OPL Book Forge 推进快的共同点是：入口先承诺一个 domain deliverable loop，让 executor 在同一 session / deliverable run 里持续产出可审阅 artifact；质量门用于回修和 owner handoff，不把每个中间状态拆成独立控制面。MAS 当前相反：论文推进被拆成多个 owner-route、DHD、paper recovery、provider admission、OPL readback、typed blocker、gate replay 和 projection surface，任何一环 current identity 不一致就回到等待或稳定阻塞。

因此新 MAS 应从 `PaperMissionRun` candidate / readback 继续升级为 `PaperMissionTransaction + StageTerminalDecision` 主路径：医学论文 executor 在 MAS stage 内持有粗粒度 transaction，先产出论文工作品，再由 MAS terminalizer 在同一 stage 内给出 `StageTerminalDecision`。只有 terminal decision 已把 artifact delta、owner answer、typed blocker、human interrupt、route-back 或 exit-handler 归一化后，OPL 才消费派生出的 route command。OPL 负责 session / attempt / queue / retry / resume / transport，不消费 MAS 内部 DHD、owner-route、default dispatch 或 PaperRecovery 作为论文主线。

## Fresh Evidence

2026-06-22 fresh read-only audit 使用以下命令，不执行 apply、hydrate、tick、redrive 或 provider start：

```bash
scripts/run-python-clean.sh -m med_autoscience.cli study progress \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml \
  --study-id 002-dm-china-us-mortality-attribution \
  --format json

scripts/run-python-clean.sh -m med_autoscience.cli study progress \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml \
  --study-id 003-dpcc-primary-care-phenotype-treatment-gap \
  --format json

scripts/run-python-clean.sh -m med_autoscience.cli runtime domain-health-diagnostic \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml \
  --studies 002-dm-china-us-mortality-attribution 003-dpcc-primary-care-phenotype-treatment-gap \
  --request-opl-stage-attempts \
  --dry-run
```

关键读回：

| Study | Fresh status | Direct failing boundary | Cross-surface evidence |
| --- | --- | --- | --- |
| DM002 `002-dm-china-us-mortality-attribution` | `current_stage=queued`、`paper_stage=publishability_gate_blocked`、`active_run_id=null`。`study progress` 指向 `analysis-campaign/run_quality_repair_batch`，但 DHD dry-run 消费到 `accepted_closeout_typed_blocker`。 | 当前 work unit 已落到 `typed_blocker`，blocker 为 `domain_owner_action_dispatch_execution_count_zero`：provider attempt 收到 OPL refs，但 MAS `domain-owner-action-dispatch` apply 选中 0 个 execution，`gate_clearing_batch` owner receipt 未写出。 | MAS progress 说 owner action ready；DHD 说 accepted typed blocker；runtime health 说 `missing_live_session` / `quest_marked_running_but_no_live_session`；authority snapshot 又要求 OPL lifecycle readback。论文主线被 owner dispatch、typed blocker 和 runtime handoff 分裂卡住。 |
| DM003 `003-dpcc-primary-care-phenotype-treatment-gap` | `current_stage=queued`、`paper_stage=analysis-campaign`、`active_run_id=null`。`study progress` 指向 `paper_recovery_domain_blocked`，next safe action 为 `honor_stable_typed_blocker`。 | owner gate 已接受 `deny_and_stable_typed_blocker`，work unit 仍围绕 `medical_prose_write_repair` / `publication_gate_replay` 等 recovery/action identity 旋转。 | progress 表面显示 human / authority blocker 已成为 current truth；DHD 又保留 OPL transition request / provider-admission readback 要求。系统能解释为什么不动，但未把解释变成新的论文 delta、owner decision packet 或可消费修稿。 |

根因深度归类：

| Layer | Diagnosis |
| --- | --- |
| L0 symptom | 论文线长时间停在 queued / repair / quality / domain_blocked，active run 为空，用户看不到实质完成。 |
| L1 failing boundary | owner action 到 provider attempt 到 MAS owner receipt / typed blocker 的闭环不是一个粗粒度 deliverable transaction，而是多个 projection / handoff / dispatch / gate surface 串联。 |
| L2 cross-surface evidence | DM002 的 progress owner action、DHD typed blocker、runtime missing live session、authority lifecycle readback 互相指向不同 owner；DM003 的 stable blocker 与 OPL transition request 同时存在。 |
| L3 owner repair path | 设计 owner 是 MAS + OPL 的边界：OPL 应持有 session / attempt / queue / outbox / StageRun；MAS 应只持有 medical paper mission policy、artifact authority、quality verdict、owner receipt / typed blocker 和 human gate。修复路径是新建 executor-first mission loop，再迁移旧 study。 |
| L4 prevention | 把“paper-facing artifact delta or accepted owner blocker”作为 primary progress metric，把 currentness / read-model / DHD / storage / admission 修复列入 sidecar platform repair，不再让平台修复默认中断论文主线。 |

2026-06-23 implementation/readback evidence 使用当前 `main` 工作区代码和真实 DM-CVD profile，不执行 apply、hydrate、tick、redrive、provider start，也不写 Yang / publication / controller / owner / runtime authority surface：

```bash
scripts/run-python-clean.sh -m med_autoscience.cli study progress \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml \
  --study-id 002-dm-china-us-mortality-attribution \
  --format json

scripts/run-python-clean.sh -m med_autoscience.cli study progress \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml \
  --study-id 003-dpcc-primary-care-phenotype-treatment-gap \
  --format json

scripts/run-python-clean.sh -m med_autoscience.cli runtime domain-health-diagnostic \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml \
  --studies 002-dm-china-us-mortality-attribution 003-dpcc-primary-care-phenotype-treatment-gap \
  --request-opl-stage-attempts \
  --dry-run

scripts/run-python-clean.sh -m med_autoscience.cli paper-mission inspect \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml \
  --study-id 002-dm-china-us-mortality-attribution \
  --format json

scripts/run-python-clean.sh -m med_autoscience.cli paper-mission consume-candidate \
  --candidate /tmp/mas_paper_mission_dm002_candidate_20260623.json \
  --dry-run \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.local.toml \
  --study-id 002-dm-china-us-mortality-attribution \
  --format json
```

`003-dpcc-primary-care-phenotype-treatment-gap` 使用同一 profile 和 `/tmp/mas_paper_mission_dm003_candidate_20260623.json` 跑 `paper-mission inspect` / `consume-candidate`。读回产物保存在 `/tmp/mas_paper_mission_dm002_cli_inspect_20260623.json`、`/tmp/mas_paper_mission_dm003_cli_inspect_20260623.json`、`/tmp/mas_paper_mission_dm002_cli_consume_20260623.json`、`/tmp/mas_paper_mission_dm003_cli_consume_20260623.json`。

| Surface | Fresh finding | Current claim boundary |
| --- | --- | --- |
| PaperMissionTransaction contract/readback boundary | `contracts/paper_mission_transaction_contract.json`、`med_autoscience.paper_mission_transaction.PaperMissionTransaction`、`PaperMissionRun.paper_mission_transaction` required field、`paper-mission` CLI transaction pickup/readback、`study_progress` top-level `stage_terminal_decision` / `opl_route_command` 已落地。 | 可以声明 repo contract、validator、CLI/read-model shape 已改为 transaction / terminal decision / route command split；不能声明 OPL hosted run、live provider run、paper artifact completion、owner receipt、publication-ready 或 current package。 |
| OPL runtime carrier bridge | `paper-mission inspect` 与 `study_progress` 顶层现在投影 request-only `opl_runtime_carrier.surface_kind=mas_domain_progress_transition_request`，并用独立 `opl_runtime_carrier_readback` / `opl_runtime_readback_status` 消费 OPL terminal closeout readback。carrier 由 `PaperMissionTransaction.opl_route_command` 派生，包含 `paper_mission_transaction_ref`、`stage_terminal_decision_ref`、`opl_route_command_ref`、aggregate identity、route / attempt / request idempotency、`required_postcondition` 和 `DomainProgressTransitionRuntime` contract ref。DM002 fresh readback 已从 stale `waiting_for_opl_runtime_live_readback` 修正为 `opl_runtime_terminal_readback_observed` / `terminal_closeout_observed`，并把 terminal closeout 折叠为 operator-facing `terminal_owner_gate`：`owner=one-person-lab`、`gate_kind=typed_blocker`、`blocked_reason=opl_runtime_lifecycle_readback_required`、`can_claim_paper_progress=false`、`authority_materialized=false`，同时覆盖 `next_owner_or_human_decision` 为 non-executable owner route。`terminal_owner_gate` 还会生成 readback-only `terminal_owner_gate_authority_readback`，携带 MAS authority kernel 可消费的 accepted owner-answer shapes、`typed_blocker_ref` / `closeout_ref`、`consume_result.status=typed_blocker`、`write_plan.written_files=[]` 和 no-provider-admission boundary。DM003 没有 terminal closeout，因此不生成 `terminal_owner_gate` / `terminal_owner_gate_authority_readback`；它仍通过 `stage_terminal_decision=typed_blocker` / `next_owner_or_human_decision.next_owner=one-person-lab` 表达当前 owner gate，且未错误触发 provider start。 | 可以声明 MAS 已把 OPL terminal closeout readback 与 carrier request ABI 分离，provider terminal observed 不再被误读成 domain completion，并且 CLI / study_progress 的 owner-gate consume packet 已明确 current next owner。不能声明 carrier 已变成 OPL outbox、event、StageRun、provider attempt、running proof、owner receipt、typed blocker authority file、human gate、domain-ready 或 paper progress。 |
| New paper mission default entry | CLI `paper-mission inspect/start/resume/consume-candidate` 已接入 `PaperMissionRun` validator；product entry `medical_paper_product_entry.default_action_intent` 指向 `paper_mission/start_or_resume`；domain-handler export 通过 `/paper_mission_default_tasks` 输出默认 `paper_mission/start_or_resume` task，`/pending_family_tasks` 不再承载默认 paper loop。若 workspace 已有 `ops/medautoscience/paper_mission_one_shot_migration/**/<study_id>/paper_mission_run.json`，`inspect/start/resume` 与 default task 会返回 `paper_mission_materialized_readback`，而不是 generic planned no-write plan。 | 可以声明 repo 默认 product/domain-handler 入口已转向物化 `PaperMissionRun` readback；不能声明 live provider run、paper artifact completion、owner receipt、publication-ready 或 current package。 |
| DM002 canary consume | `paper-mission inspect` contract validation 为 `validated`、`mission_state=planned`、`consume_result.status=not_consumed`；`consume-candidate` contract validation 为 `validated`、`mission_state=consumed`、`consume_result.status=accepted`、`authority_materialized=false`、`authority_consume_readback.status=accepted_candidate`、`write_plan.written_files=[]`、`mutation_policy.writes_yang=false`、`writes_authority=false`。 | 这证明 DM002 canary candidate 可被 MAS authority consume path 接收为 no-write candidate readback；不能写成真实 owner receipt、paper body patch、publication eval、controller decision、current package 或投稿完成。 |
| DM003 canary consume | `paper-mission inspect` contract validation 为 `validated`、`mission_state=planned`、`consume_result.status=not_consumed`；`consume-candidate` contract validation 为 `validated`、`mission_state=stable_blocker`、`consume_result.status=typed_blocker`、`authority_materialized=false`、`authority_consume_readback.status=typed_blocker_required`、`write_plan.written_files=[]`、`mutation_policy.writes_yang=false`、`writes_authority=false`。 | 这证明 DM003 canary 能把当前 typed blocker 转成 authority consume readback；不能写成 typed blocker 文件已物化、human gate 已写、owner receipt 已写或 runtime 已恢复。 |
| DM002 / DM003 one-shot migration | `paper-mission inspect --one-shot-migration` 使用 fresh progress + DHD dry-run payload 生成每篇 `legacy_truth_import_pack`、正式 `PaperMissionRun`、`default_readback.current_mission`、`next_owner`、`required_output`、`consume_candidate_status`、`mission_candidate_artifact_delta` 和 `owner_decision_packet`。DM002 `consume_candidate_status=accepted`、`next_owner=analysis-campaign`；DM003 `consume_candidate_status=typed_blocker`、`next_owner=one-person-lab`。两篇 `current_mission.legacy_blocker_is_default_execution_state=false`，Big-Bang 输出包写到 `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/paper_mission_one_shot_migration/bigbang_20260623/...`，每篇 6 个非权威 JSON：`legacy_truth_import_pack.json`、`paper_mission_run.json`、`default_readback.json`、`candidate_manifest.json`、`mission_candidate_artifact_delta.json`、`owner_decision_packet.json`；`writes_authority=false`、`writes_runtime=false`、`writes_yang_authority=false`、`writes_yang_ops_candidate_package=true`。 | 可以声明 DM002/DM003 旧 truth 已冻结为 mission input、旧 blocker 已降级为 decision constraint / provenance / non-degradation evidence，默认读面切到 `PaperMissionRun` 字段，并且每篇已有可接力的非权威 mission candidate artifact delta / owner decision packet；不能声明 OPL hosted run、owner receipt、typed blocker authority file、publication eval、controller decision、current package 或 paper body 已物化。 |
| Old default dispatch demotion | `domain_handler_export._mark_legacy_default_executor_tasks` 会把 `domain_owner/default-executor-dispatch` 标为 `migration_diagnostic_only` / `default_paper_mission_entry=false`；tombstone `dhd_owner_route_dispatch_paper_recovery_default_paper_mainline` 禁止旧链路声明默认 mainline、paper progress、runtime-ready、DM002/DM003 complete；`no_active_default_caller_proof.proof_scope` 覆盖 product entry、domain-handler dispatch / pending tasks、action catalog、MCP manifest 和 plugin skill ordinary path。 | 可以声明旧 dispatch / DHD / PaperRecovery 不再是默认 paper mission 主线；不能声明旧 diagnostic、ABI、fixture、migration 或 provenance refs 已全部物理删除。 |
| Remaining legacy references | 有界 caller/search evidence 仍命中 DHD、PaperRecovery、`domain_owner/default-executor-dispatch` carrier / ABI / fixture / migration references；`contracts/runtime/legacy-active-path-tombstones.json.no_active_default_caller_proof.legacy_reference_rigor_policy` 已把每类允许引用绑定到 allowed use、required evidence、forbidden claims 和 `can_select_next_paper_stage=false` / `counts_as_paper_progress=false` / `can_claim_runtime_ready=false`。 | 这些引用只能作为 runtime diagnostic、authority consume/readback、OPL StageRun ABI carrier、migration diagnostic、history provenance 或 legacy fixture；不能升级成默认论文推进、runtime-ready、paper progress 或 DM002/DM003 complete claim。paper progress 仍必须来自 `PaperMissionRun` / `PaperMissionTransaction` artifact delta 加 MAS owner receipt、stable typed blocker、human gate 或 route-back，并绑定同一 currentness identity。 |

## 设计理念调整

1. 从 `status-first` 改为 `artifact-first`。每轮必须产生 canonical manuscript / figure / table / evidence ledger / reviewer response / owner decision packet / stable blocker 中至少一种。read-model clean、DHD clean、queue empty、receipt accounting、projection freshness 只算平台观测。
2. 从 `controller-first` 改为 `executor-first`。MAS 入口默认启动或恢复一个 paper mission executor，让它在粗粒度任务包内连续完成写作、修订、证据对齐、review response 和 gate clearing。controller 负责 admission、validation、materialization、receipt signing 和 forbidden-write guard，不负责把每个中间判断拆成下一次执行。
3. 从 `many current identities` 改为 `single transaction identity`。一个 `PaperMissionTransaction` 只有一个 transaction id、一个 current objective、一个 artifact delta ledger 和一个 terminal decision。内部可以有 reviewer、writer、gate 子步骤，但外层只追踪同一 transaction identity 下的 deliverable progress。
4. 从 `gate blocks progress` 改为 `gate shapes repair`。AI reviewer、publication gate、data/source gate 发现问题后，应生成 repair brief、required artifact delta 和 owner handoff。只有数据/隐私/权限、不可逆写入、human decision、forbidden authority write 才阻断 mission run。
5. 从 `platform repair on critical path` 改为 `platform repair sidecar`。OPL lease、provider admission、currentness、DHD scope、projection drift、storage/index/read-model 问题默认是 repair lane。除非它直接解除当前 paper mission 的合法执行阻断，否则不能抢占论文 executor。
6. 从 `MAS owns runtime-like behavior` 改为 `MAS owns minimal medical authority`。MAS 长期保留医学 truth、source readiness、publication quality、artifact authority、memory accept/reject、owner receipt / typed blocker / human gate；attempt、queue、resume、retry、dead-letter、session shell、workbench、provider lifecycle 归 OPL。

## Target Architecture

| Layer | New owner | Responsibility |
| --- | --- | --- |
| `medical-paper product entry` | MAS generated/direct entry + OPL hosted shell | `paper-mission start|resume|inspect|consume`。用户只面对“推进这篇论文到下一个可审阅/可投稿 milestone”的产品入口。 |
| `PaperMissionTransaction` | MAS stage domain owner | 同一 transaction identity 下的 objective、mission input、candidate artifact delta、decision constraints、forbidden-write guard、terminalizer input 和 owner-answer boundary。现有 `PaperMissionRun` 只作为 candidate/readback shape 与迁移输入，不能再作为长期顶层 runtime envelope。 |
| `StageTerminalDecision` | MAS terminalizer | 在 MAS stage 内把 transaction outcome terminalize 为 `artifact_delta`、`owner_receipt_candidate`、`route_back`、`stable_typed_blocker`、`human_interrupt`、`retry_catch` 或 `exit_handler`。非 terminal intermediate status 不交给 OPL 当作下一论文主线。 |
| `OPL route command` | OPL runtime substrate | 只消费 `StageTerminalDecision` 派生的 route command，负责 attempt、queue、resume、retry/dead-letter、provider lifecycle、stdout/log 和 current-control readback；不消费 DHD/owner-route/default dispatch/PaperRecovery 的内部状态作为 paper mission progress。 |
| `Mission workspace` | MAS study workspace | mission-scoped candidate artifacts、draft patches、reviewer issue map、gate-clearing plan、submission candidate、source refs、artifact delta ledger。 |
| `MAS Authority Kernel` | MAS | source/data readiness、forbidden write guard、publication policy、quality verdict acceptance、artifact/package authority、owner receipt、typed blocker、human gate。 |
| `Review / Gate Kernel` | MAS | 独立 AI reviewer / auditor / publication gate 只消费 mission artifacts，输出 repair brief、route-back、quality gate receipt、stable blocker 或 publication handoff。 |
| `Progress Workbench` | MAS projection + OPL workbench | 首屏只显示 paper-facing delta、current mission objective、next forced delta、owner/human decision、artifact pickup。平台 currentness 放 diagnostics。 |
| `Platform repair sidecar` | OPL / MAS repo repair lane | DHD/currentness/dispatch/storage/read-model 修复，必须带 owner、allowed writes、verification 和 absorption path；不计论文进度。 |

最小命令语义应收敛为：

```text
medautosci paper-mission start --profile <profile> --study-id <study> --objective <objective>
medautosci paper-mission resume --profile <profile> --study-id <study> --mission-id <mission>
medautosci paper-mission inspect --profile <profile> --study-id <study> --format json
medautosci paper-mission consume-candidate --profile <profile> --study-id <study> --candidate <path>
```

这些命令是目标 contract sketch，不是本文授权的现有 CLI claim。当前已落地的 `PaperMissionRun` 读面应被解释为 `PaperMissionTransaction` 的 candidate/readback 兼容层；后续机器合同应把 terminal decision 和 OPL route command 明确分开。

## 功能不降级映射

| Existing MAS capability | New design preservation |
| --- | --- |
| study truth / source readiness | 保留在 MAS Authority Kernel；mission 只能引用和请求消费，不能自行改 truth。 |
| publication eval / AI reviewer quality | 保留独立 reviewer/auditor invocation；executor 不能自审关闭 gate。 |
| controller decisions | 缩小为 mission admission、policy decision、gate decision 和 owner receipt materialization；不再作为 generic next-action queue。 |
| owner receipt / typed blocker | 保留为 terminal owner answer。区别是 blocker 必须绑定 mission objective 和 next recoverable path，不能只是状态解释。 |
| human gate | 保留，但必须携带最小 decision packet、options、risk、resume condition 和 artifact refs。 |
| evidence / review ledger | mission run 必须更新或提出 candidate patch；MAS consume path 决定接收、拒绝或 route-back。 |
| artifact authority / current package | 仍由 MAS gate 授权；mission candidate 不自动成为 current package。 |
| OPL current-control / provider lifecycle | 完全上收 OPL；MAS 只发 terminal decision 派生的 route command 并消费 OPL readback，不生成或手写 provider authority。 |
| progress portal / workbench | 改为 artifact-first IA：论文进展、下一 owner、人类决策、可拾取文件优先；platform repair 折叠。 |
| external learning / sidecars | 只能作为 mission helper / advisory refs；不能成为 hard gate 或 completion claim。 |

## 先立后破迁移路线

### Phase 0: Freeze old critical path

目标：停止继续在旧 DHD / owner-route / provider-admission 链上补 guard 作为主线。

必须做：

- 标记旧链路为 `legacy_governed_path`，只允许 audit、consume existing receipt、produce stable blocker 或 migrate。
- 对 DM002/DM003 fresh export truth pack：study config、current manuscript/package refs、publication eval、controller decisions、evidence/review ledger、latest owner receipt / typed blocker、OPL current-control refs。
- 建立 migration no-write boundary：不得在 export 时改 paper body、publication eval、controller decision、owner receipt、typed blocker、human gate 或 runtime queue。

### Phase 1: Build new mission entry beside old system

目标：先造新方式，不动旧 truth。

必须做：

- 新增 `PaperMissionTransaction` / `StageTerminalDecision` 目标合同、mission artifact manifest、mission progress schema、forbidden-write guard；现有 `PaperMissionRun` contract 作为 candidate/readback 兼容层接入，不再定义长期顶层 owner。
- 新增 `paper-mission inspect` 和 `paper-mission start --dry-run`，先只生成 mission plan / candidate workspace / touchpoint protocol。
- 把 B002 / B003 现有 foreground paper sprint protocol 升级为正式 `mission candidate` 消费协议。
- Progress Workbench 优先显示 mission artifact delta，而不是 DHD/currentness 字段。

验收：一个新 mission 能在不写 authority surface 的前提下，为 DM002 或 DM003 产出可审阅 mission plan、artifact delta ledger 和 owner decision packet。

### Phase 2: Migrate DM002 / DM003 as canaries

目标：用新 mission loop 推进旧项目，证明功能不降级。

必须做：

- 每篇建立一个 mission：DM002 目标为 gate-clearing + claim/evidence repair；DM003 目标为 medical prose write repair + publication gate replay decision。
- mission executor 先产出 paper-facing candidate：issue map、manuscript patch plan、必要 section/caption/table patch、reviewer/gate response draft、owner decision packet。
- MAS consume path 对 candidate 做 `accept / reject / route-back / typed blocker / human gate`，不允许 candidate 自封 publication-ready。
- 若 OPL runtime 可用，mission 由 OPL hosted run 承载；若 OPL 缺 lease/readback，则 foreground mission 继续产物主线，同时登记 repair lane。

验收：每篇至少形成一个可消费 artifact delta 或 stable owner decision packet，并且 MAS/OPL 有明确 consume/refuse path。

2026-06-23 one-shot migration cutover：`paper-mission inspect --one-shot-migration` 已把 DM002/DM003 旧系统 truth 冻结为 `legacy_truth_import_pack`，每篇 import pack 包含 `current_artifact_refs`、`publication_eval_refs`、`controller_decision_refs`、`evidence_and_review_ledger_refs`、`legacy_owner_state_refs`、`opl_current_control_refs`、`legacy_constraints` 和 `decision_constraints`。随后生成正式 `PaperMissionRun`：DM002 为 `gate_clearing_claim_evidence_repair`，DM003 为 `medical_prose_write_repair_publication_gate_replay`。旧 blocker 保留在 `mission_input` / `legacy_constraints` / `decision_constraints` / `source_refs` / `non_degradation_evidence`，并显式标为 `legacy_blocker_is_default_execution_state=false`；默认读面改为 `current_mission`、`next_owner`、`required_output`、`consume_candidate_status`。Big-Bang candidate package 还为每篇物化 `mission_candidate_artifact_delta.json` 和 `owner_decision_packet.json`，前者 `counts_as_paper_progress=true` 但 `candidate_is_authority=false`，后者 `packet_status=candidate_ready_for_mas_consume` 且 `authority_materialized_by_this_packet=false`。该 cutover 是 no-write migration readback 和非 authority candidate package；只允许写 Yang `ops/medautoscience/paper_mission_one_shot_migration/...` 下的非权威 candidate package，不写 Yang study truth/runtime authority、publication eval、controller decisions、owner receipt、typed blocker、human gate、current package、runtime queue/provider attempts 或 paper body。

### Phase 3: Cut over default execution

目标：新任务默认走 mission loop。

必须做：

- `domain-handler export` 不再默认导出旧 `domain_owner/default-executor-dispatch` 粒度任务；改导出由 `StageTerminalDecision` 派生的 `paper_mission/start_or_resume` / route command。
- 旧 owner-route/DHD 只作为 diagnostic / migration consumer / provenance input，不能再生成主线 next action。
- `study progress` 顶层状态改用 mission state：`running_mission`、`candidate_ready_for_consumption`、`waiting_human_decision`、`stable_blocker`、`terminal_handoff`。
- DHD/currentness/OPL readback 只显示在 platform diagnostics。

验收：新 study 和 DM002/DM003 后续回合都能从 `paper-mission inspect` 读到唯一 next objective、latest paper delta、next owner 和 forbidden claims。

2026-06-23 progress/workbench slice：`study_progress` projection 和 Progress Portal / study workbench 已新增 artifact-first mission summary read model。顶层暴露 `mission_state`、`current_objective`、`latest_artifact_delta`、`next_owner_or_human_decision`、`terminal_owner_gate`、`terminal_owner_gate_authority_readback`、`platform_diagnostics`；内部 `artifact_first_mission_summary.paper_mission_run` 对齐 `contracts/paper_mission_run_contract.json` / `paper-mission-run.v1` 和 `med_autoscience.paper_mission_run.PaperMissionRun` canonical shape。`terminal_owner_gate` 只在同一 mission identity 的 OPL terminal closeout 被观察到时存在，用来首屏表达“当前不可继续 provider admission，应 route 到 owner/human gate”；`terminal_owner_gate_authority_readback` 是 MAS authority kernel 的 readback-only consume packet，用来表达 accepted owner-answer shapes 和 no-write boundary。两者都不是 MAS owner receipt、typed blocker authority materialization、human gate 或 paper progress。DHD、currentness、storage、owner-route、dispatch 和 PaperRecovery 只折叠为 diagnostics / migration / provenance，不再作为 progress/workbench 默认论文主线。

2026-06-23 CLI/product-entry/domain-handler slice：`paper-mission inspect/start/resume/consume-candidate` 已作为 no-write readback 入口接入 CLI，product entry 的 `medical_paper_product_entry.default_action_intent` 指向 `paper_mission/start_or_resume`，domain-handler export 通过 `/paper_mission_default_tasks` 输出默认 `paper_mission/start_or_resume` task，并把旧 `domain_owner/default-executor-dispatch` task 标成 `migration_diagnostic_only`。`consume-candidate` 现在调用 MAS authority consume readback，把 accepted / rejected / route-back / typed blocker / human gate 映射回 `PaperMissionRun.consume_result` 与 `mission_state`。该 slice 只证明默认入口与 dry-run/consume readback 边界已经转向 PaperMissionRun；它不声明 live provider run、paper body patch、current package 或 publication-ready。

2026-06-23 one-shot default readback slice：`paper-mission inspect --one-shot-migration --study-progress-payload <progress.json> --domain-health-diagnostic-payload <dhd.json>` 已能直接读出 DM002/DM003 的新默认 mission 状态。DM002 读面为 `current_mission.objective_kind=gate_clearing_claim_evidence_repair`、`next_owner=analysis-campaign`、`required_output.kind=owner_decision_packet_or_consumable_artifact_delta`、`consume_candidate_status=accepted`、`mission_candidate_artifact_delta.surface_kind=paper_mission_candidate_artifact_delta`、`owner_decision_packet.next_owner=analysis-campaign`；DM003 读面为 `current_mission.objective_kind=medical_prose_write_repair_publication_gate_replay`、`next_owner=one-person-lab`、`required_output.kind=owner_decision_packet_or_consumable_artifact_delta`、`consume_candidate_status=typed_blocker`、`mission_candidate_artifact_delta.surface_kind=paper_mission_candidate_artifact_delta`、`owner_decision_packet.next_owner=one-person-lab`。两者旧 blocker 只在 migration provenance / decision constraints 中出现，不能再作为默认 executor 主状态。

2026-06-23 PaperMissionTransaction design slice：顶层目标语义升级为 `PaperMissionTransaction + StageTerminalDecision`。`PaperMissionRun` 保留为当前 no-write candidate/readback 和 one-shot migration 兼容 shape；真正的长期主路径要求 MAS stage 内 terminalize：writer / reviewer / gate / consume-candidate / blocker / human-interrupt / route-back 都必须归一成 `StageTerminalDecision`，然后只把 route command 交给 OPL。OPL 可执行 retry、resume、dead-letter、transport 和 provider lifecycle，但不得把 DHD、owner-route、default dispatch、PaperRecovery、queue empty 或 currentness probe 当作 paper progress 或 terminal owner answer。

### Phase 4: Retire old way

目标：彻底退役旧控制面，而不是长期双轨。

退役条件：

- old DHD / owner-route / dispatch / recovery surface 没有 default product-entry、domain-handler、MCP、skill 或 OPL active caller。
- 每个 old surface 有 replacement parity：`PaperMissionTransaction`、`StageTerminalDecision`、MAS authority kernel、OPL route-command/readback 或 tombstone。
- no-forbidden-write proof 覆盖 study truth、publication eval、controller decisions、paper body、owner receipt、typed blocker、human gate、current package 和 runtime state。
- DM002/DM003 canary 至少各产生一个被 MAS consume path 处理的 mission artifact delta、owner receipt、route-back、human gate 或 stable typed blocker。
- active docs、product docs、skill docs 和 progress portal 不再把旧 DHD/dispatch/recovery 链写成主执行方式。

2026-06-23 tombstone slice：`contracts/runtime/legacy-active-path-tombstones.json` 新增 `dhd_owner_route_dispatch_paper_recovery_default_paper_mainline`，把旧 DHD / owner-route / dispatch / PaperRecovery 默认主路径降为 `diagnostics_migration_provenance_only`，并禁止 product/default domain-handler mainline、paper progress、publication-ready、runtime-ready、provider-running、DM002 complete 和 DM003 complete claim。该 tombstone 关闭默认叙事边界，不等于旧物理 caller 全部删除。

2026-06-23 caller proof status：有界 caller/search evidence 已证明旧路径仍有 repo 内 active references。`domain-health-diagnostic` 仍作为 runtime diagnostic / authority consumer 暴露；`paper_recovery_state` / PaperRecovery 仍被 `current_work_unit`、`study_progress`、DHD report 和 provider-admission projection 消费；`domain_owner/default-executor-dispatch` 仍作为 OPL StageRun ABI、migration diagnostic、legacy fixture 和 transition carrier 出现在源码/测试/contract。`contracts/runtime/legacy-active-path-tombstones.json#/no_active_default_caller_proof` 现在显式列出 default-surface proof scope：product entry、domain-handler dispatch / pending tasks、family action catalog、MCP tool manifest 和 plugin skill ordinary path；focused tests 断言默认 paper mission replacement 为 `paper_mission/start_or_resume`，旧 carrier 如出现必须是 `default_paper_mission_entry=false` / `migration_diagnostic_only=true`。当前能声明的是“默认 product/domain-handler/MCP/skill/action-catalog surface 不再把旧链路暴露为 paper mission mainline”；不能声明所有旧 diagnostic / ABI / fixture / provenance references 已物理删除。

2026-06-23 clean paper mission slice：旧 `domain_owner/default-executor-dispatch` 不再进入 ordinary `pending_family_tasks`。`domain_handler_export` 只把它收集为 `legacy_dispatch_diagnostics`，默认 paper loop task 只出现在 `/paper_mission_default_tasks`；`/pending_family_tasks` 只保留 explicit owner handoff / migration compatibility 任务，所有非默认任务固定 `default_paper_mission_entry=false`、`can_select_next_paper_stage=false`、`can_authorize_provider_admission=false`、`counts_as_paper_progress=false`。手工向 `domain-handler dispatch` 传入 legacy task 会 fail closed，reason 固定为 `legacy_default_executor_dispatch_tombstoned`。`domain_handler_dispatch` 在 action catalog 和 agent tool arsenal 中降为 read-only / descriptor-only boundary，不再声明可产生 owner receipt、typed blocker、domain truth、publication quality、artifact gate 或 current package 写入。新增 `paper-mission package-candidate` 将物化 `PaperMissionRun` 打包为 foreground candidate package，固定写入非权威 `ops/medautoscience/paper_mission_candidate_package/...`，输出 `paper_mission_readback`、`candidate_manifest`、`mission_candidate_artifact_delta`、`owner_decision_packet` 和 foreground summary；该 package 只服务 owner-consumption-first，不是 authority truth、runtime truth、paper body patch、owner receipt、typed blocker、human gate、publication eval、controller decision 或 current package。

2026-06-23 governed consume ledger slice：`paper-mission consume-candidate` 现在支持 `--dry-run` 与 `--output-root` 二选一。`--dry-run` 保持既有 readback-only 行为；`--output-root` 只允许写 `ops/medautoscience/paper_mission_consumption_ledger/...` 下的 governed consume evidence，包含 `consume_record.json`、`consume_readback.json`、`stage_terminal_decision.json`、`opl_route_command.json` 与 `opl_route_handoff.json`。`consume_record.surface_kind=mas_paper_mission_candidate_consumption_record`，固定 `authority_materialized=false`、`candidate_is_authority=false`、`counts_as_owner_consumption_evidence=true`、`counts_as_stage_terminalizer_evidence=true`、`counts_as_opl_route_handoff_evidence=true`、`counts_as_paper_progress=false`、`counts_as_runtime_truth=false`、`writes_authority=false`、`writes_runtime=false`、`writes_yang_authority=false`。one-shot migration 与 foreground `package-candidate` 写出的 `candidate_manifest.json` 都携带 sidecar refs，使 consume readback 能拾取同一 `PaperMissionTransaction`，不回落到 placeholder identity；只有 materialized transaction 的 accepted / route-back command 会标记 `ready_for_opl_route_command`，typed blocker / human gate outcome 稳定落 owner authority gate。它把 DM002 accepted candidate、DM003 typed-blocker-required candidate 这类 outcome 变成可复核 owner-consumption / terminalizer / route-handoff evidence；仍不是 owner receipt、typed blocker authority file、human gate authority file、publication eval、controller decision、current package、OPL outbox/event/StageRun、runtime queue/provider attempt 或 paper body patch。

### 2026-06-23 旧残留清理与二次污染审计

本节回答“旧历史残留是否全面彻底清理干净，防止二次污染”。结论是：默认论文主线污染口已经 `done`，全物理删除仍是 `partial`。旧 MAS / MDS / DHD / owner-route / dispatch / PaperRecovery 相关残留只能作为 diagnostics、migration input、ABI carrier、fixture 或 provenance 读取；凡要重新进入默认论文推进，必须重新经过 `PaperMissionTransaction`、`StageTerminalDecision`、MAS authority consume path、no-forbidden-write guard 和 OPL route-command/readback。

| Residual / pollution risk | Status | Current evidence | Remaining gap / forbidden interpretation |
| --- | --- | --- | --- |
| 默认产品入口回流旧链路 | `done` | product entry、domain-handler、action catalog、MCP / skill ordinary path 共享 `paper_mission/start_or_resume`；domain-handler default task 不再把旧 dispatch 作为 paper mission mainline。 | 这只证明默认入口不再走旧链路；不能声明 live OPL hosted run 或论文完成。 |
| 旧 DHD / owner-route / dispatch / PaperRecovery 主线污染 | `done` | tombstone `dhd_owner_route_dispatch_paper_recovery_default_paper_mainline` 将旧链路降为 `diagnostics_migration_provenance_only`，并禁止 paper progress、publication-ready、runtime-ready、provider-running、DM002 complete、DM003 complete claim。 | 旧面可继续作为诊断、迁移输入或 ABI/provenance；不得再写成默认 executor mainline。 |
| 旧 default-executor ordinary queue 复活 | `done` | `domain_handler_export` 现在把 legacy dispatch 从 ordinary tasks 分离到 `legacy_dispatch_diagnostics`；默认 `paper_mission/start_or_resume` 只在 `/paper_mission_default_tasks`，`pending_family_tasks` 不再承载默认 paper loop，也不再把 DHD/default-executor/PaperRecovery action 当作可调度论文主线。 | legacy diagnostics 可保留解释旧状态；不得被 OPL 普通队列当成论文推进 carrier。 |
| 手工 legacy dispatch 复活 | `done` | `domain-handler dispatch` 对 `domain_owner/default-executor-dispatch` 返回 fail-closed receipt，reason=`legacy_default_executor_dispatch_tombstoned`，并指向 replacement `paper_mission/start_or_resume` / MAS authority consume。 | 这不是 legacy task 的兼容执行；operator 不能靠手工 dispatch 绕回旧主路径。 |
| `domain_handler_dispatch` 权限误导 | `done` | action catalog / agent tool arsenal 把 `domain_handler_dispatch` 降为 read-only / descriptor-only boundary，去掉 owner receipt / typed blocker 生成承诺。 | 真正 owner receipt、typed blocker、human gate 仍只由 MAS authority kernel / terminal owner gate consume path materialize。 |
| 旧 truth / blocker 导入到新 mission | `done` | one-shot migration 把 DM002/DM003 旧状态冻结为 `legacy_truth_import_pack`，旧 blocker 进入 `mission_input` / `legacy_constraints` / `decision_constraints` / `source_refs` / `non_degradation_evidence`，并显式 `legacy_blocker_is_default_execution_state=false`。 | 这是 no-write import，不是 authority materialization 或 paper body patch。 |
| 禁止写 authority surface | `done` | `PaperMissionRun` / `PaperMissionTransaction` readback 固定 `candidate_writes_authority=false`，禁止写 `publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker、human gate、current_package、runtime queue/provider attempts 和 Yang authority。 | no-write readback 不能替代 owner receipt、typed blocker、human gate 或 current package freshness。 |
| 非权威 foreground candidate package | `done_for_consumable_candidate_package` | `paper-mission package-candidate` 只在存在 materialized `PaperMissionRun` 时输出 package，写入 `ops/medautoscience/paper_mission_candidate_package/...`，固定 `candidate_is_authority=false`、`writes_authority=false`、`writes_runtime=false`、`writes_yang_authority=false`。 | candidate package 可作为 owner-consumption-first 输入；不能替代 governed authority materialization 或真实论文正文/图表/证据账本写入。 |
| 旧 physical caller / ABI / fixture 全部删除 | `partial` | 有界 caller evidence 仍命中 DHD、PaperRecovery、`domain_owner/default-executor-dispatch` 的 runtime diagnostic、authority readback、OPL StageRun ABI、migration diagnostic、legacy fixture、transition carrier。 | 若要物理删除，需逐项证明 replacement parity、no-active-caller、no-forbidden-write 和 tombstone/provenance。 |
| 真实论文产物与 authority consume 闭环 | `partial` | DM002/DM003 已有非权威 candidate artifact delta、owner decision packet、transaction terminal decision / route command readback。 | 仍缺真实 study workspace manuscript / figure / table / evidence ledger / reviewer response delta 被 MAS authority materialize 或 route-back。 |

## Completion Audit

| Item | Current status | Fresh evidence | Gap / forbidden interpretation |
| --- | --- | --- | --- |
| Top-level transaction semantics | `done_for_contract_and_readback_shape` | `contracts/paper_mission_transaction_contract.json`、`PaperMissionTransaction` validator、`PaperMissionRun.paper_mission_transaction` required field、CLI transaction readback 和 `study_progress` transaction projection 均已落地；OPL 只消费 terminal decision 派生 route command。 | 这是 repo contract/readback/CLI shape landing，不是 OPL hosted run、live provider run、paper body delta、owner receipt、typed blocker authority file、publication-ready 或 current package proof。 |
| New entry exists | `done_for_materialized_default_readback` | CLI `paper-mission` parsers/readback、product entry `default_action_intent=paper_mission/start_or_resume`、domain-handler `/paper_mission_default_tasks`、contract validation `validated`；有物化 one-shot mission 时，`paper-mission inspect/start/resume` 和 domain-handler default task 返回 `paper_mission_materialized_readback`。 | 这不是 live mission execution、paper artifact completion、owner receipt 或 provider running proof。 |
| DM002 / DM003 one-shot migration cutover | `done_for_no_write_default_readback_cutover` | `paper-mission inspect --one-shot-migration` 为两篇生成 `legacy_truth_import_pack`、正式 `PaperMissionRun`、`current_mission`、`next_owner`、`required_output`、`consume_candidate_status`、`mission_candidate_artifact_delta` 和 `owner_decision_packet`；DM002 `accepted`，DM003 `typed_blocker`；两者 `legacy_blocker_is_default_execution_state=false`，candidate package 已物化到 Yang `ops/medautoscience/paper_mission_one_shot_migration/bigbang_20260623`，每篇 6 个非 authority JSON，`output_manifest.writes_authority=false`、`writes_runtime=false`、`writes_yang_authority=false`。 | 这是一次性迁移读面和非 authority candidate package，不是 OPL live run、authority 文件物化、paper body patch、current package 或 publication-ready。 |
| Paper mission produces work | `done_for_non_authority_candidate_delta_and_decision_packet` | `PaperMissionRun` contract / validator、artifact-first mission summary、DM002/DM003 one-shot candidate packages、每篇 `mission_candidate_artifact_delta.json` 和 `owner_decision_packet.json`、DM002 `consume_result.status=accepted`、DM003 `consume_result.status=typed_blocker`、两者 authority readback `written_files=[]`。 | 已完成旧 truth 冻结、新 mission 默认读面 cutover、以及每篇可接力的非权威 mission candidate artifact delta / owner decision packet；仍缺真实 manuscript / figure / table / evidence ledger / reviewer response 写入 study workspace 并被 authority materialize。 |
| Standard stage completion policy | `done_for_pack_conformance_and_transition_boundary` | `stage_control_plane.stages[].stage_contract.stage_completion_policy` 覆盖 6 个 Foundry stage；`contracts/foundry_agent_series.json` 的 `required_stage_packets`、`series_design_profile.stage_pack_sections` 和 MAS domain-specific packet list 均包含 `stage_completion_policy`；OPL scaffold validator `status=passed` / `blockers=[]`；`make test-meta` 通过。 | 这关闭“stage 有产出但缺标准终态 packet 导致 OPL 无法安全自动推进”的 pack/conformance 缺口；不能声明 OPL 判断医学内容、provider completion 等于 stage complete、DM002/DM003 paper progress、owner receipt、runtime-ready 或 publication-ready。 |
| MAS authority preserved | `done_for_no_write_consume_boundary` | `consume_paper_mission_candidate` 与 CLI `consume-candidate` 均保留 accepted / rejected / route-back / typed blocker / human gate outcome；DM002/DM003 fresh consume readback 均 `authority_materialized=false` 且不写 authority。 | 不能把 readback 写成真实 `publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker、human gate、current package 或 paper body mutation。 |
| OPL terminal closeout readback overlay | `done_for_readback_boundary` | `paper-mission inspect` 与 `study_progress` 在 `opl_runtime_carrier` 之外投影 `opl_runtime_carrier_readback`。同一 study / work unit / fingerprint 且 `record_only_surface=true` 的 closeout 才能给出 `opl_runtime_terminal_readback_observed`；带 provider/domain completion 或 domain-ready claim 的 closeout fail closed。DM002 readback 为 terminal closeout observed + domain gate pending；DM003 仍为 typed blocker/non-start。 | 这是 readback/currentness 修复，不是 MAS authority materialization、OPL runtime readiness、paper artifact delta、owner receipt、typed blocker file、human gate、publication-ready 或 paper progress。 |
| OPL owns runtime | `not_satisfied_live` | 设计与 forbidden-write guard 指向 OPL runtime owner；MAS no-write readback 禁止写 runtime queue/provider attempts。 | 还缺 OPL-hosted `PaperMissionRun` attempt/session/readback；不能从 dry-run inspect、queue empty、read-model clean 或 DHD dry-run 推导 runtime ready。 |
| Platform repair demoted | `done_for_projection_boundary` | `artifact_first_mission_summary.platform_diagnostics.counts_as_paper_progress=false`，product/docs/status 把 DHD/currentness/storage/dispatch/PaperRecovery 折叠为 diagnostics / migration / provenance。 | 这只关闭默认读面和完成口径，不说明平台修复已经全部完成。 |
| Old path retired | `done_for_default_surface_retirement` | Tombstone contract 禁止默认 mainline claim；`no_active_default_caller_proof.proof_scope` 覆盖 product entry、domain-handler dispatch / pending tasks、family action catalog、MCP tool manifest、plugin skill ordinary path；domain-handler export 不再把 legacy dispatch 放入 ordinary pending queue，手工 legacy dispatch fail closed；action catalog/tool arsenal 把 dispatch 面降为 read-only descriptor；focused tests 锁住 replacement / forbidden claims / allowed legacy reference classes。 | 这只证明旧链路不再是默认 paper mission 主线；有界 caller evidence 仍命中 DHD、PaperRecovery、default-executor-dispatch 的 diagnostic / authority readback / OPL ABI / fixture / migration / provenance references，不能把它们说成全部物理删除。 |
| Foreground candidate package usable | `done_for_no_write_candidate_package_surface` | `paper-mission package-candidate` 输出 package manifest、paper mission readback、candidate manifest、mission candidate artifact delta、owner decision packet 和 foreground owner-decision summary，全部固定 no-authority/no-runtime/no-Yang-authority writes。 | 这是让 DM002/DM003 能继续 owner-consumption-first 的可用版本切片；真实论文产物仍需后续 MAS authority consume / route-back / human gate / typed blocker 或 governed artifact delta。 |

`100%` 只能在上述 evidence 全部新鲜可读时声明。文档、plan、schema、focused tests、DHD dry-run、queue empty、read-model clean、contract/tombstone landed、CLI no-write readback、one-shot migration package 或 old surface deletion 均不能单独支撑目标态完成；DM002/DM003 只有在 authority consume readback 或等价 owner-answer readback 指向真实 artifact delta、owner receipt、route-back、human gate、stable typed blocker 或 rejection，并且所需 authority/runtime owner 明确消费后，才可计入目标态 paper completion。

## Immediate Next Work

1. 在 OPL hosted run 和 MAS authority materialization 接入前，继续把 `paper-mission` CLI / domain-handler 输出标为 no-write candidate/readback；不得声明 runtime-ready、provider-running、publication-ready、DM002 complete 或 DM003 complete。
2. 下一轮真正论文推进必须从 one-shot migration package 进入 MAS stage transaction，先 terminalize 为 `StageTerminalDecision`，再由 MAS authority consume/route-back/human-gate/typed-blocker surface 处理，最后只把 route command 交给 OPL。
3. 若要物理删除旧 diagnostic / ABI / fixture / provenance refs，必须先逐项证明 replacement parity 与 no-forbidden-write；不能把 default-surface retirement 等同于全物理删除。
