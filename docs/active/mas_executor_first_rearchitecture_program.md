# MAS executor-first 重构目标与迁移计划

Owner: `MedAutoScience`
Purpose: `executor_first_rearchitecture_program`
State: `active_plan`
Machine boundary: 本文是人读目标架构、根因归类和迁移计划。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、OPL current-control / provider attempt ledger、MAS controller durable surfaces、真实 workspace artifact、owner receipt、typed blocker、human gate 和 publication gate。本文不授权手写 `publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker、human gate、runtime queue/provider attempt 或 `current_package`。

## 当前判断

MAS 当前问题不是单篇论文执行者能力不足，而是系统形态把主要能量放在 currentness、handoff、read-model、authorization 和 false-claim 防护上，导致论文主线经常被平台控制链吞没。DM002 / DM003 在 30 多小时后仍未形成目标态完成，说明这是架构问题，不是继续给旧链路补一个 projection guard 就能解决。

RCA 和 OPL Book Forge 推进快的共同点是：入口先承诺一个 domain deliverable loop，让 executor 在同一 session / deliverable run 里持续产出可审阅 artifact；质量门用于回修和 owner handoff，不把每个中间状态拆成独立控制面。MAS 当前相反：论文推进被拆成多个 owner-route、DHD、paper recovery、provider admission、OPL readback、typed blocker、gate replay 和 projection surface，任何一环 current identity 不一致就回到等待或稳定阻塞。

因此新 MAS 应改为 `executor-first paper mission`：先让医学论文 executor 持有粗粒度任务包并产出论文工作品，再由 MAS minimal authority kernel 做质量、证据、权限和出版门控。运行调度和 session 延续交给 OPL；MAS 不再自建或保留平行 runtime/control-plane。

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
| New paper mission default entry | CLI `paper-mission inspect/start/resume/consume-candidate` 已接入 `PaperMissionRun` validator；product entry `medical_paper_product_entry.default_action_intent` 指向 `paper_mission/start_or_resume`；domain-handler export 默认追加 `paper_mission/start_or_resume` task。 | 可以声明 repo 默认 product/domain-handler 入口已转向 no-write `paper-mission` readback；不能声明 live provider run、paper artifact completion、owner receipt、publication-ready 或 current package。 |
| DM002 canary consume | `paper-mission inspect` contract validation 为 `validated`、`mission_state=planned`、`consume_result.status=not_consumed`；`consume-candidate` contract validation 为 `validated`、`mission_state=consumed`、`consume_result.status=accepted`、`authority_materialized=false`、`authority_consume_readback.status=accepted_candidate`、`write_plan.written_files=[]`、`mutation_policy.writes_yang=false`、`writes_authority=false`。 | 这证明 DM002 canary candidate 可被 MAS authority consume path 接收为 no-write candidate readback；不能写成真实 owner receipt、paper body patch、publication eval、controller decision、current package 或投稿完成。 |
| DM003 canary consume | `paper-mission inspect` contract validation 为 `validated`、`mission_state=planned`、`consume_result.status=not_consumed`；`consume-candidate` contract validation 为 `validated`、`mission_state=stable_blocker`、`consume_result.status=typed_blocker`、`authority_materialized=false`、`authority_consume_readback.status=typed_blocker_required`、`write_plan.written_files=[]`、`mutation_policy.writes_yang=false`、`writes_authority=false`。 | 这证明 DM003 canary 能把当前 typed blocker 转成 authority consume readback；不能写成 typed blocker 文件已物化、human gate 已写、owner receipt 已写或 runtime 已恢复。 |
| Old default dispatch demotion | `domain_handler_export._mark_legacy_default_executor_tasks` 会把 `domain_owner/default-executor-dispatch` 标为 `migration_diagnostic_only` / `default_paper_mission_entry=false`；tombstone `dhd_owner_route_dispatch_paper_recovery_default_paper_mainline` 禁止旧链路声明默认 mainline、paper progress、runtime-ready、DM002/DM003 complete。 | 可以声明旧 dispatch 不再是 paper mission 默认入口；不能声明旧 DHD / dispatch / recovery surface 已全部物理删除或满足 no-active-caller。 |
| Remaining legacy references | 有界 caller/search evidence 仍命中 DHD、PaperRecovery、`domain_owner/default-executor-dispatch` carrier / ABI / fixture / migration references。 | 物理 no-active-caller proof 仍未满足；旧面只能继续作为 diagnostic、migration、authority readback 或 provenance carrier 分类处理。 |

## 设计理念调整

1. 从 `status-first` 改为 `artifact-first`。每轮必须产生 canonical manuscript / figure / table / evidence ledger / reviewer response / owner decision packet / stable blocker 中至少一种。read-model clean、DHD clean、queue empty、receipt accounting、projection freshness 只算平台观测。
2. 从 `controller-first` 改为 `executor-first`。MAS 入口默认启动或恢复一个 paper mission executor，让它在粗粒度任务包内连续完成写作、修订、证据对齐、review response 和 gate clearing。controller 负责 admission、validation、materialization、receipt signing 和 forbidden-write guard，不负责把每个中间判断拆成下一次执行。
3. 从 `many current identities` 改为 `single mission identity`。一个 paper mission run 只有一个 `mission_id`、一个 current objective、一个 artifact delta ledger 和一个 terminal owner answer。内部可以有 reviewer、writer、gate 子步骤，但外层只追踪同一 mission identity 下的 deliverable progress。
4. 从 `gate blocks progress` 改为 `gate shapes repair`。AI reviewer、publication gate、data/source gate 发现问题后，应生成 repair brief、required artifact delta 和 owner handoff。只有数据/隐私/权限、不可逆写入、human decision、forbidden authority write 才阻断 mission run。
5. 从 `platform repair on critical path` 改为 `platform repair sidecar`。OPL lease、provider admission、currentness、DHD scope、projection drift、storage/index/read-model 问题默认是 repair lane。除非它直接解除当前 paper mission 的合法执行阻断，否则不能抢占论文 executor。
6. 从 `MAS owns runtime-like behavior` 改为 `MAS owns minimal medical authority`。MAS 长期保留医学 truth、source readiness、publication quality、artifact authority、memory accept/reject、owner receipt / typed blocker / human gate；attempt、queue、resume、retry、dead-letter、session shell、workbench、provider lifecycle 归 OPL。

## Target Architecture

| Layer | New owner | Responsibility |
| --- | --- | --- |
| `medical-paper product entry` | MAS generated/direct entry + OPL hosted shell | `paper-mission start|resume|inspect|consume`。用户只面对“推进这篇论文到下一个可审阅/可投稿 milestone”的产品入口。 |
| `PaperMissionRun` | OPL runtime envelope | 同一 mission identity 下的 session、attempt、resume、provider lifecycle、stdout/log、retry/dead-letter、current-control readback。 |
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

这些命令是目标 contract sketch，不是本文授权的现有 CLI claim。

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
| OPL current-control / provider lifecycle | 完全上收 OPL；MAS 只消费 OPL readback，不生成或手写 provider authority。 |
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

- 新增 `PaperMissionRun` contract、mission artifact manifest、mission progress schema、forbidden-write guard。
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

### Phase 3: Cut over default execution

目标：新任务默认走 mission loop。

必须做：

- `domain-handler export` 不再默认导出旧 `domain_owner/default-executor-dispatch` 粒度任务；改导出 `paper_mission/start_or_resume`。
- 旧 owner-route/DHD 只作为 diagnostic / migration consumer，不能再生成主线 next action。
- `study progress` 顶层状态改用 mission state：`running_mission`、`candidate_ready_for_consumption`、`waiting_human_decision`、`stable_blocker`、`terminal_handoff`。
- DHD/currentness/OPL readback 只显示在 platform diagnostics。

验收：新 study 和 DM002/DM003 后续回合都能从 `paper-mission inspect` 读到唯一 next objective、latest paper delta、next owner 和 forbidden claims。

2026-06-23 progress/workbench slice：`study_progress` projection 和 Progress Portal / study workbench 已新增 artifact-first mission summary read model。顶层暴露 `mission_state`、`current_objective`、`latest_artifact_delta`、`next_owner_or_human_decision`、`platform_diagnostics`；内部 `artifact_first_mission_summary.paper_mission_run` 对齐 `contracts/paper_mission_run_contract.json` / `paper-mission-run.v1` 和 `med_autoscience.paper_mission_run.PaperMissionRun` canonical shape。DHD、currentness、storage、owner-route、dispatch 和 PaperRecovery 只折叠为 diagnostics / migration / provenance，不再作为 progress/workbench 默认论文主线。

2026-06-23 CLI/product-entry/domain-handler slice：`paper-mission inspect/start/resume/consume-candidate` 已作为 no-write readback 入口接入 CLI，product entry 的 `medical_paper_product_entry.default_action_intent` 指向 `paper_mission/start_or_resume`，domain-handler export 默认追加 `paper_mission/start_or_resume` task，并把旧 `domain_owner/default-executor-dispatch` task 标成 `migration_diagnostic_only`。`consume-candidate` 现在调用 MAS authority consume readback，把 accepted / rejected / route-back / typed blocker / human gate 映射回 `PaperMissionRun.consume_result` 与 `mission_state`。该 slice 只证明默认入口与 dry-run/consume readback 边界已经转向 PaperMissionRun；它不声明 live provider run、paper body patch、current package 或 publication-ready。

### Phase 4: Retire old way

目标：彻底退役旧控制面，而不是长期双轨。

退役条件：

- old DHD / owner-route / dispatch / recovery surface 没有 default product-entry、domain-handler、MCP、skill 或 OPL active caller。
- 每个 old surface 有 replacement parity：mission loop、MAS authority kernel、OPL runtime readback 或 tombstone。
- no-forbidden-write proof 覆盖 study truth、publication eval、controller decisions、paper body、owner receipt、typed blocker、human gate、current package 和 runtime state。
- DM002/DM003 canary 至少各产生一个被 MAS consume path 处理的 mission artifact delta、owner receipt、route-back、human gate 或 stable typed blocker。
- active docs、product docs、skill docs 和 progress portal 不再把旧 DHD/dispatch/recovery 链写成主执行方式。

2026-06-23 tombstone slice：`contracts/runtime/legacy-active-path-tombstones.json` 新增 `dhd_owner_route_dispatch_paper_recovery_default_paper_mainline`，把旧 DHD / owner-route / dispatch / PaperRecovery 默认主路径降为 `diagnostics_migration_provenance_only`，并禁止 product/default domain-handler mainline、paper progress、publication-ready、runtime-ready、provider-running、DM002 complete 和 DM003 complete claim。该 tombstone 关闭默认叙事边界，不等于旧物理 caller 全部删除。

2026-06-23 caller proof status：有界 caller/search evidence 已证明旧路径仍有 repo 内 active references。`domain-health-diagnostic` 仍作为 runtime diagnostic / authority consumer 暴露；`paper_recovery_state` / PaperRecovery 仍被 `current_work_unit`、`study_progress`、DHD report 和 provider-admission projection 消费；`domain_owner/default-executor-dispatch` 仍作为 OPL StageRun ABI、migration diagnostic、legacy fixture 和 transition carrier 出现在源码/测试/contract。当前能声明的是“默认 product/domain-handler mainline 已转向 PaperMissionRun，旧链路默认主线 claim 被 tombstone 禁止”；不能声明“old DHD / dispatch / recovery surface 已满足 no-active-caller physical retirement”。

## Completion Audit

| Item | Current status | Fresh evidence | Gap / forbidden interpretation |
| --- | --- | --- | --- |
| New entry exists | `done_for_no_write_default_entry` | CLI `paper-mission` parsers/readback、product entry `default_action_intent=paper_mission/start_or_resume`、domain-handler default task、contract validation `validated`。 | 这不是 live mission execution、paper artifact completion、owner receipt 或 provider running proof。 |
| Paper mission produces work | `partial_canary_candidate_readback` | `PaperMissionRun` contract / validator、artifact-first mission summary、DM002/DM003 canary candidate manifests、DM002 `consume_result.status=accepted`、DM003 `consume_result.status=typed_blocker`、两者 `written_files=[]`。 | 还缺真实 manuscript / figure / table / evidence ledger / reviewer response / owner decision packet 物化到 study workspace 并被 authority consume；当前只是 no-write canary candidate/readback。 |
| MAS authority preserved | `done_for_no_write_consume_boundary` | `consume_paper_mission_candidate` 与 CLI `consume-candidate` 均保留 accepted / rejected / route-back / typed blocker / human gate outcome；DM002/DM003 fresh consume readback 均 `authority_materialized=false` 且不写 authority。 | 不能把 readback 写成真实 `publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker、human gate、current package 或 paper body mutation。 |
| OPL owns runtime | `not_satisfied_live` | 设计与 forbidden-write guard 指向 OPL runtime owner；MAS no-write readback 禁止写 runtime queue/provider attempts。 | 还缺 OPL-hosted `PaperMissionRun` attempt/session/readback；不能从 dry-run inspect、queue empty、read-model clean 或 DHD dry-run 推导 runtime ready。 |
| Platform repair demoted | `done_for_projection_boundary` | `artifact_first_mission_summary.platform_diagnostics.counts_as_paper_progress=false`，product/docs/status 把 DHD/currentness/storage/dispatch/PaperRecovery 折叠为 diagnostics / migration / provenance。 | 这只关闭默认读面和完成口径，不说明平台修复已经全部完成。 |
| Old path retired | `partial_default_retired_physical_open` | Tombstone contract 禁止默认 mainline claim；domain-handler export 标记 legacy dispatch 为 `migration_diagnostic_only`；focused tests 锁住 replacement/forbidden claims。 | 有界 caller evidence 仍命中 DHD、PaperRecovery、default-executor-dispatch carrier / ABI / fixture / migration references；no-active-caller physical proof 未满足。 |

