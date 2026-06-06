# MAS / OPL Stage Native 状态机设计

Owner: `MedAutoScience` / `OPL Framework`
Purpose: `stage_native_state_machine_design`
State: `active_design_foundation_landed`
Machine boundary: 本文是人读顶层设计。机器真相继续归 `agent/` semantic pack、`contracts/`、源码、CLI/MCP/API 行为、OPL runtime ledger、StageRun 状态、真实 study workspace artifact、owner receipt 和 typed blocker。
Date: `2026-06-05`

## 结论

Stage Native 的原始思路是正确的：一个 Stage 的产出集中在 stage-owned folder 里，维护者和 operator 能通过目录快速理解已经产出什么、缺什么、下一步应该去哪里。RCA 智能体推进顺滑，正是因为它的 stage folder、role artifact、review/export receipt 和 closeout 口径集中，状态判断没有被拆成多套解释链。

MAS 当前的问题不是 Stage Native 方向错了，而是 Stage Native 的完成口径还没有彻底落到目录、manifest、receipt/blocker 上。只要目录外还存在多套逻辑分别解释 currentness、admission、next owner、latest projection 和 closeout，就会重新出现互相覆盖、重复 redrive、read-model 漂移和人工盯守。

目标不是重建一套 MAS controller system。目标是把 Stage Native 落到底：

```text
stage folder + stage_manifest + role artifacts + owner receipt / typed blocker
```

`StageRun Kernel` 只是这个 Stage Native 体系的最小状态壳，用来表达一个 Stage 当前处于 declared、inputs-ready、running、terminalizing、accepted 还是 blocked。它不拥有医学质量，不替代 stage folder，不新增一组 controller，也不让 `latest.json`、progress projection、portal 或 workbench 反向决定 Stage 是否完成。

## 当前落地状态

2026-06-05 foundation tranche 已落地到 MAS 主干，并在后续 canonical path follow-through 中收敛到当前 Stage Native 文件名；对应 MAS 提交线是 `3eb66cbe`、`6495460c`、`6ef10650`：

- MAS profile：`contracts/stage_run_kernel_profile.json` 固定 `StageRun`、`ArtifactRef`、`OwnerReceipt`、`TypedBlocker`、`ReadModel`、launch admission、default read surface、canary scope、Stage-internal strategy refs、legacy wrapper retirement 和 projection boundary。
- MAS adoption binding：`contracts/stage_artifact_kernel_adoption.json` 绑定 `stage folder + stage_manifest + role artifacts + owner receipt / typed blocker`，并明确 StageRun Kernel 不是 MAS controller system。
- MAS canonical stage folder：materializer / index 当前使用 `stage_manifest.json`、`receipts/owner_receipt.json`、`receipts/typed_blocker.json`、`inputs/consumed_artifact_refs.json`、`lineage/prov.json` 和 `projection/current_owner_delta.json`。
- MAS projection：`src/med_autoscience/controllers/stage_run_kernel.py` 从 stage folder / manifest / receipt / blocker 派生 refs-only StageRun projection；`study_progress_parts/stage_kernel_projection.py` 在 physical stage folder 存在时优先采用 manifest-backed `current_owner_delta`。
- MAS canary tests：`tests/stage_run_kernel_cases/test_ai_reviewer_stage_run_kernel.py` 覆盖 AI reviewer publication eval rebuild 的 owner receipt、typed blocker、provider terminal 不等于 domain accepted，以及 `study progress` 优先 manifest-backed blocker；这些是 synthetic canary，不是 live DM002 / DM003 owner-chain closeout。
- MAS terminal handoff apply：`publication_handoff_owner_gate` 现在要求可信 OPL execution authorization / provider attempt / lease / closeout binding。缺授权时 fail closed，返回 OPL-owned execution authorization blocker，不改 MAS owner receipt、typed blocker、publication eval、controller decision、paper、package 或 `current_package`；有授权时只写 stage-native `handoff_owner_receipt.json` 或 `receipts/typed_blocker.json`，并把 `closeout_binding`、`current.json`、`projection/current_owner_delta.json`、`latest_owner_answer_ref`、`hard_gate.owner_answer_*` 和 `delta_id` 绑定到 StageRun / manifest / current pointer / source fingerprint / idempotency key。
- MAS readiness follow-up：DM002 / DM003 live workspace 当前已产出 `medical_paper_readiness_not_ready` typed blocker，`projection/current_owner_delta.json` 指向 `MedAutoScience / complete_medical_paper_readiness_surface`。该 owner surface 已进入 MAS callable / owner-route / default-executor / dispatch：它从 `medical_paper_readiness.next_action.surface_key` 取得当前能力面，只消费与当前 surface 匹配的 dispatch / request / ref payload，避免旧 dispatch 重放；缺 payload / 缺 surface key 时写 stable owner blocker。2026-06-06 follow-through 已补齐 `literature_provider_runtime`、`study_line_selection`、`archetype_analysis_contract` 和 `bounded_analysis_candidate_board` 四类 owner-authored payload / materializer：provider runtime 可从 ready literature intelligence 或联网 provider adapters 生成 provider-backed payload 与 response ledger；study line 可从 canonical decision 或 route-decision artifact 物化；analysis contract 可从 `study.yaml`、profile 和 resolver 写入 `paper/medical_analysis_contract.json`；bounded board 可从 resolved analysis contract 的 required packages 生成 bounded explore candidates。这些路径只写 readiness canonical surface、action result、readiness projection 和 owner blocker，不写 paper / package / publication truth。Fresh read-only check 显示 DM002 已到 `ready_count=4/13`、下一 surface 是 `bounded_analysis_candidate_board`；DM003 仍为 `ready_count=0/13`、下一 surface 是 `literature_provider_runtime`。真实 DM002 / DM003 live paper readiness evidence 继续由对应 owner run 关闭。
- MAS current execution read-model：`current_execution_envelope` 的顶层 state precedence 是非 superseded typed blocker > live running provider attempt > parked / executable action projection。OPL live running attempt 能压过 stale action queue、stale parked projection 和 runtime-admission/recovery blocker，但不能压过 `typed_closeout_packet_required`、`medical_paper_readiness_not_ready` 这类当前 owner blocker。`action_queue` 是 evidence-only；running attempt 的 `next_work_unit` 只能来自 live attempt / runtime health / stage attempt / workflow ref，不能从 stale action queue 借用。
- OPL substrate：`/Users/gaofeng/workspace/one-person-lab` 持有 refs-only StageRun contract、read-model rebuild primitive、family conformance 和默认 CLI/read surface；OPL 侧 Stage Native Kernel rollout 继续按 OPL repo 的 live diff、验证和提交记录判断，MAS 文档不把 OPL dirty lane 写成已吸收。

