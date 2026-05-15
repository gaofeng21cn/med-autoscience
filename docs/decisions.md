# 关键决策记录

## 2026-05-15：完成态消费、AI reviewer provenance 与 owner handoff 必须进入 transition matrix

- 决策：MAS 论文控制面把三类真实卡死模式纳入 domain transition table / matrix tests。第一，DM002 这类 reviewer rebuttal route coverage 已 `coverage_complete=true`、11/11 route covered、active upstream repair 为 0 且 publication gate clear 时，旧 reviewer-revision/task-intake work unit 必须让位给 finalize / bundle-stage owner，不能继续派 `review_matrix` / `action_plan` coverage 检查；bundle-stage finalize 也不能继续沿用旧 `publication_gate_blocker_review` 这类 review work unit，必须投到明确的 submission authority / delivery sync closure。第二，DM003 这类 gate clear 但 `publication_eval` 仍是 mechanical projection 且 `ai_reviewer_required=true` 时，必须先回 AI reviewer workflow，不能被 active runtime 或 finalize-looking action 抢跑。第三，Obesity 这类 AI reviewer 已给出 blocked verdict / must-fix gaps 且 gate 仍 blocked 时，必须按 publication gate blocker / bounded repair 处理；如果旧 work unit 已 `owner_handoff + terminal_consumed=true`，runtime prompt 不能继续携带旧授权重新执行同一指纹。
- 理由：三篇真实 paper line 证明问题不是 Codex CLI 不会执行明确指令，而是 MAS 分散判断没有把“论文证据面已经完成/需要下一个 owner/仍被 gate 真阻断”消费成下一条 transition。局部 completion receipt、active run、controller decision、publication eval、task intake 和 lifecycle handoff 任何一层抢占都会制造几十小时同 stage 打转。
- OPL/MAS 边界：OPL 以后应提供通用 state-machine runner、幂等 tick、attempt/retry/dead-letter、human gate transport、dispatch receipt 与 matrix runner；MAS 继续持有 domain transition spec、AI reviewer / publication gate / claim-evidence-display / artifact authority 的解释和 oracle fixtures。OPL 可以执行 MAS 声明的 transition spec，但不能把 mechanical projection 或 provider completion 写成医学质量结论。
- 影响：新增状态转换必须先落 matrix case，再改实现。`study-state-matrix` 对单 study projection error 采用 fail-closed 行并继续投影其他 study，避免一个旧配置字段让整个 workspace transition surface 失明；旧配置本身仍是错误，不被兼容为有效配置。

## 2026-05-14：Domain transition table 集中管理，OPL 提供通用状态机执行底座

- 决策：MAS 的论文控制面状态转换必须收口成 MAS-owned domain transition table / transition matrix，而不是继续分散在 `publication_work_units`、`study_outer_loop`、`owner_priority`、`controller_authorization` 等局部判断点里各自解释下一步。transition table 的输入至少包括 `publication_supervisor_state`、publication gate report、`publication_eval/latest.json` 推荐动作、task intake、controller decision authorization 与 runtime liveness；输出必须固定 `decision_type`、`route_target`、`next_work_unit`、`controller_action`、owner、idempotency/fingerprint 和 fail-closed blocker。
- 理由：DM002/DM003/Obesity 等真实 paper line 反复暴露同类问题：状态转换概念上清晰，但实现分散会让 gate clear、bundle-stage、publishability blocked、stale authority、task-intake residue 和 runtime recovery 各层互相覆盖。集中 transition table 能把“输入状态组合 -> route/work_unit/action”的行为变成可审计矩阵，并用 table-driven oracle tests 防止同类漂移。
- OPL/MAS 边界：通用状态机执行底座、transition schema、幂等 tick、attempt/retry/dead-letter、human gate transport、dispatch receipt、transition matrix runner 和 cross-domain parity 可以上移到 OPL framework。医学研究语义不得上移：`stale_submission_minimal_authority`、`publication_gate`、`bundle_stage_blocked`、claim/evidence/display blocker、AI reviewer judgement、submission authority、paper quality 与 artifact/package authority 仍由 MAS 定义并测试。OPL 执行 MAS 声明的 transition spec；MAS 持有 domain transition table 和 oracle fixtures。
- 影响：后续控制面修复不能只补单点 if/else。凡新增或修改状态转换，必须同步更新 MAS domain transition table / matrix tests；当 OPL framework 的通用 state-machine runner 可用时，MAS 应把现有 domain transition table 作为 domain spec 接入 OPL runner，而不是让 OPL 重新解释医学状态。

## 2026-05-10：MAS 对齐 OPL Temporal-backed production runtime，Temporal 为 OPL 生产必需 substrate

- 决策：MAS 与 OPL 的长期托管口径从 Hermes-first 更新为 Temporal-backed OPL family runtime：`OPL Product Entry -> OPL stage-led family runtime provider -> MAS sidecar export/dispatch -> MAS domain entry/projection`。Temporal 是 OPL production online runtime 的必需 substrate；Hermes-Agent 迁移后作为可选 Agent executor adapter、显式 hosted/proof backend 或可选安装模块保留，不再作为目标 24h session/wakeup substrate，local provider 只作为 MAS direct/local diagnostics 或 OPL dev/CI/offline baseline。
- 理由：MAS 需要长期自治、human gate、retry/dead-letter、route-back 和 progress projection，但医学研究 stage、AI reviewer、publication gate、evidence/review ledger、route decision 与 artifact/package authority 必须仍由 MAS 持有。Temporal/provider 可以改善运行可靠性，但不能成为第二研究 truth owner。
- 影响：`medautosci sidecar export|dispatch` 继续是 OPL provider 到 MAS owner surface 的受控桥接；OPL/Temporal/Hermes/local provider 只能 enqueue、dispatch、signal、query、投影 attempt/receipt，不得写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper package、evidence ledger、review ledger 或 artifact gate。2026-05-10 Hermes-first MAS sidecar bridge 决策保留为迁移背景，但后续新投入按 Temporal-backed production runtime 解释。

