# Historical External Runtime Dependency Gate

这份文档原本服务 MAS 吸收 MDS 过程中的 external runtime blocker。2026-05-11 之后，MAS monolith closeout 已经把默认运行、默认诊断、默认进度面和默认质量入口收回到 `med-autoscience`；因此本文降级为 **explicit executor/proof diagnostic / historical backend / explicit archive import / parity audit gate**，不再是 MAS 默认可用性的停车结论。

历史停车终态

- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`

现在只用于解释旧 cutover blocker package，不得被引用为当前 MAS 默认运行阻塞。

它回答三件事：

1. 什么时候仍然不能声称 explicit hosted executor/proof path、historical backend audit 或旧 cutover readiness 已完成
2. 哪些问题已经是 `med-autoscience` repo 内部可验证的 canonical surface
3. 哪些问题仍然必须依赖 external runtime / external workspace / human interaction 才能继续

它不授权：

- external `Hermes` runtime truth 写入
- `med-deepscientist` 写入
- cross-repo write
- 提前宣称 cutover 已完成
- 把外部 workspace paper truth gap 伪装成 repo-side runtime contract 缺陷
- 把 explicit executor/proof diagnostic 或 historical backend blocker 重新解释成 MAS 默认 runtime、默认 diagnostic 或质量依赖

display / paper-facing asset packaging 独立线也不属于本文的 blocker 处理范围。

## 1. 当前 blocker 的正式含义

截至当前 repo-side mainline，仓内已经完成：

- authority / outer-loop / delivery plane convergence
- real-study relaunch and verify
- integration harness activation baseline
- 面向上游 `Hermes-Agent` 目标的 repo-side outer-runtime seam 默认 owner 切换
- `MedDeepScientist` deconstruction map 的 repo-tracked 冻结

因此当前的 `blocked` 不是说 MAS monolith baseline 仍未建立，而是说：

- repo 内已经把 `MedAutoScience domain owner -> OPL/provider sidecar bridge -> explicit executor/proof diagnostic / historical backend audit` 的边界冻结完成
- MAS 默认运行与默认诊断已经不要求外部 MDS repo / daemon / runtime root / WebUI
- 继续前进到 OPL provider long-run soak、explicit Hermes executor/proof evidence、historical backend audit 或 archive-import parity，还需要外部证据

## 2. Repo-side canonical evidence surface

下面这些 surface 属于当前 repo-side 已冻结的 blocker audit 面：

### 2.1 文档 truth

在 external gate 未清除前，repo-side 手工测试与稳定化的执行清单统一收口到：

- `manual_runtime_stabilization_checklist.md`
- `../../runtime/contracts/runtime_boundary.md`
- `../../runtime/contracts/runtime_handle_and_durable_surface_contract.md`
- `../../runtime/contracts/runtime_backend_interface_contract.md`
- `../../runtime/contracts/agent_runtime_interface.md`
- `../repo-ops/merge_and_cutover_gates.md`
- `../../references/med-deepscientist/upstream_intake.md`
- `../../references/med-deepscientist/med_deepscientist_deconstruction_map.md`
- 本文 `external_runtime_dependency_gate.md`

### 2.2 可执行检查 surface

- `doctor`
- `hermes-runtime-check`
- `backend-audit --refresh`
- `inspect_hermes_runtime_contract(...)`
- `inspect_behavior_equivalence_gate(...)`
- `inspect_workspace_contracts(...)`
- `inspect_med_deepscientist_repo_manifest(...)`

对应实现固定在：

- `src/med_autoscience/doctor.py`
- `src/med_autoscience/hermes_runtime_contract.py`
- `src/med_autoscience/controllers/hermes_runtime_check.py`
- `src/med_autoscience/workspace_contracts.py`
- `src/med_autoscience/med_deepscientist_repo_manifest.py`
- `src/med_autoscience/controllers/backend_audit.py`

### 2.3 Repo-native regression surface

- `tests/test_med_deepscientist_repo_manifest.py`
- `tests/test_hermes_runtime_contract.py`
- `tests/test_hermes_runtime_check.py`
- `tests/test_workspace_contracts.py`
- `tests/test_deepscientist_upgrade_check.py`

这些测试负责证明：

- external `Hermes-Agent` repo / launcher / managed python / `~/.hermes` state root / gateway service 状态可被 fail-closed 识别
- controlled fork 身份可被稳定识别
- `MEDICAL_FORK_MANIFEST.json` 的关键字段可被稳定消费
- `behavior_equivalence_gate.yaml` 结构、`phase_25_ready` 与 `critical_overrides` 会 fail-closed
- `doctor`、`hermes-runtime-check` 与 `backend-audit` 会把 gate 结果收口成结构化 blocking verdict

## 3. 当前仍然必须由 external surface 提供的证据

当前 remaining blocker 必须拆成四类，而且都不是当前 repo 单独写文档就能消掉的：

### 3.1 explicit `hermes_agent` executor/proof 诊断证据

repo-side 能检查的是：

- explicit `hermes_agent` executor/proof lane 与旧 Hermes provenance 是否有结构化 readiness / diagnostic proof
- controller / transport / durable surface 是否只认 backend-generic contract
- `runtime_binding.yaml` 是否写出 substrate / research-backend 双层 metadata
- external `Hermes-Agent` repo / launcher / `.venv` / `~/.hermes/state.db` / sessions root / gateway service 是否存在结构化 proof surface
- 当前 external `Hermes-Agent` 缺的是 repo 路径、provider 配置还是 gateway service 是否可被区分

但 repo-side 不能凭空生成：

- external `Hermes` runtime repo / workspace / daemon 的真实部署证据
- external `Hermes` runtime root / launcher / layout 真相
- `~/.hermes/.env` 或 `config.yaml` 里的真实 provider / model 凭证与配置
- live gateway owner process 的真实运行
- explicit `hermes_agent` executor/proof lane 与当前 repo-side contract 的真实端到端一致性证明

### 3.2 controlled fork / upstream tracking 真实证据

repo-side 能检查的是：

- profile 是否在 `explicit_archive_import_ref` 下配置了 controlled backend repo root
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
uv run --python 3.14 python -m med_autoscience.cli doctor hermes-runtime --profile <profile>
uv run --python 3.14 python -m med_autoscience.cli doctor backend-audit --profile <profile> --refresh
uv run --python 3.14 python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>
uv run --python 3.14 python -m med_autoscience.cli study progress-projection --profile <profile> --study-id <study_id>
uv run --python 3.14 python -m med_autoscience.cli publication gate --quest-root <quest_root> --apply
uv run --python 3.14 python -m med_autoscience.cli runtime domain-health-diagnostic --quest-root <quest_root> --apply
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

那么旧 cutover 终态可以继续保持：

- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`

