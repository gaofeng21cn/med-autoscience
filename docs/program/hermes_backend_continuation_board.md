# Hermes Backend Continuation Board

这份文档把 `P2 controlled cutover -> physical monorepo migration` 中，当前仍可在 repo 内诚实继续推进的 runtime / gateway / architecture 主线冻结下来。

它明确声明：

- 旧 `Codex-default host-agent runtime` 不再是长期产品方向，只保留为迁移期对照面与 regression oracle
- 当前主线只推进 `MedAutoScience gateway -> Hermes outer runtime substrate -> MedDeepScientist controlled research backend`
- display / paper-facing asset packaging 独立线明确排除，不得混入本线

它不是：

- external `Hermes` runtime repo / workspace / daemon truth 已清除的声明
- `behavior_equivalence_gate` 已放行的声明
- physical monorepo migration 已开始的声明
- `MedDeepScientist` 已完全退场的声明

## 1. 当前子线要解决什么

当前 Hermes continuation 只解决四件事：

1. 让 `Hermes` 成为 repo-tracked 默认 outer runtime substrate owner
2. 让 controller / outer-loop / transport / durable surface 真正只认 backend-generic contract
3. 让 `MedDeepScientist` 退回 controlled research backend，而不是 hidden authority truth
4. 把 `MedDeepScientist` 解构地图写成可继续实现、可验证的 repo-tracked artifact

当前 repo-side 已落到的 continuation 子面包括：

- `study_runtime_router` / `study_runtime_transport` / workspace onboarding 已以 `managed_runtime_transport` 和 `Hermes-backed managed runtime` 作为主线口径
- `figure_loop_guard` / `medical_publication_surface` 的 runtime stop seam 已收口到通用 managed runtime transport authority
- `med_deepscientist_transport` 仅继续保留兼容别名，不再作为新的 authority 命名基线

## 2. 当前 repo-side 允许打开的范围

当前允许在 repo 内打开的 write-set 只包括：

1. `runtime backend interface` / `runtime_backend` registry 与 fail-closed contract 校验
2. `Hermes` adapter / default outer substrate wiring
3. `runtime_binding.yaml`、`study_runtime_status`、`runtime_watch` 对 substrate / research-backend metadata 的 durable-surface freeze
4. `MedDeepScientist` deconstruction map、docs / tests / preflight 的同步收口

## 3. Promotion invariants

这条 continuation board 必须始终保持下面这些不变量：

1. formal-entry matrix 不变：
   - default formal entry = `CLI`
   - supported protocol layer = `MCP`
   - internal controller surface = `controller`
2. repo-tracked 产品主线继续按 `Auto-only` 理解
3. 当前默认 outer runtime substrate owner 固定为：
   - `runtime_backend_id = hermes`
   - `runtime_engine_id = hermes`
4. 当前 controlled research backend 固定为：
   - `research_backend_id = med_deepscientist`
   - `research_engine_id = med-deepscientist`
5. `program_id / study_id / quest_id / active_run_id` 不得混写
6. study-owned artifact 与 quest-owned artifact 不得混写
7. 不允许 hidden fallback chain、silent downgrade、synthetic truth rewrite
8. display / paper-facing asset packaging 独立线不得混入本线

## 4. 明确排除范围（Excluded scope）

下面这些事情当前继续明确排除：

1. external `Hermes` runtime repo / workspace / daemon truth 写入
2. `behavior_equivalence_gate` 真实放行
3. external workspace contract widening
4. cross-repo write
5. physical monorepo migration
6. 把 `MedDeepScientist` 直接写成已经完全退场
7. display / paper-facing asset packaging 独立线

## 5. 当前 repo-side 验证面

当前 continuation 至少要有下面这些 repo-native proof surface：

- `tests/test_runtime_backend.py`
- `tests/test_runtime_transport_hermes.py`
- `tests/test_runtime_protocol_layout.py`
- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_study_runtime_router.py`
- `tests/test_runtime_contract_docs.py`
- `tests/test_dev_preflight_contract.py`

如果当前改动同时触及 integration-harness wording，还要继续补跑：

- `tests/test_integration_harness_activation_package.py`

## 6. Promotion 口径

只有当下面条件同时满足时，才允许把这条 continuation 的 repo-side 子目标表述为已完成：

1. `Hermes` default outer substrate wiring 已通过 fresh verification
2. `runtime_binding.yaml` 与相关 status / watch surface 已写出 substrate / research-backend 分层语义
3. `MedDeepScientist` deconstruction map 已 repo-tracked，且能对应代码与验证面
4. repo-tracked docs 已明确写清目标、边界、验证、promotion invariants、excluded scope、真实 blocker
5. external runtime / workspace / human gate 仍被诚实保留为 blocker

## 7. 真实 blocker

即使这条 continuation 在 repo 内完成，下面这些 blocker 依然存在：

1. external `Hermes` runtime 的真实 daemon / workspace / repo 证据仍不在当前仓内
2. `MedDeepScientist` controlled fork 与 `behavior_equivalence_gate` 仍未放行
3. external workspace / paper truth gap / `waiting_for_user` 仍不由当前仓单独清除
4. physical migration 仍然必须等待 external runtime / workspace / human gate 真实清除