## 2026-05-10：Hermes-first OPL family runtime 与 MAS sidecar bridge

- 状态：已被同日 Temporal-backed production runtime 决策 supersede。保留本段用于解释 Hermes-first sidecar bridge 的迁移背景和当前 legacy provider 口径。

- 历史决策：当时的迁移假设是让外部 `Hermes-Agent` 由 OPL 管理，承担常驻 gateway、cron/webhook wakeup、session store、delivery/notification、approval transport 与 family queue tick；OPL 持有 typed family queue / dispatch contract；MAS 持有 study truth、publication judgment、quality gate、artifact/package authority 和 domain recovery decision。
- 当前生命周期处置：这不是当前目标 topology。当前 OPL-hosted production path 以 Temporal-backed OPL family runtime 为生产必需 substrate；`Hermes-Agent` 只保留为 explicit optional Agent executor adapter、provider/proof lane 或历史迁移背景。任何当前文档或代码入口都不得把本段写成 Full online target。
- 保留价值：本段只解释 `sidecar export|dispatch` 为什么成为 OPL provider 到 MAS owner surface 的受控桥。sidecar 仍禁止写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper package 或 artifact gate；这些 truth 只能由对应 MAS owner surface 产生。MAS standalone/local diagnostics 仍可使用 MAS-owned local scheduler；Full online readiness 由 OPL 侧 Temporal provider readiness 判定。

## 2026-05-10：MAS 作为 OPL stage-led framework 上的独立 domain agent

- 决策：MAS 的 OPL 对齐口径固定为：MAS 是可直接由 Codex App skill 调用、也可由 OPL stage-led family framework 托管的独立 medical research domain agent。OPL 只持有 stage descriptor discovery、typed queue、wakeup、handoff、receipt、approval/retry/dead-letter、trace/projection 和 parity；MAS 持有医学 stage pack、prompt/skill、study truth reducer、evidence/review ledger、AI reviewer、publication gate、route decision 和 artifact/package authority。
- 理由：MAS 的价值在医学研究自治与论文质量闭环。如果把研究路线、质量判断或 publication readiness 上收到 OPL，会制造第二 truth owner，也会削弱 Codex CLI 在 MAS stage 内的自主探索能力。OPL 应提供 durable framework 能力，不能成为 MAS 的领域大脑。
- 影响：direct MAS skill path 保持一等入口；经 OPL 调用时必须回到同一套 MAS-owned CLI/MCP/product-entry/controller/stage surface。后续流程优化优先改 MAS stage policy、prompt、skill、AI reviewer、quality gate 和 route/decision receipt；不得把医学研究思路写成 OPL 机械脚本分流。

## 2026-05-11：OPL 是完整 stage-led 智能体运行框架，MAS 是医学论文 domain agent

- 决策：OPL 的新定位固定为完整智能体运行框架，而不是只做入口聚合或 product-entry facade。OPL 可以作为外部依赖承载 MAS：它负责 stage attempt、provider abstraction、queue/wakeup、retry/dead-letter、human-gate signal/query、attempt receipt、projection、shared lifecycle/index/restore primitives 和跨 domain skeleton。`Stage` 是大型任务步骤；Agent executor 是 stage 内最小执行单位，`Codex CLI` 是当前第一公民 concrete executor。
- 理由：MAS 已经在 monolith closeout 中验证了医学论文 domain 的 runtime、lifecycle、artifact、restore、stage knowledge 和质量闭环经验，但这些“智能体运行外围”不应长期由 MAS 私有维护。上收 OPL 能减少 MAS/MAG/RCA 重复底座，同时保持 MAS 对医学研究、论文质量和交付 authority 的唯一所有权。
- 影响：MAS 文档必须把 OPL 作为可依赖运行框架表达，同时继续禁止 OPL/Temporal/Hermes/local provider 写 MAS study truth、publication judgement、quality gate、current package、evidence/review ledger 或 artifact authority。MAS direct skill / local diagnostic path 可以独立运行；一旦进入 OPL-hosted production path，Temporal readiness 是必需前提。MAS 是 OPL family 中的医学论文/研究 domain agent；旧 MDS/DeepScientist/Hermes-first/外部 runtime 完善线只能作为 history、provenance、optional executor/provider adapter、backend audit、upstream intake 或 parity reference 出现。

## 2026-05-10：Autonomy continuation ticket 成为 read-model 到执行闭环的桥

- 决策：`slo_status=breach`、`runtime_liveness_status=parked`、`runtime_decision=blocked` 或 `safe_reconcile_ready` 不能只停留在 read model。只要 controller 未给出 `stop_loss` / terminal stop，且没有 hard human confirmation gate，MAS sidecar export 必须生成一条幂等 `pending_family_tasks[]`，默认 task kind 为 `runtime_supervisor/reconcile-apply`。
- 理由：成熟长期 agent 工程的核心不是常驻进程本身，而是 durable identity、持久状态、可恢复 task、checkpoint、retry/dead-letter、human gate 与事件唤醒。Temporal 强调 crash-proof durable execution；Pydantic AI durable execution 明确面向 restart、long-running 和 human-in-the-loop；Cloudflare Agents 也把长期 agent 表达为 durable identity + SQLite state + schedules/fibers，而不是一直运行的进程。MAS 对应落点是把“发现了问题”转成 domain-owned executable ticket，再由 OPL provider 在线底座唤醒、入队和派发。
- 影响：`pending_family_tasks` 是 MAS 授权 OPL 入队的唯一跨仓自动推进桥。OPL 可以 enqueue / retry / dead-letter / notify / dispatch，但不能解释医学质量或直接写 truth。MAS sidecar dispatch 收到 `runtime_supervisor/reconcile-apply` 后，必须回到 MAS 自己的 `runtime_supervisor_reconcile` owner chain，执行 `scan -> consume -> execute-dispatch -> rescan`，并用 receipt 说明是否启动 Codex worker、是否 blocked、是否 no-op 或是否需要 human gate。

