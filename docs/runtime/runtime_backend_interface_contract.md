# Runtime Backend Interface Contract

## 1. 目标

冻结 `MedAutoScience -> managed runtime backend` 的单一 contract，使 `MedAutoScience` 只依赖 `runtime backend interface` contract，而不再把 `med-deepscientist` 当作内建实现真相。

当前默认已注册 backend 仍是：

- `runtime_backend_id = med_deepscientist`
- `runtime_engine_id = med-deepscientist`

但这两个字段现在只是当前实现，不再是 `MedAutoScience` controller 层的硬编码身份。

当前 repo-side 允许继续推进的下一棒是：

- [`../program/hermes_backend_continuation_board.md`](../program/hermes_backend_continuation_board.md)
- [`../program/hermes_backend_activation_package.md`](../program/hermes_backend_activation_package.md)

它们只负责把 `Hermes` 作为非默认 backend 接入准备，不改变当前默认 backend owner。

## 2. Backend 选择规则

`MedAutoScience` 解析 study execution 时，按下面顺序选择 backend：

1. `execution.runtime_backend_id`
2. `execution.runtime_backend`
3. `execution.engine` 映射到已注册 backend

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

`MedAutoScience` controller 只能通过这层 contract 调 backend，不得再直接依赖 backend-specific module name 作为控制逻辑判断条件。

## 3.1 Registry validation

backend registry 当前必须 fail-closed 校验：

1. `BACKEND_ID` 非空
2. `ENGINE_ID` 非空
3. 上述 controller-facing callable 全部存在
4. callable 参数表与 contract surface 对齐，不允许缺字段、意外新增必填字段，或把 required 参数改成别的名字

这条规则的意义是：

- 不让 backend abstraction 停留在“只有两个 ID 字段”的假抽象
- 在 `Hermes` 接入前就把 controller callsite 所依赖的最小可执行 contract 冻结出来

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

`runtime_binding.yaml` 现在必须同时写出 backend-generic 元数据：

- `runtime_backend_id`
- `runtime_backend`
- `runtime_engine_id`
- `runtime_home`
- `runtime_quests_root`

当前保留的兼容字段：

- `engine`
- `runtime_root`
- `med_deepscientist_runtime_root`

其中：

- `runtime_home` 是 backend home / runtime state root
- `runtime_quests_root` 是 quest collection root
- `runtime_root` 当前仍与 `runtime_quests_root` 对齐

这意味着后续接入 Hermes 时，controller/outer-loop 不应再依赖 `med_deepscientist_runtime_root` 这一实现名义字段。

## 6. 当前仓库边界

这份 contract 完成的是：

- controller 与 transport 之间的 backend abstraction freeze
- managed runtime 判定从 backend contract 出发，而不是从具体 backend 名字出发
- `runtime_binding.yaml` 写出 backend-generic durable fields

这份 contract 还没有完成的是：

- Hermes external runtime truth / workspace truth
- Hermes default owner switch
- workspace physical layout 的完全去 `med-deepscientist` 化
- physical monorepo migration

所以当前正确顺序仍然是：

1. freeze backend contract
2. 完成 repo-side `Hermes` backend continuation / activation package
3. 完成 controlled cutover
4. 再决定 physical monorepo migration