## 5. 与其他 canonical docs 的关系

- `../../runtime/contracts/runtime_boundary.md`
  - 裁定 `MedAutoScience` / `Hermes` / `MedDeepScientist` 的 authority 边界
- `../../runtime/contracts/runtime_handle_and_durable_surface_contract.md`
  - 裁定 handle / durable surface / gate semantics
- `../repo-ops/merge_and_cutover_gates.md`
  - 裁定 merge gate 与 runtime cutover gate 的区别
- `../../runtime/contracts/agent_runtime_interface.md`
  - 提供 agent / operator 应走的正式命令入口
- `../../references/med-deepscientist/upstream_intake.md`
  - 裁定 controlled fork intake 与 comparison ref 语义
- `manual_runtime_stabilization_checklist.md`
  - 收口 `doctor -> hermes-runtime-check -> backend-audit` 的手工验证顺序
- `../../references/med-deepscientist/med_deepscientist_deconstruction_map.md`
  - 裁定哪些能力仍在 backend、哪些应迁往 substrate
- `external_runtime_dependency_gate.md`（本文）
  - 把当前 external blocker 精确收口成 repo-side canonical audit package

## 6. 当前结论

当前 repo-side 的正确表述是：

- MAS monolith mainline 已把默认 runtime / diagnostic / progress / quality owner 收回 MAS。
- explicit `hermes_agent` executor/proof lane、旧 Hermes provenance、historical MDS backend audit、explicit archive import 和 parity oracle 仍可被检查，但它们不是 MAS 默认可用性前置条件。
- repo 内不再需要伪造新的 same-repo tranche 来解释 explicit executor/proof diagnostic 或 historical backend 阻塞。
- 当前 Hermes continuation / activation / deconstruction map 的完成，不替代 explicit executor/proof diagnostic 或 historical backend blocker 本身。
- 真正继续前进仍然依赖 OPL provider soak、explicit executor/proof evidence、external workspace truth 或 human-required interaction。

因此旧正式停车终态：

- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`

只能作为历史 cutover blocker 语义保留。当前 MAS 默认路径的状态必须从 `docs/status.md`、`progress_projection`、`domain_health_diagnostic`、`publication_eval/latest.json`、`controller_decisions/latest.json` 和 MAS owner receipts 判断。
