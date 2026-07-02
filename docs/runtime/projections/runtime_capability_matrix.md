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
| `opl.scholarskills.*` | `one-person-lab` for execution; `MedAutoScience` for owner gate | `codex_cli_or_hosted_capability_executor` | `one-person-lab` | `repo_capability_surface_landed` | `scientific_capability_registry` 的 summary / inventory / index / resolve / invoke / CLI owner-consumption ABI、十模块 descriptor consumer、refs-only execution receipt candidate consumer、file-materialized package refs consumer、owner-gate request readback；module catalog/source truth 来自外部 `mas-scholar-skills` repo，不由 MAS docs 复制维护。OPL Connect 默认同步 `mas-scholar-skills`、`medical-research-lit`、`medical-research-write`、`medical-research-review` 和 `medical-research-figure` 到 `.codex/skills/<skill_id>`；其中写作、审稿和图件 skill 正文也由外部 repo 单源维护。非 Display 的 `lit`、`tables`、`stats`、`submit`、`write`、`review`、`data`、`intake`、`omics` descriptor 还暴露 `externalization_guard`，把 migration priority 和 MAS retained authority 固定为 no-second-truth guard。 | 真实论文 truth 仍缺 MAS owner receipt、quality gate receipt、route-back evidence、stable typed blocker、human gate 或 canonical artifact delta；`externalization_guard` 只证明 MAS 不把这些模块写成 authority owner，不证明外部模块已运行或 owner gate 已接受。 |
| `opl.scholarskills.display.gallery_review_refs` | `one-person-lab` for compact ScholarSkills review package; `MedAutoScience` for paper-local Display Pack source and authority boundary | `human_review_ref_package` | `one-person-lab` | `compact_review_refs_only` | 只允许 PDF gallery、reference、status、quality audit、manifest、snapshot 这类 compact review refs 进入 ScholarSkills local install / review index；MAS `outputs/display-pack-gallery/` build workspace 和单图 exports 仍是可再生成本地输出，不作为 workspace / quest install 内容。 | Gallery review refs 不证明 publication-ready、artifact authority、visual audit receipt、owner acceptance 或 paper truth；不得复制 render caches、single-figure PNG/SVG/HTML exports、dependency locks 或 run-context files 到每个 workspace / quest。 |
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
