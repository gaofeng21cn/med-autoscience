# 运行句柄与持久表面合同

## 文档目的

这份文档用于把 `MedAutoScience` 当前主线的 execution handle contract 与 durable surface contract 单独冻结出来，避免它们继续散落在 README、controller 文档、测试描述和本地 handoff 说明中。

它只覆盖主线 `runtime / gateway / contract` 迁移，不覆盖 display / paper-facing asset packaging 独立支线。

## 1. 当前统一前提

- 当前 repo-tracked 主线拓扑固定为：
  - `MedAutoScience` = 唯一研究入口、research gateway、study / workspace authority owner
  - `Hermes` = 默认 outer runtime substrate owner
  - `MedDeepScientist` = controlled research backend
- 旧 `Codex-default host-agent runtime` 只保留为迁移期对照面与 regression oracle，不再是长期产品方向。
- 当前 formal-entry matrix：
  - `default_formal_entry = CLI`
  - `supported_protocol_layer = MCP`
  - `internal_controller_surface = controller`
- 当前仓库产品主线继续按 `Auto-only` 理解。
- future `Human-in-the-loop`：作为 compatible sibling 或 upper-layer product，复用同一 substrate，而不是把本仓改成同仓双模。
- external `Hermes` runtime repo / workspace / daemon truth 仍未进入当前仓内；当前 repo-side 只冻结 controller-facing outer substrate contract。

## 2. Execution Handle Contract

### `program_id`

- 角色：当前 `research-foundry-medical-mainline` 的 control-plane / report-routing 指针
- 典型锚点：
  - `README*`
  - `docs/status.md`
  - `docs/program/research_foundry_medical_mainline.md`
  - `docs/program/external_runtime_dependency_gate.md`
- 边界：
  - 它服务 repo-tracked 主线识别、报告路由与 blocker 归类
  - 它不是 `study_id`
  - 它不是 `quest_id`
  - 它不是 `active_run_id`

### `study_id`

- 角色：医学研究主线中的持久聚合根身份
- 典型落点：
  - `studies/<study_id>/study.yaml`
  - `studies/<study_id>/artifacts/publication_eval/latest.json`
  - `studies/<study_id>/artifacts/controller_decisions/latest.json`
  - `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- 边界：
  - 它代表 study 对象本身
  - 它不因单次 runtime 重启而变化

### `quest_id`

- 角色：当前“上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam”绑定到 controlled research backend 后的正式 managed execution handle
- 典型落点：
  - `runtime_binding.yaml`
  - `study_runtime_status`
  - `runtime_watch`
  - `ops/med-deepscientist/runtime/quests/<quest_id>/`
- 边界：
  - 它是 study 绑定到受控 runtime 后的正式 handle
  - pause / resume / stop / startup-context sync 等 transport 都围绕它执行
  - 当前 quest-local durable state 仍落在 `MedDeepScientist` runtime root，但 authority truth 不再由 backend 品牌名隐式决定
  - 它不能被 `study_id`、`program_id` 或 `active_run_id` 取代

### `active_run_id`

- 角色：当前 live daemon run 的细粒度执行句柄
- 典型落点：
  - `runtime_liveness_audit.active_run_id`
  - `bash_session_audit` / `runtime_audit`
  - `quest.yaml` / daemon session snapshots
- 边界：
  - 只有 quest 处于 live execution 时才有意义
  - 它描述的是 quest 内部当前活跃 run，而不是上层 managed quest 身份
  - 它绝不能倒灌成 `quest_id`、`study_id` 或 `program_id`

## 3. Durable Surface Contract

当前主线至少要把以下表面视为 canonical durable surface：

- `runtime_binding.yaml`
  - substrate / backend binding 总表面
  - 必须回显：
    - `runtime_backend_id`
    - `runtime_backend`
    - `runtime_engine_id`
    - `research_backend_id`
    - `research_backend`
    - `research_engine_id`
    - `runtime_home`
    - `runtime_quests_root`
- `study_runtime_status`
  - study 侧状态总表面
  - 必须回显 `study_id`、`quest_id`、`runtime_backend_id`、`research_backend_id`、decision / reason、runtime gate 摘要
- `runtime_watch`
  - quest 侧 watch / intervention 表面
  - 当前默认仍落在 `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/runtime_watch/`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
  - study 侧 publication verdict latest surface
- `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
  - quest 侧 escalation record surface
- `studies/<study_id>/artifacts/controller_decisions/latest.json`
  - study 侧 outer-loop / controller decision latest surface
- `studies/<study_id>/artifacts/runtime/last_launch_report.json`
  - study 侧最近一次 runtime launch / reentry / sync 记录

## 4. Gate Semantics

当前主线下，gate semantics 统一按下面这条 fail-closed 链理解：

1. `runtime_binding.yaml`
   - 先冻结当前 substrate / research-backend 绑定，不允许 hidden authority rewrite
2. `study_runtime_status`
   - 再汇总 workspace contracts、startup data readiness、startup boundary、runtime reentry、completion state
3. `runtime_escalation_record`
   - 当 runtime 不能诚实继续推进时，把 quest 级升级原因落盘
4. `publication_eval/latest.json`
   - 把发表判断落在 study 自有表面，而不是挂回 runtime 临时目录
5. `controller_decisions/latest.json`
   - outer loop 基于 publication eval 与 runtime escalation 形成下一步决策
6. controller action
   - 只允许走 `ensure_study_runtime`、`pause_runtime`、`stop_runtime` 等受控 surface

这条链路里：

- `Hermes` 负责 outer substrate binding 与 backend-generic contract，不负责伪造 study judgment truth
- `MedDeepScientist` 不拥有上层 judgment truth
- study-owned artifact 与 quest-owned artifact 不能混写
- 当 runtime 不可达或 contract 不满足时，必须 fail-closed，而不是本地写旁路冒充成功
- 不允许 hidden fallback、silent downgrade、synthetic truth rewrite

## 5. Repo-Tracked Truth 与本地控制面的边界

- repo-tracked truth 负责：
  - formal-entry matrix
  - execution handle contract
  - durable surface contract
  - gate semantics
  - `Hermes -> MedDeepScientist` 当前主线拓扑
- 本地未跟踪 handoff scratch 只负责：
  - 机器私有 continuation note
  - 临时观察记录
  - 非规范化的本地协作上下文

前者不能被后者替代；后者也不能被误写成产品 runtime truth。

当前仍未被 repo 单独清除的真实 blocker 是：

- external `Hermes` runtime repo / workspace / daemon truth
- `MedDeepScientist` controlled fork 与 `behavior_equivalence_gate`
- external workspace / paper truth gap / human-required interaction
