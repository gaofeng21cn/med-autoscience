# 当前状态

**更新时间：2026-05-04**

## 当前角色

- `Med Auto Science` 是面向专病研究的独立医学研究 domain agent，单一 MAS app skill 承接稳定可调用面，负责研究问题进入、工作区语境、证据推进、人话进度和论文相关文件交付。
- 仓库首页负责用户入口；`CLI`、`MCP`、`controller` 负责操作与自动化入口。
- `Med Auto Science` 作为独立 medical research domain agent，对外先由单一 MAS app skill 统一承接；direct path 和经过 OPL 的 integration handoff 共享同一套研究语义。
- 对外稳定 capability surface 继续是本地 CLI、workspace commands / scripts、durable truth surface 与 repo-tracked contract，方便 `Codex` 直接调用。
- `OPL` 是上层 family-level session/runtime/projection 整合入口，并维护 shared modules/contracts/indexes；它不改写 MAS 的 domain owner 语义。
- `OPL Runtime Manager` 是 OPL 侧新增的薄运行管理/投影目标层，负责把 MAS registration/projection 接到外部 `Hermes-Agent` substrate、native helper catalog、高频状态索引与 doctor/repair/resume 面；它不持有 MAS study truth、publication gate 或 evidence/review ledger。
- `Hermes-Agent` 只在可选 hosted runtime target / reference-layer 语境出现；当前受控研究后端继续是 `MedDeepScientist`，但它在单项目主线里只保留 research backend、行为等价 oracle、上游 intake buffer 三个迁移期角色。
- 2026-05-01 之后的当前主线新增了两层 reducer truth：`StudyTruthKernel` 统一 study 级 next action / package authority / publication gate 解释，`RuntimeHealthKernel` 统一 worker liveness / retry budget / recovery escalation；普通 read 只生成 shadow projection，materialized truth 只能由显式 reconcile、controller tick 或 runtime watch apply 写入。
- 同一轮主线还把医学稿件初稿质量从“gate 后置拦截”前移为 pre-draft runtime concern：`medical journal prose`、IMRAD section contract、reporting-guideline obligations 与 first-draft generation model 应在 study charter / quality OS 中可见。
- AI-first 的当前语义是可运行质量线：pre-draft quality runtime、AI reviewer workflow、artifact rebuild proof、operations state 和真实论文 soak。文档只做人工可读收敛，不新增 wording gate，不改测试或 preflight contract。
- 本轮跨仓审计发现本机 `med-deepscientist` root checkout 的 `main` ahead `origin/main` 11 个提交；这些未推送提交只作为本地 companion audit fact，不作为 MAS 当前公共真相、OPL 公共真相或 release-facing contract 输入。

## 当前推荐使用方式

