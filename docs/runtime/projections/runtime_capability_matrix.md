# Runtime Capability Matrix

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime projection and read-model semantics for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable projection support only; projection truth remains in source, tests, CLI/read-model output, runtime artifacts, ledgers, and owner receipts.

这份 contract 学习 `DeepScientist` 的 runner / settings / admin health surfaces，但在 `MAS` 中只固定 runtime capability 与 doctor 投影，不扩展 provider 主线，也不把 MAS 提升为 generic runtime owner。

## 目标

`MAS` 需要知道当前 runtime backend 能不能承担长时间医学研究，而不是只知道某个 binary 是否存在。

每个 runtime capability item 至少投影以下能力：

- `capability_id`
- `transport_owner`
- `executor_kind`
- `provider_owner`
- `mcp_ready`
- `long_running_tool_timeout_sec`
- `supports_pause_resume`
- `supports_user_message_queue`
- `supports_artifact_inventory`
- `supports_workspace_file_refs`
- `doctor_status`
- `blocking_reasons`

## Provider / executor 分类

- `opl_hosted_stage_runtime`：默认 hosted autonomous runtime machine ref。`provider_owner=one-person-lab`，production online substrate 为 OPL/Temporal；MAS 只消费 `current_control_state`、provider attempt refs、typed closeout、owner receipt 或 typed blocker。
- `codex_cli`：当前第一公民 Agent executor kind。它可以作为 direct MAS path 或 OPL provider-backed stage 内的 executor，但不能写成 MAS 自持 scheduler / queue / worker residency。
- `med_deepscientist_backend`：历史 fixture、explicit archive/import、backend audit、upstream intake buffer 与 parity oracle reference；不作为 MAS 默认 backend。
- `hermes_agent`：上游外部 executor / diagnostic / provenance reference，可经显式 adapter 进入 proof lane；不作为 MAS 生产 online substrate，也不替代 OPL/Temporal provider。

## Doctor 规则

runtime doctor 不应只返回 pass/fail。它必须说明：

1. OPL `current_control_state` 或 explicit direct path 是否提供当前 attempt / owner refs。
2. pause / resume / stop 是 OPL runtime owner handoff、MAS typed blocker，还是历史 diagnostic/provenance。
3. user message / approval / wakeup 是否有 durable OPL transport 或 MAS owner-route refs。
4. artifact inventory 和 workspace file refs 是否能投影到用户面，且不会被提升为 artifact authority。
5. 当前 blocker 是配置、凭据、provider 不可达、timeout、owner receipt 缺失，还是 contract 不支持。

## OPL Capability Runtime / ScholarSkills 投影

