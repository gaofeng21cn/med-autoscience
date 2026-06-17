# 不可变约束（Invariants）

Owner: `MedAutoScience`
Purpose: `stable_invariants`
State: `active_policy`
Machine boundary: 本文是人读不可变约束。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、runtime/controller durable surfaces、真实 workspace artifact、owner receipts 和 repo-native verification。

以下约束是仓库运行语义的最低不变集，任何变更都不得破坏。

## 运行真相与默认入口

- repo-tracked contract、durable surface、stable runtime / controller surface 和 generated artifact 是当前权威；本地工具状态、历史 session、prompt、log 或 hook 只能归档到用户级状态，不得替代仓库真相。项目级 `.codex/` 与 `.omx/` 已退役。
- formal-entry matrix 固定为 `CLI`（默认入口）/ `MCP`（协议层）/ `controller`（控制面）；能力表达遵循 `policy -> controller -> overlay -> adapter` 主链路，避免旁路。
- `MedAutoScience` 对外第一身份固定为独立 medical research domain agent，单一 MAS app skill 承接稳定 capability surface；OPL handoff、product-entry manifest 与其他机器桥接只作为集成或参考层，不改写第一主语。
- 默认执行链是 `OPL/Temporal hosted autonomous runtime + Codex CLI default stage executor + MAS stable capability surface`。任务启动后，持久在线调度、唤醒、retry、resume、attempt ledger 和 worker residency 归 OPL/Temporal；`Codex CLI` 是 stage 内默认 concrete executor；Codex App 不是外围持续 driver。`hermes_agent` 只允许作为显式非默认 executor / proof lane，旧 Hermes provider 或 local carrier 只能进入 history / provenance / dev / CI / offline diagnostic 语境。
- OPL-hosted production path 必须依赖 Temporal-backed provider transport / record / dispatch stage attempt；local / legacy substrate 不能生成 MAS 医学研究 truth，也不能替代 OPL Full online readiness。
- MAS 不得新增或恢复 generic daemon、scheduler、attempt loop、queue hydration、retry/dead-letter、resume 或 worker residency owner；这些只能作为 OPL/Temporal owner route 的 refs、receipt、typed blocker 或 tombstone/provenance surface 被 MAS 投影。

## OPL 边界与标准 Agent 目标

