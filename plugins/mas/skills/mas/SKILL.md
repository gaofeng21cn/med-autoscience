---
name: mas
description: Use when Codex should operate MedAutoScience through its stable runtime, controller, overlay, and workspace contracts instead of ad-hoc scripts.
---

# MAS App Skill

当 Codex 需要通过稳定运行面操作 `MedAutoScience`，而不是把仓库当成临时脚本集合来直接拼装时，使用这个 app skill。

## 这个 app skill 是什么

- `MedAutoScience` 的 direct domain entry / handler target；它把 Codex 调回 MAS owner surface，而不是让本仓长期拥有 Skill descriptor。
- OPL generated descriptors 是 CLI、MCP、Skill、product-entry、status、workbench metadata 的统一 owner；MAS repo-local skill 文件只保留当前 direct path 约束、handler target 说明和 domain authority 护栏。
- MAS 保留 `MedAutoScienceDomainEntry`、CLI/controller/workspace commands、study truth、publication quality、artifact gate、current package authority、memory writeback decision 和 owner receipt signer。
- skill 入口只有一个；`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress`、`product-entry-status` 等命令是 MAS domain handler contract，供 OPL generated surfaces 或 direct path 调用。
- `product-entry manifest` 暴露 MAS-owned domain action intents、handler target refs 与 authority boundaries；CLI、MCP、Skill、product/status/workbench descriptors 由 OPL 从同一份 pack/compiler input 生成或托管。
- OPL Full online runtime 由 OPL framework-managed provider substrate 承担长期在线、唤醒、session/delivery/approval transport；MAS 通过 `sidecar export` / `sidecar dispatch` 暴露受控桥接，仍持有 study truth、publication quality、artifact gate 与 current package authority。

## 核心规则

优先走已有的 `MedAutoScience` 运行时 contract：

- 如果 workspace 还不存在，优先调用 MCP tool `init_workspace`
- `medautosci workspace init`
- `medautosci doctor report --profile <profile>`
- `medautosci doctor profile --profile <profile>`
- `medautosci workspace bootstrap --profile <profile>`
- `medautosci runtime watch --runtime-root <runtime-root>`
- `medautosci runtime overlay-status --profile <profile>`
- `medautosci runtime install-overlay --profile <profile>`
- `medautosci doctor backend-audit --profile <profile> --refresh`
- `medautosci sidecar export --profile <profile> --format json`
- `medautosci sidecar dispatch --task <task.json> --format json`
- plugin-local MCP launcher: `plugins/mas/bin/medautosci-mcp`

如果 `medautosci` 不在 `PATH` 上，用模块入口：

```bash
uv run python -m med_autoscience.cli doctor report --profile <profile>
```

## Domain runtime 护栏

- 用户点名 `MAS` / `Med Auto Science`，或任务属于医学研究 workspace、study runtime、论文、证据包、分析包、publication gate、submission/finalization 等 MAS 覆盖范围时，必须通过 MAS product-entry、controller、overlay 或 study runtime surface 推进。
- 不得用 ad-hoc Python/R 脚本、通用文档/PDF/Office skill、直接编辑 manuscript、直接搬运 artifact、手写状态文件或 prompt-only 研究链来替代 MAS 的 controller/runtime。
- 任何研究产物写入前，必须先读取 product entry status/preflight/start 或 study progress/runtime status，确认 `study_id`、workspace、current stage、human gate 与 durable surface。
- 如果某个所需能力在 MAS surface 中缺失，应回到 repo 层补最小 callable/controller surface 并验证，而不是在单个 study workspace 旁路实现。
- 只有用户明确要求“探索 MAS 之外的替代技术路线”或“只做离线草稿、不进入 MAS runtime”时，才可以使用通用工具；回复中必须标明该路线不更新 MAS truth surface。

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
- `sidecar export` 只给 OPL family runtime 提供 MAS-owned read-only projection、pending family task 和 source ref；不得把该 projection 当作研究真相、质量结论或 artifact authority
- `sidecar dispatch` 只接收 OPL typed queue 的 guarded task，并回到 MAS owner surface 产出 domain control receipt / recommended command；不得直接写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper package、artifact gate 或 study truth
- `paper_autonomy/repair-recheck` task 只能通过 MAS-owned repair executor 修改 canonical manuscript / evidence ledger / review ledger / revision log，并必须写 owner receipt、gate replay request、AI reviewer recheck request 和 package freshness proof；缺结构化 canonical patch 时返回 typed blocker，不把 repair note 写入正文
- `paper_autonomy/ai-reviewer-recheck` task 只能触发 MAS supervisor executor 的 AI reviewer workflow；最终质量、publishability 或 submission-facing readiness 仍以 AI reviewer-backed `publication_eval/latest.json` 和 publication gate truth 为准
- 当前已落地的是 MAS repo-level AI-first paper autonomy callable loop 与 read-only real-paper soak projection；不要把它表述成 Hermes Full App 打包、MAG/RCA adapters、真实 24h gateway restart soak 或三篇 live paper finalization 已完成
- 保持 `MedAutoScience` 作为 domain handler target，不要把 controller、profile、overlay、workspace 逻辑塌缩进 plugin 私有文件
- 保持 CLI 和 controller handler 入口稳定，避免破坏 OPL generated descriptors 和 direct path 的兼容性
- plugin-local MCP 通过当前 repo checkout 的 `uv run --directory <repo-root> --extra analysis medautosci-mcp` 启动
- 旧 `deepscientist-*` / `med-deepscientist-*` overlay 目录名和 `doctor med-deepscientist-upgrade` 只保留为 internal compatibility surface；workspace project skill 可见面应清理旧 `deepscientist-*` 目录，避免与 `medical-research-*` 双暴露

## 首先应读的文件

- `bootstrap/README.md`
- `docs/runtime/control/controllers.md`
- `docs/runtime/control/runtime_supervision_loop.md`
- `docs/runtime/display/progress_portal.md`
- `docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md`

## 典型任务

- 审核某个 workspace profile 是否接对
- 为新的病种 workspace 建立骨架并接入 Codex 驱动执行
- 检查 overlay 是否漂移，必要时重覆写
- 运行 runtime watch 并归纳阻塞点
- 通过可审计命令驱动数据资产和投稿交付 controller
