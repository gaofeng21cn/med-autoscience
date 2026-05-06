# 关键决策记录

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

- 决策：长线目标固定为 `MAS AI-first Research OS`。MAS 作为唯一 research / quality / publication / artifact / user-visible truth owner；MDS 收敛为 replaceable backend、behavior oracle 与 upstream intake buffer。机械系统只负责 evidence、status、completeness、blocker、projection 与 replay；AI reviewer workflow 持有科学质量、医学写作质量、publishability 与 submission-facing readiness。
- Authority anchor：AI reviewer artifacts 持有科学质量；机械系统只负责 evidence、status、completeness、blocker、projection 与 replay。
- 理由：近期论文修复证明，机械 gate 先给 ready、下游再补救会把质量风险推迟到最贵的阶段。AI-first 的真实落点应前移到 pre-draft quality runtime、AI reviewer workflow、artifact rebuild proof、operations state 与真实论文 soak，而不是在文档层增加措辞约束。
- 影响：新增架构、质量、运行、产物、观测或 MDS 吸收能力时，必须回到 [MAS AI-first Research OS Architecture](./references/ai_first_research_os_architecture.md) 的 owner / authority / proof 口径；physical monorepo absorb 只能在 parity proof、owner cutover、rollback surface 与质量不降级证明成立后进行。本决策不新增文档 wording gate，不修改测试或 preflight contract。

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
- 影响：`runtime-supervisor-consume`、`artifacts/supervision/consumer/*` 与 `artifacts/supervision/requests/*` 都是 handoff/request/dispatch surface；它们不得修改 `paper/current_package` 或 `manuscript/current_package`，不得放宽 quality/publication gate。`runtime-supervisor-execute-dispatch` 可以调用 `publication_gate` owner surface 物化 gate-owned `publication_eval/latest.json`，但不能合成 AI reviewer judgement；AI reviewer output 仍必须来自结构化 reviewer workflow。submission milestone parking 不授权人工 patch；后续稿件反馈仍必须走 durable revision intake 与 MAS/MDS relaunch/resume。

## 2026-05-05：Supervisor scan 采用 current truth owner-route reconcile 合同

