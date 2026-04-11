# Runtime Backend Interface Contract

## 1. 目标

冻结 `MedAutoScience -> managed runtime backend` 的单一 contract，使 `MedAutoScience` 只依赖 `runtime backend interface` contract，而不再把 `med-deepscientist` 当作内建实现真相。

当前默认 outer runtime substrate owner 是：

- `runtime_backend_id = hermes`
- `runtime_engine_id = hermes`

当前 controlled research backend 是：

- `research_backend_id = med_deepscientist`
- `research_engine_id = med-deepscientist`

旧 `Codex-default host-agent runtime` 不再是长期产品方向；direct `med_deepscientist` backend lane 只保留为兼容 / regression oracle。

## 2. Backend 选择规则

`MedAutoScience` 解析 study execution 时，按下面顺序选择 backend：

1. `execution.runtime_backend_id`
2. `execution.runtime_backend`
3. 对 `auto_entry == on_managed_research_intent` 的历史 managed execution：
   - 若 profile 固定 `managed_runtime_backend_id = hermes`
   - 且 legacy `execution.engine` 指向 `med_deepscientist` 或为空
   - controller 先把 execution 归一化到 `Hermes` outer substrate
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
- `med_deepscientist_runtime_root`

这意味着 controller / outer-loop 不应再依赖 `med_deepscientist_runtime_root` 这一实现名义字段来推导 authority truth。

## 6. 当前仓库边界

这份 contract 完成的是：

- controller 与 transport 之间的 backend abstraction freeze
- `Hermes` 作为默认 outer substrate owner 的 repo-side 闭环
- `MedDeepScientist` 作为 controlled research backend 的显式 durable metadata

这份 contract 还没有完成的是：

- external `Hermes` runtime truth / workspace truth
- `MedDeepScientist` backend 的完全退场
- workspace physical layout 的完全去 `med-deepscientist` 化
- physical monorepo migration
