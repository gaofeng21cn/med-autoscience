# OPL App MAS Runtime Workbench Program

Status: `active product enabler; content-level owner doc`
Date: `2026-05-14`
Owner: `MedAutoScience Product Projection + OPL Runtime Manager integration boundary`
Purpose: 定义当前 P1 产品化线路：把 MAS 论文自治进度变成 OPL App Runtime Workbench 中的人用运行工作台。
Machine boundary: 本文是人读 owner/program 文档。实现真相应进入稳定 JSON/API contract、MAS action receipt、OPL App/runtime manager contract、UI test、截图证据和真实 workspace evidence。
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
| Live Console | `landed_read_model` | run/session/log/terminal observation |
| conversation / route read models | `landed_read_model` | executor timeline 和 route-decision trail |
| terminal attach gate | `owner_gate_landed` | fail-closed attach/input/resize/detach authority |
| pause/resume/stop owner actions | `landed_owner_receipt_path` | MAS authority 下的 controlled runtime action |
| `mas_opl_runtime_workbench_projection` | `landed_read_only_projection` | App-facing projection gate，登记在 `contracts/test-lane-manifest.json` |
| Stage Deliverable Review / Index projection | `landed_read_only_locator_projection` | 展示 latest review page、deliverable index、freshness、claim impact、human annotation、next owner 和 blocker；不写 MAS truth |
| OPL provider attempt/readiness refs | `provider_readiness_projection_ready` | OPL production proof 可被 MAS product-entry / sidecar ingestion 投影为 provider available；App 只能展示 provider refs 和 typed blocker |
| publication-route memory refs | `body_free_grouping_review_projection_ready` | 展示 consumed refs、writeback receipt refs、freshness、rejected reason、workspace/stage/route family/status grouping 和 stale/deprecated review summary；不展示 memory body，不接受 writeback |

剩余产品缺口不是“旧 P1 文档里的所有功能都要做”。当前缺口是把这些现有 MAS projection、Stage Review locator、publication-route memory refs / grouping / review summary、provider readiness refs 和 action receipts 变成 OPL App 里的主用户运行面，同时 local Portal / Live Console 保留为 diagnostic、debug 和 evidence。

P1 的当前规划状态来自 [MAS Current Development Lines](./current_development_lines.md)。P1 只承担 `functional_follow_through_gate`：把已经存在的 MAS / OPL refs、receipts、blockers 和 action boundaries 产品化。真实 provider-hosted paper progress 仍归 P0 / P2 owner surfaces；P1 不用 UI 状态、provider completion 或 queue status 宣布论文进展。

## 活跃内容 Lane

| priority | lane | 当前范围 | 不在范围 |
| --- | --- | --- | --- |
| `P1.1` | `read_only_study_workbench` | OPL App-native MAS study drilldown，展示 status、next owner、blocker、route/decision trail、executor conversation、terminal/log tail、artifacts、source refs。 | terminal input、runtime apply、publication readiness decision |
| `P1.2` | `action_receipt_transport` | pause/resume/stop/reconcile dry-run UI 调 MAS owner endpoint，展示 receipt、拒绝原因、idempotency 和 next state。 | 直接写 MAS runtime SQLite、controller decisions、publication eval、current package、ledger 或 terminal command file |
| `P1.3` | `interactive_terminal_attach` | 仅当 MAS terminal attach status 可用时启用 App terminal panel；input/resize/detach 经 MAS token/lease/idempotency/audit gate。 | 恢复旧 MDS WebSocket owner，或用 chat 伪装 terminal input |
| `P1.4` | `stage_review_and_memory_drilldown` | 将 Stage Deliverable Review / Index 与 publication-route memory body-free refs 分组展示：latest review page、claim impact、paper asset delta、freshness、human annotation、consumed/writeback refs、rejected reason、operator grouping、stale/deprecated review summary。 | 把人工注释、memory refs 或 review page 变成 quality verdict / publication readiness |
| `P1.5` | `provider_workbench_join` | 在 OPL production proof ingestion 已可用的基础上，把 MAS study workbench 与 OPL provider readiness、family queue、approval transport、stage attempt status、typed blocker 和 domain activity soak refs 合并显示。 | 把 provider attempt completion 或 production residency proof 当成 paper progress |

