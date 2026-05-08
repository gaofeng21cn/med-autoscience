# Runtime Backend Interface Contract

## 1. 目标

冻结 `MedAutoScience -> managed runtime backend` 的单一 contract，使 `MedAutoScience` 只依赖 `runtime backend interface` contract，而不再把 `med-deepscientist` 当作内建实现真相。

当前默认 MAS runtime owner 是：

- `runtime_owner = mas_runtime_os`
- `runtime_substrate = mas_runtime_core`
- `runtime_backend_id = mas_runtime_core`
- `runtime_engine_id = mas-runtime-core`

当前 controlled research backend 是：

- `research_backend_id = mas_runtime_core`
- `research_engine_id = mas-runtime-core`

旧 `Codex-default host-agent runtime` 继续作为本机执行配置来源；direct `med_deepscientist` backend lane 只保留为 frozen source archive / historical fixture / explicit legacy diagnostic，不作为 runnable dependency。

默认 MAS operation 的外部 MDS 依赖必须由 machine-readable contract 明确表达：

- `external_mds_required_for_default_operation = false`
- external MDS 只服务 frozen source provenance、historical fixture 和显式 legacy restore/import/backend-audit diagnostic
- profile JSON 顶层不得重新暴露 `med_deepscientist_*` 字段；legacy diagnostic 字段只能位于 `legacy_diagnostic.read_only`

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

## 3.1 Registry validation

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
- `legacy_diagnostic.med_deepscientist_runtime_root`

这意味着 controller / outer-loop 不应再依赖 `med_deepscientist_runtime_root` 这一实现名义字段来推导 authority truth。

## 6. 当前仓库边界

这份 contract 完成的是：

- controller 与 transport 之间的 backend abstraction freeze
- MAS Runtime OS / `mas_runtime_core` 作为默认 runtime owner/substrate 的 repo-side 闭环
- `MedDeepScientist` 作为 frozen archive / historical fixture / explicit legacy diagnostic 的显式边界
- default MAS operation 不依赖 external `med-deepscientist` repo / runtime root
- external MDS 只作为显式 backend audit、legacy restore/import diagnostic、historical fixture 和 source provenance target

这份 contract 还没有完成的是：

- optional hosted runtime / workspace truth packaging
- future upstream source intake review；external MDS repo 只能作为 source archive / historical fixture 保留在 default operation 之外
- GitHub default-branch contributor surface 的 post-push 检查；本地 no-history guard 已阻止上游 history / co-author footprint 进入 MAS commits
