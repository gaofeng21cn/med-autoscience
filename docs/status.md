# 当前状态

**更新时间：2026-04-26**

## 当前角色

- `Med Auto Science` 是面向专病研究的独立医学研究 domain agent，单一 MAS app skill 承接稳定可调用面，负责研究问题进入、工作区语境、证据推进、人话进度和论文相关文件交付。
- 仓库首页负责用户入口；`CLI`、`MCP`、`controller` 负责操作与自动化入口。
- `Med Auto Science` 作为独立 medical research domain agent，对外先由单一 MAS app skill 统一承接；direct path 和经过 OPL 的 integration handoff 共享同一套研究语义。
- 对外稳定 capability surface 继续是本地 CLI、workspace commands / scripts、durable truth surface 与 repo-tracked contract，方便 `Codex` 直接调用。
- `OPL` 是上层 family-level session/runtime/projection 整合入口，并维护 shared modules/contracts/indexes；它不改写 MAS 的 domain owner 语义。
- `OPL Runtime Manager` 是 OPL 侧新增的薄运行管理/投影目标层，负责把 MAS registration/projection 接到外部 `Hermes-Agent` substrate、native helper catalog、高频状态索引与 doctor/repair/resume 面；它不持有 MAS study truth、publication gate 或 evidence/review ledger。
- `Hermes-Agent` 只在可选 hosted runtime target / reference-layer 语境出现；当前受控研究后端继续是 `MedDeepScientist`，但它在单项目主线里只保留 research backend、行为等价 oracle、上游 intake buffer 三个迁移期角色。

## 当前推荐使用方式

- 用户视角：给出病种、数据、目标问题和期望论文结果，在同一个工作区里持续推进研究。
- 研究推进视角：围绕同一条课题线管理问题定义、证据补足、进度反馈和文件交付。
- 命令行操作视角：当前最小操作路径仍是 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 这一组接口；对外它们都收口在单一 `Med Auto Science` app skill 之下，并继续通过 repo-tracked command contracts 被调用。

## 当前执行与监管模型

- 当前仓库跟踪主线继续按 `Auto-only` 理解。
- 默认执行仍继承本机 `Codex` 配置；仓库侧监管继续围绕外部运行时目标做状态检查和恢复判断。
- 方向锁定后的普通科研推进、论文质量判断与 `bounded_analysis` 一类有限补充分析默认由 `MAS` 自主完成。
- `MDS` 侧的 `publishability_gate_mode` 与 base skill 本地附加层清理继续服务 authority 去重；通用研究阶段纪律继续沿 `DeepScientist` / `MDS` base skill 维护，医学质量、医学稿件规则、submission hygiene 与 `publication gate` blocker 继续由 `MAS` 的 study charter、overlay、ledger、controller surface 承担。
- human gate 收口到方向重置、重大 claim 边界变化和投稿前最终审计。
- 关键持久表面继续围绕 `study_charter`、`evidence_ledger`、`review_ledger`、`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json`。
- 关键身份继续围绕 `program_id`、`study_id`、`quest_id`、`active_run_id`；用户面优先呈现 `study_id`、任务摘要、阻塞和下一步。

## 当前 active tranche

