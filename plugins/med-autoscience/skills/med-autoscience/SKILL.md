---
name: med-autoscience
description: Use when Codex should operate MedAutoScience through its stable runtime, controller, overlay, and workspace contracts instead of ad-hoc scripts.
---

# MedAutoScience App Skill

Series: OPL Foundry Agent
Skill id: med-autoscience
Legacy alias: mas
Ordinary path: study -> stage -> domain owner receipt or typed blocker -> handoff
Executable command surface: `medautosci foundry status|inspect|interfaces|validate|doctor|peers --format json`
Paper mission readback/control surface: `medautosci paper-mission inspect|drive|terminalize-stage`
OPL series command surface: `opl foundry agents inspect mas --json`

当 Codex 需要通过稳定运行面操作 `MedAutoScience`，而不是把仓库当成临时脚本集合来直接拼装时，使用这个 app skill。

## 这个 app skill 是什么

- `MedAutoScience` 的 direct domain entry / handler target；它把 Codex 调回 MAS owner surface，而不是让本仓长期拥有 Skill descriptor。
- OPL generated descriptors 是 CLI、MCP、Skill、product-entry、status、workbench metadata 的统一 owner；MAS repo-local skill 文件只保留当前 direct path 约束、handler target 说明和 domain authority 护栏。
- `medautosci foundry ...` 是 MAS 的只读 OPL Foundry Agent series identity / interface surface；顶层 `medautosci status|inspect|interfaces|validate|doctor` 是同一读面的薄 alias。`med-autoscience` 是当前 Codex plugin / skill 机器名；`mas` 继续只保留为 series agent id / brand shorthand，不作为本机 PATH readiness 的唯一证据，也不要用它判断 shell 命令是否安装；macOS 上 `/opt/homebrew/bin/mas` 通常是 Mac App Store CLI。旧 `runtime`、`index`、`stage-artifact`、裸 MCP/server 细节只作为 diagnostic 或 handler target，不是新用户 command surface。
- MAS 保留 `MedAutoScienceDomainEntry`、CLI/controller/workspace commands、study truth、publication quality、artifact gate、current package authority、memory writeback decision 和 owner receipt signer。
- skill 入口只有一个；`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress`、`product-entry-status` 等命令是 MAS domain handler contract，供 OPL generated surfaces 或 direct path 调用。
- `product-entry manifest` 暴露 MAS-owned domain action intents、handler target refs 与 authority boundaries；CLI、MCP、Skill、product/status/workbench descriptors 由 OPL 从同一份 pack/compiler input 生成或托管。
- OPL Full online runtime 由 OPL framework-managed provider substrate 承担长期在线、唤醒、session/delivery/approval transport；MAS 通过 `domain-handler export` / `domain-handler dispatch` 暴露受控 domain handler target，仍持有 study truth、publication quality、artifact gate 与 current package authority。

## 核心规则

优先走已有的 `MedAutoScience` 运行时 contract：

- 如果 workspace 还不存在，优先走 OPL generated surface 或 `medautosci workspace init`；只有显式接入 `medautosci-mcp` direct lane 时才调用 MCP tool `init_workspace`
- `medautosci workspace init`
- `medautosci doctor report --profile <profile>`
- `medautosci doctor profile --profile <profile>`
- `medautosci workspace bootstrap --profile <profile>`
- `medautosci runtime watch --runtime-root <runtime-root>`
- `medautosci runtime overlay-status --profile <profile>`
- `medautosci runtime install-overlay --profile <profile>`
- `medautosci doctor backend-audit --profile <profile> --refresh`
- `medautosci paper-mission inspect --profile <profile> --study-id <study_id> --format json`
- `medautosci paper-mission drive --profile <profile> --study-id <study_id>`
- `medautosci paper-mission terminalize-stage --profile <profile> --study-id <study_id> --format json`
- `medautosci paper-mission inspect --profile <profile> --study-id <study_id> --request-opl-runtime-readback --format json`
- `medautosci paper-mission receipt-owner-consumption --profile <profile> --study-id <study_id> --paper-mission-readback-file <inspect-readback.json> --apply-typed-blocker --format json`
- `medautosci paper-mission typed-blocker-resolution --profile <profile> --study-id <study_id> --paper-mission-readback-file <inspect-readback.json> --apply-route-redesign --format json`
- `medautosci study progress --profile <profile> --study-id <study_id> --format json`
- `medautosci domain-handler export --profile <profile> --format json`
- `medautosci domain-handler dispatch --task <task.json> --format json`
- plugin-local MCP launcher: `plugins/med-autoscience/bin/medautosci-mcp`

如果 `medautosci` 不在 `PATH` 上，用模块入口：

