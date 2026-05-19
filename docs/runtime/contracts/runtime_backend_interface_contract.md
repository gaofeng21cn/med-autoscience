# Runtime Backend Interface Contract

## 1. 目标

冻结 `MedAutoScience -> OPL generic runtime + MAS domain runtime adapter` 的单一 contract，使 `MedAutoScience` 只依赖 runtime backend interface contract 暴露 domain owner receipt / typed blocker / diagnostic adapter，而不再把 `med-deepscientist` 或 MAS 私有 runtime core 当作通用运行框架真相。

当前默认 generic runtime owner 是：

- `runtime_owner = one-person-lab`
- `runtime_substrate = opl_provider_backed_stage_runtime`
- `runtime_backend_id = mas_runtime_core`
- `runtime_engine_id = mas-runtime-core`
- `runtime_backend_role = mas_domain_owner_receipt_adapter`
- `runtime_backend_is_generic_owner = false`

当前 research backend identity 是：

- `research_backend_id = mas_runtime_core`
- `research_engine_id = mas-runtime-core`

旧 `Codex-default host-agent runtime` 继续作为 executor 配置来源；direct `med_deepscientist` backend lane 只保留为 frozen source archive / historical fixture / explicit archive import reference，不作为 runnable dependency。

默认 MAS operation 的外部 MDS 依赖必须由 machine-readable contract 明确表达：

- `external_mds_required_for_default_operation = false`
- external MDS 只服务 source provenance、historical fixture 和 explicit archive import reference
- profile JSON 顶层不得重新暴露 `med_deepscientist_*` 字段；历史引用面只能位于 `source_provenance`、`historical_fixture_ref` 与 `explicit_archive_import_ref`

## 2. Backend 选择规则

`MedAutoScience` 解析 study execution 时，按下面顺序选择 backend：

1. `execution.runtime_backend_id`
2. `execution.runtime_backend`
3. 对 `auto_entry == on_managed_research_intent` 的历史 managed execution：
   - 若 legacy `execution.engine` 指向 `med_deepscientist` 或为空
   - controller 先把 execution 归一化到 `mas_runtime_core`
4. 其余场景再使用 `execution.engine` 映射到已注册 backend

fail-closed 规则：

- 如果 `execution.runtime_backend_id` / `execution.runtime_backend` 被显式设置，但仓内没有注册对应 backend，`study_runtime_status` 必须返回阻断，而不是静默降级成 lightweight
- 如果 execution 里没有显式 backend，且 `execution.engine` 也映射不到任何已注册 backend，才可判定为非 managed runtime execution

## 3. Backend Contract Surface

managed runtime backend 必须显式暴露：

- `BACKEND_ID`
- `ENGINE_ID`

并实现下列 controller-facing 操作：

- `resolve_daemon_url(...)`
- `create_quest(...)`
- `resume_quest(...)`
- `relaunch_stopped_quest(...)`
- `pause_quest(...)`
- `stop_quest(...)`
- `get_quest_session(...)`
- `inspect_quest_live_runtime(...)`
- `inspect_quest_live_execution(...)`
- `update_quest_startup_context(...)`
- `artifact_complete_quest(...)`
- `artifact_interact(...)`

可选但当前主线已使用的扩展 metadata：

- `CONTROLLED_RESEARCH_BACKEND_ID`
- `CONTROLLED_RESEARCH_ENGINE_ID`

`MedAutoScience` controller 只能通过这层 contract 调 backend，不得再直接依赖 backend-specific module name 作为控制逻辑判断条件。

## 3.1 MAS runtime adapter implements only domain receipt/diagnostic role

`mas_runtime_core` 不是把 MDS daemon 嵌入 MAS，也不是启动外部 `med-deepscientist` daemon。它当前只作为 MAS domain runtime adapter / owner receipt surface / standalone diagnostic 实现 controller-facing operation shape；generic scheduler、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine 和 workbench owner 归 OPL provider-backed stage runtime。