`100%` 只能在上述 evidence 全部新鲜可读时声明。文档、plan、schema、focused tests、DHD dry-run、queue empty、read-model clean、contract/tombstone landed、CLI no-write readback 或 old surface deletion 均不能单独支撑目标态完成；DM002/DM003 只有在 authority consume readback 或等价 owner-answer readback 指向真实 artifact delta、owner receipt、route-back、human gate、stable typed blocker 或 rejection 时才可计入目标态 paper progress。

## Immediate Next Work

1. 将旧 `domain_owner/default-executor-dispatch`、DHD 和 PaperRecovery references 分成三类：必须保留的 diagnostic / authority readback、OPL ABI / provenance carrier、可删除默认 caller；只对第三类做物理退役。
2. 对可删除 caller 做 focused no-active-caller proof：product entry、domain-handler default export、MCP/skill/default action catalog、OPL active caller 均不得再把旧链路作为 paper mission mainline。
3. 在 OPL hosted run 接入前，继续把 `paper-mission` CLI / domain-handler 输出标为 no-write readback；不得声明 runtime-ready、provider-running、publication-ready、DM002 complete 或 DM003 complete。
4. 下一轮真正论文推进必须从 canary readback 进入 study workspace artifact delta 或 owner decision packet 物化，并由 MAS authority consume/route-back/human-gate/typed-blocker surface 处理。