## 2026-05-10：Paper Progress SLO 成为自动推进闭环的最高运行目标

- 决策：MAS 自动运行的最高 SLO 固定为“论文是否产生可验证增量”，而不是 worker 是否 live、controller 是否写 packet、gate audit 是否刷新。有效进度只认 canonical manuscript/table/figure/result 变化、submission source/current package freshness proof、AI reviewer judgement 更新、publication gate replay 后 owner 前进。live worker 超过 grace window 仍无 meaningful artifact delta 时，必须投影为 `live_no_paper_delta` / `paper_progress_stall`，并进入 controller-owned redrive 或 owner handoff。
- 决策：`paper_progress_reconciler` 成为 paper-line 推进判断的单一 controller-style reconcile surface。它每次 tick 从当前 truth surfaces 重算 `desired_state`、`current_state`、`delta`、`decision` 与 `action_receipt`，不依赖旧 repair packet、旧 handoff 文案或上一轮补丁记忆。`runtime-supervisor-reconcile` 必须携带该 receipt；dry-run 不 dispatch，apply 只在 callable owner、fresh source fingerprint、非 human gate 与可解释 owner route 成立时写 outbox receipt。
- 决策：Paper work unit 采用 transaction contract。每个 work unit 必须能在 `owner_callable_registry` / owner route / batch lifecycle 中解释 `owner`、`callable_surface`、`required_inputs`、`required_outputs`、`artifact_delta_predicate`、`gate_replay_target`、`idempotency_key` 与 `source_fingerprint`。terminal success 需要同时有 owner receipt、required output、artifact delta 或 gate replay result；repeat suppression 只能阻断重复派单，不能阻断 handoff 到下一 owner。
- 决策：work-unit outbox 是幂等与安全重试的唯一落账面。`paper_work_unit_outbox` 对相同 `idempotency_key` + 相同 intent 返回等价 replay receipt；同 key 不同 intent fail-closed；同 `source_fingerprint` 已启动 worker 时写 `duplicate_source_fingerprint` receipt，不重复启动 worker，也不阻断 owner handoff / gate replay。SQLite sidecar 表 `paper_work_unit_receipts` 只索引 receipt 和 cursor，不成为 paper/publication authority。
- 决策：owner callable registry 是 owner 可执行性的机器锚点。当前注册 owner 包括 `MAS/controller`、`ai_reviewer`、`publication_gate`、`quality_repair_batch`、`gate_clearing_batch` 与 `delivery_sync`；`owner_callable_surface_missing` 只能成为 controller-consumable blocker 或 repo-level missing callable blocker，不能把 `requires_user_input=false` 的 `waiting_for_user` 投影成真实用户等待。
- 决策：`PaperProgressState` 的用户面状态固定为七类：`progressing`、`awaiting_controller_redrive`、`blocked_controller_route`、`awaiting_callable_owner`、`awaiting_human`、`downstream_only`、`terminal_delivered`。所有进度入口至少投影 `actual_write_active`、`package_delivered`、`meaningful_artifact_delta`、`next_owner`、`why_not_progressing` 与 `safe_reconcile_command`；Progress Portal workspace dashboard 只做 human-facing projection，不写 truth。
- 决策：runtime retry budget exhausted 不再直接等于 external supervisor。若 paper work unit、owner route、source fingerprint、quality/publication gate 可解释，reconciler 先给 `MAS/controller` recovery lease reset / redrive；只有 route 缺失、callable 缺失或 repo-level owner gap 无法解释时，才暴露 repo-level blocker。Obesity 这类 `supervisor_only=true` 且有 artifact delta 的 live worker 显示为 `supervisor_only/live_quality_repair`，delivery missing 保持 downstream。
- 理由：三篇论文的共同失败模式是控制面有活动但论文无增量。成熟控制面经验也指向同一结论：Kubernetes controller 通过 current/desired state reconcile 推进状态；AWS idempotent API 通过 caller intent token 让 retry 安全，并用 timeout / retry / backoff / jitter 控制重试风暴；Temporal Activity 要求可恢复业务 activity 自身具备 timeout、heartbeat、retry 与 idempotency；SRE SLO adoption 要把 SLO 贴近用户旅程。MAS 的用户旅程就是论文资产是否产生可验证增量，对应落点是 owner route、idempotency key、source fingerprint、artifact delta predicate 与 gate replay proof。
- 影响：DM002 的 retry-budget / controller route 卡点应被投影为 controller redrive 或唯一 repo-level blocker；DM003 的 `blocked_turn_closeout_waiting_for_owner` / `owner_callable_surface_missing` 在 `requires_user_input=false` 时由 registry repair 或 MAS/controller 消费；Obesity 的 AI reviewer queue 由 callable `ai_reviewer` 消费，publishability 未放行前 delivery 缺失只能作为 downstream blocker 展示。repo capability landed 不等于 live controlled apply completed；真实三篇论文仍要在 repo gates 全绿后用 artifact delta、gate replay、owner 前进和 freshness proof 单独验收。
- 参考：[Kubernetes controller](https://kubernetes.io/docs/concepts/architecture/controller/)；[AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)；[AWS timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter)；[Temporal Activity definition](https://docs.temporal.io/activity-definition)；[Google SRE SLO adoption](https://sre.google/static/pdf/SloAdoptionAndUsageInSre.pdf)。

## 2026-05-09：MAS 持有 supervision scheduler contract，local 成为默认 adapter

- 决策：`MAS supervision scheduler contract` 是 MAS standalone/local diagnostics 的 outer supervision owner；`local` 是 MAS 本地默认 scheduler adapter，macOS 落到 MAS-owned LaunchAgent。OPL Full online runtime 的 family-level wakeup 由 OPL family runtime provider 承担，再通过 MAS sidecar dispatch 进入 domain owner surface。MAS 的运行架构按 Runtime Core、Supervisor Scheduler、Product Projection 三层表达：Runtime Core 由 `MAS Runtime OS` / `mas_runtime_core` 持有；Supervisor Scheduler 只负责按 cadence 唤醒 MAS-owned tick、记录 job/run receipt、暴露 SLO / drift；Product Projection 只读展示进度、日志、阻塞和下一步。
- 理由：fresh repo 状态显示 scheduler 应承担单一、可替换的 adapter 工作：生成 tick script、注册/更新/触发/删除 job、提供 job registry/latest run/session projection 和 liveness。它不持有研究执行、turn continuation、publication judgment、quality authority 或 study truth。成熟工程实践也要求 scheduler 只生产可审计触发，幂等、并发、missed-run、receipt 和 migration 由系统 contract 明确表达。
- 影响：`runtime-supervision-status`、`runtime-ensure-supervision` 与 `runtime-remove-supervision` 在 MAS standalone/local diagnostics 中默认走 MAS-owned `local` adapter；OPL Full package、runtime tray 和 installer 将 family runtime provider readiness 作为 Full online readiness 前置条件。两层 readiness 必须分开显示，避免把 provider 或 Hermes 写成 MAS study truth 或质量 owner。

## 2026-05-08：MAS monolith closeout 取代外部 MDS 默认运行依赖

- 决策：`med-autoscience` 是唯一日常 repo、唯一研究入口和默认 operation owner。外部 `med-deepscientist` checkout 不再是 MAS 默认 study/status/progress/cockpit operation 的运行必需依赖；保留的 MDS / DeepScientist 价值只能作为显式 backend audit、explicit archive import reference、upstream intake 或 parity oracle 出现。
- 理由：no-history physical absorb 已把 source provenance、author guard、capability parity fixtures、retained capability absorb 与 default-runtime-retirement 落到 repo-level guard；继续把 MDS 写成默认 backend 会重新制造第二 owner 和安装依赖漂移。
- 影响：未来从 MDS / DeepScientist 学习或引入能力，必须记录 source ref/hash、snapshot checksum、license refs、capability classification、remaining surface inventory、MAS owner、authority boundary、tests、parity proof 与 no-history contributor audit；classification 只允许 `mas_owned`、`rewrite_in_mas`、`fixture_only`、`retire`、`external_source_archive_only`。`publication_eval/latest.json`、`controller_decisions/latest.json`、`study_runtime_status`、`runtime_watch`、paper/manuscript/current_package 与 artifact rebuild proof 不得被 MDS 写回或授权。

## 2026-05-07：Controller work-unit evidence adoption 只识别受控证据，不改变 AI-first 质量 owner

- 决策：controller work-unit evidence adoption 固定为 objective evidence / freshness / currentness 的识别与路由机制，不成为论文质量、投稿 readiness 或 AI reviewer judgement 的替代 owner。`cold_archive`、`report_history`、runtime report store 和 restore proof 只能作为 restore / report evidence source；它们可以证明某个受控 work unit、artifact 或 runtime event 曾经发生，也可以参与 currentness/freshness 判断，但不能直接关闭 `publication_eval/latest.json`、`controller_decisions/latest.json`、AI reviewer workflow 或 submission-facing quality gate。若 worker 已完成受控 work unit，supervisor 的下一步是 gate recheck、owner route 前进或转交下一 owner，不得重复派发同一 work unit。
- 理由：DM002/DM003 的 fresh 只读状态显示，两条线当前都需要从 `study_runtime_status`、`study_progress`、`runtime_supervision/latest.json`、`publication_eval/latest.json` 与 `controller_decisions/latest.json` 判断是否 live、是否 stale、是否需要人工介入；repo 修复或 lifecycle/archive proof 成立不等同于 study 已恢复。机械脚本若把 archived report、history replay 或 fresh timestamp 当成质量 authority，会重新制造“同一 work unit 被反复执行”或“旧包被误读为当前包”的风险。
- 影响：runtime supervisor、consumer 和 execute-dispatch 只能采用带 stable work-unit fingerprint、owner、required output surface 与 freshness/currentness proof 的 evidence。NF-PitNET 003 不因本次 DM002/DM003 风险核对被触碰；DM002/DM003 必须用 fresh runtime truth surfaces 判断 live managed runtime、stale supervision、no-live-worker 和 publication gate blocker。前台检测到 live managed runtime 或 `execution_owner_guard.supervisor_only=true` 时进入 supervisor-only；若只是 repo-side fix landed、archive proof verified 或 report history 可恢复，仍只能表述为平台/证据面状态，不能宣称 study 已恢复或论文包已放行。

## 2026-05-06：宏观状态、owner route 与文件生命周期进入同一 current-truth 合同

- 决策：MAS 用户宏观状态固定为 `writer_state/user_next/reason` 三段短枚举，materialized surface 是 `artifacts/runtime/study_macro_state/latest.json`；`owner_route` 固定为 `scan -> consume -> execute-dispatch -> rescan` 的唯一执行票据。request handoff、default executor dispatch 和 executor 都必须校验 route、allowed action 与 idempotency key。终局止损文件生命周期采用 `terminal_study_file_lifecycle_plan` dry-run surface，只有不可重开 `stop_loss` 才能标记 runtime history 精简候选，物理 apply 仍要求 manifest、sha256 与 restore proof。
- 理由：近期 DM001、DM002、NF002/NF003 与 stop-loss workspace 的故障显示，runtime liveness、publication gate、AI reviewer、dispatch executor 和 storage cleanup 若各自使用局部判断，会在修复一层后暴露下一层漂移。成熟控制面把 current/desired state 收敛、幂等重试 token、sidecar index 和 manifest/checksum preservation 分开处理；MAS 的落点是文件 authority + reducer + owner route + SQLite sidecar receipt。
- 影响：`study-state-matrix` 优先读取 materialized macro state；`study_progress` 默认读不再物化 AI-first ledgers；consumer request handoff 与 executor 都受 owner route gate 约束；runtime health 显式 source signature 幂等；cleanup apply 消费 retention report 时必须重新校验 target sha256。`user_next=none/reason=stop_loss/reopen_allowed=false` 可以开启 terminal file lifecycle dry-run，但不能裸删历史文件。
- 参考：[Kubernetes controller reconcile loop](https://kubernetes.io/docs/concepts/architecture/controller/)；[AWS Builders Library idempotent API client request token](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)；[SQLite Application File Format](https://www.sqlite.org/appfileformat.html)；[RFC 8493 BagIt manifest/checksum contract](https://www.rfc-editor.org/rfc/rfc8493)。

## 2026-05-05：Repo Markdown / README prose 不再由 pytest 锁定措辞

- 决策：repo-tracked Markdown / README prose 进入 `documentation_review_only` 分类，由人工/Agent review 负责，不再用 pytest 脚本读取文档并断言标题、链接、段落、固定短语或 intake 表格内容。preflight 对 docs-only 变更不规划 pytest 命令；workflow、配置、源码、测试、JSON/YAML/TOML contract、生成器输出、运行时模板和生成产物行为仍按对应 owner surface 验证。
- 理由：文档是接力和审阅材料，脚本锁措辞会把表达、锚点和链接变成伪 contract，导致小文案变更触发无关失败，也会诱导后续 Agent 为了测试去 patch 文档。真正需要机器门禁的是可执行行为、schema、CLI/MCP/API、reader/export/restore contract 和 runtime/product surface。
- 影响：退役现有纯 Markdown/README wording tests；`dev_preflight_contract` 保留 `documentation_review_only` 分类以显式识别 docs-only 变更，但其 planned commands 为空。后续新增测试不得重新引入 repo docs wording anchors；若文档内容需要可验证约束，应先把约束上升为结构化 contract、代码生成器、schema 或运行时资产，再测试该 contract/生成结果。

## 2026-05-05：Runtime lifecycle 历史与索引采用 SQLite sidecar，authority surface 继续保留文件形态

- 决策：MAS/MDS 的 runtime lifecycle、storage audit、watch state、run/report history 与 retention ledger 进入 SQLite sidecar 方向；SQLite 只持有可索引历史、摘要、游标、路径引用、checksum 与投影缓存，不替代 `publication_eval/latest.json`、`controller_decisions/latest.json`、`study_runtime_status`、`runtime_binding.yaml`、dataset manifest、restore index、paper/manuscript/current_package 等 authority 或交付产物。
- 理由：真实 `.ds` 膨胀来自运行态 mirror、日志、run/codex home/history/worktree 与 audit 历史产生的大量小文件，而不是 Git 源码仓本身。SQLite 官方把应用状态文件格式、pile-of-files 替代、事务更新、并发读取与小对象聚合列为成熟适用场景；Git 的 `untracked-cache`、`fsmonitor`、`sparse-index` 只能改善 Git working tree/index 扫描，不能解决 MAS/MDS 自己生成的 runtime 小文件生命周期。
- 影响：新增 runtime/storage/history 能力时，默认把“latest / canonical authority / human delivery”继续写成可恢复文件，把“append-heavy telemetry / historical report index / retention ledger / cursor pagination / compact projection”写入 SQLite sidecar。SQLite 文件必须是可重建或可导出索引层；任何需要医学质量、publication readiness、artifact authority 或 restore safety 的判断仍回到 MAS durable truth surface 和 MDS restore contract。
- 参考：SQLite Application File Format、SQLite WAL、SQLite Archive / SQLAR、SQLite small-blob filesystem benchmark；Git `update-index` 的 untracked-cache/fsmonitor 与 sparse-checkout sparse-index 文档。

## 2026-05-02：MAS AI-first Research OS 成为长线目标架构

- 决策：长线目标固定为 `MAS AI-first Research OS`。MAS 作为唯一 research / quality / publication / artifact / user-visible truth owner；MDS 已收敛为显式 backend audit、explicit archive import reference、upstream intake 与 parity oracle companion。机械系统只负责 evidence、status、completeness、blocker、projection 与 replay；AI reviewer workflow 持有科学质量、医学写作质量、publishability 与 submission-facing readiness。
- Authority anchor：AI reviewer artifacts 持有科学质量；机械系统只负责 evidence、status、completeness、blocker、projection 与 replay。
- 理由：近期论文修复证明，机械 gate 先给 ready、下游再补救会把质量风险推迟到最贵的阶段。AI-first 的真实落点应前移到 pre-draft quality runtime、AI reviewer workflow、artifact rebuild proof、operations state 与真实论文 soak，而不是在文档层增加措辞约束。
- 影响：新增架构、质量、运行、产物、观测或 MDS 吸收能力时，必须回到 [MAS AI-first Research OS Architecture](./references/mainline/ai_first_research_os_architecture.md) 的 owner / authority / proof 口径；MDS no-history absorb 只允许在 parity proof、owner cutover、rollback surface 与质量不降级证明成立后以 MAS-authored snapshot 落地。当前 no-history absorb 已关闭为 repo-level guard/parity/default-dependency-retirement；更大的 runtime core ingest、controlled cutover 或平台结构调整仍需独立 gate。本决策不新增文档 wording gate，不修改测试或 preflight contract。

## 2026-05-01：StudyTruthKernel 成为 study 级用户可见真相 reducer

- 决策：`StudyTruthKernel` 固定为 MAS study 级运行真相 reducer。`study_runtime_status` 与 `study-progress` 可以投影 shadow snapshot，但 `artifacts/truth/latest.json` 只能由显式 reconcile、controller tick 或 materialize 调用刷新。
- 理由：近期 stopped / finalize / package authority / reviewer revision / publication gate 事故证明，多个 read-model 各自解释 next action 会制造 authority drift。把 dominance rules 收口到单一 reducer，才能让 package authority、publication gate 解释、delivery state 和 human gate 输出一致。
- 影响：后续 truth/gate/status 事故必须同时补 reducer rule、fixture test 与 runbook entry；`MDS` 输出只能作为 runtime/native/review event 进入 MAS truth event，再由 MAS reducer 产生用户可见动作。

## 2026-05-01：RuntimeHealthKernel 成为 runtime liveness 与 recovery reducer

- 决策：`RuntimeHealthKernel` 固定为 `(study_id, quest_id)` 的运行健康 reducer。`runtime_health_snapshot` 负责 worker liveness、retry budget、recover/relaunch/escalate 语义；`last_launch_report` 只能保留最近动作摘要，不再作为 live worker authority。
- 理由：恢复链路曾把 stale run handle、fresh supervisor tick、daemon probe 和 worker liveness 混成一类状态，容易无限 recovering 或误报 live。运行健康必须用 event history 和有限状态机收口。
- 影响：`runtime watch --apply`、`runtime reconcile-health` 与 controller tick 才能 materialize health；runtime health 只能驱动 runtime action，不得反向覆盖 `StudyTruthKernel.canonical_next_action`、publication gate、package authority 或 delivery state。

## 2026-05-05：Supervisor request ownership 与 submission milestone parking 收口到 request-only / controller-stop 边界

- 决策：portable supervisor scan 可以生成外层可消费的 request packet，但 `publication_gate_specificity_required` 的 owner 固定为 `publication_gate`，`return_to_ai_reviewer_workflow` 的 owner 固定为 `ai_reviewer`，supervisor consumer 只写 owner handoff task、consumer packet 和 default executor dispatch。第三步 `runtime-supervisor-execute-dispatch` 只能在 prompt contract 与 forbidden surfaces 完整时调用 owner-authorized repo surface，或写明 blocked reason。对 stopped submission/finalize milestone，supervisor 只能刷新 controller-owned parked decision、确认或停止 runtime 资源，并把 repair lifecycle 写成 `state=parked` / `authority=controller_stop`。
- 理由：近期 supervisor parking 与 request queue 修复证明，如果外层 scan/consumer 直接推断 publication quality、AI reviewer judgement 或 paper package 状态，会重新制造第二 owner。外层工程代理需要的是清晰的 request owner、required output surface 和 forbidden surface，而不是替代 MAS quality/publication authority。
- 影响：`runtime-supervisor-consume`、`artifacts/supervision/consumer/*` 与 `artifacts/supervision/requests/*` 都是 handoff/request/dispatch surface；它们不得修改 `paper/current_package` 或 `manuscript/current_package`，不得放宽 quality/publication gate。`runtime-supervisor-execute-dispatch` 可以调用 `publication_gate` owner surface 物化 gate-owned `publication_eval/latest.json`，但不能合成 AI reviewer judgement；AI reviewer output 仍必须来自结构化 reviewer workflow。submission milestone parking 不授权人工 patch；后续稿件反馈仍必须走 durable revision intake 与 MAS-controlled relaunch/resume。

## 2026-05-05：Supervisor scan 采用 current truth owner-route reconcile 合同

- 决策：`runtime-supervisor-scan` 固定为 controller-style reconcile loop。它每轮先读取当前 `study_runtime_status`、`study_progress`、`publication_eval/latest.json`、`controller_decisions/latest.json` 与 `StudyTruthKernel` epoch，再产出唯一 `owner_route`。`runtime liveness`、retry budget、publication gate、AI reviewer 与 dispatch executor 都只能作为 current truth 输入或 owner action，不得各自用局部判断覆盖当前 owner。若当前 controller decision 与 publication work-unit fingerprint 对齐，且 controller action 明确要求同线 runtime redrive，no-live / retry-exhausted 只能路由给 `mas_controller`，不能升级成 `external_supervisor`。
- 理由：DM001/DM002/DM003/NF002 的连续故障显示，单点修补 stopped、package handoff、AI reviewer 或 executor 都会暴露另一层漂移。成熟控制面通常把 current state 与 desired state 的收敛放在一个 reconcile loop 中；幂等重试需要调用方意图 token；可重试 activity 必须有稳定 idempotency key。MAS 的对应合同就是 `truth_epoch + source_fingerprint + next_owner + allowed_actions`。
- 影响：`owner_route` 是 `scan -> consume -> execute-dispatch -> rescan` 的唯一执行票据。consumer 只能传播 route；executor 执行前必须比对最新 route，并拒绝 `owner_route_stale` 或 `owner_route_next_owner_mismatch`。同一 scan 即使生成多个候选 action，`allowed_actions` 也只包含当前 `next_owner` 可执行的动作；其他 action 只能留作观测或下一轮 owner，不得被同 tick executor 抢跑。runtime redrive 还必须把当前 controller decision 和同 fingerprint 的 actionable publication targets 写入 runtime authorization，避免 MDS 因缺可执行 target 把当前 work unit 再次判成 gate pending。完成态、completion evidence owner、auto-runtime parked、manual hold 与 stop-loss 都必须通过同一 route 投影，避免 stale lifecycle、publication gate 或 AI reviewer 队列重新打开已完成或已停驻论文线。
- 2026-05-15 补充：MAS-owned `domain-transition::*` fingerprint 是 controller-owned transition authority，不要求反向伪装成 `publication_eval.recommended_actions`。live Codex CLI prompt 的读取链路固定为 `domain_transition_table -> controller_decisions/latest.json -> runtime_state.last_controller_decision_authorization -> prompt`；只要 controller decision 已物化、未要求 human confirmation、fingerprint work-unit id 与 `next_work_unit.unit_id` 匹配、action type 落在该 transition 的白名单内，就可以 relay 到 runtime authorization。旧 prompt、旧 task-intake、旧 publication action 或旧 default executor dispatch 都不得覆盖这条当前 controller authority。
- 参考：[Kubernetes Controllers current/desired state reconcile loop](https://kubernetes.io/docs/concepts/architecture/controller/)；[AWS Builders Library “Making retries safe with idempotent APIs”](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)；Temporal Activity idempotency and retry guidance。

## 2026-05-01：医学稿件初稿质量前移为 manuscript-native prose 合同

- 决策：first draft 质量不再只依赖 `medical_publication_surface` 后置拦截；`study_charter.paper_quality_contract.structured_reporting_contract.first_draft_quality_contract` 与 quality OS 必须在写作前提供 IMRAD section purpose、reporting-guideline obligations、clinical question / population / timepoint / outcome / display-to-claim map，以及 manuscript-native medical journal prose 要求。
- 理由：真实稿件修订暴露出 MAS 初稿可能把 controller checklist、figure/table anchor、author-confirmation placeholder、claim-boundary 标签和 operations/review 语言带进正文。医学论文初稿必须从临床问题、研究设计、结果解释和投稿读者问题出发。
- 影响：写作 route 在判断 draft ready 前必须检查这些输入；缺少支撑时 route back 到同线写作修复或有限补充分析。`medical_publication_surface` 继续作为 safety net，而不是主写作策略。

## 2026-04-26：稿件反馈后的 stopped milestone 统一视为 revision reactivation

- 决策：已达投稿包、submission-ready 或 finalize 里程碑后，如果收到用户、导师或审稿层面的稿件反馈，必须把该反馈作为同一 study 的 `reviewer_revision` reactivation intake 处理。`stopped` 状态和 `current_package` 存在只说明旧里程碑曾经成立，不能授权 Codex 前台直接修改 `manuscript/current_package/` 后宣称完成。
- 理由：003 / 004 类 manuscript revision 暴露出重复误判风险：Agent 容易把“quest 已停车”误读成“当前包可人工小修”。这会绕开 MAS/MDS 的 study truth、claim-evidence、review ledger 和 package regeneration 链路。
- 影响：`submit-study-task` 对非 live reviewer revision 要返回 reactivation guidance；workspace AGENTS、agent-entry templates、legacy write/finalize overlays 和 invariants 都必须显式要求先 durable intake，再 MAS-controlled relaunch/resume，最后从 canonical paper authority 重新生成 `current_package`。

## 2026-04-26：初稿质量升级扫描进入 study charter 与 reviewer-first route-back

- 决策：`study_charter.paper_quality_contract` 固定新增 first-draft quality contract；写作 route 在判断 draft ready 前必须扫描已验证数据资产是否支持更强的时间点、角色/人群、中心/地理、指南对应、亚组/关联分析和现实采用约束叙事。若当前初稿过轻且不改变锁定 claim 边界，默认 route back 到 `analysis-campaign` 做有限补充分析。
- 理由：近期 manuscript 修改反馈暴露出一个系统性问题：初稿如果只按已有结果描述成稿，容易漏掉数据资产本身已经能支撑的更强 paper shape。把这类反馈上收到 MAS 合同层，可以在初稿前阻断“描述性够用”的低质量出口。
- 影响：后续 `survey_trend_analysis`、写作 route、reviewer-first 检查与 evidence/review 合同都必须先问“数据资产还能否支撑更强且可验证的论文形态”，再决定写作、有限补充分析或 human gate。

## 2026-04-26：OPL Runtime Manager 作为薄运行管理层接入 MAS projection

- 状态：已被 2026-05 的 OPL stage-led family runtime provider 与 Temporal-backed production substrate 口径 supersede。保留本段用于追溯薄管理层阶段。

- 历史决策：MAS 与 OPL 的长线对齐曾采用 `OPL Runtime Manager / opl family-runtime -> configured family runtime provider -> MAS sidecar export/dispatch -> MAS domain entry/projection` 的分层口径。当前读法应收口为 `OPL Product Entry -> OPL stage-led family runtime provider -> MAS sidecar export/dispatch -> MAS domain entry/projection`。MAS 只暴露 task registration、runtime_control projection、status/artifact locator、approval/wakeup boundary、sidecar guarded dispatch 与现有 durable truth surface；旧 `OPL Runtime Manager` 只作为历史薄管理层名词保留，不成为 MAS 研究 truth 或执行器 owner。历史 Hermes online substrate 口径只作为迁移背景；Hermes-Agent 当前是可选 Agent executor adapter / proof lane。
- 理由：这能先获得长期托管、唤醒、健康检查和跨域状态索引的收益，同时保留 MAS 自己的 study authority、publication gate 与 evidence/review ledger。若未来需要自有长期常驻 sidecar，也能沿 Runtime Manager 的 adapter/projection contract promotion，而不重写 MAS domain truth。
- 影响：后续涉及 OPL handoff、runtime_control、product-entry manifest、status projection、sidecar export/dispatch 或 hosted lane 的文案，都必须使用 OPL stage-led family runtime provider / hosted integration 口径；MAS durable truth surface 仍是唯一研究真相。

## 2026-04-21：公开主语固定为独立 domain agent，单一 app skill 承接稳定 surface

- 决策：`Med Auto Science` 的对外第一身份固定为“可被 Codex 或其他通用 agent 直接调用的独立 medical research domain agent”；其单一 MAS app skill 承接稳定 callable surface；`OPL` 只承担 OPL stage-runtime session/runtime/projection 编排与 shared modules/contracts/indexes。
- 理由：公开主语直接决定用户入口与 owner 语义。将 MAS 固定为独立 domain agent，并把稳定 surface 收口到单一 app skill，才能避免把 MAS 误写成 OPL 内部模块，也避免把桥接载荷写成第一主语。
- 影响：README 与核心 docs 必须明确 domain agent、单一 app skill、CLI/workspace commands 和 durable surface 的主次关系；`OPL handoff`、`product-entry manifest` 与 OPL stage-led framework 术语只作为集成和运行框架边界，不作为对外第一身份。

## 2026-04-11：历史 docs 骨架与分层

- 历史决策：以 `project / architecture / invariants / decisions / status` 作为 docs 核心骨架，并将其余文档收口到 `capabilities/`、`program/`、`runtime/`、`references/`、`history/omx/`。
- 理由：避免文档平铺，确保入口明确、角色清晰、可维护。
- 影响：删除冗余的 `documentation-governance.md`，统一文档规则入口。
- 当前读法：本决策的核心骨架仍有效；目录 taxonomy 已被 2026-05 文档组合治理 supersede。当前 recurring material 使用 `active/public/product/runtime/delivery/source/policies/specs/references/history`，旧 `program/` 与 `capabilities/` 只作为历史迁移来源或 path-stable provenance 读取。

## 2026-04-11：OMX 退役并归档

- 决策：OMX 只作为历史材料保留在 `docs/history/omx/`，`.omx/` 禁止作为当前 workflow 入口。
- 理由：避免历史工具状态干扰 repo-tracked 真相。
- 影响：OMX 相关材料仅保留为参考，不进入当前运行路径。

## 2026-04-11：冻结 runtime backend interface

- 决策：`MedAutoScience` controller 只通过 `runtime backend interface contract` 访问 managed runtime backend，不把 `med-deepscientist` 具体实现名作为 controller 判定真相，也不把外部 MDS checkout 当成默认 operation dependency。
- 理由：为 Hermes 等新 backend 接入提供稳定 contract，先完成 backend abstraction，再进入 controlled cutover。
- 影响：`runtime_binding.yaml` 增加 backend-generic 字段；显式声明但未注册的 backend 必须 fail-closed 阻断。

## 2026-04-11：目标 runtime 方向优先于旧 substrate 延长线

- 决策：后续新增投入默认服务“OPL Temporal-backed family runtime，Temporal 作为 production required substrate”这条目标形态，而不是继续把旧默认 substrate 或 Hermes-first 路线深磨成长期产品方向。
- 理由：历史基线和过渡实现仍然有价值，但它们应作为迁移桥、兼容层与回归基线存在，不能反向决定主线目标。
- 影响：所有后续 tranche 都必须明确区分“当前 repo-verified baseline”与“长线目标”，并保持 display 独立支线不被主线误伤。

## 2026-04-11：当前仓内的 `Hermes` 只代表 repo-side seam，不代表上游集成已落地

- 决策：仓内保留的 `Hermes` 命名，只能表示 repo-side outer-runtime seam / shim / contract owner，不得写成“上游 `Hermes-Agent` 已成为当前 runtime owner”。
- 理由：迁移期曾经通过受控 `MedDeepScientist` backend 承接长时执行，但当前 no-history physical absorb 已关闭外部 MDS 默认依赖；文档与命名必须诚实反映这条 closeout。
- 影响：后续所有 runtime 文档都必须把“目标中的上游 `Hermes-Agent`”“MAS-owned default operation surface”和“显式可选 MDS diagnostic / intake / oracle refs”拆开表述；display / paper-facing asset packaging 独立线继续排除在当前 tranche 外。

## 2026-04-12：固定 runtime substrate 与 research executor 分层

- 决策：外层 runtime substrate / orchestration owner 必须与 MAS-owned research owner surface 分层；OPL-hosted production path 由 Temporal-backed OPL family runtime 承担，Temporal 是 production required provider，Hermes-Agent 只保留为可选 Agent executor adapter 或 executor/proof lane，不得替代 MAS-owned research owner surface 或把外部 MDS repo 重新变成默认执行脑。
- 理由：当前真正高风险的不是“没有统一执行脑”，而是“没有统一长期在线 runtime substrate”。若在外层 runtime ownership 尚未稳定前，就强制把 backend 内部的 `Codex + skills` 执行生态整体替掉，最容易出现功能降级。
- 影响：后续继续学习 `MedDeepScientist` / DeepScientist 时，必须按 source provenance、executor route、owner boundary、contract 与 parity proof 决定是否吸收；不允许把“接入 Hermes”偷换成“已完成研究执行 owner 替换”。

## 2026-04-20：方向锁定后的质量与自治默认收口到 MAS

- 决策：方向锁定之后，普通科研推进、论文质量判断、reviewer concern 排序、证据充分性判断与 `bounded_analysis` 一类有限补充分析推进，默认由 `MAS` 自主完成；human gate 收口到重大边界与最终投稿前审计。
- 理由：长时间自治和医学论文质量需要同一 owner、同一 study truth 和同一审计边界，`MAS` 已经持有 study authority、workspace authority、证据推进与人工接手点，适合承担默认裁决权。
- 影响：后续 program、status、runtime 与 eval 文档都要按这个 owner 边界写作；`MDS` 只保留显式 backend audit、explicit archive import reference、行为等价 oracle 与上游 intake buffer。

## 2026-04-20：study charter 承载质量总合同

- 决策：study charter 成为医学质量总合同入口，统一冻结研究问题、claim、证据强度、有限补充分析边界、review 与 submission hygiene 约束；`paper evidence ledger` 与 `review ledger` 作为该合同的执行记录与审阅记录。
- 理由：论文质量提升依赖一份前置、持续、可审计的合同，后续 evidence/review ledger 围绕这份合同推进，才能把设计、分析、审阅和投稿收口到同一条 `MAS` 主线。
- 影响：后续涉及 evidence、review、submission hygiene、bounded analysis 的 owner 叙事，都要显式回指 study charter contract，而不是分散写成独立局部机制。