- `resolve_daemon_url` 返回本地 runtime root URI，只作为 backend identity / locator。
- `create_quest` 在 `runtime/quests/<quest_id>` 下创建普通 quest directory、`quest.yaml` 和 create payload。
- `resume_quest` / `relaunch_stopped_quest` / `pause_quest` / `stop_quest` 写入 `.ds/runtime_state.json` 和 `artifacts/runtime/mas_runtime_events.jsonl`，形成可回放状态与事件。
- `resume_quest` 不得释放 stopped/failed terminal state；只有 controller 已决策为 stopped relaunch 时，才能走 `relaunch_stopped_quest`。
- `get_quest_session`、`inspect_quest_live_runtime`、`inspect_quest_live_execution` 读取 MAS local state、runtime files 和 event refs，返回与 controller contract 对齐的 session/liveness projection。
- `chat_quest`、`artifact_complete_quest`、`artifact_interact` 只记录 MAS runtime event / queue / artifact handoff，不调用 MDS HTTP API。

因此，旧 MDS daemon 的长期价值被拆成两部分：controller-facing operation shape 由 `ManagedRuntimeBackend` contract 保留，generic runtime owner 归 OPL，MAS adapter 只签收 domain receipt、typed blocker、event refs 与 diagnostic projection；MDS 只保留 frozen source archive、historical fixture、explicit archive import / provenance reference 和 read-only backend audit，不再保留 runnable MAS transport。

## 3.2 Registry validation

backend registry 当前必须 fail-closed 校验：

1. `BACKEND_ID` 非空
2. `ENGINE_ID` 非空
3. 上述 controller-facing callable 全部存在
4. callable 参数表与 contract surface 对齐，不允许缺字段、意外新增必填字段，或把 required 参数改成别的名字

这条规则的意义是：

- 不让 backend abstraction 停留在“只有两个 ID 字段”的假抽象
- 在 `Hermes` outer substrate owner 已切入后，继续把 controller callsite 所依赖的最小可执行 contract 冻结出来

## 4. Managed Runtime 判定

managed runtime execution 的正式条件是：

- backend 已通过 contract 成功解析
- `execution.auto_entry == on_managed_research_intent`

因此，下面这些语义不再允许直接绑死到 `engine == med-deepscientist`：

- supervisor tick required
- runtime event required
- autonomous runtime notice required
- execution owner guard required
- pending interaction / session probing required
- outer-loop managed runtime input contract required

## 5. Runtime Binding Durable Surface

`runtime_binding.yaml` 现在必须同时写出：

- `runtime_backend_id`
- `runtime_backend`
- `runtime_engine_id`
- `research_backend_id`
- `research_backend`
- `research_engine_id`
- `runtime_home`
- `runtime_quests_root`

当前保留的兼容字段：

- `engine`
- `runtime_root`
- `historical_fixture_ref.runtime_root`

这意味着 controller / outer-loop 不应再依赖 `med_deepscientist_runtime_root` 这一实现名义字段来推导 authority truth。

## 6. 当前仓库边界

这份 contract 完成的是：

- controller 与 OPL generic runtime / MAS domain adapter 之间的 backend abstraction freeze
- OPL provider-backed stage runtime 作为默认 generic runtime owner/substrate 的 repo-side contract，`mas_runtime_core` 只作为 domain adapter / owner receipt / diagnostic surface
- `MedDeepScientist` 作为 frozen archive / historical fixture / explicit archive import reference 的显式边界
- default MAS operation 不依赖 external `med-deepscientist` repo / runtime root
- external MDS 只作为显式 backend audit、historical fixture / explicit archive import reference、historical fixture 和 source provenance target
- optional hosted runtime / workspace truth packaging 已由 MAS Progress Portal 承接：`artifacts/runtime/progress_portal/hosted_package.json` 只打包 MAS-owned read-model payload、HTML 入口、source refs、conditions 和 OPL handoff refs，不消费 MDS WebUI 或 external MDS runtime root

这份 contract 还没有完成的是：

- future upstream source intake review；external MDS repo 只能作为 source archive / historical fixture 保留在 default operation 之外
- GitHub default-branch contributor surface 的 post-push 检查；本地 no-history guard 已阻止上游 history / co-author footprint 进入 MAS commits
