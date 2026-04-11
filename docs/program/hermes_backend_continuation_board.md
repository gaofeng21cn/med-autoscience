# Hermes Backend Continuation Board

这份文档把 `P2 controlled cutover -> physical monorepo migration` 中，当前 **仍可在 repo 内诚实继续推进** 的 Hermes 相关子线冻结下来。

它不是：

- external runtime gate 已清除的声明
- `runtime cutover` 已放行的声明
- `Hermes` 已成为当前默认 runtime owner 的声明
- workspace physical layout 已去 `med-deepscientist` 化的声明

当前 frozen status 是：

- `integration harness activation baseline` 已 absorbed
- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB` 仍然成立
- 但 repo-side 仍允许继续推进一个更窄的 consumer-only continuation：
  - `runtime backend interface` 继续收紧
  - `Hermes` backend 受控接入准备

## 1. 当前子线要解决什么

当前 Hermes continuation 只解决两件事：

1. 让 controller / outer-loop / transport / durable surface 真正只认 `runtime backend interface` contract
2. 让 `Hermes` 以非默认 backend 的身份进入受控接入准备，而不是继续把 `med-deepscientist` 模块名当作 authority truth

## 2. 当前 repo-side 允许打开的范围

当前允许在 repo 内打开的 write-set 只包括：

1. `runtime_backend` registry 与 fail-closed contract 校验
2. `Hermes` backend adapter / registration / contract wiring
3. `runtime_binding.yaml` 对 backend-generic durable fields 的继续冻结
4. repo-tracked docs / tests / preflight 对上述 truth 的同步收口

## 3. Promotion invariants

这条 continuation board 必须始终保持下面这些不变量：

1. formal-entry matrix 不变：
   - default formal entry = `CLI`
   - supported protocol layer = `MCP`
   - internal controller surface = `controller`
2. repo-tracked 产品主线继续按 `Auto-only` 理解
3. 当前 default backend 继续是：
   - `runtime_backend_id = med_deepscientist`
   - `runtime_engine_id = med-deepscientist`
4. `Hermes` 只允许作为显式注册、显式选择、fail-closed 的非默认 backend
5. `program_id / study_id / quest_id / active_run_id` 不得混写
6. study-owned artifact 与 quest-owned artifact 不得混写
7. 不允许 hidden fallback chain、silent downgrade、synthetic truth rewrite

## 4. 明确排除范围（Excluded scope）

下面这些事情当前继续明确排除：

1. 把 `Hermes` 直接写成当前默认 runtime owner
2. external Hermes runtime repo / workspace / daemon truth 写入
3. `behavior_equivalence_gate` 真实放行
4. external workspace contract widening
5. cross-repo write
6. physical monorepo migration
7. display / paper-facing asset packaging 独立线

## 5. 当前 repo-side 验证面

当前 continuation 至少要有下面这些 repo-native proof surface：

- `tests/test_runtime_backend.py`
- `tests/test_runtime_transport_hermes.py`
- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_runtime_contract_docs.py`
- `tests/test_dev_preflight_contract.py`

如果当前改动同时触及 integration-harness wording，还要继续补跑：

- `tests/test_integration_harness_activation_package.py`

## 6. Promotion 口径

只有当下面条件同时满足时，才允许把这条 continuation 的 repo-side 子目标表述为已完成：

1. `Hermes` backend registry / adapter / durable-surface wiring 已通过 fresh verification
2. repo-tracked docs 已明确写清目标、边界、验证、promotion invariants、excluded scope、真实 blocker
3. 当前默认 backend 仍未被切换
4. external runtime / workspace / human gate 仍被诚实保留为 blocker

## 7. 真实 blocker

即使这条 continuation 在 repo 内完成，下面这些 blocker 依然存在：

1. external Hermes runtime 的真实 daemon / workspace / repo 证据仍不在当前仓内
2. `behavior_equivalence_gate` 与 controlled cutover 仍未放行
3. external workspace / paper truth gap / `waiting_for_user` 仍不由当前仓单独清除
4. physical migration 仍然必须等待 external runtime / workspace / human gate 真实清除
