# Delivery Plane Contract Map

这份文档把当前 `delivery / publication plane` 与相邻 `runtime / eval / outer-loop` artifact 的正式边界收口成一个 repo-tracked canonical bridge。

它不替代：

- `./study_runtime_control_surface.md`
- `./study_runtime_orchestration.md`
- `./outer_loop_wakeup_and_decision_loop.md`

而是回答两个在 P2 必须冻结的问题：

1. 哪些 surface 是 **controller-authorized delivery surface**
2. `runtime_escalation_record -> publication_eval -> study_decision_record -> delivery/publication guards` 这条 artifact map 到底如何闭环，哪些对象只是 shell / projection

## 1. 当前冻结结论

当前 P2 只冻结 delivery/publication plane 与 artifact boundary；P1 formal control semantics 继续保持：

- `pause_runtime = recoverable`
- `stop_runtime = terminal stop`
- `stop_after_current_step = unsupported / fail-closed`
- `rerun = unsupported executable action`
- `requires_human_confirmation = dispatch gate`

### 1.1 不新增 delivery authority root

当前 delivery plane 不新增新的 authority root。

上游 authority 仍然来自：

1. `study_charter`
2. `charter_parameterized_input.delivery`
3. controller 编译出的 delivery contract family（submission target / reporting contract / shortlist 等）

### 1.2 当前 controller-authorized delivery surface

当前允许被 controller 当作正式 delivery source 的 surface 只有：

- `study_root/paper/`
- `study_root/paper/submission_minimal/`
- `study_root/paper/journal_submissions/<publication_profile>/`
- 上述 surface 上的 `paper_bundle_manifest.json`、`submission_manifest.json`、`compile_report.json`

这些 surface 可以被：

- `study_delivery_sync`
- `publication_gate`
- `medical_publication_surface`
- delivery/publication plane 的其他 controller

稳定消费，但它们也只是 **controller-authorized delivery source**，不是新的 study authority root。

### 1.3 当前只允许作为 projection / shell / consumer surface 的对象

以下对象当前只能是 projection / shell / guard / report，不得被反向抬升成 authority root：

- `study_root/manuscript/`
- `study_root/artifacts/final/`
- `study_root/manuscript/submission_package/`
- `study_root/manuscript/submission_package.zip`
- `study_root/manuscript/journal_package_mirrors/<publication_profile>/`
- `quest_root/artifacts/reports/publishability_gate/*.json`
- `quest_root/artifacts/reports/runtime_watch/*.json`
- `study_root/artifacts/runtime/last_launch_report.json`

## 2. Artifact map

| 对象 | owner / plane | 稳定 surface | 允许的正式用途 | 明确不允许 |
| --- | --- | --- | --- | --- |
| `launch_report` | runtime orchestration helper | `study_root/artifacts/runtime/last_launch_report.json` | 回显最近一次 runtime dispatch / decision / daemon result | 充当 study authority、delivery truth root |
| `runtime_escalation_record` | runtime-owned event artifact | `quest_root/artifacts/reports/escalation/runtime_escalation_record.json` | 表达 runtime 已超出本地自治 envelope，并通过 `summary_ref` / `runtime_context_refs` 指向 runtime context | 直接替代 publication verdict 或 study decision |
| `publication_eval` | eval-owned verdict artifact | `study_root/artifacts/publication_eval/latest.json` | 表达 publishability verdict / gaps / recommended actions；读取 `runtime_context_refs` 与 `delivery_context_refs` | 从 runtime path 或 publication shell path 读取“伪 latest” |
| `study_decision_record` | controller-owned outer-loop decision artifact | `study_root/artifacts/controller_decisions/<timestamp>_<decision_id>.json` + `latest.json` | 把 `runtime_escalation_ref` 与 `publication_eval_ref` 收口成 next controller action | 绕过 eval 或 human gate 直接 dispatch 未冻结动作 |
| `study_delivery_sync` | controller-owned delivery materializer | `study_root/manuscript/delivery_manifest.json` 与同步出的 `manuscript/`、`artifacts/final/` | 把 controller-authorized `paper/` package 投影成 human-facing handoff surface | 把 `manuscript/` / zip / mirror 反向当成 authority root |
| `publication_gate` | controller-owned delivery guard | `quest_root/artifacts/reports/publishability_gate/*.json` | 检查 `paper/`、`paper_bundle_manifest`、`submission_minimal`、medical publication surface 是否允许继续写 | 从 unmanaged submission surface 或 shell mirror 推回 controller truth |
| `runtime_watch` | controller-owned poll/report shell | `quest_root/artifacts/reports/runtime_watch/*.json` + `state.json` | 周期扫描 controller reports，并汇总 managed study actions | 充当新的 authority root 或直接重写 delivery truth |