| capability_id | transport_owner | executor_kind | provider_owner | doctor_status | projection evidence | blocking_reasons |
| --- | --- | --- | --- | --- | --- | --- |
| `opl_capability_runtime` | `one-person-lab` | `opl_runway_or_hosted_provider` | `one-person-lab` | `projection_only_until_live_readback` | MAS 只消费 capability descriptor、prepared run-context ref、execution receipt candidate ref、artifact manifest ref、owner-consumption evidence packet 和 no-forbidden-write proof。 | 缺 OPL live invocation、StageRun / outbox / provider attempt readback、same-identity terminal closeout 或 owner-consumed refs时，不能声明 runtime-ready 或 production-ready。 |
| `mas-scholar-skills.*` | `one-person-lab` for execution; `MedAutoScience` for owner gate | `codex_cli_or_hosted_capability_executor` | `one-person-lab` | `repo_capability_surface_landed` | `scientific_capability_registry` 的 summary / inventory / index / resolve / invoke / CLI owner-consumption ABI、八个 active professional module descriptor consumer、refs-only execution receipt candidate consumer、file-materialized package refs consumer、owner-gate request readback；module catalog/source truth 来自外部 `mas-scholar-skills` repo，不由 MAS docs 复制维护。OPL Connect 默认同步 `mas-scholar-skills`、`medical-research-lit`、`medical-manuscript-writing`、`medical-manuscript-review`、`medical-figure-design`、`medical-figure-style`、`medical-figure-composer`、`medical-statistical-review`、`medical-table-design`、`medical-submission-prep` 和 `medical-data-governance` 到 `.codex/skills/<skill_id>`；`medical-figure-style` / `medical-figure-composer` 是 Display module 子 Skill，不新增 active module。MAS 还在 `optional_skill_ids` / optional path templates 中暴露外部 source 的 optional advanced / medical-method specialist skills：structural biology、protein design、genomics foundation models、single-cell modeling、indication dossier、PDF evidence exploration、scientific compute diagnostics、protocol/SAP、cohort phenotyping、claim map、reference integrity、rebuttal strategy、display QC、causal inference 和 survival analysis；这些只供 OPL Connect source 物化时按需同步真实 skill，不进入默认 core。这个 `.codex/skills/` 同步是 Codex discovery 的必要物理机制，但同步副本只是 runtime projection。写作、审稿、图件和临床数据治理的 stage 主提示词仍由 MAS overlay / stage owner surface 维护，专业 skill 正文与 optional specialist 正文由外部 repo 单源维护。`omics` 没有稳定 MAS 组学专业 workflow 前不作为 active module 暴露；通用 source / external-learning intake 归 OPL Framework 或 MAS stage/source surface。 | 真实论文 truth 仍缺 MAS owner receipt、quality gate receipt、source readiness verdict、route-back evidence、stable typed blocker、human gate 或 canonical artifact delta；classification / externalization guard 和 optional readback 只证明 MAS 不把这些模块或 optional specialist 写成 authority owner，不证明外部模块已运行、optional skill 已安装或 owner gate 已接受。 |
| `academicforge_claude_science.skill_first_pack` | `one-person-lab` for sync/execution substrate; `MedAutoScience` for owner gate | `codex_skill_first_professional_playbook` | `one-person-lab` | `descriptor_refs_landed_live_execution_tail_open` | AcademicForge / Claude Science 32 skill 学习不落成 MAS 私有脚本。MAS 只暴露 `academicforge_claude_science_skill_first_pack`、`academicforge_life_science_specialist_skills`、`academicforge_scientific_compute_runner_skill` 三类 descriptor-only capability：MAS Scholar Skills 用 dedicated `medical-figure-style` / `medical-figure-composer` 承接 figure-style / figure-composer，并由 `medical-figure-design` orchestrator route 回 Display；paper-narrative、literature-review、pdf-explore 进入对应专业 Skill；新增/外置高级专业 skill 承接结构预测、蛋白设计、基因组、单细胞、indication dossier、PDF explorer 和 compute runner。 | Skill 是否实际同步、provider 是否可用、endpoint 是否注册、GPU job 是否成功、专科产物是否被 owner 接受，都需要 OPL Connect / Runway / MAS owner readback；descriptor refs 不能声明 runtime-ready、analysis complete、paper progress 或 publication readiness。 |
| `opl_connect.external-skills` | `one-person-lab` for search/inspect/sync; `MedAutoScience` for owner gate | `selective_specialist_skill_sync` | `one-person-lab` | `on_demand_gap_surface_only` | Codex discovery helper `external-scientific-skills` 只在 current owner delta 出现罕见/重型/专科科学能力缺口时使用：用户显式命名工具/数据库，核心 ScholarSkills route-back 指出缺口，stage policy 判断八个核心 Skill 不足，或联网/云计算/敏感数据路径需要 policy / approval。调用顺序是 external-skills `search -> inspect -> sync`，示例包括 `scanpy`、`pydeseq2`、pathway enrichment、Nextflow、RDKit、PyHealth。 | 不允许 bulk load 外部库，不允许 K-Dense 成为 MAS authority，不允许外部 specialist 写 study truth、paper body、artifact authority、owner receipt、typed blocker、human gate、publication eval、controller decisions、submission package 或 `current_package`；输出只可作为 refs-only candidate 或 owner-gate request。 |
| `kdense_byok_pattern_refs` | `one-person-lab` for Stagecraft / Atlas / Workspace / Ledger / Console / Connect / Runway; `MedAutoScience` for owner gate | `codex_cli_as_opl_harness` | `one-person-lab` | `repo_projection_landed_refs_only` | K-Dense BYOK 只作为 `/tmp/kdense-byok` pattern source，并由 `build_kdense_byok_pattern_advisory`、`build_kdense_byok_catalog_surfaces` 和 `build_kdense_byok_runtime_surfaces` 输出 refs：workflows -> OPL Stagecraft recipe catalog 候选，databases.json -> OPL Atlas source-ref candidate catalog，21 specialists -> Codex specialist roster / independent reviewer lanes，file tree / preview / LaTeX / PDF -> OPL Workspace / Ledger / Console display pattern，cost ledger -> Ledger budget receipts，interview form -> MAS human-gate schema 候选，MCP / Modal -> Connect / Runway policy，OpenRouter Fusion -> watch-only reviewer briefing。 | 不引入 Pi runtime dependency，不要求 K-Dense app、本地 web server、Pi subagent engine、Modal、MCP server、OpenRouter Fusion、外部 skill bulk load、真实 connector credentials 或真实 OPL App UI 才能运行 MAS；K-Dense refs 不能写 study truth、source readiness verdict、paper body、artifact authority、owner receipt、typed blocker、human gate、publication eval、controller decisions、provider attempt、submission package、`current_package`、runtime-ready 或 paper progress。 |
| `mas-scholar-skills.display.gallery_review_refs` | `one-person-lab` for compact ScholarSkills review package; `MedAutoScience` for paper-local Display Pack source and authority boundary | `human_review_ref_package` | `one-person-lab` | `compact_review_refs_only` | 只允许 PDF gallery、reference、status、quality audit、manifest、snapshot 这类 compact review refs 进入 ScholarSkills local install / review index；MAS `outputs/display-pack-gallery/` build workspace 和单图 exports 仍是可再生成本地输出，不作为 workspace / quest install 内容。 | Gallery review refs 不证明 publication-ready、artifact authority、visual audit receipt、owner acceptance 或 paper truth；不得复制 render caches、single-figure PNG/SVG/HTML exports、dependency locks 或 run-context files 到每个 workspace / quest。 |
| `paper_mission_submission_milestone_candidate_package` | `MedAutoScience` | `codex_cli` | `MedAutoScience` for package; OPL only after route handoff | `candidate_package_surface_landed` | `paper-mission package-candidate` 输出 16 个非 authority files，包括 `owner_consumption_request.json`、`owner_blocker_packet.json`、`submission_milestone_checklist.json` 和 paper-facing candidate artifact refs。 | `submission_milestone_candidate` 不是 submission-ready、publication-ready、current package、OPL provider attempt 或 governed owner acceptance。 |

Doctor 对这三类 capability 的结论必须分账：descriptor / package / owner-gate request 可以是 repo capability landed；live runtime invocation、provider closeout、owner gate accepted 和 paper truth accepted 必须等待对应 authority surface。缺 capability 或缺 owner response refs 默认 fail-open，不阻断 current owner action；只有命中 source/data/evidence、owner-route identity、forbidden write、不可逆 mutation、independent reviewer、publication gate、human gate 或 MAS hard gate 时才升级为 blocker。

## Timeout 规则

长时间研究默认由 OPL provider-backed stage runtime 承担，MAS projection 只显示 timeout 能力和 blocker refs。降低 timeout 必须有明确理由，并且不得破坏：

- long-running bash / analysis task
- artifact refresh
- publication package rebuild
- runtime watch / outer-loop wakeup

## 不吸收范围

本 contract 不要求 MAS 追随 upstream 的 Claude、Kimi、OpenCode provider 扩面，也不要求 MAS 私有接管 Temporal / queue / retry-dead-letter / worker residency。它只吸收“runtime capability 应被显式投影和验证”的思路；provider truth 继续归 OPL，domain truth 与 authority refs 继续归 MAS。