这次落地关闭的是 StageRun Kernel 的 profile / projection / focused canary foundation、terminal publication handoff 的功能面 owner-answer binding、typed blocker 后续 owner surface 的可执行入口，以及 `literature_provider_runtime` / `study_line_selection` / `archetype_analysis_contract` / `bounded_analysis_candidate_board` 四个 readiness surface 的 owner-authored follow-through 缺口。real paper readiness evidence 仍开放：DM002 / DM003 现在不是等 OPL authorization 或 publication handoff callable，而是等 MAS `complete_medical_paper_readiness_surface` 在真实 owner run 中继续补齐当前 readiness surface，或产出匹配当前 StageRun/source/idempotency 的 owner receipt、quality gate receipt、typed blocker、human gate 或 route-back evidence。补偿链 retirement / tombstone 现在由 `contracts/runtime/legacy-active-path-tombstones.json#/stage_native_compensation_retirement_gate` 固定：fresh live evidence 必须同时包含 OPL StageRun status、MAS receipt/blocker、stage manifest、`study progress` current owner delta，并用 same work-unit keys 一致绑定；gate 未满足前只能保留 tombstone / provenance / delete-gate context，不能物理退役。因此不能把本次 foundation / binding / payload-authoring landing 写成论文线完成、publication-ready、domain-ready、production-ready、`current_package` fresh、或补偿链已全部物理退役。

## 设计原则

1. Stage folder 是 artifact / evidence 面。
2. `stage_manifest.json` 是 Stage 目录内的结构合同。
3. role artifact 说明“做过什么”和“产出了什么”。
4. `owner_receipt.json` / `typed_blocker.json` 是唯一推进口径。
5. `StageRun Kernel` 只派生当前状态，不独立解释医学语义。
6. OPL 承担运行基座：attempt、lease、worker、retry、event log、projection rebuild。
7. MAS 承担 domain authority：stage semantics、quality gate、publication verdict、artifact authority、owner receipt、typed blocker。

一句话：

```text
文件存在证明 evidence 存在；receipt/blocker 才证明 Stage 已关闭或被明确阻断。
```

## 外部成熟经验的抽象

以下经验只作为设计校准，不复制外部 runtime 形状：

