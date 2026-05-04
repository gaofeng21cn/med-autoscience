# MAS/MDS Unified Enhancement Program

Status: `active integration program`
Date: `2026-05-04`
Owner: `MedAutoScience`

## 结论

这 15 条继续增强建议大多必要，但不应继续按三组清单各自推进。它们本质上落在同一个问题上：真实论文运行、文件交付、控制面一致性、provider 运营、质量校准和结构治理都在描述同一条 end-to-end research operating system，只是观察层不同。继续分散推进会重新制造 owner 重叠：入口再解释一次下一步，文件层再解释一次 stale/ready，控制面再解释一次 apply/backfill，观测层再解释一次 provider/outcome，最终让医生和 Agent 都读到多套相似判断。

统一方案是把这些建议收敛成 5 条 program lane，并强制每条 lane 只有一个 authority owner：

1. `L1_real_workspace_longitudinal_soak`
2. `L2_pi_action_projection`
3. `L3_outcome_calibration_and_provider_ops`
4. `L4_delivery_and_legacy_upgrade_visibility`
5. `L5_natural_boundary_and_audit_compaction`

其中 `L1` 是证据来源，`L2` 是医生入口投影，`L3` 是观测和校准，`L4` 是文件交付与旧包升级可见性，`L5` 是结构债和 audit bucket 治理。`L2/L3/L4` 不得独立声明 publication readiness、submission authority 或 canonical next action；这些仍由 `StudyTruthKernel`、`RuntimeHealthKernel`、AI reviewer-backed `publication_eval/latest.json`、`controller_decisions/latest.json` 和 canonical artifact proof 持有。

## 外部工程依据

- `strangler_fig`：旧能力替换应逐面包裹、迁移和切换；本项目中表现为先做 read model / fitness function，再 capability-by-capability absorb，而不是 big-bang rewrite。
- `architecture_fitness_functions`：架构约束必须进入可执行检查；本项目中表现为 meta tests、owner-boundary report、line budget、Sentrux structure lane。
- `team_topologies_cognitive_load`：复杂系统要按团队/API/认知负载划边界；本项目中表现为医生入口只输出 PI-level 判断，维护者入口保留 ledger/audit/detail。
- `sre_toil_elimination_and_observability`：重复人工排查、重复返工和不可解释状态都是 toil；本项目中表现为 provider health、delivery traffic-light、legacy queue、outcome calibration 必须变成稳定投影，而不是临时说明。
- `owner_private_truth_surfaces`：权威状态只能由 owner 写入、由 projection 消费；本项目中表现为 `study truth / quality truth / runtime truth / artifact truth` 不被 entry、observability、MDS oracle 或 file inspector 重写。

可追溯参考：

- Martin Fowler 的 Strangler Fig Application：`https://martinfowler.com/bliki/OriginalStranglerFigApplication.html`
- Thoughtworks / Evolutionary Architecture fitness functions：`https://www.thoughtworks.com/insights/books/building-evolutionary-architectures`
- Team Topologies 关于 team API 与认知负载的架构划分：`https://teamtopologies.com/`
- Google SRE Book, Eliminating Toil：`https://sre.google/sre-book/eliminating-toil/`
- 本仓库 owner-boundary fitness function：`docs/architecture.md#masmds-owner-boundary-fitness-function`

## 15 条建议归并评估