## 3. 当前闭环的正式读写顺序

1. `study_runtime_execution` / `study_runtime_protocol` 落 `launch_report`
2. runtime 需要升级时写 `runtime_escalation_record`
3. eval plane 在 `study_root/artifacts/publication_eval/latest.json` 写 `publication_eval`
4. `study_outer_loop_tick(...)` 读取：
   - `runtime_escalation_ref`
   - eval-owned `publication_eval latest`
5. outer-loop durable 写 `study_decision_record`
6. downstream controller 只允许在冻结动作面内继续：
   - `ensure_study_runtime`
   - `pause_runtime`
   - `stop_runtime`
7. delivery/publication plane 继续消费 controller-authorized delivery source：
   - `publication_gate` 看 `paper/` / `paper_bundle_manifest` / `submission_minimal`
   - `study_delivery_sync` 把 `paper/` package materialize 到 `manuscript/`
8. `runtime_watch` 作为 poll shell 聚合 controller reports 与 managed study actions，但不升格成 authority root；当前它仍是 **poll/report shell**，不是已经直接内建 `study_outer_loop_tick(...)` dispatch 的 owner
   - 在同一扫描内，`runtime_watch` 必须先评估 `medical_publication_surface`，再评估 `publication_gate`；不能让同一扫描里的 gate verdict 忽略刚暴露出的 publication-surface blocker

## 4. Fail-closed rules

当前必须继续 fail-closed：

1. `publication_eval` 只能读取 eval-owned `study_root/artifacts/publication_eval/latest.json`
2. `study_outer_loop_tick(...)` 不接受缺失或不匹配的 `runtime_escalation_ref`
3. `study_delivery_sync` 不得把 `manuscript/`、zip、journal mirror 当作 authority root
4. `publication_gate` 发现 unmanaged submission surface 时必须阻塞
5. `runtime_watch` 只记录/聚合 controller report，不重新定义 controller truth

## 5. 与现有文档的桥接

- `./study_runtime_control_surface.md`
  - 裁定 `pause / stop / rerun / requires_human_confirmation` 语义
- `./study_runtime_orchestration.md`
  - 裁定 runtime orchestration、transport、`launch_report_path`
- `./outer_loop_wakeup_and_decision_loop.md`
  - 裁定 `runtime_escalation_record -> publication_eval -> study_decision_record` durable outer loop
- `./delivery_plane_contract_map.md`（本文）
  - 裁定 delivery/publication plane 与上述 artifact 的 owner / surface / non-authority 边界

若发生冲突：

1. `study_runtime_control_surface.md` 先裁定 formal control semantics
2. `study_runtime_orchestration.md` 裁定 runtime/transport artifact persistence
3. `outer_loop_wakeup_and_decision_loop.md` 裁定 outer-loop durable decision loop
4. 本文裁定 delivery/publication plane 的 surface role 与 artifact map

## 6. 对应 planning truth

与本文相关的 planning 讨论已经吸收到 repo-tracked canonical docs；当前应直接以这些运行面与程序文档为准，而不是再回到任何机器私有 scratch 或历史 planning note 查默认入口。

本文的作用是把这些 planning truth 固定到 repo-tracked canonical docs 中，避免控制语义重新散回本地未跟踪面。