- `OPL` 是 stage-led、以 Agent executor 为最小执行单位的完整智能体运行框架，持有 family-level session/runtime/projection、stage attempt、queue、wakeup、approval/retry/dead-letter 与 shared modules/contracts/indexes；它不把 MAS 改写为内部模块或研究 owner。
- `OPL Runtime Manager`、native helper 与高频状态索引只能缓存、探测和投影 MAS 已暴露的 durable truth surface；不得成为 MAS scheduler kernel、session store、memory store、study truth、publication gate、artifact authority、concrete executor owner，或替代 `progress_projection`、`domain_health_diagnostic`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`study_charter`、evidence ledger、review ledger。
- MAS 的目标态高于当前实现分布。当前仓内 scheduler、runner、SQLite/lifecycle、workspace/source intake、memory/artifact transport、Portal/workbench、CLI/MCP/Skill/product-entry/sidecar/status wrapper 只能作为迁移输入；不得因为已有 active caller 或当前能跑就写成长期合理。
- MAS 作为标准 OPL Agent 的长期形态是 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`。通用 transport、ledger、index、lifecycle、runner、workbench、observability 和 wrapper 必须上收到 OPL primitive / pack compiler / App shell，或收薄成 domain authority refs / diagnostic provenance path。
- MAS / OPL 下一层重构必须遵守 [MAS / OPL Agent OS 目标运行架构与重构计划](./runtime/designs/mas_opl_agent_os_target_operating_architecture.md) 的 owner split：OPL Agent OS 持有 Pack Compiler、StageRun Kernel、State Index Kernel、Route Reconciler、Lifecycle Plane、Observability Plane 和 Workbench Shell；MAS 只持有 Declarative Medical Research Pack、Medical Authority Kernel 和 domain-owned refs / receipts / blockers。Scientific Capability Registry、Light / Co-Scientist / EvoScientist / PaperSpine / ARIS / ARK / AutoSci 等外部能力不得变成默认 admission layer、第二 route table、quality owner、artifact authority、publication gate 或 memory authority。
- MAS / OPL ordinary progress 的理想 spine 固定为 [MAS / OPL 进度运行时理想蓝图](./runtime/designs/mas_opl_progress_runtime_ideal_blueprint.md) 中的 `DomainIntent -> OPL Command -> OPL Event -> OPL Transactional Outbox -> StageRun / ToolInvocation -> MAS OwnerAnswer -> Derived Projection`。新增或保留 surface 只要承担 command log、event log、transactional outbox、fixed-point reconcile、StageRun lifecycle、human gate transport、state index、workbench shell 或 observability transport，就必须归 OPL primitive；只要承担 medical policy、owner receipt、typed blocker、quality verdict、artifact/source/memory authority 或 route-back/human answer consumption，就必须归 MAS authority surface。
- `mas_mds_module_boundary_audit_report` 和 `mas_mds_architecture_owner_boundary_report` 是这条 progress spine 的结构 fitness function。任何 MAS group / layer 声称 `command_log`、`event_log`、`transactional_outbox`、`fixed_point_reconciler`、provider admission、attempt lifecycle、state index、workbench shell、tool selector 或 capability runtime authority，或打开对应 private capability flag，都必须 fail closed；只允许 MAS 暴露 `policy_adapter`、`owner_callable_adapter`、`authority_result_validator`、`body_free_diagnostic_projection`、`derived_projection`、`domain_authority_function` 或 `tombstone_or_provenance` 角色。
- 通用 lifecycle substrate 归 OPL / shared family layer：stage attempt、queue、retry/dead-letter、resume、attempt ledger、locator/index、restore/retention shell、generic memory/artifact transport、observability 和 App/workbench shell。MAS 只能把这些 surface 读成 refs、receipt、typed blocker、no-forbidden-write proof 或 diagnostic projection；它们不能生成医学研究 truth、publication quality verdict、artifact mutation authorization、memory accept/reject verdict 或 source readiness verdict。
- 文档和计划必须先设理想态，再找差距；差距不是妥协清单。处理清楚 active caller、替代 surface、provenance 和必要证据后，旧模块、旧接口、旧测试、旧目录、旧文案和兼容面默认删除、archive 或 tombstone。

## MAS Domain Authority 与 AI-first 质量

- MAS 必须持有无法声明化的医学 authority function：publication quality verdict、AI reviewer-backed quality decision、artifact mutation authorization、publication-route memory accept/reject、source readiness verdict、owner receipt signer 或必要医学 helper implementation。缺少接口、active caller、不能上收原因、receipt/blocker/ref 输出边界和 no-forbidden-write 证据时，必须作为功能/结构差距处理。
- Retained Medical Authority Kernel 的机器读根是 `contracts/authority_kernel_inventory.json`，生成入口是 `src/med_autoscience/authority_kernel_inventory.py::build_authority_kernel_inventory`。新增或保留 MAS authority function 时，必须在 inventory 中列出 category、owner、active caller refs、allowed writes、forbidden authority、output refs、cannot-lift-to-OPL reason 与 retirement gate 或 upcollect target；generic runtime / OPL substrate owner 不得被列为 MAS retained authority。inventory presence 只表示 `inventory_landed_physical_thinning_pending`，不能被写成 authority fully retired、production-ready、paper-line progress、publication-ready 或 artifact mutation authorized。
- AI-first 质量判断必须由 AI reviewer / author artifact 持有；schema、gate、scorecard、audit 只能持有结构、证据引用、机械完整性与阻塞投影。缺少 `assessment_provenance.owner=ai_reviewer` 的 `publication_eval/latest.json` 不得驱动 reviewer-first ready、bundle-only remaining、finalize-ready 或 submission-facing 质量闭环。
- Hypothesis portfolio / evidence pack 只能作为 MAS-owned 研究探索和证据审计 shape。Co-Scientist 式 generation、reflection、ranking、Elo、proximity、evolution 或 meta-review signal 都是 current-owner-native JIT affordance / reviewer-briefing 输入；`next-delta tournament`、`bounded micro-candidate generation`、`critique-as-repair-hint`、`reusable lesson extraction`、`triggered meta-review` 和 `opportunistic knowledge prefetch` 默认可用但不默认运行，只能在当前 owner / gate 显式声明或由 current delta 形态隐含需要时帮助 route 更快选择下一 owner action、帮助 reviewer / auditor 更快发现缺口、帮助 memory 复用失败路径。它们不得替代 source readiness verdict、AI reviewer / auditor quality gate、publication gate、human/expert gate、artifact authority、memory accept/reject decision、owner receipt 或 stable typed blocker；也不得变成 admission gate、route blocking layer、quality closure、publication readiness、paper progress、production-ready 或真实 paper-line closeout。
- AI reviewer-backed `publication_eval/latest.json` 只有在 reviewer OS currentness proof 覆盖当前 canonical manuscript surface（`paper/draft.md`、`paper/manuscript.md` 或 `paper/build/review_manuscript.md`）且 digest/时间戳不陈旧时，才能关闭 `return_to_ai_reviewer_workflow` 的 required output；否则 materializer/dispatcher 必须视为 pending，repeat suppression 不得吞掉复评。
- `allow_write` 必须按写面拆语义：publication gate 的 `allow_write=false` 只阻止下游投稿包、bundle、submission proofing、`current_package` 和 delivery mirror 写入；MAS managed runtime worker 在 controller-authorized analysis-campaign/write work unit 下仍可修改 canonical `paper/` 修订面。
- 投稿包、submission-ready 或 finalize 后的用户、导师、审稿反馈是同一 study 的重新激活信号；必须先写入 durable revision intake，再通过 MAS-controlled relaunch/resume 接管 canonical paper surface 并重新生成投影包，不得让前台直接修改 `manuscript/current_package/`。
- 大型 public data 默认保持 remote-only；只有 durable study charter 或 analysis plan 明确用途、体积预算、复用位置与清理/保留策略后，才允许下载或物化完整资产。

## Read Model、票据与恢复

- `study_macro_state/latest.json` 是用户宏观状态的唯一 read model，用户可见投影固定从 `writer_state/user_next/reason` 派生；缺少 canonical macro state 或出现 writer 冲突时必须 fail-closed 为 `inspect/conflict`。
- `owner_route` 是 `scan -> consume -> execute-dispatch -> rescan` 的唯一执行票据。request handoff、default executor dispatch 和执行端都必须校验 `route_epoch/source_fingerprint/next_owner/allowed_actions/idempotency_key`，旧 dispatch 文件不能绕过 workspace-level consumer latest。
- 稳定控制面只承认 `macro_state`、`owner_route`、`receipt_or_blocker` 和 `evidence_refs`。细分 runtime/status reason、supersession reason、publication supervisor phase、operator/workbench 文案和 projection-local status 只能作为 diagnostic/read-model detail 或 typed blocker payload，不得单独授权执行、恢复、写 artifact、刷新 publication eval 或关闭质量门。
- Runtime health append 只有在显式 `source_signature` 相同的情况下幂等返回 existing diagnostic event；没有 OPL lifecycle proof 的 recover/launch/release/escalation 类事件不得写成 MAS lifecycle 事实或消耗 retry budget。retry/dead-letter、attempt ledger、worker liveness、canonical runtime action 和 runtime lifecycle owner 均归 OPL/Temporal，MAS 只能投影 body-free diagnostic refs、owner receipt、typed blocker 或 route-back evidence。
- 文件生命周期治理不得从 cleanup plan 反向推断 study truth；终局止损文件生命周期 plan 只能由 materialized macro state 授权，物理 apply 仍要求 manifest、sha256、restore index 与 restore proof。
- lifecycle refs SQLite store 只做 refs index、read model、receipt 和幂等检索，不替代 paper/manuscript/package、publication eval、controller decision、user intervention memory、restore metadata 或 dataset manifest。
- 开发 checkout 只保存 repo source、docs、schema/contract、locator/index、receipt ref、restore/retention policy 与 authority-function descriptor。真实 workspace state、runtime artifact、receipt instance、paper/package/export artifact、临时 build/cache/venv/pycache/pytest cache/install sync 副产物必须写入受控 study workspace/runtime artifact root 或用户级 runtime state。
- `runtime/authority_functions/` 的语义只限最小 MAS authority function anchor；它不得变成 runtime artifact root、generic lifecycle engine、session store、scheduler、runner、queue、workbench 或 memory body store。
- OPL 上收通用 workspace/file lifecycle primitive 后，MAS 私有 scheduler/runner/session/workbench 残留只能作为迁移输入、domain authority refs、diagnostic provenance 或 tombstone；不得继续定义长期结构。

## MDS / DeepScientist 与 legacy 进入规则

- `MDS` 只能作为显式可选 runtime/native/review event source、backend audit、explicit archive import reference、upstream intake 或行为等价 oracle；MAS 的 `StudyTruthKernel` 持有 `canonical_next_action`、publication gate 解释、package authority 解释和 delivery state。
- `MDS` 只能作为显式可选 runtime health probe / native runtime event source；MAS 的 `RuntimeHealthKernel` 只持有 diagnostic reducer、domain blocker interpretation、owner receipt / typed blocker refs 和 legacy-compatible action hints。`canonical_runtime_action`、worker liveness、retry budget、runtime escalation lifecycle 与 allowed controller actions 的执行授权归 OPL current-control / StageRun / Observability readback；MAS 不得把这些 hint 升级为私有 runtime authority。
- MDS parity 不允许被读成科研记录降级：核心科研审计必须继续由 MAS 研究 evidence pack、negative / failed-path ledger、decision trace、artifact lineage / reproducibility refs、AI reviewer / auditor record、owner receipt 或 stable typed blocker 承担。旧 MDS daemon residency、GitOps state management、interactive artifact mutation UX、WebSocket terminal attach 和 workspace-local service 是 retired 或 OPL-owned product/runtime direction，不是 MAS 当前能力缺口。
- truth/gate/status 或 liveness/recovery 事故必须同时落 reducer rule、fixture test 与 runbook entry。后续 MDS / DeepScientist 相关能力只能沿 owner matrix、strangler refactor 和 architecture fitness functions 进入。
- `mas_mds_architecture_owner_boundary_report` 是 architecture owner boundary fitness function。entry projection、observability、MDS backend/oracle 或 runtime diagnostic adapter 不得声明或替代 `study_truth`、`scientific_quality`、`medical_writing_quality`、`publication_readiness`、`submission_authority`、`artifact_authority` 或 `user_visible_next_action`；也不得声明或替代 OPL-owned `runtime_health`、`canonical_runtime_action`、attempt ledger、worker liveness、retry/dead-letter 或 runtime lifecycle。
- 重新打开默认 dependency、未带 provenance/parity proof 的 physical absorb、未带 rollback surface 的 owner switch、以及用 MDS mechanical oracle 替代 MAS AI reviewer / controller authority 的变更都必须 fail-closed。

## 工程方法

- 不采用降级处理、兜底方案、临时补丁、启发式方法、局部稳定化手段，避免以非严谨通用算法的后处理补救作为主策略。
- 重大变更必须在独立 worktree 中完成，保持可追溯与可回滚。
- 一旦目标 runtime topology 已明确，新增投入默认服务目标形态；旧 substrate 只允许作为迁移桥、回归基线或 provenance 存在。

## 文档与结构

- `docs/project.md`、`docs/architecture.md`、`docs/invariants.md`、`docs/decisions.md`、`docs/status.md` 是核心骨架。
- 文档按 `active/`、`public/`、`product/`、`runtime/`、`delivery/`、`source/`、`policies/`、`specs/`、`references/`、`history/` 分类收口，不得平铺堆放；旧 `program/` 与 `capabilities/` 只作为 `docs/history/**` 中的迁移来源或 provenance 目录名出现。
- 理想态差距和开发计划必须按目标态拆分 `功能/结构差距` 与 `测试/证据差距`；现有通用功能面应由 OPL 承担时，即使可运行，也写成功能/结构差距。
- `当前实际` 只能作为迁移起点、风险和证据来源；不得反向约束理想态，不得把现有私有实现包装成长期设计。
- `contracts/` 是机器可读 contract root；模块边界 contract 归入 `contracts/modules/`，叙述性说明留在 `docs/`。
- `docs/**` 是中文内部开发与维护参考；稳定路径优先使用无语言后缀 `.md` 承载中文 canonical 内容。
- 根层 `README*` 是否保留公开双语入口，由产品分发和 public 需求单独决定。

## 验证

- 统一验证入口为 `scripts/verify.sh`。
- 不带参数的 `scripts/verify.sh` 是本地 smoke 入口，负责 sanity 与 fast tests，不代表完整回归。
- `scripts/verify.sh regression` 是显式回归入口，默认由 advisory/nightly 承接。
- `scripts/verify.sh ci-preflight <base-ref>` 是 push CI 入口，必须基于 repo-tracked preflight contract 展开变更面检查，并与 build 共同保护 `main` / `development`。
- `regression`、`display`、`submission`、`family` 与 `meta` lane 由 advisory/nightly 承接，不回灌到 push quick-checks。
- `smoke`、`ci-preflight` 与 `full` 的耗时预算只用于观察和提醒；duration drift 与相对基线百分比变化通过 advisory run log、summary artifact、只读 history summary 或 release/full 记录暴露，不得成为 push quick-checks 的新增阻塞项。
- 修改 machine-readable contract surface、测试入口或运行语义时，至少补跑 `make test-meta`；纯叙述性 docs-only 变更按 `documentation_review_only` 处理。
- Python / pytest 验证必须通过 clean runner 路由 bytecode、`uv sync` project venv、pytest cache 与仓库外稳定 `UV_CACHE_DIR`；开发 checkout 不应产生 `.venv`、`__pycache__`、`.pytest_cache`、`.uv-cache` 或 `*.egg-info` 副产物，也不得让 provider stage 继承用户全局 uv cache 后因宿主权限/沙箱漂移阻断 owner callable。默认 short-lived runner 临时目录不得承载可复用依赖缓存；需要 DHD/provider/MCP 长驻或重复调用复用时，必须显式设置 `MAS_CLEAN_RUNNER_REUSE_ENV=1`，可选用 `MAS_CLEAN_RUNNER_REUSE_ROOT` 指向 checkout 外受控目录，runner 将在该根下复用 `venv`、`uv-cache`、`pycache`、`egg-info` 与 sync marker，并拒绝 checkout 内复用根或 `MAS_CLEAN_RUNNER_EGG_INFO_BASE`。
- Study runtime 的 analysis bundle 准备必须修复将被 worker 实际使用的 study workspace Python；不得通过创建或依赖 MAS checkout 内 `.venv` 来伪造 ready 状态。