```bash
uv run python -m med_autoscience.cli doctor report --profile <profile>
```

## OPL ScholarSkills 外挂能力边界

`ScholarSkills` 的 active 模块只有 `display`、`tables`、`stats`、`lit`、`write`、`review`、`submit` 和 `data` 八个，它们是 OPL-managed academic capability pack，不是 MAS 私有执行器。`intake` 不是 active ScholarSkills 模块：OPL `domain_intake` 原则在 MAS 侧映射到 `contracts/mas-paper-study-stage-pack.json` 的 `01-study_intake` 和 `src/med_autoscience/study_task_intake*.py` surfaces。`omics` 在 MAS 有稳定真实组学专业 workflow 前只作为 deferred/reference，不作为 active ScholarSkills 模块。MAS 直接调用入口不变：先通过 MAS owner surface 读取 `study progress`、current owner delta、publication supervisor state 和 authority boundary，再用 `scientific_capability_registry` 做能力发现、resolve、refs-only invocation projection 或 owner-consumption evidence。

执行可用性来自 OPL Connect 同步到 workspace 或 quest 的本地 skill，而不是 MAS 仓内 plugin mirror：

```bash
opl connect sync-skills --domain mas-scholar-skills --scope workspace --target-workspace <workspace_root> --json
opl connect sync-skills --domain mas-scholar-skills --scope quest --target-quest <quest_root> --json
```

ScholarSkills 产物默认只是 refs-only candidate、materialized package refs 或 execution receipt candidate。只有 MAS owner receipt、typed blocker、reviewer receipt、route-back evidence、publication gate 或 controller decision 接受后，才可计入 study truth、paper progress、artifact authority、current package freshness 或 publication readiness。

## OPL terminal attempt / next work unit 快速入口

当 OPL terminal attempt 已完成，但 MAS study progress 仍停在 queued、handoff、stale current-control 或旧 work unit 时，不要先找旧 DHD/owner-route 入口。`study progress --format json` 是只读投影；当前主路是先读 `paper-mission inspect`，再由 `paper-mission terminalize-stage` 或 `paper-mission drive` 消费 StageOutcome / owner receipt / typed blocker / route-back evidence，并让 OPL 接力下一 stage。

稳定用法：

```bash
medautosci paper-mission inspect \
  --profile <profile> \
  --study-id <study_id> \
  --format json
```

Stage 已有 terminal packet / closeout 时，走 StageOutcome 消费入口：

```bash
medautosci paper-mission terminalize-stage \
  --profile <profile> \
  --study-id <study_id> \
  --format json
```

如果 terminalizer 产出 `route_back_candidate_checkpoint`，不要同义 redrive 同一个 OPL route。先生成包含 OPL terminal receipt 的 inspect readback，再按 owner-consumption 给出的 expected apply mode 收束：

```bash
medautosci paper-mission inspect \
  --profile <profile> \
  --study-id <study_id> \
  --request-opl-runtime-readback \
  --format json > /tmp/mas-paper-mission-readback.json

medautosci paper-mission receipt-owner-consumption \
  --profile <profile> \
  --study-id <study_id> \
  --paper-mission-readback-file /tmp/mas-paper-mission-readback.json \
  --apply-typed-blocker \
  --format json
```

当缺失的是投稿/来源硬事实，但仍需要给用户审计 `current_package` 或 TODO/human-gate 包时，继续走 typed-blocker resolution，而不是阻断在旧 route-back：

```bash
medautosci paper-mission inspect \
  --profile <profile> \
  --study-id <study_id> \
  --request-opl-runtime-readback \
  --format json > /tmp/mas-paper-mission-readback.json

medautosci paper-mission typed-blocker-resolution \
  --profile <profile> \
  --study-id <study_id> \
  --paper-mission-readback-file /tmp/mas-paper-mission-readback.json \
  --apply-route-redesign \
  --format json
```

执行后再用 `medautosci study progress --profile <profile> --study-id <study_id> --format json` 确认 canonical `StageOutcome` / `NextActionEnvelope` 消费结果、`current_stage`、typed blocker、typed-blocker resolution successor 和 next owner。旧 `current_work_unit` / `current_executable_owner_action` 只能作为 legacy diagnostic-only / retired drilldown，不得当成正常 readback 或第二权威。`runtime domain-health-diagnostic`、`owner-route-reconcile` 与旧 default-executor dispatch 只允许作为显式 diagnostic / tombstone / migration provenance；默认监督、automation 或不确定 current fingerprint 时不得把它们作为推进入口。

## Domain runtime 护栏