| original | 判断 | 归并 lane | 处理方式 |
| --- | --- | --- | --- |
| 自动科研 1：更多真实 disease workspace 长期 soak | 必要 | `L1_real_workspace_longitudinal_soak` | 保留为主证据线，必须覆盖投前、返修、重开、换线、最终重建。 |
| 自动科研 2：用户入口动作语言压缩成 PI 判断 | 必要 | `L2_pi_action_projection` | 合并为单一 user-visible action projection；不得在 frontdesk/cockpit/progress 各写一套判断。 |
| 自动科研 3：投稿结果反馈 calibration regression | 必要 | `L3_outcome_calibration_and_provider_ops` | 与 AI reviewer calibration corpus、quality regression 合并；只做校准/回归，不直接授权 ready。 |
| 自动科研 4：provider freshness/outage/citation drift | 必要 | `L3_outcome_calibration_and_provider_ops` | 与 calibration 同 lane，因为它们都是 observability inputs。 |
| 自动科研 5：journal-family writing pack | 必要但需约束 | `L2_pi_action_projection` / `L3_outcome_calibration_and_provider_ops` | 作为 AI reviewer / authoring input 和 archetype pack，不成为机械 writing authority。 |
| 自动科研 6：first full draft authorization 到 submission package rebuild 闭环时延 | 必要 | `L1_real_workspace_longitudinal_soak` | 作为 soak proof 的 latency/recovery acceptance，不单独开 fast lane。 |
| 文件管理 1：legacy upgrade queue | 必要 | `L4_delivery_and_legacy_upgrade_visibility` | 做 workspace-level queue/read model；升级仍由 controller-authorized sync 自然发生。 |
| 文件管理 2：医生友好 current_package README | 必要 | `L4_delivery_and_legacy_upgrade_visibility` | 做 delivery projection 模板：投稿文件、audit/reproducibility、非 edit source。 |
| 文件管理 3：大文件结构瘦身 | 必要 | `L5_natural_boundary_and_audit_compaction` | 进入结构治理 lane；按 Sentrux/line budget top targets 逐步拆。 |
| 文件管理 4：真实 journal profile fixture matrix | 必要 | `L3_outcome_calibration_and_provider_ops` | 作为 journal-family pack 的 fixture matrix，覆盖 cover letter/checklist/supplement naming。 |
| 文件管理 5：delivery status 红黄绿可视化 | 必要 | `L4_delivery_and_legacy_upgrade_visibility` | 统一 traffic-light read model：current/stale/legacy_pending/missing。 |
| 控制面 1：真实 workspace backfill blockers | 必要 | `L4_delivery_and_legacy_upgrade_visibility` | backfill plan 仍 read-only；写入必须显式 controller apply。 |
| 控制面 2：audit_log compaction policy | 必要但后置 | `L5_natural_boundary_and_audit_compaction` | 先补 restore/index/provenance contract，再允许 compaction。 |
| 控制面 3：旧 worktree ownership audit | 必要 | `L5_natural_boundary_and_audit_compaction` | 作为 cleanup safety gate；只清理本轮或明确 owner 的 absorbed worktree。 |
| 控制面 4：历史大文件/高复杂函数低风险拆分 | 必要 | `L5_natural_boundary_and_audit_compaction` | 与文件管理 3 合并，避免两条结构治理 lane 重复。 |

## Program Lanes

### L1 real workspace longitudinal soak

Owner: `MedAutoScience runtime + quality`

目的：用真实 disease workspace 证明纵向闭环，而不是只靠 synthetic fixtures。最小证据矩阵必须覆盖：

- pre-submission
- revision
- reopen same paper line
- route change / line switch
- final rebuild from canonical source
- first full draft authorization to submission package rebuild latency
- failure recovery and replay evidence

Authority boundary：`L1` 只产生 proof/evidence；它不能直接改写 publication readiness。ready 仍由 AI reviewer-backed `publication_eval/latest.json`、evidence/review ledger、controller decision 和 artifact rebuild proof 共同给出。

### L2 PI action projection

Owner: `MedAutoScience product entry`
Status: `landed as projection-only read model`

目的：把多个用户入口压缩成同一套 PI-readable next action，例如：

- 补文献
- 改统计
- 降级 claim
- 重开同一论文线
- 换线
- 进入 AI reviewer
- 进入 submission package rebuild

Authority boundary：`study-progress` 是源头投影，`workspace-cockpit` 和 `product-frontdesk` 只能消费同一 action payload。入口文案不得根据文件状态、provider 状态或 MDS oracle 另算下一步。

落地面：`med_autoscience.controllers.pi_action_projection` 暴露单一 `pi_action_projection` read model；`study_progress` 负责生成 full payload，MCP compact study-progress surface 保留压缩后的同一投影，product-entry workspace study item 只透传/压缩该 payload。该 surface 固定 `projection_only=true`，`can_set_canonical_next_action=false`，`can_authorize_publication_readiness=false`，`can_authorize_submission=false`，不得成为 canonical next action、publication readiness 或 submission package authority。

### L3 outcome calibration and provider ops

Owner: `MedAutoScience Observability OS`

目的：把真实投稿结果、AI reviewer calibration、provider freshness、partial outage、citation drift、journal-family fixture matrix 放在同一条 observability lane，形成质量回归与运营健康投影。