- 用户视角：给出病种、数据、目标问题和期望论文结果，在同一个工作区里持续推进研究。
- 研究推进视角：围绕同一条课题线管理问题定义、证据补足、进度反馈和文件交付。
- 命令行操作视角：当前最小操作路径仍是 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 这一组接口；对外它们都收口在单一 `Med Auto Science` app skill 之下，并继续通过 repo-tracked command contracts 被调用。`product-frontdesk` 只是内部操作回路与 projection contract，不是独立公开产品入口。

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
- 2026-05-02 长线目标架构已固定为 `MAS AI-first Research OS`：MAS Core、Quality OS、Runtime OS、Artifact OS、Evaluation OS、Observability OS 与 MDS Deconstruction 共同定义后续 owner、authority、contract 与 parity proof。当前阶段继续按能力逐步落地，不做一次性物理迁移。
- 质量闭环结构化的 owner 继续落在 `study_charter`、`paper evidence ledger`、`review ledger`：把方向锁定后的普通科研推进、论文质量裁决、`bounded_analysis` 边界、reviewer concern 与 submission hygiene 压成同一套 `MAS` quality contract。
- AI-first 质量边界的当前目标是把 `publication_gate` / `medical_reporting_audit` 生成的机械投影，与 AI reviewer 读取 manuscript、evidence ledger、review ledger 和 study charter 后形成的质量判断分开。机械投影表达 blocker/projection/replay，AI reviewer workflow 才能承接科学质量、医学写作质量和 submission-facing readiness。
- 投稿前质量授权口径保持 fail-closed：只有由 AI reviewer 读取 manuscript、evidence ledger、review ledger 与 study charter 后形成的 judgement，才能进入 scientific quality、medical writing quality、publishability 或 submission-facing readiness 判断。
- 当前 repo-side 可用表面应能表达质量修复路线：当前是同线写作修复、`bounded_analysis` 一类有限补充分析、finalize / bundle 收口，还是 human gate。文档不把这些 route 词汇变成机械 wording gate。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`study-progress` 与 `product-entry` 是当前用来投影 quality closure、route-back、controller action 和用户可见下一步的主要表面；具体 route 能否闭合，以真实 study 的 durable surface 和 artifact rebuild proof 为准。
- 用户可见真相投影的 owner 继续落在 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json`：用户与维护者都应能从同一条 `MAS` 主线上读到当前阶段、关键证据、阻塞、下一步、恢复点与 human gate 原因。
- `study-progress`、`workspace-cockpit`、`product-frontdesk` 应围绕同一组 operations state 解释自动推进、runtime recovery、restore point、artifact pickup 和 human gate；它们不能制造第二套研究判断。
- `StudyTruthKernel` shadow layer 与 `RuntimeHealthKernel` shadow layer 是当前读状态基础：普通 read 不刷新 materialized truth；materialized truth / health 只能由显式 reconcile、controller tick 或 runtime watch apply 写入。
- medical journal prose 质量合同已经进入当前文档口径：first draft 应是医学期刊可读的 manuscript-shaped prose，不能把 controller checklist、figure/table anchor、author-confirmation placeholder、内部 claim-boundary 标签或 operations/review 语言带入正文。
- workspace Git/storage 边界已收紧为轻量外层 Git + generated/runtime/artifact 排除 + explicit storage audit repair；runtime-storage apply-mode release estimate 必须反映实际 apply strategy，而不是 gross candidate size。
- `run_gate_clearing_batch`、quality review follow-through、same-line route truth 与 autonomy soak 相关表面都是当前 proof/soak 的候选证据面；它们是否已经形成可发表工作流证据，仍需真实论文线继续 soak。
- proof/soak 口径当前围绕真实 study 的长期自治、pre-draft 质量运行、AI reviewer workflow、artifact rebuild proof 与 operations state 是否闭合，不围绕 `MDS` 再造一套长期 owner 面；`MDS` 只保留 migration oracle、backend compatibility、upstream intake buffer 三个迁移期角色。
- 当前 tranche 的 repo-side 落点是单项目 owner truth、用户可见边界和 program/mainline 口径收紧；这一步不推进 `physical monorepo absorb`、跨仓 `runtime core ingest` 或把 `MDS` 重新解释成并行产品面。
- `build_product_entry.return_surface_contract`、`skill-catalog` domain projection、`mainline-status` / `mainline-phase` / `product-frontdesk` / `product-entry-manifest` 继续作为 caller 读取 MAS/MDS owner boundary、runtime continuity、artifact locator 与 progress truth 的入口；这些入口只能投影 MAS durable truth，不能替代研究质量判断。
- OPL 或其他 caller 读取这些入口时，只能把它们当作 MAS durable truth 的投影与内部 command contract；不得把 MDS、product-frontdesk 或 product-entry manifest 写成并行 owner 面。
- 当前 tranche 的通过条件是：`MAS` 能默认自治推进方向锁定后的研究与有限补充分析，用户可见 truth 与 durable surface 对齐，major boundary 与最终投稿审计之外不再把 human 判断留在 `MDS` 或隐藏 owner 面里。真实论文 soak 仍是整体 AI-first 质量闭环的主要证据面；Open Auto Research 的真实 study soak 已用 DM002 完成，不再是 OAR repo-level capability 缺口。

## 当前验收与 proof 口径

- 验收先看结构是否闭合：study charter 质量总合同、evidence/review ledger 执行记录、runtime/progress truth projection 三层要能沿同一条 `MAS` 主线解释。
- 验收还要看语义是否可读：当质量闭环要求回到某条现有主线时，`MAS` 能说清“回到哪条线、当前关键问题是什么、为什么先做这一步”。
- proof 先看 owner 是否单一：质量判断、有限补充分析推进、运行恢复与用户面进度解释默认都由 `MAS` 负责；`MDS` 提供 oracle 对照与 backend 兼容，不承担长期双 owner。
- soak 先看真实 study 能否长期成立：长时间运行、停滞后的恢复、pre-draft 质量判断、AI reviewer workflow、artifact rebuild proof、human gate 触发、投稿前审计前的持续推进，都要在真实 durable surface 上读得出来。
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
- `MAS` 已声明 `OPL` family contract adoption：`contracts/opl-gateway/family-contract-adoption.json` 与 `docs/references/opl_family_contract_adoption.md` 把 runtime attempt、medical quality projection、incident learning 与 product operator projection 映射回 MAS-owned durable surfaces；`OPL` 只消费投影，不持有 study truth 或 publication judgment。
- `physical monorepo absorb`、`runtime core ingest` 与更大的平台化结构调整继续是 post-gate 长线，不属于当前 tranche 的 repo-side 验收面。
- 自有长期常驻 OPL sidecar 不是当前 MAS 侧目标；只有当外部 `Hermes-Agent` substrate 无法表达 task/wakeup/approval/audit/product isolation contract 时，才通过 OPL Runtime Manager 的已冻结 adapter/projection 边界进入 promotion 评估。

## 当前维护重点

1. 保持 `README*` 与 `docs/README*` 继续面向医生、课题负责人和潜在使用者。
2. 保持 `docs/project.md`、`docs/status.md`、`docs/architecture.md` 对齐同一套产品边界、执行回路和 owner 层级。
3. 保持 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 作为 MAS 的核心可执行回路，同时保持 `CLI`、`MCP`、`controller` 作为正式操作与自动化入口。
4. 保持 `OPL Runtime Manager`、外部 `Hermes-Agent` substrate 与 MAS durable projection 的 owner split 清晰；维护者细节继续留在 reference / program 层。
5. 把“医学论文质量 + 长时间全自动驾驶优化”正式收口到 `MAS` 单项目主线，由 `controller_charter / runtime / eval_hygiene` 共同承担 owner；`MDS` 迁移期角色继续收敛为 research backend、行为等价 oracle、上游 intake buffer。
6. 把 study charter 作为质量总合同入口；`paper evidence ledger` 与 `review ledger` 作为该合同的执行与审阅记录，统一承载主结果、`bounded_analysis`、reviewer concern 与 submission hygiene 的落地状态。
7. 把用户可见真相投影压实到 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json` 这一组 durable surface 上，让当前阶段、关键证据、阻塞、下一步、恢复点、artifact pickup 与 human gate 原因都能被同一条 `MAS` 主线读取；当前统一出口已经收口成 `autonomy_contract + restore_point + autonomy_soak_status`、`quality_closure_truth + quality_closure_basis + quality_review_followthrough` 与 `research_runtime_control_projection` 三条互补 truth。
8. 把 `StudyTruthKernel`、`RuntimeHealthKernel` 与 first-draft prose quality contract 视为当前读状态与 pre-draft quality runtime 的核心文档面；维护者先读 [Study Truth Kernel Contract](./runtime/study_truth_kernel.md)、[Runtime Health Kernel Contract](./runtime/runtime_health_kernel.md)、[Medical Manuscript First-Draft Quality Policy](./policies/medical_manuscript_first_draft_quality.md) 和 [AI-first Quality Boundary Policy](./policies/ai_first_quality_boundary.md)。
9. 把“持续学习 `DeepScientist` 方法论”收口为 `MAS` 的长期 program lane：维护者先读 [DeepScientist Latest-Update Learning Protocol](./program/deepscientist_latest_update_learning_protocol.md)、[MedDeepScientist Method Learning Disciplines](./program/med_deepscientist_method_learning_disciplines.md)、[MedDeepScientist Continuous Learning Plan](./program/med_deepscientist_continuous_learning_plan.md) 和 [MedDeepScientist Upstream Source Provenance](./program/med_deepscientist_upstream_source_provenance.md)。当用户说“学习一下 `DeepScientist` 的最新更新”时，默认启动 fresh upstream audit、decision matrix、并行 worktree 落地、验证、吸收回 `main` 和清理的完整流程；先区分“upstream learned common research discipline”和“MAS-own governance / medical-quality surfaces”，再决定哪些 lesson 进入 `controller_charter`、`runtime`、`eval_hygiene` owner 面，哪些继续留在 `MDS` 的 oracle / intake / parity companion 面。
10. 把外部 agent orchestration 学习记录作为后续编排参考入口：维护者先读 [External Agent Orchestration Learning Intake 2026-04-30](./program/external_agent_orchestration_learning_intake_2026_04_30.md)，只吸收可加强 MAS 长期自治、work-unit 状态、隔离 workspace、retry/backoff/reconciliation、observability、hosted worker trust boundary、structured handoff、evidence-over-claims 与 AI reviewer gate 的合同或模板。继续学习时按该记录的 `Continued Learning Saturation Protocol` 执行：固定 source SHA、记录新增 source file coverage、分类 adopt/watch/reject，并在只剩外部 owner、tracker-specific mechanics、generic persona routing、marketing/product lifecycle、non-medical QA label、cryptographic identity runtime 或重复表述时，把当前 snapshot 标记为 `MAS-actionable saturated`。
11. 把近期 open-source Auto Research 项目族学习记录作为 PaperOrchestra 相邻参考入口：维护者先读 [Open Auto Research Learning Intake 2026-05-04](./program/open_auto_research_learning_intake_2026_05_04.md)。PaperBench-style hierarchical rubrics、PaperQA2-style scientific literature evidence graph、STORM/Open Deep Research-style perspective-first evidence compression、LangGraph/OpenHands/SWE-agent-style runtime trajectory proof、AI-Scientist-v2 / AutoResearchClaw-style candidate path graph 已落成 MAS-owned read-model，并通过 `study_progress`、`workspace-cockpit`、`product-frontdesk` 和 MCP 只读投影暴露 ready / blocked / needs_review 与下一步动作；`open_auto_research_projection` 当前是 read-only status surface，读入口只走 `build_*`，正式 artifact materialization 必须由显式 controller/runtime authority 入口承担。rubric score、trajectory replay 和 candidate path decision 只能作为 calibration / observability / planning evidence，不能替代 `publication_eval/latest.json`、`controller_decisions/latest.json`、`study_runtime_status`、study truth 或 submission readiness owner；这些 lesson 只能落到 MAS `Quality OS`、`Evaluation OS`、`Runtime OS`、`Artifact OS`、`Observability OS` 或 operator projection，不能把外部 framework、skill pack、provider runtime、generic role library、non-medical benchmark 或 auto-paper generator 提升为 MAS study truth、publication owner、controller decision owner 或 artifact authority。DM002 真实 study soak 已在 `002-dm-china-us-mortality-attribution` 上完成：controller-authorized soak 只写 OAR read-model source artifacts 与 `artifacts/runtime/open_auto_research_soak/latest.json`，四类 capability 投影为 `3 ready / 1 needs_review / 0 blocked`，`study_progress` 读入口仍不创建 `open_auto_research_projection/latest.json`，`product-frontdesk`、`workspace-cockpit` 与 MCP 均能显示四个下一步动作；当前 blocked verdict 来自 AI reviewer required、publication gate blocked 与 runtime recovering 这些论文/runtime truth，不是 OAR repo-level 功能缺口，也不构成 submission-ready 声明。
12. 当前 mainline 收口记录见 [Plan Completion Ledger](./program/plan_completion_ledger.md) 的 `2026-05-04-mas-mainline-closeout-cleanup`：OAR/DM002 与 portable supervisor 相关 repo-level 能力保持 landed truth；重复 DM002 closeout 提交已进入远端历史，不做历史重写；`.sentrux` baseline refresh 按外部结构基线 lane 处理，本地 mainline 通过后续纠偏提交恢复到 closeout 前 baseline；`mas-delivery-v2-integration`、`mas-root-cockpit-dirty-reconcile`、`mas-external-sentrux-baseline-preserve` 与 `mas-v6-*` 仍是显式保留的外部活跃 lane。