- 用户点名 `MAS` / `Med Auto Science`，或任务属于医学研究 workspace、study runtime、论文、证据包、分析包、publication gate、submission/finalization 等 MAS 覆盖范围时，必须通过 MAS product-entry、controller、overlay 或 study runtime surface 推进。
- 不得用 ad-hoc Python/R 脚本、通用文档/PDF/Office skill、直接编辑 manuscript、直接搬运 artifact、手写状态文件或 prompt-only 研究链来替代 MAS 的 controller/runtime。
- 任何研究产物写入前，必须先读取 product entry status/preflight/start 或 study progress/runtime status，确认 `study_id`、workspace、current stage、human gate 与 durable surface。
- 如果某个所需能力在 MAS surface 中缺失，应回到 repo 层补最小 callable/controller surface 并验证，而不是在单个 study workspace 旁路实现。
- 只有用户明确要求“探索 MAS 之外的替代技术路线”或“只做离线草稿、不进入 MAS runtime”时，才可以使用通用工具；回复中必须标明该路线不更新 MAS truth surface。

## 用户论文反馈与大改边界

- 用户对论文提出修改、导师意见、审稿意见、补分析、补参考文献、扩正文、重画图、改结果/讨论/表图或投稿包要求时，先按 `reviewer_revision` / paper-mission task intake 理解，并读取 `study progress` 与 `paper-mission inspect`，不要默认进入前台直接改稿。
- Fast-lane 只允许小范围、低风险、不会改变证据面或论文结构的修正，例如错字、局部措辞、单个格式问题、显然的 caption 小修；即使 fast-lane 执行，也必须留下 MAS 格式记录或候选 delta，说明 `candidate_is_authority=false`、影响范围和后续 owner 路径。
- 下列事项不是 fast-lane，必须走 MAS owner route / candidate package / revision work unit / OPL-MAS handoff：新增或替换参考文献批量集合、正文扩写或重写、补充结果图表、重画 paper-facing figures、改变 claim-evidence/display surface、修改统计或方法证据、构建或刷新 submission package、影响 publication gate 或 current package 的任何动作。
- 大修改意见默认不是 fast-lane：先形成 structured `reviewer_revision` checklist；超过 text-only 微修时触发 Agent Lab suite + FeedbackOps dispatch request + OMA/developer work order 或 refs-only improvement proposal；修订 closeout 必须带 coverage audit，并在 stage attempt readback 中保留专业 skill 调用 refs、duration/token/cost 观测或 typed missing reason。
- registry、phenotype-atlas 或 treatment-gap 稿件进入 Agent Lab/OMA 自进化时，质量地板必须带 clinical discovery contract、Methods reconstructability、finding-led Results、recorded-care review terminology、medication-capture sensitivity 和 current-evidence-bounded revision scope refs；这些 refs 只驱动 repo patch / owner route-back regression，不授权 publication-ready、submission-ready、current package 或 owner receipt。
- Codex foreground 可以产出 paper-facing candidate、diagnostic delta、修复建议或候选包，但这些在 MAS owner 消费前不是 authority；不得把 foreground 文件生成、脚本通过、包存在、figure render 成功或 refs-only package 表述为 paper progress、current package freshness、submission-ready、publication-ready、owner receipt、typed blocker 或 human gate 已完成。
- 对已经发生的 foreground 大改，正确补救路径是立刻停止继续改正文，登记结构化 candidate/revision delta，经 `paper-mission package-candidate` / `consume-candidate` 或当前 study 的合法 owner route 消费，再用 fresh `study progress` / `paper-mission inspect` 报告 MAS 是否接受、route back、typed blocker、human gate 或仍只是 foreground artifact。
- 对新增分析、补图表、重构故事线、AI review 或投稿包刷新这类非 fast-lane 请求，`package-candidate` / `consume-candidate` 只是中间证据，不是任务终点。消费到 `accepted_submission_milestone_candidate` 后必须继续跑 `paper-mission drive --submit-opl-runtime`，直到 fresh readback 出现下一 review/write/finalize/package owner、稳定 typed blocker、human gate、owner receipt，或 OPL live attempt 正在执行；不得停在候选包交付。
- 如果最新 consumption ledger 已形成 `route_back_candidate_checkpoint`，旧 `typed_blocker_resolution` successor 只能作为 diagnostic/provenance；不得覆盖新的 `domain_transition.next_action`。当 domain transition 指向具体 `paper.review.*` / `paper.write.*` / finalize/package work unit 时，drive 应继续 direct handoff 到 OPL，而不是返回 `owner_action_ready_no_redrive`。
- 禁止直接写入或伪造 `publication_eval/latest.json`、`controller_decisions/latest.json`、owner receipt、typed blocker、human gate、`manuscript/current_package`、runtime queue/provider attempts 或 Yang study truth surface 来让前台大改看起来已被 MAS 承认。

