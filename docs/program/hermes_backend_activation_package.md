# Hermes Backend Activation Package

这份文档把当前 repo-side 允许打开的最小 `Hermes` backend activation package 固定下来。

它的目标不是切换 current default backend，而是把 `Hermes` 接入准备压成一个 **repo-tracked、可验证、可审计** 的 package。

## 1. 当前 package 的正式含义

当前 package 只声明：

1. `Hermes` 已被纳入 `runtime backend interface` contract 的显式注册对象
2. controller / transport / durable surface 已能通过 backend-generic contract 识别 `Hermes`
3. `Hermes` 仍然不是默认 backend owner
4. 这条 package 不清除 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`

## 2. 当前最小实现面

当前最小实现面固定为：

1. `src/med_autoscience/runtime_backend.py`
   - backend registry 必须 fail-closed 校验 `BACKEND_ID`、`ENGINE_ID` 与 required callable contract
2. `src/med_autoscience/runtime_transport/hermes.py`
   - `Hermes` adapter 作为受控 onramp 进入 registry
3. `runtime_binding.yaml`
   - 继续把 `runtime_backend_id` / `runtime_backend` / `runtime_engine_id` 作为 authority metadata
4. docs / tests / preflight
   - 把 repo-side truth 收口成稳定、可重复验证的 package

## 3. 当前 activation rule

当前 `Hermes` 的 repo-side activation rule 固定为：

1. 只有当 execution 显式写出：
   - `runtime_backend_id = hermes`
   - 或 `runtime_backend = hermes`
   - 或 `engine = hermes`
   时，controller 才能把该 study 解析为 `Hermes` managed runtime backend
2. 如果 execution 显式声明了未注册 backend，必须 fail-closed
3. 如果没有显式声明 backend，当前默认仍回到 `med_deepscientist`

## 4. Durable-surface freeze

当前 package 要求：

1. `runtime_binding.yaml` 始终写出：
   - `runtime_backend_id`
   - `runtime_backend`
   - `runtime_engine_id`
   - `runtime_home`
   - `runtime_quests_root`
2. 当前兼容字段继续保留：
   - `engine`
   - `runtime_root`
   - `med_deepscientist_runtime_root`
3. 即使 backend 为 `Hermes`，controller / outer-loop 也必须优先消费 backend-generic fields，而不是继续把兼容字段名当 authority truth

## 5. 当前 package 明确不打开的面

下面这些面当前继续关闭：

1. `Hermes` default owner switch
2. `Hermes` external repo / runtime root / daemon layout 真相写入
3. behavior equivalence claim
4. cross-repo write
5. external workspace writer widening
6. physical monorepo migration

## 6. 当前验证面

当前 package 的最小 proof surface 固定为：

- `tests/test_runtime_backend.py`
- `tests/test_runtime_transport_hermes.py`
- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_runtime_contract_docs.py`
- `tests/test_dev_preflight_contract.py`

## 7. 与 external gate 的关系

当前 `Hermes` activation package 与 external blocker 的关系必须按下面这条口径理解：

1. 这条 package 允许 repo-side 继续收紧 backend contract 与 adapter wiring
2. 它不替代 `external_runtime_dependency_gate.md`
3. 它不授权把 `runtime cutover`、`end-to-end harness`、physical migration 写成既成事实
