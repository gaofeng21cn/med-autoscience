# OPL App MAS Runtime Workbench Program

Status: `active product enabler; content-level owner doc`
Date: `2026-05-14`
Owner: `MedAutoScience Product Projection + OPL Runtime Manager integration boundary`
Purpose: 定义当前 P1 产品化线路：把 MAS 论文自治进度变成 OPL App Runtime Workbench 中的人用运行工作台。
State: `active_support`
Machine boundary: 本文是人读 owner/program 文档。实现真相应进入稳定 JSON/API contract、domain-handler owner-route handoff、OPL App/runtime manager contract、UI test、截图证据和真实 workspace evidence。
完整历史记录：[2026-05-11 OPL App MAS Runtime Workbench full record](../history/program/opl_app_mas_runtime_workbench_program_2026_05_11_full_record.md)。

## 当前角色

本文是 MAS program portfolio 的 P1。P1 不是完整 WebUI 重写计划。它只持有 P0 所需的产品面：用户能打开 OPL App，进入 MAS paper line，看懂进度、阻塞、路线、产物，并且只触发 MAS 授权的动作。

当前读法是内容级：

- P1 的用户结果和 MAS/OPL owner 边界留在本文；
- 详细 UX 参考、旧 phase 表、外部工程参考和 open decisions 留在归档 full record；
- 共享 runtime/provider 义务归 P2；
- 论文质量、route decision、publication readiness 和 artifact authority 归 P0 / MAS owner surfaces。

## 当前状态

MAS 已具备相关 repo surface：

| surface | state | current use |
| --- | --- | --- |
| Progress Portal payload / per-study page | `landed_read_model` | source projection 和 diagnostic HTML |
| MAS private Live Console / conversation read models | `retired_physical_no_alias` | history/provenance only；运行 drilldown 归 OPL `current_control_state` |
| route read models | `landed_read_model` | route-decision trail |
| terminal attach gate | `retired_physical_no_alias` | 不作为 MAS owner gate 保留；terminal/log/provider drilldown 归 OPL `current_control_state` |
| pause/resume/stop owner actions | `landed_owner_receipt_path` | domain-handler / OPL owner-route handoff refs |
| `mas_opl_runtime_workbench_projection` | `landed_read_only_projection` | App-facing projection gate，登记在 `contracts/test-lane-manifest.json` |
| paper route lens | `landed_refs_only_projection` | 每篇 paper/study 暴露 current route、route attempts、owner receipt refs、typed blocker refs、reviewer/gate refs、artifact/source/workspace refs 和 next route/action refs；不携带 manuscript/artifact body，不声明 publication ready |
| Stage Deliverable Review / Index projection | `landed_read_only_locator_projection` | 展示 latest review page、deliverable index、freshness、claim impact、human annotation、next owner 和 blocker；不写 MAS truth |
| Stage Operating Layer workbench projection | `stage_operating_layer_primary_projection` | OPL App workbench 首屏必须只读展示 `stage_kernel_projection` 派生的 current stage、artifact roles、missing outputs、accepted receipts、blocker、next owner 和 provider liveness；缺 stage kernel surface 时 fail-closed 为 pending lane |
| `stage_artifact_index` workbench projection | `derived_secondary_locator_projection` | OPL App workbench 可在 secondary diagnostics 中展示每个 stage 的 artifact refs、latest review page/index refs、owner receipt、freshness、next owner、typed blocker 或 human gate；它是 derived refs-only locator，不是 truth source，不写 artifact body、study truth、quality verdict 或 publication readiness |
| OPL provider attempt/readiness refs | `provider_readiness_projection_ready` | OPL production proof 可被 MAS product-entry / domain projection ingestion 投影为 provider available；App 只能展示 provider refs 和 typed blocker |
| publication-route memory refs | `body_free_grouping_review_projection_ready` | 展示 consumed refs、writeback receipt refs、freshness、rejected reason、workspace/stage/route family/status grouping 和 stale/deprecated review summary；不展示 memory body，不接受 writeback |

剩余产品缺口不是“旧 P1 文档里的所有功能都要做”。当前缺口是把这些现有 MAS projection、Stage Review locator、publication-route memory refs / grouping / review summary、provider readiness refs 和 owner-route handoff refs 变成 OPL App 里的主用户运行面；MAS local Progress Portal 只保留 read-only diagnostic / evidence projection，旧 Live Console 只作为 history/provenance 读取。

P1 的当前规划状态来自 [MAS Current Development Lines](./current-development-lines.md)。P1 只承担 `functional_follow_through_gate`：把已经存在的 MAS / OPL refs、receipts、blockers 和 action boundaries 产品化。真实 provider-hosted paper progress 仍归 P0 / P2 owner surfaces；P1 不用 UI 状态、provider completion 或 queue status 宣布论文进展。