## 操作约束

- 任何写操作之前，先读 workspace 当前状态
- 对 `study_runtime_status` 或 `ensure_study_runtime` 的返回，必须检查 `autonomous_runtime_notice`
- 对 `study_runtime_status.execution_owner_guard` 或同名 payload，必须把它当作当前 study 的执行所有权真相源
- 对 `study_runtime_status.publication_supervisor_state` 或同名 payload，必须把它当作论文当前全局阶段的真相源
- 只要 `autonomous_runtime_notice.required=true`，就表示该 study 已处于 live managed runtime；无论是本次刚启动，还是接管到已在运行的 quest，都必须立刻显式通知用户
- 通知里必须给出可监督入口，至少包括 `browser_url`；如果返回了 `quest_session_api_url` 和 `active_run_id`，也要一并告诉用户
- 只要 `execution_owner_guard.supervisor_only=true`，前台就必须进入 supervisor-only 监管态，不得继续直接推进 study-local 执行
- 在 supervisor-only 状态下，不得直接写入 `execution_owner_guard.runtime_owned_roots` 覆盖的 runtime-owned surface；如需人工接管，先显式暂停 runtime
- 不允许在已检测到 live managed runtime 的情况下继续隐式推进对话而不告知用户自动驾驶已经在运行
- 只要 `publication_supervisor_state.bundle_tasks_downstream_only=true`，就不得把 paper bundle 缺件表述成当前 next step；必须明确说明那只是后续件，待 `publication_gate` 放行后再做
- 只要 `publication_supervisor_state.bundle_tasks_downstream_only=true`，就把 bundle/build/proofing 当作硬阻断，不得在前台抢跑
- 当 `paper_contract_health` 给出 `recommended_next_stage` / `recommended_action` 时，默认只把它们解释为 paper-line local recommendation，除非 `publication_supervisor_state` 已明确进入对应全局阶段
- 数据资产变更要走 controller 命令和结构化 payload，不直接手改 registry
- `domain-handler export` 只给 OPL family runtime 提供 MAS-owned read-only projection、pending family task 和 source ref；不得把该 projection 当作研究真相、质量结论或 artifact authority
- `domain-handler dispatch` 只接收 OPL typed queue 的 guarded task，并回到 MAS owner surface 产出 domain control receipt / recommended command；不得直接写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper package、artifact gate 或 study truth
- `paper_autonomy/repair-recheck` task 只能通过 MAS-owned repair executor 修改 canonical manuscript / evidence ledger / review ledger / revision log，并必须写 owner receipt、gate replay request、AI reviewer recheck request 和 package freshness proof；缺结构化 canonical patch 时返回 typed blocker，不把 repair note 写入正文
- `paper_autonomy/ai-reviewer-recheck` task 只能触发 MAS supervisor executor 的 AI reviewer workflow；最终质量、publishability 或 submission-facing readiness 仍以 AI reviewer-backed `publication_eval/latest.json` 和 publication gate truth 为准
- 当前已落地的是 MAS repo-level AI-first paper autonomy callable loop 与 read-only real-paper soak projection；不要把它表述成 Hermes Full App 打包、MAG/RCA adapters、真实 24h online-runtime restart soak 或三篇 live paper finalization 已完成
- 保持 `MedAutoScience` 作为 domain handler target，不要把 controller、profile、overlay、workspace 逻辑塌缩进 plugin 私有文件
- 保持 CLI 和 controller handler 入口稳定，避免破坏 OPL generated descriptors 和 direct path 的兼容性
- plugin-local MCP 通过当前 repo checkout 的 `scripts/run-python-clean.sh -m med_autoscience.mcp_server` 启动，避免 repo-local `.venv`、`__pycache__` 和 editable install metadata 污染
- 旧 `deepscientist-*` / `med-deepscientist-*` overlay 目录名和 `doctor med-deepscientist-upgrade` 只保留为 internal compatibility surface；workspace project skill 可见面应清理旧 `deepscientist-*` 目录，避免与 `medical-research-*` 双暴露

## 首先应读的文件

- `bootstrap/README.md`
- `docs/runtime/control/controllers.md`
- `docs/runtime/contracts/runtime_boundary.md`
- `docs/runtime/domain_authority_refs_index_guard.md`
- `docs/runtime/projections/study_progress_projection.md`
- `docs/product/README.md`
- `docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md`

## 典型任务

- 审核某个 workspace profile 是否接对
- 为新的病种 workspace 建立骨架并接入 Codex 驱动执行
- 检查 overlay 是否漂移，必要时重覆写
- 运行 runtime watch 并归纳阻塞点
- 通过可审计命令驱动数据资产和投稿交付 controller
