# External Runtime Dependency Gate

这份文档把当前正式停车终态

- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`

收紧成一个 **repo-tracked、可审计、可验证** 的 blocker package。

它回答三件事：

1. 当前为什么仍然不能声称进入更大的 `end-to-end harness / cutover readiness`
2. 哪些问题已经是 `med-autoscience` repo 内部可验证的 canonical surface
3. 哪些问题仍然必须依赖 external runtime / external workspace / human interaction 才能继续

它不授权：

- external `Hermes` runtime truth 写入
- `med-deepscientist` 写入
- cross-repo write
- 提前宣称 cutover 已完成
- 把外部 workspace paper truth gap 伪装成 repo-side runtime contract 缺陷

display / paper-facing asset packaging 独立线也不属于本文的 blocker 处理范围。

## 1. 当前 blocker 的正式含义

截至当前 repo-side mainline，仓内已经完成：

- authority / outer-loop / delivery plane convergence
- real-study relaunch and verify
- integration harness activation baseline
- `Hermes-backed outer runtime` 的 repo-side 默认 owner 切换
- `MedDeepScientist` deconstruction map 的 repo-tracked 冻结

因此当前的 `blocked` 不是说 repo-side baseline 仍未建立，而是说：

- repo 内已经把 `MedAutoScience gateway -> Hermes outer substrate -> controlled research backend` 的最小正式链路冻结完成
- 继续前进到更大的 `runtime cutover gate` 或 `end-to-end harness`，还需要 external evidence

## 2. Repo-side canonical evidence surface

下面这些 surface 属于当前 repo-side 已冻结的 blocker audit 面：

### 2.1 文档 truth

在 external gate 未清除前，repo-side 手工测试与稳定化的执行清单统一收口到：

- `./manual_runtime_stabilization_checklist.md`
- `../runtime/runtime_boundary.md`
- `../runtime/runtime_handle_and_durable_surface_contract.md`
- `../runtime/runtime_backend_interface_contract.md`
- `../runtime/agent_runtime_interface.md`
- `./merge_and_cutover_gates.md`
- `./upstream_intake.md`
- `./med_deepscientist_deconstruction_map.md`
- 本文 `./external_runtime_dependency_gate.md`

### 2.2 可执行检查 surface

- `doctor`
- `med-deepscientist-upgrade-check --refresh`
- `inspect_behavior_equivalence_gate(...)`
- `inspect_workspace_contracts(...)`
- `inspect_med_deepscientist_repo_manifest(...)`

对应实现固定在：

- `src/med_autoscience/doctor.py`
- `src/med_autoscience/workspace_contracts.py`
- `src/med_autoscience/med_deepscientist_repo_manifest.py`
- `src/med_autoscience/controllers/med_deepscientist_upgrade_check.py`

### 2.3 Repo-native regression surface

- `tests/test_med_deepscientist_repo_manifest.py`
- `tests/test_workspace_contracts.py`
- `tests/test_deepscientist_upgrade_check.py`
- `tests/test_external_runtime_dependency_gate.py`

这些测试负责证明：

- controlled fork 身份可被稳定识别
- `MEDICAL_FORK_MANIFEST.json` 的关键字段可被稳定消费
- `behavior_equivalence_gate.yaml` 结构、`phase_25_ready` 与 `critical_overrides` 会 fail-closed
- `doctor` 与 `med-deepscientist-upgrade-check` 会把 gate 结果收口成结构化 blocking verdict

## 3. 当前仍然必须由 external surface 提供的证据

当前 remaining blocker 必须拆成四类，而且都不是当前 repo 单独写文档就能消掉的：

### 3.1 external `Hermes` runtime 真证据

repo-side 能检查的是：

- `Hermes` 是否已成为默认 outer substrate owner
- controller / transport / durable surface 是否只认 backend-generic contract
- `runtime_binding.yaml` 是否写出 substrate / research-backend 双层 metadata

但 repo-side 不能凭空生成：

- external `Hermes` runtime repo / workspace / daemon 的真实部署证据
- external `Hermes` runtime root / launcher / layout 真相
- external `Hermes` runtime 与当前 repo-side contract 的真实端到端一致性证明

### 3.2 controlled fork / upstream tracking 真实证据

repo-side 能检查的是：

- profile 是否配置了 `med_deepscientist_repo_root`
- repo 根目录是否存在 `MEDICAL_FORK_MANIFEST.json`
- manifest 是否可解析
- comparison ref 是否能指向受控 fork 的 `upstream/main`

但 repo-side 不能凭空生成：

- external `med-deepscientist` fork 的真实 manifest 内容
- external fork 的 remote / branch / commit 历史
- 真实 intake 是否已经在 fork 中完成

### 3.3 `behavior_equivalence_gate.yaml` 放行

repo-side 能检查的是：

- `ops/med-deepscientist/behavior_equivalence_gate.yaml` 是否存在
- `schema_version` 是否存在
- `phase_25_ready` 是否为布尔值且为 `true`
- `critical_overrides` 是否为结构化清单

但 repo-side 不能替 workspace 自动完成：

- 把仍在 site-packages / local patch 的行为补丁迁出
- 把 `critical_overrides` 从待处理状态改为已清除
- 把 `phase_25_ready` 从 `false` 改成 `true`

### 3.4 真实 workspace contract / paper truth gap / human gate

repo-side 可以规定必须做的受控热身命令与观察项：

```bash
uv run --python 3.14 python -m med_autoscience.cli doctor --profile <profile>
uv run --python 3.14 python -m med_autoscience.cli med-deepscientist-upgrade-check --profile <profile> --refresh
uv run --python 3.14 python -m med_autoscience.cli ensure-study-runtime --profile <profile> --study-id <study_id>
uv run --python 3.14 python -m med_autoscience.cli publication-gate --quest-root <quest_root> --apply
uv run --python 3.14 python -m med_autoscience.cli watch --quest-root <quest_root> --apply
```

但 repo-side 不能替外部 workspace / study 自动清除：

- 真实 workspace 路径与 launcher 配置缺口
- external workspace 上的 overlay / bootstrap 整体修复
- `waiting_for_user`
- quest paper `draft.md` 的 `Methods` 结构缺口
- `endpoint_provenance_note.md` 缺失
- 任何 external workspace paper truth gap

## 4. 当前正式判定规则

只有当下面两件事同时成立时，才允许把 blocker 继续表述为 repo-side 未完成：

1. repo 内缺少上述 canonical doc / controller / test / preflight surface
2. 或这些 repo-side surface 本身验证不通过

如果 repo-side surface 已完整且验证通过，而问题仍停在：

- external `Hermes` runtime 真证据缺失
- `MEDICAL_FORK_MANIFEST.json` 真实内容
- `behavior_equivalence_gate.yaml` 未放行
- external workspace contract 未绿
- 热身 study 仍卡在 `waiting_for_user` 或 paper truth gap

那么正式终态就必须继续保持：

- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`

