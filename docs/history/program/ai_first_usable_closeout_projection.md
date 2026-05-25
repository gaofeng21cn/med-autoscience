# AI-first Usable Closeout Projection

Owner: `MedAutoScience`
Purpose: `program_history_record`
State: `history_provenance`
Machine boundary: 人读 program/process 历史记录。当前执行顺序、gap、runtime truth 和 owner boundary 继续归 active owner docs、核心五件套、contracts、source、runtime/controller surfaces 和 owner receipts。

本 note 是 `plan_completion_ledger` 的接力附件。它定义本轮 AI-first usable closeout 的最终可填写模板和语义边界，供后续吸收并行 lane 时逐项填入真实证据。

本 note 只证明运行闭环的 repo-level closeout 形态已经可用：计划项可以被登记、接力、验证和保留边界。它不宣称真实论文 soak 已完成，也不宣称真实论文质量改善、submission readiness 或 artifact 修复已经被证明。

## Projection 模板

| 字段 | 填写语义 |
| --- | --- |
| `plan_id` | 稳定计划 ID，建议使用日期加 lane 名。 |
| `planned_items` | 本轮可逐项判定的计划项。 |
| `landed_commits` | 已吸收 commit、分支或 `none`；外部活跃 owner 写 `external_active_owner`。 |
| `tests_run` | 实际运行的验证命令；未运行写 `none` 并说明原因。 |
| `pushed` | `yes`、`no`、`not_performed_by_request` 或 `external_active_owner`。 |
| `worktrees_cleaned` | 只记录本轮 worktree/branch；未清理写 `not_performed_by_request`。 |
| `live_surface_verified` | 真实 workspace 或 stable runtime surface 的只读验收；没有写 `none`。 |
| `skipped_with_user_acceptance` | 经用户明确接受后跳过的项目；没有写 `none`。 |
| `remaining_gaps` | 尚未闭环的问题；没有写 `none`。 |
| `handoff_receiver` | 下一接手者、外部 active owner 或 `none`。 |
| `handoff_entrypoint` | 下一次继续时读取的文档、surface、branch、PR 或命令。 |
| `out_of_scope_boundaries` | 本轮明确不触碰的 live artifact、worktree、risk 或 soak 边界。 |
| `closure_claim` | 本轮允许声明的闭环级别。 |
| `claim_boundary` | 本轮禁止外推成真实论文质量或投稿完成的边界。 |

## 本轮可填写计划项

| item_id | closeout semantics | usable evidence to fill later | claim boundary |
| --- | --- | --- | --- |
| `dispatch default materialization` | 默认 dispatch 路径已经能物化为可审阅、可接力的 repo-level evidence。 | landed commits; focused tests; read-only entry surface check. | 只证明默认物化路径可登记和复核，不证明真实论文质量改善。 |
| `operator lifecycle` | operator 的 open、handoff、close 或保留 owner 状态能进入 ledger。 | lifecycle surface tests; operator entrypoint; owner state. | 只证明生命周期状态可投影，不证明 operator 已完成真实论文 soak。 |
| `cross-study runtime integration` | cross-study runtime 集成结果可以按 study-independent 方式登记。 | integration tests; runtime projection surface; affected study list. | 只证明跨 study 投影闭环可用，不读取或修补 DM002 live artifact。 |
| `quality learning ops report` | quality learning 的 ops 报告可作为观察性证据进入 closeout。 | report path; queue state; tests for required fields. | 只证明 learning ops 可报告，不宣称质量学习已经改善真实论文。 |
| `external lane safety gate` | 外部活跃 lane、risk 线和上游 review owner 能被保留并阻止误清理。 | owner list; preserved worktree or branch state; focused meta test. | 只证明边界保护可记录，不清理任何外部 worktree。 |
| `usable closeout projection` | 本 note 与 ledger template 能承载最终 closeout 填写。 | this note; lightweight meta test; verification command. | 只证明 closeout projection 可用，不新增 wording gate。 |

## 本轮边界

- 不新增文档 wording gate、publication gate、submission gate 或 runtime authority。
- 不修改 `README*`、`docs/status.md` 或 live study artifact。
- 不读写 `DM002` live artifact。
- 不清理任何 worktree。
- `risk-*`、外部 active worktree、上游 review PR 和真实论文 soak 继续由对应 owner 或后续 lane 处理。

## 可登记结论

本轮可登记为：`usable_closeout_projection_ready`。

该结论的含义是 closeout ledger 和接力材料已经具备最终填写结构，轻量 meta 测试可以检查字段和边界存在。它不是 wording gate，也不是论文质量、真实 manuscript soak、submission readiness 或 live artifact 修复的完成证明。