Workbench 的 Stage Operating Layer 必须按 stage-kernel-first 呈现：用户打开 paper line 时，首屏只读显示 `stage_kernel_projection` 派生的 current stage、artifact roles、missing outputs、accepted receipts、blocker、next owner 和 provider liveness。`stage_artifact_index` / Stage Deliverable Index 是 derived projection，只能作为 secondary locator/drilldown；typed closeout、controller/read-model/currentness、telemetry、evidence-tail 和 repair 只能作为 secondary diagnostics，用于解释为什么可继续、为什么等待 provider、为什么 route back 或为什么 blocked。缺 `stage_kernel_projection` 时 Workbench 必须 fail-closed 为 pending lane；UI projection 固定 `writes_mas_truth=false`、`claims_publication_ready=false`、`current_truth_source=stage_kernel_projection`。

## 活跃内容 Lane

| priority | lane | 当前范围 | 不在范围 |
| --- | --- | --- | --- |
| `P1.1` | `read_only_study_workbench` | OPL App-native MAS study drilldown，展示 status、next owner、blocker、route/decision trail、artifacts、source refs，并可并列展示 OPL `current_control_state` 的 runtime drilldown refs。 | terminal input、runtime apply、publication readiness decision |
| `P1.2` | `owner_route_handoff_transport` | pause/resume/stop/reconcile UI 展示 domain-handler / OPL owner-route handoff refs、拒绝原因和 next owner。 | 直接写 MAS runtime SQLite、controller decisions、publication eval、current package、ledger 或 terminal command file |
| `P1.3` | `runtime_drilldown_join` | App 只读并列展示 OPL `current_control_state` / provider attempt drilldown refs；MAS 不提供 terminal attach owner gate。 | 恢复旧 MDS WebSocket owner、MAS terminal input/resize/detach、或用 chat 伪装 terminal input |
| `P1.4` | `stage_review_and_memory_drilldown` | 在 Stage Operating Layer 之后，将 `stage_artifact_index`、Stage Deliverable Review / Index 与 publication-route memory body-free refs 作为 secondary diagnostics 分组展示：stage artifact refs、latest review page、claim impact、paper asset delta、freshness、human annotation、consumed/writeback refs、rejected reason、operator grouping、stale/deprecated review summary。 | 把 artifact refs、人工注释、memory refs 或 review page 变成 quality verdict / publication readiness；写 artifact body 或 MAS truth |
| `P1.5` | `provider_workbench_join` | 在 OPL production proof ingestion 已可用的基础上，把 MAS study workbench 与 OPL provider readiness、family queue、approval transport、stage attempt status、typed blocker 和 domain activity soak refs 合并显示。 | 把 provider attempt completion 或 production residency proof 当成 paper progress |

这些 lane 可以独立推进。后续 patch 可以只触碰一个 lane，只要它改善内容级结果并保持 owner 边界。

## Planning Gate Classification

| workbench gate | gate class | current planning status | done evidence |
| --- | --- | --- | --- |
| `stage_operating_layer_primary` | `functional_follow_through_gate` | `required_primary; projection_landed_app_polish_pending` | OPL App / Workbench 首屏展示 stage kernel current stage、artifact roles、missing outputs、accepted receipts、blocker、next owner 和 provider liveness；缺 stage kernel surface 时 fail-closed/pending；不写 MAS truth、不展示 artifact body、不声明 publication ready。 |
| `stage_artifact_index_drilldown` | `functional_follow_through_gate` | `secondary_diagnostic; projection_landed_app_polish_pending` | OPL App / Workbench 在 secondary drilldown 展示 `stage_artifact_index` / Stage Deliverable Index 的 artifact refs、latest review page、owner receipt、freshness、next owner、human gate 和 typed blocker；它是 derived projection，不是 truth source。 |
| `stage_review_and_memory_drilldown` | `functional_follow_through_gate` | `implemented_read_model; app_polish_pending` | OPL App / Workbench 展示 latest review page、stage index、claim impact、freshness、memory consumed/writeback refs、rejected reason、operator grouping、review summary 和 typed blocker；不写 MAS truth。 |
| `owner_route_handoff_transport` | `functional_follow_through_gate` | `planned; domain-handler handoff refs landed` | Pause/resume/stop/reconcile 意图返回 domain-handler / OPL owner-route handoff refs、refusal reason 和 next owner；App 不写 runtime SQLite、controller decision、publication eval 或 package。 |
| `runtime_drilldown_join` | `functional_follow_through_gate` | `planned; OPL current_control_state owner` | App 只读展示 OPL provider/attempt/runtime drilldown refs；MAS 不写 terminal command queue，也不维护 terminal owner gate。 |
| `provider_attempt_join` | `functional_follow_through_gate` | `planned; provider refs available` | App 能把 provider readiness、attempt refs、human gate transport、dead-letter 和 domain typed blockers 与 MAS study projection 并列展示；provider done 不等于 paper progress。 |

