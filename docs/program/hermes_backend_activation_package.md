# Hermes Backend Activation Package

这份文档把当前 repo-side 允许打开的最小 `Hermes` activation package 固定下来。

它的目标不是伪造 external `Hermes` runtime 已就位，而是把 `Hermes` 作为默认 outer runtime substrate owner 的 repo-side 闭环压成一个可验证、可审计、可继续收口的 package。

## 1. 当前 package 的正式含义

当前 package 只声明：

1. `Hermes` 已成为 repo-tracked 默认 outer runtime substrate owner
2. `MedAutoScience` 继续是唯一研究入口与 research gateway
3. `MedDeepScientist` 现在以 controlled research backend 身份被记录与调用
4. 这条 package 不清除 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`

## 2. 当前最小实现面

当前最小实现面固定为：

1. `src/med_autoscience/runtime_backend.py`
   - `runtime backend interface` / backend registry 必须 fail-closed 校验 `BACKEND_ID`、`ENGINE_ID` 与 required callable contract
   - 默认 outer substrate owner 固定为 `hermes`
2. `src/med_autoscience/runtime_transport/hermes.py`
   - `Hermes` adapter 作为 controller-facing outer substrate 进入 registry
   - 受控 research backend metadata 明确回指 `med_deepscientist`
3. `runtime_binding.yaml`
   - 同时写出 `runtime_backend_*` 与 `research_backend_*` 元数据
4. docs / tests / preflight
   - 把 repo-side truth 收口成稳定、可重复验证的 package

## 3. 当前 activation rule

当前 `Hermes` 的 repo-side activation rule 固定为：

1. execution 显式写出下面任一项时，controller 直接解析为 `Hermes` outer substrate：
   - `runtime_backend_id = hermes`
   - `runtime_backend = hermes`
   - `engine = hermes`
2. 对历史 `engine = med-deepscientist` managed execution，如果 profile 固定 `managed_runtime_backend_id = hermes`，controller 会把它提升为：
   - `runtime_backend_id = hermes`
   - `runtime_engine_id = hermes`
   - `research_backend_id = med_deepscientist`
   - `research_engine_id = med-deepscientist`
3. 如果 execution 显式声明了未注册 backend，必须 fail-closed
4. direct `med_deepscientist` backend lane 只保留为兼容 / regression oracle，不再是主线 owner

## 4. Durable-surface freeze

当前 package 要求：

1. `runtime_binding.yaml` 始终写出：
   - `runtime_backend_id`
   - `runtime_backend`
   - `runtime_engine_id`
   - `research_backend_id`
   - `research_backend`
   - `research_engine_id`
   - `runtime_home`
   - `runtime_quests_root`
2. 当前兼容字段继续保留：
   - `engine`
   - `runtime_root`
   - `med_deepscientist_runtime_root`
3. controller / outer-loop 必须优先消费 backend-generic fields，而不是继续把兼容字段名当 authority truth

## 5. 当前 package 明确不打开的面

下面这些面当前继续关闭：

1. external `Hermes` repo / runtime root / daemon layout 真相写入
2. behavior equivalence claim
3. cross-repo write
4. external workspace writer widening
5. physical monorepo migration
6. display / paper-facing asset packaging 独立线

## 6. 当前验证面

当前 package 的最小 proof surface 固定为：

- `tests/test_runtime_backend.py`
- `tests/test_runtime_transport_hermes.py`
- `tests/test_runtime_protocol_layout.py`
- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_study_runtime_router.py`
- `tests/test_runtime_contract_docs.py`
- `tests/test_dev_preflight_contract.py`

## 7. 与 external gate 的关系

当前 `Hermes` activation package 与 external blocker 的关系必须按下面这条口径理解：

1. 这条 package 允许 repo-side 把默认 outer substrate owner 切到 `Hermes`
2. 它不替代 `external_runtime_dependency_gate.md`
3. 它不授权把 `runtime cutover`、`end-to-end harness`、physical migration 写成既成事实
