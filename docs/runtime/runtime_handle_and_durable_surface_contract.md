# 运行句柄与持久表面合同

## 文档目的

这份文档用于把 `Med Auto Science` 当前主线的 execution handle contract 与 durable surface contract 单独冻结出来，避免它们继续散落在 README、controller 文档、测试描述和本地 handoff 说明中。

它只覆盖论文配图以外的主线，不覆盖 display 资产化独立支线。

## 1. 当前统一前提

- 当前默认本地形态：`Codex-default host-agent runtime`
- 当前 formal-entry matrix：
  - `default_formal_entry = CLI`
  - `supported_protocol_layer = MCP`
  - `internal_controller_surface = controller`
- 当前仓库主线：`Auto-only`
- future `Human-in-the-loop`：作为 compatible sibling 或 upper-layer product，复用同一 substrate，而不是把本仓改成同仓双模
- `MedDeepScientist`：受控 execution surface，不是系统本体

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

- 角色：受控 `MedDeepScientist` managed quest 的正式运行句柄
- 典型落点：
  - `ops/med-deepscientist/runtime/quests/<quest_id>/`
  - `runtime_binding.yaml`
  - `study_runtime_status`
  - `runtime_escalation_record`
  - `runtime_watch`
- 边界：
  - 它是 study 绑定到受控 runtime 后的正式 managed execution handle
  - pause / resume / stop / startup-context sync 等 transport 都围绕它执行
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

- `study_runtime_status`
  - study 侧状态总表面
  - 必须回显 `study_id`、`quest_id`、decision / reason、runtime gate 摘要
- `runtime_watch`
  - quest 侧 watch / intervention 表面
  - 默认落在 `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/runtime_watch/`
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

1. `study_runtime_status`
   - 先汇总 workspace contracts、startup data readiness、startup boundary、runtime reentry、completion state
2. `runtime_escalation_record`
   - 当 runtime 不能诚实继续推进时，把 quest 级升级原因落盘
3. `publication_eval/latest.json`
   - 把发表判断落在 study 自有表面，而不是挂回 runtime 临时目录
4. `controller_decisions/latest.json`
   - outer loop 基于 publication eval 与 runtime escalation 形成下一步决策
5. controller action
   - 只允许走 `ensure_study_runtime`、`pause_runtime`、`stop_runtime` 等受控 surface

这条链路里：

- `MedDeepScientist` 不拥有上层 judgment truth
- study-owned artifact 与 quest-owned artifact 不能混写
- 当 runtime 不可达或 contract 不满足时，必须 fail-closed，而不是本地写旁路冒充成功

## 5. Repo-Tracked Truth 与本地控制面的边界

- repo-tracked truth 负责：
  - formal-entry matrix
  - execution handle contract
  - durable surface contract
  - gate semantics
- 本地未跟踪 handoff scratch 只负责：
  - 机器私有 continuation note
  - 临时观察记录
  - 非规范化的本地协作上下文

前者不能被后者替代；后者也不能被误写成产品 runtime truth。