| 经验来源 | 可吸收原则 | MAS / OPL 映射 |
| --- | --- | --- |
| [Temporal durable execution](https://docs.temporal.io/) | runtime 持久化 workflow/activity 状态，worker 可恢复。 | OPL 负责 attempt、lease、retry、terminal closeout；MAS 不恢复私有 attempt loop。 |
| [Kubernetes reconciliation](https://kubernetes.io/docs/concepts/extend-kubernetes/) | `.spec` 与 `.status` 分离，状态从观察和事件收敛。 | StageRun 只需要最小 `spec/status/observed_generation`；不把这种模式扩展成 MAS 多 controller。 |
| [Airflow deferrable operators](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/deferring.html) | 等待外部条件时释放 worker，事件回来再恢复。 | human gate、provider admission、external resource wait 进入 deferred state，不占用 executor。 |
| [Prefect states](https://docs.prefect.io/v3/concepts/states) | 运行态要明确区分 pending、running、paused、failed、crashed、completed。 | `paused`、`admission_pending`、`running_provider_attempt`、`typed_blocked`、`infra_crashed` 不混成一个 progress 字段。 |
| [Argo artifacts](https://argo-workflows.readthedocs.io/en/stable/walk-through/artifacts/) / [Kubeflow artifacts](https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/artifacts/) | artifact 是一等输入输出，有 URI、metadata、lineage。 | Stage folder 内每个输出都有 `ArtifactRef`、role 和 lineage，不从任意文件存在性推断完成。 |
| [OpenLineage](https://openlineage.io/) / [W3C PROV](https://www.w3.org/TR/2013/NOTE-prov-overview-20130430/) | run、artifact、agent、lineage 必须可追踪。 | 每个 StageRun 记录 consumed refs、produced refs、owner receipt、typed blocker 和 agent invocation。 |
| [AI Co-Scientist](https://arxiv.org/abs/2502.18864) | 科研 stage 内可包含 generation、debate、evolution、meta-review。 | Stage 内部可以有 strategy kernel；Stage 外部状态壳保持薄，只调度、持久化和投影 refs。 |

## 和 Stage Native / RCA 思路的关系

这是强化 Stage Native，不是推翻 Stage Native。

| 原 Stage Native 思路 | 目标态补足 |
| --- | --- |
| 每个 Stage 的产出放到对应目录。 | 保留 stage folder，并要求目录内有 `stage_manifest.json`。 |
| 看目录和文件大概知道当前状态。 | 看 `stage_manifest + required_roles + receipt_or_blocker` 精确知道状态。 |
| 当前 Stage 搞定就进入下一个 Stage。 | 当前 Stage 只有在产出 `OwnerReceipt` 或 stable `TypedBlocker` 后才 route 到下一 Stage。 |
| 文件存在说明该步骤做过。 | 文件存在只说明 evidence 存在；role 是否 current、是否满足 gate、是否被 receipt 消费由 manifest 和 receipt/blocker 判定。 |
| RCA 通过 stage output 顺滑推进。 | MAS 应复用 RCA 的 role artifact / receipt closeout 口径，减少目录外的 controller 解释层。 |

理想 Stage folder：

```text
artifacts/stage_outputs/07-independent_review_and_revision/
  stage_manifest.json
  inputs/
    consumed_artifact_refs.json
  outputs/
    independent_reviewer_record.json
    revision_action_matrix.json
  receipts/
    owner_receipt.json
    typed_blocker.json
  lineage/
    prov.json
    openlineage_event.json
  projection/
    current_owner_delta.json
```

`outputs/` 是 artifact evidence，`receipts/` 是 transition authority，`projection/` 是人机读面。没有 receipt 或 blocker，目录再完整也不能自动进入下一 Stage。

## 最小对象模型

| 对象 | Owner | 职责 |
| --- | --- | --- |
| `StudyRun` | MAS | 一篇论文线的长期语义实体，持有 study truth、publication route 和 domain boundary。 |
| `StageRun` | OPL runtime + MAS stage spec | 一个 Stage 的最小状态壳，包含 `spec/status/observed_generation`。 |
| `WorkUnitRun` | OPL | Stage 内一次可执行 work unit，绑定 attempt、lease、retry、terminal closeout。 |
| `ArtifactRef` | MAS authority / OPL locator | 任何正文、表图、评审、分析、gate 输出的 immutable ref、hash、role、lineage。 |
| `OwnerReceipt` | MAS | 成功推进状态的唯一 domain 凭证。 |
| `TypedBlocker` | MAS | 阻断状态的唯一 domain 凭证，必须给 owner、required input、blocked surface 和 next safe action。 |
| `ReadModel` | OPL / product projection | 从 StageRun event log 和 MAS receipt/blocker 重建，只读，不拥有 truth。 |

## StageRun Kernel 状态机

默认主链：

```text
Declared
  -> InputsReady
  -> Admitted
  -> Running
  -> Terminalizing
  -> DomainAccepted
  -> NextStageReady
```

允许异常分支：

```text
NeedsHumanDecision
NeedsExternalResource
RetryScheduled
TypedBlocked
InfrastructureCrashed
Superseded
```

状态语义：

- `Declared`：Stage spec 已存在，但 input refs 尚未满足。
- `InputsReady`：required role artifact 和 knowledge packet 满足 entry contract。
- `Admitted`：OPL 已接受 work unit，生成 task / lease / attempt。
- `Running`：provider attempt 有 live proof。
- `Terminalizing`：provider 已写 closeout，OPL 正在 ingest。
- `DomainAccepted`：MAS 已消费 closeout 并签 `OwnerReceipt` 或 `TypedBlocker`。
- `NextStageReady`：route 产生下一 StageRun spec 或 human gate。

关键不变量：

- `provider completed` 不等于 `DomainAccepted`。
- `latest.json refreshed` 不等于 `OwnerReceipt`。
- `stage folder has files` 不等于 `NextStageReady`。
- `active_run_id` 非空不等于有效 paper progress。

## OPL 基座优化

OPL 应提供 StageRun Kernel 所需的通用 runtime substrate：

1. 持有 `StageRun.spec/status` 和 event log。
2. queue、hold、admission、lease、attempt、retry、dead-letter、terminal closeout 全部围绕 `StageRun`。
3. `observed_generation` 防止旧 work unit / 旧 request 在修复后继续消耗新预算。
4. retry budget 绑定 `{stage_run_id, generation, input_fingerprint, failure_signature}`，不是只按 work unit 名称累计。
5. hold/release 必须 scope exact，并投影到 operator read model；不允许旧 study-wide hold 静默挡住当前 Stage。
6. terminal closeout ingest 后触发 read-model rebuild，不要求 MAS wrapper 人工逐个 reconcile。
7. 默认 operator API 是 `current_owner_delta`，而不是长 runtime reason 串。

OPL 不做：

- 不判断医学质量。
- 不写 MAS study truth、publication verdict、artifact body、memory body 或 `current_package`。
- 不把 task completion 升级为 domain completion。

## MAS 优化

MAS 应进一步收敛为 Stage Pack + minimal authority functions：

1. 每个 Stage 在 `agent/` 和 machine contracts 中声明 objective、entry refs、required artifact roles、tool policy、quality gate、closeout obligation。
2. authority function 只产出 `OwnerReceipt`、`TypedBlocker`、safe action refs、artifact authority receipt、memory accept/reject/blocker receipt。
3. publication eval、controller decision、progress projection 都从 receipt/blocker 派生。
4. route 只选择下一 owner / action / StageRun spec，不修 runtime state。
5. AI reviewer / auditor 必须是独立 invocation；executor 自审不能关闭 quality gate。

MAS 当前多段补偿链应收敛为：

```text
MAS emits OwnerActionRequest
OPL creates StageRun / WorkUnitRun
Provider returns CloseoutPacket
MAS consumes packet
MAS signs OwnerReceipt or TypedBlocker
OPL projects current_owner_delta
```

这不是新增 MAS controller，而是减少 MAS controller：让现有 `owner-route-reconcile`、`domain-action-request-materialize`、`domain-owner-action-dispatch` 这类互相补偿的路径逐步退役或合并到一个 Stage closeout loop。

## 防止解释层打架的规则

1. 一个字段只能有一个 writer。`StageRun.status` 归 OPL；`OwnerReceipt` / `TypedBlocker` 归 MAS。
2. 一个状态只能有一个 transition authority。进入下一 Stage 只看 receipt/blocker，不看散落的 `latest.json`。
3. 一个 Stage 只能有一个 active generation。旧 request、旧 provider attempt、旧 redrive 自动 supersede。
4. read-model 可丢可重建。任何 read-model 不能反向写入 truth。
5. file presence 只作为 evidence，不作为 authority。
6. platform repair 和 paper progress 分账。修 currentness / liveness / projection 不计论文实质进展。

## DM002 / DM003 Canary 路径

第一条 canary 不从所有 Stage 开始，只选当前高频故障点：AI reviewer publication eval rebuild。

目标：

1. 定义 `StageRun` schema 和 `ai_reviewer_publication_eval_rebuild` Stage spec。
2. 将当前 `return_to_ai_reviewer_workflow` 包装为一个 `WorkUnitRun`。
3. Stage folder 中要求：
   - `stage_manifest.json`
   - `inputs/consumed_artifact_refs.json`
   - `outputs/ai_reviewer_record.json`
   - `receipts/owner_receipt.json` 或 `receipts/typed_blocker.json`
   - `lineage/prov.json`
4. OPL attempt terminal 后必须进入 `Terminalizing`，MAS 消费 closeout 后进入 `DomainAccepted`。
5. `publication_eval/latest.json` 只能由 receipt 派生刷新，不能作为 route authority。
6. `study progress` 默认输出 StageRun status 和 current owner delta。

Canary 完成标准：

- DM002 / DM003 各自产生一个 fresh `OwnerReceipt` 或 stable `TypedBlocker`；当前 terminal handoff 已满足 typed-blocker closeout，并把下一 owner delta 指向 `complete_medical_paper_readiness_surface`。
- OPL StageRun status、MAS receipt/blocker、stage manifest、MAS `study progress` 四者一致，且 owner answer 已带 `closeout_binding` / `current_pointer_ref` / `source_fingerprint` / `idempotency_key` 绑定。
- 不需要人工运行 `owner-route-reconcile` 才能看见新状态。
- 旧 attempt / 旧 request 不再消耗新 generation 的 retry budget。

## 推荐落地顺序

1. 文档冻结：本文进入 active docs，并在 gap plan 中声明 StageRun Kernel 是 Stage Native 的最小状态壳。
2. Contract first：新增 `contracts/stage_run_kernel_profile.json`，定义 `StageRun`、`ArtifactRef`、`OwnerReceipt`、`TypedBlocker`、`ReadModel` 边界。
3. OPL canary：在 OPL 基座实现 StageRun refs-only status/read-model，先不改所有 domain agent。
4. MAS canary：只迁移 AI reviewer publication eval rebuild，不碰全论文路线。
5. Stage folder manifest：为 DM002 / DM003 当前 stage folder 生成 manifest-backed role map。
6. Projection cutover：`study progress` 优先读 StageRun status + receipt/blocker，`latest.json` 降为 evidence projection。
7. 删除补偿链：按 `contracts/runtime/legacy-active-path-tombstones.json#/stage_native_compensation_retirement_gate` 判断；fresh live owner evidence 证明 OPL StageRun status、MAS receipt/blocker、stage manifest、`study progress` current owner delta 四者对同一 work unit 一致后，才退役同一 work unit 上的重复 reconcile/materialize/dispatch 补丁路径；gate 未满足时只保留 tombstone/provenance/delete-gate context。

## 验收标准

设计层验收：

- 文档明确 Stage Native 与 StageRun Kernel 的关系。
- 文档明确 StageRun Kernel 不是新增 MAS controller system。
- 文档明确 OPL / MAS authority boundary。
- 文档明确 file presence、provider completion、read-model refresh 不能作为 Stage completion。
- 文档明确 DM002 / DM003 canary 的第一步。

工程层验收：

- `StageRun` schema 可 machine validate。
- OPL 能从 StageRun event log rebuild read model。
- MAS authority function 只返回 receipt/blocker。
- DM002 / DM003 canary 不需要人工反复 reconcile。
- focused tests 能证明旧 attempt supersession、retry budget reset、terminal closeout consumption 和 projection rebuild。

## 不做的事

- 不恢复 MAS 私有 scheduler / queue / worker / attempt ledger。
- 不新增 MAS controller system。
- 不把 RCA 的目录成功经验简化成“有文件就完成”。
- 不把 `publication_eval/latest.json`、`controller_decisions/latest.json` 或 progress projection 写成 primary authority。
- 不用临时复制 legacy `paper/` body 文件解决 currentness。
- 不把 OPL provider completion 写成 publication-ready。
- 不把 Stage strategy kernel 里的 ranking / proximity / debate 分数写成医学质量结论。

## 当前回答口径

如果问“这和之前 Stage Native 思路是否兼容”，答案是：

> 兼容。Stage Native 是 artifact/evidence 的正确载体；StageRun Kernel 是 Stage Native 的最小状态壳，不是新的 controller 群。RCA 顺滑说明目录化 stage output + role artifact + receipt closeout 的路线成立。MAS 卡住不是因为目录化错了，而是目录之外还有多套逻辑在抢着解释完成、currentness、admission 和下一 owner。新的设计是把目录产出保留下来，把完成判断集中到 manifest-backed role artifact、owner receipt 和 typed blocker。
