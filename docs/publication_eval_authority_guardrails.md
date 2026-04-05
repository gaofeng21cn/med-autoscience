# Publication Eval Authority Guardrails

这份 memo 作为 `research-foundry-medical-mainline` 当前 `publication eval minimal schema` 子线的 critic lane 产物，专门枚举最容易发生的 authority-mixing failure modes，以及本轮最小 contract 应先固定的 guardrails。

目标不是扩大发明新的实现面，而是防止 `controller / runtime / eval / delivery` 四层在 schema 收敛阶段重新混叠。

## Boundary Recap

当前最小边界应固定为：

- `controller authority`
  - 持有 `study_charter`、publication objective、route bias、stop/continue/reroute 的正式决策权
- `runtime authority`
  - 持有 quest execution truth、runtime audit、runtime escalation record
- `eval authority`
  - 持有 publication-facing `verdict / gap / recommended_action` 判据对象
- `delivery authority`
  - 持有 manuscript / report / submission / bundle 等 paper-facing artifact

因此，`publication eval` 的职责应是：

- 读取来自 controller / runtime / delivery 的权威输入或 durable refs
- 生成 eval-owned verdict artifact
- 为 controller 提供 stop / continue / reroute / promotion 的判据

而不应：

- 反写 controller truth
- 接管 runtime execution truth
- 把 delivery artifact 误当成 authority root

## Authority-Mixing Failure Modes And Guardrails

| Failure mode | 为什么危险 | 必须先固定的 guardrail |
| --- | --- | --- |
| **1. Eval 反写 controller truth**：publication eval 直接改写 `study_charter`、publication objective、claim family 或 route bias | 让 eval 从判据层滑成 controller；之后任何 verdict 都可能悄悄改变研究目标 | eval 只产出独立 verdict artifact；若需要改 charter，必须通过 controller-own 的单独 mutation / decision surface 完成 |
| **2. Runtime 自我认证 publishability**：runtime create/resume/write 路径直接宣称 `ready_for_promotion` 或“仍值得发” | 把“还能运行”混成“值得发表”，破坏 runtime / eval 边界 | runtime 只允许输出 execution facts 与 `runtime_escalation_record`；`overall_verdict` 由 eval plane 独占 |
| **3. `startup_contract` 被重新抬升成 authority root**：把 publication verdict、gap、promotion state 长期塞回 `startup_contract` | 把 controller->runtime projection 重新变成混合 authority 大对象 | `startup_contract` 继续只做 projection / transport；publication eval 必须落成独立 artifact，而不是 nested startup state |
| **4. Delivery artifact 被误当 verdict root**：manuscript draft、submission bundle 或 checklist completion 被直接当作“评估已通过” | delivery completeness 不等于 claim viability；容易把弱结果包装成可投 | delivery surface 只能作为 eval 输入或 evidence ref；promotion 需要显式 eval artifact/ref，而不是靠 bundle 存在性推断 |
| **5. `recommended_actions` 变成隐式 controller 命令**：下游自动把 eval action 当必须执行的指令 | controller 决策权被语义偷渡；后续很难分清“建议”与“命令” | `recommended_actions` 明确是 advisory；controller 必须显式 adopt / reject / defer；不得自动执行 |
| **6. 把 publication gate 当成完整 eval plane**：把 `publication_gate_policy`、checklist gate 或单次 write 前 gate 直接当成全部 publication eval | 会把 policy gate / workflow gate / verdict substrate 三层压扁，之后很难扩展 claim viability、gap prioritization、promotion 判断 | publication gate 只应是 eval 或 controller 消费 verdict 的一层 policy surface；不能替代完整 eval artifact |
| **7. 直接把 medical publication policy 压成 core eval schema** | 把 medical-specific policy、journal hygiene、submission discipline 与通用 verdict substrate 混成一层 | core schema 先只保留最小 verdict/gap/action；TRIPOD、journal、submission-specific 约束放在 policy / delivery / controller extension 层 |
| **8. 用聊天印象或临时总结充当 evidence** | verdict 失去可审计性，之后无法回看“为什么被判 weak / mixed / blocked” | `evidence_refs` 只应指向 durable artifact、runtime record、controller summary 或 delivery artifact；不允许只引用会话印象 |
| **9. Stop-loss 信号被混成 runtime liveness / blocking state** | “不值得继续投论文”会被错误解释成 runtime 崩溃或 data gate 失败 | publication verdict 只影响 controller route choice；quest live/paused/completed 仍由 runtime truth 决定 |
| **10. Eval 直接改写 delivery backlog**：评估对象顺手生成 manuscript 任务并把它当正式交付计划 | eval 层开始吞并 delivery orchestration，之后 paper-facing backlog 会失去 owner | eval 只列 gap 与推荐动作；delivery backlog 由 controller / delivery plane 单独维护 |
| **11. 复用 `runtime escalation` 词汇但不声明映射边界** | 名义复用降低成本，实际却让 eval/retry/escalate/stop-loss 语义互相污染 | 若复用 `recommended_actions` vocabulary，必须显式声明“共享 token / 分离 authority”；更安全的首轮做法是先映射兼容而不是宣称同一对象 |

