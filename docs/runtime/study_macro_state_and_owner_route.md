# Study Macro State and Owner Route Contract

## 目标

MAS 的状态读取、runtime 修复、publication gate、AI reviewer 与 dispatch executor 必须先收敛到同一条当前真相，再决定下一 owner。该合同把用户可见状态拆成短枚举和细节字段，避免用超长状态名承载所有语义，也避免各层各自按局部信号恢复或停止研究。

## 三类 authority

- 论文真相继续由 canonical paper、manuscript、package、`publication_eval/latest.json`、`controller_decisions/latest.json`、`study_truth/latest.json` 等文件 surface 持有。
- 用户干预和记忆使用 append-only 文件 surface，例如 `artifacts/interventions/events.jsonl`；它记录用户做过什么、为什么暂停或重开、下一次 Agent 应如何接力。
- SQLite lifecycle store 只做 sidecar index、read model、receipt 与幂等检索。它可以索引 `study_macro_state_snapshot`、`owner_route_receipt`、`dispatch_receipt`、`surface_ref`，不能替代文件 authority。

## 宏观状态

`study_macro_state` 只暴露三段短主语义：

- `writer_state`: `live`、`queued`、`parked`、`conflict`
- `user_next`: `watch`、`submit_info`、`repair`、`revise`、`none`、`inspect`
- `reason`: `runtime`、`external_info`、`stop_loss`、`user_stop`、`quality`、`truth_conflict`、`unknown`

具体差异写入 `details` 和 `conditions`：

- DM001、NF002、NF003 同归 `parked / submit_info / external_info`，差异只体现在 journal/format/missing metadata。
- NF001、NF004、DM004 同归 `parked / none`，差异体现在 `reason`、`stop_origin`、`package_delivered` 和 `reopen_mode`。`package_delivered` 表达用户层里程碑包已经存在，不表达论文质量已清关。
- DM004 的用户停止不是永久删除。它必须保留 `reopen_allowed=true` 与 `reopen_mode=new_plan_required`，以后有新方案时通过用户干预事件重开同一 study line 或派生新计划。
- DM002、DM003 只要有 live writer 或明确 runtime owner route，归入 `live / watch / runtime` 或 `queued / repair / runtime`。

## Owner Route

每个可执行动作必须绑定 owner route：

- `truth_epoch`
- `source_fingerprint`
- `current_owner`
- `next_owner`
- `allowed_actions`
- `idempotency_key`
- `source_refs`

dispatch executor 只能执行 route 允许的动作。宏观状态为 `parked` 且原因是 `external_info`、`stop_loss`、`user_stop` 时，stale runtime recovery、platform repair 和 external supervisor escalation 必须让位给 controller stop / human gate truth。

## 复扫规则

一次 scan 的 apply 结果必须在同一轮 projection 里生效：已应用的 platform repair 不再残留为待处理队列；若修复后下一 owner 是 AI reviewer、publication gate 或用户信息补齐，返回面必须暴露这个 owner。下一轮 scan 只能基于同一 `source_fingerprint` 和 owner receipt 判断是否重复执行，不能跨 run epoch 或旧 gate 指纹污染新状态。

## 工程依据

该合同采用 CQRS/read model、durable workflow replay、idempotent command receipt 和 trace/context propagation 的工程原则。MAS 内部落点是文件 authority + reducer + owner route + SQLite sidecar index；外部名词不作为新的 runtime 依赖。