- 当前 tranche 固定为“质量闭环结构化 + 用户可见真相投影 + 对应 proof/soak 口径”。
- 质量闭环结构化的 owner 继续落在 `study_charter`、`paper evidence ledger`、`review ledger`：把方向锁定后的普通科研推进、论文质量裁决、`bounded_analysis` 边界、reviewer concern 与 submission hygiene 压成同一套 `MAS` quality contract。
- 当前 repo-side 落地已经要求质量修复写成结构化 route truth：当前是同线质量修复，还是 `bounded_analysis` 一类有限补充分析；回到哪条现有主线；当前那条主线要回答什么关键问题；为什么这是最窄、最诚实的修复路径。
- 当前 repo-side 落地已经把这层 blocked route truth 继续压进 `publication_eval/latest.json`：只要 `publication_gate` 已经知道应该 `return_to_write`、`return_to_analysis_campaign` 或 `return_to_finalize`，下游 durable surface 与 `study-progress` 就不再把它压回泛化 `return_to_controller`，而会直接投影成同线修复或有限补充分析。
- 当前 repo-side 落地已经把其中一类可确定修复的同线 route-back 前推成 controller-owned continuation step：当 `publication_eval/latest.json` 要求 `bounded_analysis`，且 `publication_gate` 的阻塞只剩 scientific-anchor 冻结、paper-facing surface repair、display/export refresh、submission-minimal replay 或 stale delivery replay 这类可批处理修复项时，`study_outer_loop` 会先执行一次 `run_gate_clearing_batch`，再把 study 送回同一条托管主线。
- 当前 repo-side 落地已经把“为什么现在已经足够继续往投稿包推进”压成稳定 truth：`evaluation_summary` / `study-progress` / `product-entry` 不只报告 blocker，也会统一投影 `quality_closure_truth + quality_closure_basis`，说明当前是仍需质量修复、已经可以继续写作，还是只剩同线 finalize / bundle 收口，以及这个判断分别建立在临床意义、证据强度、创新性定位、人工审阅准备度与发表门控哪几条依据上。
- 用户可见真相投影的 owner 继续落在 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json`：用户与维护者都应能从同一条 `MAS` 主线上读到当前阶段、关键证据、阻塞、下一步、恢复点与 human gate 原因。
- 当前 repo-side 落地已经要求 `study-progress` / `product-entry` 能明确区分：同线质量修复、有限补充分析、runtime recovery、human gate，不再把这些自治语义混成同一种“待人工确认”或“泛化 blocker”。
- 当前 repo-side 落地已经把 `study-progress`、`workspace-cockpit`、`product-frontdesk` 三个用户面收口到统一 `autonomy_contract`：当 study 处于自动推进、runtime recovery 或少数必须人工确认的节点时，三处表面都要讲同一套“为什么停、是否还能自动继续、恢复点是什么、下一次确认看什么”。
- 当前 repo-side 落地已经把这条 continuation 的 durable chain 固定在既有 `MAS` surface 上：`publication_eval/latest.json` 负责给出 route truth，`controller_decisions/latest.json` 负责记录 controller action，`artifacts/controller/gate_clearing_batch/latest.json` 负责记录 batch repair 与 gate replay，`runtime_watch` / `study-progress` 继续消费 outer-loop dispatch 与下一次确认信号。
- 当前 repo-side 落地已经把长期自治 proof/soak 继续压成稳定表面：`study-progress` 现已导出 `autonomy_soak_status`，`product-frontdesk` / `workspace-cockpit` 也开始显式消费最近一次自治续跑与其确认信号，不再只靠泛化 runtime summary 解释长跑状态。
- 当前 repo-side 落地已经把 `study-progress`、`workspace-cockpit`、`product-frontdesk` 三个用户面对论文质量 readiness 的解释也收口到统一质量 truth：当核心科学质量已经闭环、当前只剩同线写作或 finalize / bundle 收口时，用户面会直接说清“为什么已经够稳、还剩什么范围、这条判断由哪些质量依据支撑”。
- 当前 repo-side 落地已经把“初稿过轻”前置为 `study_charter.paper_quality_contract.structured_reporting_contract.first_draft_quality_contract` 与 agent-entry reviewer-first route-back 规则：写作前必须扫描已验证数据资产是否支撑更强的时间点、角色/人群、中心/地理、指南、亚组/关联和现实采用约束叙事；如果支持，就回到 `analysis-campaign` 做有限补充分析，而不是把低强度描述性初稿推进到 finalize。
- 当前 repo-side 落地已经把 `same_line_route_truth` 正式前推到 caller / frontdesk 合同：`build_product_entry.return_surface_contract.study_progress_projection_contract` 会显式声明这个字段，`workspace-cockpit` / `product-frontdesk` 的 attention queue、operator brief 和 markdown 也会直接投影“当前仍在同一论文线做什么、当前关键问题是什么”。
- 当前 repo-side 落地已经把质量复评后续动作继续前推到用户面：`study-progress` 现已导出 `quality_review_followthrough`，`workspace-cockpit` / `product-frontdesk` 可以直接解释“当前在等系统自动复评、为什么还没继续、下一次确认看什么”。
- 这条 gate-clearing batch 口径同时服务三个当前目标：对质量面，它清掉当前论文线里可确定修复的稿面/锚点/交付阻塞；对自治面，它把“先清 gate 再继续”保持在 controller-owned continuation 链里；对 single-project 边界，它继续只写 `MAS` 的 study/controller durable surface，不为 `MDS` 或其他 companion 打开新的 owner 面。
- proof/soak 口径当前围绕真实 study 的长期自治与质量闭环是否已经闭合，不围绕 `MDS` 再造一套长期 owner 面；`MDS` 只保留 migration oracle、backend compatibility、upstream intake buffer 三个迁移期角色。
- 当前 tranche 的 repo-side 落点是单项目 owner truth、用户可见边界和 program/mainline 口径收紧；这一步不推进 `physical monorepo absorb`、跨仓 `runtime core ingest` 或把 `MDS` 重新解释成并行产品面。
- 当前 `build_product_entry.return_surface_contract` 已经开始把 `single_project_boundary` 与 `study_progress` truth field contract 一并交给外部 caller；调用方可以不回 `mainline-status` 也读到 MAS/MDS owner boundary，以及 `autonomy_soak_status`、`quality_execution_lane`、`same_line_route_truth`、`quality_review_followthrough` 这些当前应消费的 progress truth 字段。
- 当前 `build_product_entry.return_surface_contract` 额外导出 `research_runtime_control_projection` 合同：调用方可统一读取 `study/session owner`、`restore_point`、`progress cursor/surface`、`artifact inventory/pickup`、`resume/check command template` 与 `research gate(approval/interrupt)` 对应字段；`workspace-cockpit` attention queue 与 operator brief 会原样携带该投影，`product-frontdesk` preview 继续消费同一条 attention item，不需要引入 display 支线。
- 当前 `mainline-status` / `mainline-phase` / `product-frontdesk` / `product-entry-manifest` / `build-product-entry.return_surface_contract` 已经同步投影 `capability_owner_boundary`：研究入口、task intake、controller outer loop、progress truth、publication quality gate、runtime recovery 与 program/mainline truth 都是 MAS-owned capability；`MDS` 只保留 migration-only 的 backend / behavior-equivalence oracle / upstream intake buffer 角色。
- 当前 tranche 的通过条件是：`MAS` 已能默认自治推进方向锁定后的研究与有限补充分析，用户可见 truth 与 durable surface 对齐，major boundary 与最终投稿审计之外不再把 human 判断留在 `MDS` 或隐藏 owner 面里。

## 当前验收与 proof 口径

- 验收先看结构是否闭合：study charter 质量总合同、evidence/review ledger 执行记录、runtime/progress truth projection 三层要能沿同一条 `MAS` 主线解释。
- 验收还要看语义是否可读：当质量闭环要求回到某条现有主线时，`MAS` 能说清“回到哪条线、当前关键问题是什么、为什么先做这一步”。
- proof 先看 owner 是否单一：质量判断、有限补充分析推进、运行恢复与用户面进度解释默认都由 `MAS` 负责；`MDS` 提供 oracle 对照与 backend 兼容，不承担长期双 owner。
- soak 先看真实 study 能否长期成立：长时间运行、停滞后的恢复、human gate 触发、投稿前审计前的持续推进，都要在真实 durable surface 上读得出来。
- 同线 continuation proof/soak 现在也包括 `run_gate_clearing_batch`：proof 看 controller 是否能沿 `publication_eval -> controller_decisions -> gate_clearing_batch record -> publication_gate replay` 保持单一 owner truth，soak 看真实 study 是否能经由这一步继续回到同一条 paper line，而不是新增人工 owner 或第二条治理面。
- 当前 stage 不要求 `MDS` 退场；要求的是 `MDS` 的存在只能解释为迁移期 proof companion，而不是另一条并行产品主线。
- 当前 stage 也不把 `physical monorepo absorb` 当作 tranche 完成信号；那属于 external/runtime/workspace gate 清完之后的 post-gate 工作。
- 当前 parity/proof 口径固定为：`behavior_equivalence_oracle`、`study_progress_projection_contract`、`publication_eval/latest.json` 与 `controller_decisions/latest.json` 共同支撑迁移期等价证明；`physical monorepo absorb` 继续是 `blocked_post_gate`，必须等 external runtime gate、多 workspace/host proof、backend deconstruction boundary 与 MAS-owned contract/test/proof surfaces 全部成立后再进入。

## 当前边界

- `Med Auto Science` 负责研究入口、工作区权威语义、证据推进和论文交付。
- `Med Auto Science` 的 direct/handoff 两条入口路径共享同一套 study truth 与 authority boundary。
- `MedDeepScientist` 继续作为受控 research backend、行为等价 oracle、上游 intake buffer 存在，不再承担独立产品入口、长期治理面或长期双 owner 语义。
- 研究者与课题负责人继续负责方向设定、重大边界变化和投稿前审计。
- 期刊投稿和外部系统交互继续由人工监督。
- `OPL` 集成、`product-entry manifest`、`handoff envelope` 和其他机器可读桥接继续留在集成层与参考层阅读。
- `physical monorepo absorb`、`runtime core ingest` 与更大的平台化结构调整继续是 post-gate 长线，不属于当前 tranche 的 repo-side 验收面。
- 自有长期常驻 OPL sidecar 不是当前 MAS 侧目标；只有当外部 `Hermes-Agent` substrate 无法表达 task/wakeup/approval/audit/product isolation contract 时，才通过 OPL Runtime Manager 的已冻结 adapter/projection 边界进入 promotion 评估。

## 当前维护重点

1. 保持 `README*` 与 `docs/README*` 继续面向医生、课题负责人和潜在使用者。
2. 保持 `docs/project.md`、`docs/status.md`、`docs/architecture.md` 对齐同一套产品边界、执行回路和 owner 层级。
3. 保持 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 作为 MAS 的核心可执行回路，同时保持 `CLI`、`MCP`、`controller` 作为正式操作与自动化入口。
4. 保持 `OPL Runtime Manager`、外部 `Hermes-Agent` substrate 与 MAS durable projection 的 owner split 清晰；维护者细节继续留在 reference / program 层。
5. 把“医学论文质量 + 长时间全自动驾驶优化”正式收口到 `MAS` 单项目主线，由 `controller_charter / runtime / eval_hygiene` 共同承担 owner；`MDS` 迁移期角色继续收敛为 research backend、行为等价 oracle、上游 intake buffer。
6. 把 study charter 升级为质量总合同入口；`paper evidence ledger` 与 `review ledger` 作为该合同的执行与审阅记录，统一承载主结果、`bounded_analysis`、reviewer concern 与 submission hygiene 的落地状态。
7. 把用户可见真相投影压实到 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json` 这一组 durable surface 上，让当前阶段、关键证据、阻塞、下一步、恢复点、artifact pickup 与 human gate 原因都能被同一条 `MAS` 主线读取；当前统一出口已经收口成 `autonomy_contract + restore_point + autonomy_soak_status`、`quality_closure_truth + quality_closure_basis + quality_review_followthrough` 与 `research_runtime_control_projection` 三条互补 truth。
8. 把“持续学习 `DeepScientist` 方法论”收口为 `MAS` 的长期 program lane：维护者先读 [DeepScientist Latest-Update Learning Protocol](./program/deepscientist_latest_update_learning_protocol.md)、[MedDeepScientist Method Learning Disciplines](./program/med_deepscientist_method_learning_disciplines.md)、[MedDeepScientist Continuous Learning Plan](./program/med_deepscientist_continuous_learning_plan.md) 和 [MedDeepScientist Upstream Source Provenance](./program/med_deepscientist_upstream_source_provenance.md)。当用户说“学习一下 `DeepScientist` 的最新更新”时，默认启动 fresh upstream audit、decision matrix、并行 worktree 落地、验证、吸收回 `main` 和清理的完整流程；先区分“upstream learned common research discipline”和“MAS-own governance / medical-quality surfaces”，再决定哪些 lesson 进入 `controller_charter`、`runtime`、`eval_hygiene` owner 面，哪些继续留在 `MDS` 的 oracle / intake / parity companion 面。