这条 lane 的输出包括：

- desk reject / major revision / accept outcome intake
- claim/统计/写作判断的过强/过弱 calibration
- provider freshness / partial outage / citation ledger drift
- journal-family writing pack fixture matrix
- cover letter / checklist / supplement naming convention coverage

Authority boundary：`L3` 只能更新 calibration inputs、health projection 和 regression evidence；不能绕过 AI reviewer 或 publication gate 直接让稿件 ready。

### L4 delivery and legacy upgrade visibility

Owner: `MedAutoScience artifact/delivery projection`

目的：把文件管理建议和控制面 backfill 建议合并成一个医生友好 delivery visibility lane。

输出必须保持三层：

- doctor view：投稿文件、红黄绿 delivery 状态、legacy pending queue、next controller-authorized sync。
- audit view：manifest、evidence ledger、review ledger、source signatures、backfill blockers。
- authority view：明确哪些不是 edit source，哪些状态只是 projection，哪些写入必须 controller apply。

Authority boundary：legacy upgrade queue、delivery traffic-light、backfill blocker report 都是 read model；只有 controller-authorized sync/apply 能写 delivery truth。

### L5 natural boundary and audit compaction

Owner: `MedAutoScience maintainability`

目的：把结构治理、audit_log 大桶、旧 worktree ownership audit、历史大文件拆分合并成一个 maintainability lane，避免每条业务线都顺手拆一点、越拆越乱。

顺序固定为：

1. ownership audit：识别 main、外部 active worktree、本轮 worktree、unknown owner。
2. structure top targets：按 Sentrux/line budget/complexity 选择低风险拆分。
3. audit compaction pre-contract：先定义 restore/index/provenance。
4. compaction implementation：只有 restore/index/provenance 测试通过后才能 compact。

Authority boundary：结构治理不改变 study truth、publication truth、delivery truth 或 runtime action；它只降低维护成本和误读风险。

## 实施顺序

第一批可并行推进：

| branch | lane | scope |
| --- | --- | --- |
| `codex/mas-soak-matrix-read-model` | `L1` | 真实 workspace 纵向 soak matrix read model 和 latency/recovery proof acceptance。 |
| `codex/mas-pi-action-projection` | `L2` | 单一 PI action payload，frontdesk/cockpit/progress 共享投影。 |
| `codex/mas-calibration-provider-ops` | `L3` | outcome calibration + provider health + journal fixture matrix read model。 |
| `codex/mas-delivery-legacy-visibility` | `L4` | legacy upgrade queue、doctor README 模板、delivery traffic-light。 |
| `codex/mas-structure-audit-compaction` | `L5` | ownership audit、structure target list、audit compaction pre-contract。 |

吸收顺序固定为 `L1 -> L2 -> L3 -> L4 -> L5`。`L2/L3/L4` 如果依赖尚未落地的 authority truth，只能声明 `projection_pending_authority`，不能自行填充权威字段。

## 验收门槛

- `make test-meta` 必须覆盖本 program 文档、15 条建议归并、5 条 lane、authority boundary 和并行吸收规则。
- `mas_mds_module_boundary_audit_report` 是 5 条 lane 的模块分层与耦合 audit 入口，由 `med_autoscience.controllers.module_boundary_audit` 暴露机器可读 module group、allowed/forbidden dependency、writable authority 和 projection-only 约束。
- `scripts/verify.sh structure` 或等价 Sentrux/line-budget lane 必须用于任何 `L5` 结构实现。
- `L1` 完成前，不得宣称真实论文质量改善、submission readiness 或 AI-first Research OS fully proven。
- `L2/L3/L4` 所有 projection 必须回指 MAS durable truth surface。
- `L5` audit compaction 必须先证明 restore/index/provenance contract，不能先删大桶再补说明。

## 当前落地范围

本次落地已包含 `L2_pi_action_projection` 的可用 read model：医生入口能从 study-progress/operator/compact payload 读取补文献、改统计、降级 claim、重开同一论文线、换线、进入 AI reviewer、进入 submission package rebuild 七类 PI-readable 动作。真实 workspace 产物、`current_package`、`publication_eval/latest.json`、`controller_decisions/latest.json`、delivery artifact 和 live runtime state 都不在本次直接修改范围内。