## 5. 与其他 canonical docs 的关系

- `../runtime/runtime_boundary.md`
  - 裁定 `MedAutoScience` / `Hermes` / `MedDeepScientist` 的 authority 边界
- `../runtime/runtime_handle_and_durable_surface_contract.md`
  - 裁定 handle / durable surface / gate semantics
- `./merge_and_cutover_gates.md`
  - 裁定 merge gate 与 runtime cutover gate 的区别
- `../runtime/agent_runtime_interface.md`
  - 提供 agent / operator 应走的正式命令入口
- `./upstream_intake.md`
  - 裁定 controlled fork intake 与 comparison ref 语义
- `./med_deepscientist_deconstruction_map.md`
  - 裁定哪些能力仍在 backend、哪些应迁往 substrate
- `./external_runtime_dependency_gate.md`（本文）
  - 把当前 external blocker 精确收口成 repo-side canonical audit package

## 6. 当前结论

当前 repo-side 的正确表述是：

- runtime mainline 已把 external blocker 相关的 doc / gate / audit / doctor / verification surface 收紧为 canonical package
- repo 内不再需要伪造新的 same-repo tranche 来解释当前阻塞
- 当前 Hermes continuation / activation / deconstruction map 的完成，不替代 external blocker 本身
- 真正继续前进仍然依赖 external runtime、external workspace 与 human-required interaction

因此当前正式停车终态继续是：

- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`