## Minimal Contract Checks For This Subline

当前这轮 `publication eval minimal schema` 至少应满足下面这些硬约束：

1. **输出只包含 eval-owned fields。**
   - 可以有 `overall_verdict`、`claim_status`、`blocking_gaps`、`recommended_actions`、`evidence_refs`
   - 不应把 `study_charter`、`startup_contract`、quest lifecycle state、submission bundle state 直接嵌进去当 authority payload

2. **跨层输入默认走 ref / summary，而不是 ownership 转移。**
   - controller 提供 charter/objective/reporting constraint 的 ref 或 compact summary
   - runtime 提供 escalation / artifact / audit refs
   - delivery 提供 manuscript / checklist / bundle refs

3. **`recommended_actions` 只能表达 route suggestion，不能表达隐式 mutation。**
   - 允许：`continue_same_line`、`bounded_analysis`、`return_to_idea`、`escalate_to_controller`
   - 不允许：带有“已经执行”的 controller/runtime side effect 语义

4. **`overall_verdict` 必须保持 publication-facing，而不是 runtime-facing。**
   - 它判断的是 publishability / promotion viability
   - 不是 daemon health、quest liveness 或 startup readiness

5. **判据理由必须能回链到 durable evidence。**
   - `reason` 不能只是一句聊天判断
   - `blocking_gaps` 应该能由 `evidence_refs` 支撑

6. **publication gate 只是 policy/gate surface，不是完整 eval plane。**
   - gate 可以消费 publication eval verdict
   - 但不能取代完整的 verdict / gap / recommended_action artifact

7. **delivery plane 只消费 verdict，不拥有 verdict。**
   - manuscript / report / submission surface 可以引用 publication eval
   - 但不应反向成为 publication eval 的 authority source

## Open Design Questions Worth Keeping Visible

这些点仍值得 leader 在主线集成时显式决策：

1. `recommended_actions` 是不是只做 **token-level compatibility**，而不直接宣布与 `runtime_escalation_record.recommended_actions` 为同一 authority object。
2. publication eval 最小 schema 是否需要额外显式区分：
   - `controller_context_refs`
   - `runtime_context_refs`
   - `delivery_context_refs`
   还是首轮先统一保留在 `evidence_refs`，避免过早扩 schema。
3. `ready_for_promotion` 是否应保留为 eval verdict，还是只作为 controller 基于 verdict 作出的后续 route decision，避免 promotion authority 过早混入 eval object。

## Recommended Integration Stance

对当前主线，更稳妥的集成姿势是：

1. 先把这些 guardrails 写进 `publication eval minimal schema` 的 PRD / test-spec / report narrative；
2. 先收紧 authority boundary 与禁止项；
3. 暂不进入 publication eval implementation；
4. 暂不把 medical publication policy、submission orchestration、delivery backlog 过度压入首轮 schema。

这样可以避免在 `harness authority convergence` 阶段，把本来应当分层演进的对象重新混成一个“会评估、会执行、会改计划、会写稿”的大表面。