- 决策：`runtime-supervisor-scan` 固定为 controller-style reconcile loop。它每轮先读取当前 `study_runtime_status`、`study_progress`、`publication_eval/latest.json`、`controller_decisions/latest.json` 与 `StudyTruthKernel` epoch，再产出唯一 `owner_route`。`runtime liveness`、retry budget、publication gate、AI reviewer 与 dispatch executor 都只能作为 current truth 输入或 owner action，不得各自用局部判断覆盖当前 owner。若当前 controller decision 与 publication work-unit fingerprint 对齐，且 controller action 明确要求同线 runtime redrive，no-live / retry-exhausted 只能路由给 `mas_controller`，不能升级成 `external_supervisor`。
- 理由：DM001/DM002/DM003/NF002 的连续故障显示，单点修补 stopped、package handoff、AI reviewer 或 executor 都会暴露另一层漂移。成熟控制面通常把 current state 与 desired state 的收敛放在一个 reconcile loop 中；幂等重试需要调用方意图 token；可重试 activity 必须有稳定 idempotency key。MAS 的对应合同就是 `truth_epoch + source_fingerprint + next_owner + allowed_actions`。
- 影响：`owner_route` 是 `scan -> consume -> execute-dispatch -> rescan` 的唯一执行票据。consumer 只能传播 route；executor 执行前必须比对最新 route，并拒绝 `owner_route_stale` 或 `owner_route_next_owner_mismatch`。同一 scan 即使生成多个候选 action，`allowed_actions` 也只包含当前 `next_owner` 可执行的动作；其他 action 只能留作观测或下一轮 owner，不得被同 tick executor 抢跑。runtime redrive 还必须把当前 controller decision 和同 fingerprint 的 actionable publication targets 写入 runtime authorization，避免 MDS 因缺可执行 target 把当前 work unit 再次判成 gate pending。完成态、completion evidence owner、auto-runtime parked、manual hold 与 stop-loss 都必须通过同一 route 投影，避免 stale lifecycle、publication gate 或 AI reviewer 队列重新打开已完成或已停驻论文线。
- 参考：[Kubernetes Controllers current/desired state reconcile loop](https://kubernetes.io/docs/concepts/architecture/controller/)；[AWS Builders Library “Making retries safe with idempotent APIs”](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)；Temporal Activity idempotency and retry guidance。

## 2026-05-01：医学稿件初稿质量前移为 manuscript-native prose 合同

- 决策：first draft 质量不再只依赖 `medical_publication_surface` 后置拦截；`study_charter.paper_quality_contract.structured_reporting_contract.first_draft_quality_contract` 与 quality OS 必须在写作前提供 IMRAD section purpose、reporting-guideline obligations、clinical question / population / timepoint / outcome / display-to-claim map，以及 manuscript-native medical journal prose 要求。
- 理由：真实稿件修订暴露出 MAS 初稿可能把 controller checklist、figure/table anchor、author-confirmation placeholder、claim-boundary 标签和 operations/review 语言带进正文。医学论文初稿必须从临床问题、研究设计、结果解释和投稿读者问题出发。
- 影响：写作 route 在判断 draft ready 前必须检查这些输入；缺少支撑时 route back 到同线写作修复或有限补充分析。`medical_publication_surface` 继续作为 safety net，而不是主写作策略。

## 2026-04-26：稿件反馈后的 stopped milestone 统一视为 revision reactivation

- 决策：已达投稿包、submission-ready 或 finalize 里程碑后，如果收到用户、导师或审稿层面的稿件反馈，必须把该反馈作为同一 study 的 `reviewer_revision` reactivation intake 处理。`stopped` 状态和 `current_package` 存在只说明旧里程碑曾经成立，不能授权 Codex 前台直接修改 `manuscript/current_package/` 后宣称完成。
- 理由：003 / 004 类 manuscript revision 暴露出重复误判风险：Agent 容易把“quest 已停车”误读成“当前包可人工小修”。这会绕开 MAS/MDS 的 study truth、claim-evidence、review ledger 和 package regeneration 链路。
- 影响：`submit-study-task` 对非 live reviewer revision 要返回 reactivation guidance；workspace AGENTS、agent-entry templates、MDS write/finalize overlay 和 invariants 都必须显式要求先 durable intake，再 MAS/MDS relaunch/resume，最后从 canonical paper authority 重新生成 `current_package`。

## 2026-04-26：初稿质量升级扫描进入 study charter 与 reviewer-first route-back

- 决策：`study_charter.paper_quality_contract` 固定新增 first-draft quality contract；写作 route 在判断 draft ready 前必须扫描已验证数据资产是否支持更强的时间点、角色/人群、中心/地理、指南对应、亚组/关联分析和现实采用约束叙事。若当前初稿过轻且不改变锁定 claim 边界，默认 route back 到 `analysis-campaign` 做有限补充分析。
- 理由：近期 manuscript 修改反馈暴露出一个系统性问题：初稿如果只按已有结果描述成稿，容易漏掉数据资产本身已经能支撑的更强 paper shape。把这类反馈上收到 MAS 合同层，可以在初稿前阻断“描述性够用”的低质量出口。
- 影响：后续 `survey_trend_analysis`、写作 route、reviewer-first 检查与 evidence/review 合同都必须先问“数据资产还能否支撑更强且可验证的论文形态”，再决定写作、有限补充分析或 human gate。

## 2026-04-26：OPL Runtime Manager 作为薄运行管理层接入 MAS projection

- 决策：MAS 与 OPL 的长线对齐采用 `OPL Runtime Manager -> external Hermes-Agent runtime substrate -> MAS domain entry/projection` 的分层口径。MAS 只暴露 task registration、runtime_control projection、status/artifact locator、approval/wakeup boundary 与现有 durable truth surface；`OPL Runtime Manager` 只负责上层管理、索引、doctor/repair/resume 与 native helper catalog，不成为 MAS 研究 truth 或执行器 owner。
- 理由：这能先获得长期托管、唤醒、健康检查和跨域状态索引的收益，同时保留 MAS 自己的 study authority、publication gate 与 evidence/review ledger。若未来需要自有长期常驻 sidecar，也能沿 Runtime Manager 的 adapter/projection contract promotion，而不重写 MAS domain truth。
- 影响：后续涉及 OPL handoff、runtime_control、product-entry manifest、status projection 或 hosted lane 的文案，都必须明确 `OPL Runtime Manager` 是 OPL 侧 thin manager over external substrate；MAS durable truth surface 仍是唯一研究真相。

## 2026-04-21：公开主语固定为独立 domain agent，单一 app skill 承接稳定 surface，OPL 只做上层 federation

- 决策：`Med Auto Science` 的对外第一身份固定为“可被 Codex 或其他通用 agent 直接调用的独立 medical research domain agent”；其单一 MAS app skill 承接稳定 callable surface；`OPL` 只承担 family-level session/runtime/projection 编排与 shared modules/contracts/indexes。
- 理由：公开主语直接决定用户入口与 owner 语义。将 MAS 固定为独立 domain agent，并把稳定 surface 收口到单一 app skill，才能避免把 MAS 误写成 OPL 内部模块，也避免把桥接载荷写成第一主语。
- 影响：README 与核心 docs 必须明确 domain agent、单一 app skill、CLI/workspace commands 和 durable surface 的主次关系；`OPL handoff`、`product-entry manifest` 与 `gateway / harness` 术语保留为内部集成或架构边界语言，不作为对外第一身份。

## 2026-04-11：统一 docs 骨架与分层

- 决策：以 `project / architecture / invariants / decisions / status` 作为 docs 核心骨架，并将其余文档收口到 `capabilities/`、`program/`、`runtime/`、`references/`、`history/omx/`。
- 理由：避免文档平铺，确保入口明确、角色清晰、可维护。
- 影响：删除冗余的 `documentation-governance.md`，统一文档规则入口。

## 2026-04-11：OMX 退役并归档

- 决策：OMX 只作为历史材料保留在 `docs/history/omx/`，`.omx/` 禁止作为当前 workflow 入口。
- 理由：避免历史工具状态干扰 repo-tracked 真相。
- 影响：OMX 相关材料仅保留为参考，不进入当前运行路径。

## 2026-04-11：冻结 runtime backend interface

- 决策：`MedAutoScience` controller 只通过 `runtime backend interface contract` 访问 managed runtime backend，不再把 `med-deepscientist` 具体实现名作为 controller 判定真相。
- 理由：为 Hermes 等新 backend 接入提供稳定 contract，先完成 backend abstraction，再进入 controlled cutover。
- 影响：`runtime_binding.yaml` 增加 backend-generic 字段；显式声明但未注册的 backend 必须 fail-closed 阻断。

## 2026-04-11：目标 runtime 方向优先于旧 substrate 延长线

- 决策：后续新增投入默认服务“上游 `Hermes-Agent` 承担外层 runtime substrate”这条目标形态，而不是继续把旧默认 substrate 深磨成长期产品方向。
- 理由：历史基线和过渡实现仍然有价值，但它们应作为迁移桥、兼容层与回归基线存在，不能反向决定主线目标。
- 影响：所有后续 tranche 都必须明确区分“当前 repo-verified baseline”与“长线目标”，并保持 display 独立支线不被主线误伤。

## 2026-04-11：当前仓内的 `Hermes` 只代表 repo-side seam，不代表上游集成已落地

- 决策：仓内保留的 `Hermes` 命名，只能表示 repo-side outer-runtime seam / shim / contract owner，不得写成“上游 `Hermes-Agent` 已成为当前 runtime owner”。
- 理由：当前真实长时执行仍通过受控 `MedDeepScientist` backend 完成；文档与命名必须诚实反映这一点。
- 影响：后续所有 runtime 文档都必须把“目标中的上游 `Hermes-Agent`”与“当前仓内的 repo-side seam”拆开表述；display / paper-facing asset packaging 独立线继续排除在当前 tranche 外。

## 2026-04-12：固定 runtime substrate 与 research executor 分层

- 决策：`Hermes-Agent` 在这条主线里优先承担 runtime substrate / orchestration owner，而不是立刻替代 `MedDeepScientist` 内部所有研究执行脑。
- 理由：当前真正高风险的不是“没有统一执行脑”，而是“没有统一长期在线 runtime substrate”。若在外层 runtime ownership 尚未稳定前，就强制把 backend 内部的 `Codex + skills` 执行生态整体替掉，最容易出现功能降级。
- 影响：后续解构 `MedDeepScientist` 时，必须按 executor route 逐类迁移，并用显式 contract + proof 决定是否替换；不允许把“接入 Hermes”偷换成“已完成单步执行器替换”。

## 2026-04-20：方向锁定后的质量与自治默认收口到 MAS

- 决策：方向锁定之后，普通科研推进、论文质量判断、reviewer concern 排序、证据充分性判断与 `bounded_analysis` 一类有限补充分析推进，默认由 `MAS` 自主完成；human gate 收口到重大边界与最终投稿前审计。
- 理由：长时间自治和医学论文质量需要同一 owner、同一 study truth 和同一审计边界，`MAS` 已经持有 study authority、workspace authority、证据推进与人工接手点，适合承担默认裁决权。
- 影响：后续 program、status、runtime 与 eval 文档都要按这个 owner 边界写作；`MDS` 继续承担迁移期 research backend、行为等价 oracle 与上游 intake buffer。

## 2026-04-20：study charter 承载质量总合同

- 决策：study charter 成为医学质量总合同入口，统一冻结研究问题、claim、证据强度、有限补充分析边界、review 与 submission hygiene 约束；`paper evidence ledger` 与 `review ledger` 作为该合同的执行记录与审阅记录。
- 理由：论文质量提升依赖一份前置、持续、可审计的合同，后续 evidence/review ledger 围绕这份合同推进，才能把设计、分析、审阅和投稿收口到同一条 `MAS` 主线。
- 影响：后续涉及 evidence、review、submission hygiene、bounded analysis 的 owner 叙事，都要显式回指 study charter contract，而不是分散写成独立局部机制。