## 当前 Contract 边界

MAS 生产或持有：

- study truth、publication judgment、paper/package authority、quality verdict、owner route、owner-route handoff refs、source refs 和 forbidden-write rules；
- `mas_opl_runtime_workbench_projection`，它是 App-facing projection，不是第二 truth source；
- `paper_route_lens` 是 `mas_opl_runtime_workbench_projection.studies[*]` 与 `reference_projection.lanes.paper_route_lens` 下的 refs-only 子面；字段固定为 `current_route`、`route_attempts`、`route_attempt_counts`、`owner_receipt_refs`、`typed_blocker_refs`、`reviewer_gate_refs`、`artifact_refs`、`source_refs`、`workspace_refs`、`next_route_refs` 和 `next_action_refs`，并固定 `body_included=false`、`claims_publication_ready=false`；
- Stage Operating Layer 的 primary projection；字段来自 `stage_kernel_projection`，覆盖 current stage、artifact roles、missing outputs、accepted receipts、blocker、next owner 和 provider liveness，并固定 `writes_mas_truth=false`、`claims_publication_ready=false`、`current_truth_source=stage_kernel_projection`；
- `stage_artifact_index` / Stage Deliverable Index 的 derived refs-only workbench projection；字段应覆盖 stage artifact refs、latest review/index refs、owner receipt refs、freshness、next owner/action refs、typed blocker refs、human gate refs 和 provider liveness refs，并固定 `body_included=false`、`writes_mas_truth=false`、`claims_publication_ready=false`，但只能作为 secondary diagnostics；
- local Progress Portal read-only diagnostic artifacts；retired Live Console history/provenance refs。

OPL App / OPL Runtime Manager 持有：

- navigation、runtime workbench layout、notification/approval transport、App history cache、panel state、IPC/WebView/native component safety 和用户交互 shell；
- typed MAS owner-route request 的 transport，以及 MAS typed handoff / receipt 的展示；
- provider/runtime queue context、OPL production proof state、managed-state freshness、typed blocker 和 domain activity soak refs。

P1 禁止写入：study truth、publication eval、controller decisions、runtime lifecycle SQLite、terminal command files、current package、submission package、evidence ledger、review ledger、stage artifact body、canonical paper body。

## 优先级调整

旧计划把 App workbench 写成四个大 phase。当前 P1 应跟随 framework-first 主线：

1. P2 先完成 OPL framework 基础和 MAS framework migration 的机器边界；
2. P1 再基于迁移后的 MAS projection / OPL provider projection 交付 read-only App-native study workbench；
3. 把 Stage Review / Index、publication-route memory refs 和 provider readiness refs 做成可 drilldown 的只读分组；
4. read-only state/source refs 可信后，再接 controlled owner-route handoff transport；
5. 对 live run 增加 OPL `current_control_state` / provider attempt drilldown join；
6. P2 完成真实 provider-hosted MAS paper-line soak 后，再把 provider queue/attempt context 从 evidence panel 升级为主工作台的一部分。

因此 local Portal polish、重复 WebUI 工作、宽泛 Electron 架构探索和旧 MDS UI parity 细节是支撑材料，不是独立 active program scope。

## 验证

P1 证据按层级判断：

1. MAS projection contract tests、focused Progress Portal tests 和 OPL `current_control_state` projection assertions；
2. OPL App/runtime manager type、IPC 和 renderer tests；
3. desktop screenshot 或 browser/Electron evidence，证明 workbench 正确展示 no-live-run、running、blocked、owner-route handoff、stale/freshness 状态；
4. controlled action apply 前先完成真实 workspace read-only soak。

P1 完成不能由文档、CLI 输出、provider status 或 queue 存在证明。完成标准是用户能在 OPL App 里检查并安全操作 MAS study，同时 MAS owner surface 仍是唯一 authority。

## 历史内容处置

上一版 P1 长文档混合了详细 UX、外部参考、phase plan、lane table、验证阶梯和 open decisions。它已经归档为 full record。需要实施细节或 provenance 时可以读取归档，但不能把归档里的每个 section 都当成当前 mandatory scope。

新的实现细节只有在成为上述活跃内容 lane 或稳定机器 contract 后，才提升回当前 owner 文档。