这些 lane 可以独立推进。后续 patch 可以只触碰一个 lane，只要它改善内容级结果并保持 owner 边界。

## Planning Gate Classification

| workbench gate | gate class | current planning status | done evidence |
| --- | --- | --- | --- |
| `stage_review_and_memory_drilldown` | `functional_follow_through_gate` | `implemented_read_model; app_polish_pending` | OPL App / Workbench 展示 latest review page、stage index、claim impact、freshness、memory consumed/writeback refs、rejected reason、operator grouping、review summary 和 typed blocker；不写 MAS truth。 |
| `safe_action_receipt_transport` | `functional_follow_through_gate` | `planned; MAS receipt path landed` | Pause/resume/stop/reconcile dry-run 返回 MAS action receipt、idempotency、refusal reason 和 next owner；App 不写 runtime SQLite、controller decision、publication eval 或 package。 |
| `terminal_attach_panel` | `functional_follow_through_gate` | `planned; owner gate landed` | 只有 attach-capable live run 才启用；input/resize/detach 经 MAS token、lease、idempotency 和 audit gate。 |
| `provider_attempt_join` | `functional_follow_through_gate` | `planned; provider refs available` | App 能把 provider readiness、attempt refs、human gate transport、dead-letter 和 domain typed blockers 与 MAS study projection 并列展示；provider done 不等于 paper progress。 |

## 当前 Contract 边界

MAS 生产或持有：

- study truth、publication judgment、paper/package authority、quality verdict、owner route、action receipt、terminal attach gate、source refs 和 forbidden-write rules；
- `mas_opl_runtime_workbench_projection`，它是 App-facing projection，不是第二 truth source；
- local Portal / Live Console diagnostic artifacts。

OPL App / OPL Runtime Manager 持有：

- navigation、runtime workbench layout、notification/approval transport、App history cache、panel state、IPC/WebView/native component safety 和用户交互 shell；
- typed MAS action request 的 transport，以及 MAS typed receipt 的展示；
- provider/runtime queue context、OPL production proof state、managed-state freshness、typed blocker 和 domain activity soak refs。

P1 禁止写入：study truth、publication eval、controller decisions、runtime lifecycle SQLite、terminal command files、current package、submission package、evidence ledger、review ledger。

## 优先级调整

旧计划把 App workbench 写成四个大 phase。当前 P1 应跟随 framework-first 主线：

1. P2 先完成 OPL framework 基础和 MAS framework migration 的机器边界；
2. P1 再基于迁移后的 MAS projection / OPL provider projection 交付 read-only App-native study workbench；
3. 把 Stage Review / Index、publication-route memory refs 和 provider readiness refs 做成可 drilldown 的只读分组；
4. read-only state/source refs 可信后，再接 controlled action receipt transport；
5. 仅对 attach-capable live run 增加 interactive terminal attach；
6. P2 完成真实 provider-hosted MAS paper-line soak 后，再把 provider queue/attempt context 从 evidence panel 升级为主工作台的一部分。

因此 local Portal polish、重复 WebUI 工作、宽泛 Electron 架构探索和旧 MDS UI parity 细节是支撑材料，不是独立 active program scope。

## 验证

P1 证据按层级判断：

1. MAS projection contract tests 和 focused Portal/Live Console tests；
2. OPL App/runtime manager type、IPC 和 renderer tests；
3. desktop screenshot 或 browser/Electron evidence，证明 workbench 正确展示 no-live-run、running、blocked、action receipt、stale/freshness 状态；
4. controlled action apply 前先完成真实 workspace read-only soak。

P1 完成不能由文档、CLI 输出、provider status 或 queue 存在证明。完成标准是用户能在 OPL App 里检查并安全操作 MAS study，同时 MAS owner surface 仍是唯一 authority。

## 历史内容处置

上一版 P1 长文档混合了详细 UX、外部参考、phase plan、lane table、验证阶梯和 open decisions。它已经归档为 full record。需要实施细节或 provenance 时可以读取归档，但不能把归档里的每个 section 都当成当前 mandatory scope。

新的实现细节只有在成为上述活跃内容 lane 或稳定机器 contract 后，才提升回当前 owner 文档。
