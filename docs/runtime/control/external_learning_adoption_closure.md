# External Learning Adoption Closure Runbook

Owner: `MedAutoScience`
Purpose: `external_learning_landing_runbook`
State: `active_runtime_support`
Machine boundary: 本文是人读 external-learning landing runbook。机器真相继续归 MAS `agent/` pack、contracts、source、generated/read-model surfaces、owner callables、worker/sidecar outputs、owner receipts、typed blockers、AI reviewer / auditor records、publication eval、controller decisions、真实 workspace artifacts、OPL current-control 和 repo-native verification。本文不引入外部 runtime，不安装外部 worker，不写 study truth、paper body、artifact body、memory body、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 `current_package`。

## 适用范围

本 runbook 适用于 Co-Scientist、Nature-skills、Academic Research Skills、AutoSci / OmegaWiki、EvoScientist / EvoSkills、ARK、ARIS、PaperSpine、PaperOrchestra、Open Auto Research、K-Dense BYOK、OpenScience 和同类自动研究框架的 MAS intake。

核心规则：**学合同不等于落地**。外部框架的模式被写进 contract、reference intake 或 design doc，只说明 MAS 接受了一个可复用 shape；只有进入 MAS-owned owner surface、generated/read-model projection、worker/sidecar execution slot、callable/action catalog、quality pack consumer、controller-authorized soak 或等价 repo-native surface，并有测试证明边界，才算 functional landing。

2026-06-23 PaperMissionTransaction 读法：外部成熟模式只能折叠成 MAS stage 内的 durable workflow、terminalizer、human interrupt、retry-catch、exit-handler、refs-only advisory 和 owner/auditor separation 共性。它们可以影响 `PaperMissionTransaction` 的 stage design 或 `StageTerminalDecision` 的 outcome taxonomy，但不能被写成依赖外部 runtime、外部 queue、外部 agent framework、外部 dashboard 或外部 memory DB；OPL 仍只消费 MAS terminal decision 派生的 route command。

## Landing Definition

每个外部学习项必须标注一个 landing status：

| status | 含义 | 能否说 landed |
| --- | --- | --- |
| `owner_surface_landed` | MAS owner surface、quality pack、source/artifact/reviewer OS 或 callable 已消费该模式。 | 可以，但必须说明 authority boundary。 |
| `read_model_landed` | generated/product-entry/domain-handler/read-model surface 可稳定投影该模式。 | 可以，但只能说 read-model landed。 |
| `sidecar_or_worker_landed` | 有非阻塞 worker、sidecar、soak 或 owner action execution slot，且声明 allowed writes / forbidden authority / outputs。 | 可以，但不能说它关闭 paper progress 或 quality gate。 |
| `contract_projection_landed` | contract 和 projection 存在，但没有独立 owner callable 或 worker scaleout。 | 只能说 projection landed，不能说 execution landed。 |
| `contract_only_gap` | 只有合同或规则，未接入 owner/read-model/worker/callable。 | 不能说 landed。 |
| `projection_only_gap` | 只有薄投影或 descriptor，缺实际 owner/worker 消费。 | 不能说 execution landed。 |
| `history_only_gap` | 只存在历史设计、旧 intake 或 provenance。 | 不能说 current landed。 |
| `not_landed_gap` | MAS 尚无机器面代表该模式。 | 不能说 learned / absorbed / landed。 |
| `watch_only` | 仅作为漂移观察、provenance 或未来参考。 | 不能进入当前运行面。 |
| `reject` | 不进入 MAS 运行面、truth surface、route surface 或 authority surface。 | 不能落地。 |

## 最小落地门槛

外部学习项从 `adopt_contract` 晋级为 landed，至少满足以下条件：

- 有 MAS / OPL owner：明确 MAS 持有 study truth、quality verdict、publication/artifact/memory/source authority，OPL 持有通用 runtime、queue、attempt、lifecycle、workbench、observability。
- 有可消费 surface：owner surface、read-model projection、worker/sidecar slot、callable/action catalog、quality pack、controller-authorized soak 或 generated surface 至少一项真实存在。
- 有输入输出边界：列出 required inputs、accepted refs、output refs、typed blocker candidate 或 owner receipt boundary。
- 有写边界：列出 allowed writes 和 forbidden writes；默认禁止写 study truth、paper body、artifact body、memory body、publication eval、controller decisions、submission/current package、quality verdict、artifact authority。
- 有 friction guard：缺失、失败、超时、低置信或预算耗尽时默认不阻断 canonical `NextActionEnvelope` / MAS owner-consumed current owner action，除非命中命名 MAS hard gate；旧 `current_executable_owner_action` 只能作为 superseded diagnostic carrier 读取。
- 有测试或验证：focused tests、generated-surface parity、contract sync check、`make test-meta` 或 `scripts/verify.sh` 覆盖 touched surface。

## Lightweight Executor Receipt Contract

MAS 当前吸收的不是 Docker / OpenHands sandbox runtime，而是 lightweight executor receipt contract。该合同用于把 Codex、`uv` clean runner、本地 process / workspace 级尝试的命令证据、stdout/stderr refs、artifact refs、changed-file refs、耗时、env fingerprint 和 failure class 结构化记录下来，供 owner / reviewer / auditor 读取。

- 默认执行层级是 `L0_host_clean_runner` 与 `L1_process_workspace`。这对应现有 Codex / `uv` clean runner / 隔离 worktree / refs-only builder 的轻量执行管理，不要求引入容器。
- `L3_containerized_sandbox` 只允许作为显式 proof lane，用于证明外部 executor receipt shape 和 no-forbidden-write 边界；它不是 ordinary path，不是 admission gate，也不因缺 Docker、缺 OpenHands 或缺 DinD 阻断当前 owner action。
- MAS 在容器内运行时，默认禁用 Docker / DinD / Docker socket mount 作为隐式授权。Docker socket 存在也只是一条 diagnostic，不会把 receipt adapter 升级成可执行 authority。
- `lightweight_executor_receipt` action catalog 入口只是只读合同 projection；它不执行命令、不启动 Docker、不挂载 Docker socket、不写 owner receipt / typed blocker / publication eval / controller decision / current package / submission package，也不关闭 stage、quality gate 或 publication readiness。

## 当前框架读法

| framework | landing status | 当前 MAS 读法 | 下一层只允许怎么推进 |
| --- | --- | --- | --- |
| Co-Scientist | `owner_surface_landed` / `read_model_landed`，execution scaleout 只按当前 owner delta 扩面 | hypothesis portfolio / evidence pack / next-delta tournament / bounded candidate / meta-review 已是 progress-first advisory layer，不是 quality authority。 | 扩展 owner action input refs 或 reviewer briefing，不引入 Co-Scientist runtime。 |
| Nature-skills | `owner_surface_landed` / `contract_projection_landed`，router/manifest/static-fragment 只按 `adopt_template` 读取；具体 worker 或 generated loader 不能默认声称 landed | stage-quality pack 和 reviewer/publication 边界已吸收多类 writing、citation、figure、reader、response patterns；2026-06-18 上游 `1cb9070fdd94929d5f267ce6585ac87e2cba60b3` 的 short router、`manifest.yaml`、`always_load`、axis-specific static fragments 与 on-demand references 只作为 `agent/stages/` + `agent/prompts/` 下 MAS stage prompt authoring、quality pack descriptor、Display Pack descriptor 的 manifest-driven loading 模式。 | 缺 ref 时补 MAS 质量包、descriptor field、owner request 或 typed blocker candidate；不复制 vendor runner，不新增第二 selector、默认 skill source、always-on advisory scan 或 Nature-skills runtime。 |
| SciPilot figure-skill | `owner_surface_landed` / `contract_projection_landed` for MAS figure refs；`professional_skill_landed` for ScholarSkills；`refs_only_sidecar_tool_shape_landed` for `figure_advisor_probe` / `figure_export_lint` | `/tmp/scipilot-figure-skill` commit `43098ddb9e6a6d142218540c114f9ed38922fc42` 只作为 scientific visualization advisor / export-lint pattern source：data profiling before chart choice、argument-first chart selection、bad-chart interception、publication-form checklist 和 PNG/AI visual self-check loop 已折回 `contracts/scipilot_figure_skill_learning_adoption.json`、figure contract / workflow packet、Stage quality pack、`docs/references/mainline/scipilot_figure_skill_learning_intake.md`、medical-display 人读边界、ScholarSkills `medical-figure-design`，以及 MAS refs-only sidecar/tool-shape metadata。 | `figure_advisor_probe` 只能输出 data profile / plot-selection / warning refs；`figure_export_lint` 只能输出 DPI / final-size / font / JPEG / SVG-raster / CJK / negative-sign warning refs。二者 nonblocking、fail-open unless route-required evidence missing；不导入 Python runtime/scripts/dependencies，不改变 R/ggplot2-first evidence path，不新增 blocking gate、default skill source、renderer、owner receipt、publication readiness 或 publication authority。 |
| Academic Research Skills | `sidecar_or_worker_landed` for refs-only claim-support advisory worker | ARS projection、medical material passport 和 source adapter rejection-log 边界已存在；`build_ars_claim_support_advisory` 现在只输出 claim-support、material passport、data-access oversight 和 unsupported-claim gap refs。 | 通过 source/material passport owner refs 或 `run_external_learning_sidecar` 输出进入当前 work unit；没有 owner receipt 前不计 study progress。 |
| AutoSci / OmegaWiki | `sidecar_or_worker_landed` for refs-only source / experiment advisory worker | typed graph、source discovery、negative memory、experiment lifecycle、reviewer verdict 和 artifact QA 作为 MAS refs / quality-pack contracts 读取；`build_autosci_source_experiment_advisory` 只发 source / experiment candidate refs。 | 绑定到当前 owner work unit 的 source discovery 或 experiment lifecycle receipts；没有 owner receipt 前不计 source readiness 或 experiment completion。 |
| EvoScientist / EvoSkills | `sidecar_or_worker_landed` as target architecture；implementation scaleout 不等于 authority | 已固定为 nonblocking current-owner-following sidecar architecture；后续只允许 implementation scaleout。 | 扩展同一 sidecar contract 下的 tool-affordance、observation-memory、failed-path、routing-eval、stop-loss candidates。 |
| ARK | `sidecar_or_worker_landed` for refs-only progress worker | 多个 progress-first contracts 已记录；`build_ark_progress_worker_advisory` 只发 micro-canary、human-decision、real-run closeout、citation lifecycle 和 no-progress evidence refs。 | 一次只把能解除当前 progress blocker 的 candidate ref 晋级为 owner receipt / typed blocker；不引入 ARK queue runtime。 |
| ARIS | `sidecar_or_worker_landed` for refs-only review-import advisory worker | history / aftercare projection / optional review sidecar provenance 已收束；`build_aris_review_import_advisory` 只发 typed input、result import、cross-model reviewer 和 experiment queue hint refs。 | 只做 typed body-free input/output refs 和 owner receipt / typed blocker import；不引入 provider runtime 或 review authority。 |
| PaperSpine | `sidecar_or_worker_landed` for refs-only manuscript authoring advisory worker | `build_paperspine_manuscript_advisory` 只读取 motivation-spine、writing-rationale、evidence-blueprint 和 LaTeX-safe audit ref family，缺 ref 时 fail-open advisory gap。 | 保持 manuscript-authoring advisory refs，不能成为 paper-writing authority、LaTeX build authority 或 publication owner。 |
| PaperOrchestra | `sidecar_or_worker_landed` for refs-only authoring DAG advisory worker | `build_paperorchestra_authoring_advisory` 只读取 authoring DAG、outline plot、literature section 和 autorater ref family，缺 ref 时 fail-open advisory gap。 | 保持 authoring DAG / evaluator advisory refs，不能成为 PaperOrchestra runtime、paper generator、autorater gate 或 publication owner。 |
| Open Auto Research | `read_model_landed` / `controller_authorized_soak`，publication owner receipt 仍是 gap | read-model / controller-authorized soak 可作 readiness accelerator。 | 保持 read-only / refs-only，加 owner receipts 前不能声明 publication readiness。 |
| K-Dense BYOK | `repo_projection_landed` for refs-only pattern advisory / catalog / runtime projection builders；OpenRouter Fusion 只 `watch_only` | `/tmp/kdense-byok` 的 326 workflows、229 database refs、21 specialists、file preview / LaTeX / PDF UI、cost ledger、interview form、MCP / Modal hooks 和 Fusion preset 已折回 `build_kdense_byok_pattern_advisory`、`build_kdense_byok_catalog_surfaces` 和 `build_kdense_byok_runtime_surfaces`，只发 OPL Stagecraft / Atlas / Workspace / Ledger / Console / Connect / Runway 候选 refs。 | 不引入 Pi runtime，不依赖 K-Dense app，不复制 skill catalog，不把 Fusion panel 当 reviewer gate；Codex CLI 仍是 OPL harness，全部输出保持 refs-only / no-authority。builder landed 不等于 runtime-ready、owner accepted、paper progress 或 publication readiness。 |
| OpenScience | `sidecar_or_worker_landed` for refs-only artifact / provenance advisory worker；native viewer / runtime 仍 `watch_only` | OpenScience master `2200ad2` (`2200ad2ec4e2ac7c7ff59c5dcdfaeb0b9a5fda66`) 只作为 local-first research workspace pattern source；`build_openscience_artifact_provenance_advisory` 已把 project-local artifact graph、claimType + graphWarnings、annotation-to-source regeneration、project-local ledger pointer / hash、skill pack governance 与 native viewer affordance 折为 refs-only candidate ref family。新增只吸收 environment / package / kernel capture、rerun-to-reproduce receipt、interactive approval / permission cards、plain-language data-flow disclosure 和 curated connector provisioning 的 owner 映射。 | 不接入 Tauri / Electron / WebUI / OpenCode sidecar / OpenScience MCP / runtime，不复制 OpenScience skill catalog，不把 native viewer、project ledger、artifact graph 或 `science_artifact` MCP 当 MAS truth、artifact authority、owner receipt、typed blocker 或 publication gate；缺 OpenScience advisory / worker / projection 默认不阻断 ordinary MAS owner action。 |
| Light | `sidecar_or_worker_landed` for MAS materializer refs only | `light-advisory-materialize` 生成基础 verified / collision / refusal / fresh-evidence advisory refs；source / data / citation / PRISMA / figure / experiment / statistics / overclaim / argument / style 等 skill-content refs 只在 payload present 或 route-required 时物化。不引入 Light runtime。 | 继续保持 refs-only、budgeted、fail-open；缺 advisory 或 content template 不阻断 owner action。 |

## Progress-first Friction Guard

外部学习默认是 acceleration layer，不是 admission layer。

- 已存在完整 canonical `NextActionEnvelope` / MAS owner-consumed current owner action 时，缺外部 advisory 不阻断 dispatch；旧 `current_executable_owner_action` 不能单独作为阻断或 dispatch authority。
- 外部 worker / sidecar / projection 只能生成 refs-only candidate、reviewer briefing、repair hint、gap visibility 或 typed blocker candidate。
- 只有当前 delta 的 route-required ref 缺失，且影响 source/data/evidence、owner-route identity、forbidden write boundary、不可逆 mutation、independent reviewer、publication gate、human gate 或 MAS hard gate 时，才允许升级为正式 typed blocker。
- 正式 typed blocker 必须由 MAS owner surface、OPL Stage Transition Authority、independent reviewer/auditor、human gate 或 typed blocker materializer 产出；sidecar completion 不能自己阻断 ordinary progress spine。

## 后续优化折回

External-learning 后续优化不再作为 MAS standalone selector / backlog 推进。当前 MAS repo-native callable 入口是 `scientific_capability_registry`，由 action catalog、MCP runtime、CLI/product-entry 和 Agent Tool Arsenal 暴露 `summary / inventory / index / resolve / invoke` ABI；CLI 另提供 `owner-consumption` 文件化 package 消费入口，用于把 MAS Scholar Skills materialized package 归一为 MAS owner-gate request/readback。hosted OPL ordinary path 仍按 OPL family-level `W3-capability-registry-fail-open` 消费这些 ABI。

- `W3-capability-registry-fail-open`：OPL `Atlas + Pack + Stagecraft` 负责 hosted current-delta-bound capability resolver / selector、fail-open policy 和 route-required blocker policy；MAS 只提供 repo-native capability registry ABI 和 domain authority boundary。
- `W4-domain-kernel-manifest`：MAS 负责声明每个 external-learning ref family 的 domain consumption boundary、forbidden authority、owner receipt / typed blocker / reviewer receipt 晋级条件。
- `W7-production-evidence-soak`：只有 ARS claim-support、AutoSci source discovery、ARK micro-canary 等 refs 被真实 owner action 消费并产出 owner receipt、typed blocker、reviewer receipt、human gate 或 route-back evidence 后，才计入 study progress。

因此，MAS 侧不得新增第二 selector、第二 active backlog、always-on sidecar、默认 advisory scan 或独立外部学习调度面；已有 `run_external_learning_sidecar` 继续只是 refs-only worker execution slot，`scientific_capability_registry` 只负责按 `current_owner_delta` 汇总、列出、解析或显式调用已落地 refs-only capability，并通过 CLI 文件输入消费 ScholarSkills package refs。

Nature-skills 2026-06-18 router/manifest 学习项也遵守同一条规则：`manifest.yaml` 的 axes / `always_load` / `references.on_demand` 可以启发 MAS-owned stage prompt authoring、stage quality pack descriptor、Display Pack descriptor 或 generated product-entry descriptor 的加载声明；canonical stage prompt source 仍是 `agent/stages/` + `agent/prompts/`，不能把 Nature-skills manifest、overlay template 或 Codex `.codex/skills` 投影当成 MAS 默认 skill source，也不能在 MAS repo 内新增独立 router selector。若未来推进实现，只能把缺口落为现有 owner surface 可消费的 descriptor field、quality pack ref floor、route-required ref、typed blocker candidate 或 OPL-hosted capability registry 消费项。

OpenScience 2026-07-04 intake 也遵守同一条规则。source ref 已刷新为 OpenScience master `2200ad2`，full SHA evidence 为 `2200ad2ec4e2ac7c7ff59c5dcdfaeb0b9a5fda66`；fresh evidence 来自 `git ls-remote https://github.com/ai4s-research/open-science.git refs/heads/master` 与本地 checkout `git rev-parse HEAD` 同值。已落地范围是 contract policy + docs + refs-only sidecar worker；该 worker 现在可从 `artifact_candidates` 生成 artifact graph refs、claim warning checks、annotation regeneration requests、project ledger pointer/hash 和 native viewer watch projection。它的可复用点不是 Tauri / Electron / WebUI app、OpenCode sidecar、OpenScience MCP server、runtime 或 skill catalog，而是 local-first research workspace 如何把 artifact graph、claim warnings、annotation regeneration、project-local ledger、environment / package / kernel capture、rerun receipt、approval cards、data-flow disclosure 和 curated connector provisioning 组织成可追溯工作面。已落地和后续晋级都只允许折回到以下 owner：

| OpenScience pattern | 推荐折回 owner | MAS / OPL 读法 |
| --- | --- | --- |
| project-local artifact graph | OPL Vault / Workspace / Ledger | 只保存 artifact refs、source refs、lineage、checksum / hash 和 provenance pointer；不写 artifact body、paper body 或 MAS artifact authority。 |
| `claimType` + `graphWarnings` | MAS Quality / Reviewer / ScholarSkills review | 推荐第一落点是 refs-only check：把 claim 类型、unsupported / stale / circular / missing-source warning 作为 reviewer briefing 或 route-back candidate，不直接生成 quality verdict。 |
| annotation-to-source regeneration | MAS Stage / Source / Quality | 推荐第一落点是 annotation-to-source-regeneration：从 reviewer annotation 回到 source refs、claim-evidence refs 或 required ref family，生成 repair hint；只有当前 delta route-required ref 涉及 source / data / evidence 时才可能升级 blocker candidate。 |
| project-local ledger pointer / hash | OPL Ledger / Vault / Console | 推荐第一落点是 project-local ledger pointer/hash：记录本地 ledger ref、content hash、workspace locator 和 displayed status，供 Console drilldown；hash 只证明 candidate provenance，不证明 owner acceptance。 |
| skill pack governance | OPL Pack / Connect / Stagecraft | 只启发 pack descriptor、allowed skill scope、dependency / permission note 和 stage use policy；不复制 OpenScience skill catalog，不新增 MAS 默认 skill source。 |
| native viewer / workspace affordance | OPL Console / Workspace | 仅作为 watch-only operator display pattern；不接入 Tauri / Electron / WebUI / OpenCode sidecar / OpenScience runtime，不把 viewer 状态写成 publication readiness、current package freshness 或 source readiness。 |
| environment / package / kernel capture | OPL Workspace / Pack / Runway / Ledger；MAS Stage / ScholarSkills | 只记录 dependency profile、package lock / install receipt、kernel endpoint/status 和 workspace run-context refs；可作为 execution receipt candidate 或 rerun precheck，不证明 source readiness、artifact authority 或 owner acceptance。 |
| rerun-to-reproduce receipt | OPL Runway / Ledger / Console；MAS Quality / Reviewer | 推荐落点是 rerun receipt candidate：记录 rerun command、input refs、env fingerprint、stdout/stderr refs、artifact hash 和 failure class；只能支撑 reviewer briefing 或 route-back candidate，不能自动关闭 quality gate。 |
| interactive approval / permission cards | OPL Console / Stagecraft / Runway；MAS Stage / human-gate route | 作为当前 action 的 permission / question request shape：action、resource、allow once / always / reject、free-text answer 和 timeout 都是 refs；只有 MAS human gate 或 owner route 消费后才能改变 truth 或 gate。 |
| plain-language data-flow disclosure | OPL Console / Connect / Pack；MAS Source / Quality | 用人读披露说明哪些 raw data / workspace files 留本机、哪些 prompt / file content / command output 会发给 provider；这是 policy / operator trust surface，不是 source readiness verdict 或 privacy approval receipt。 |
| curated connector provisioning | OPL Connect / Pack / Runway；MAS Stage / Source / ScholarSkills | 只把 vetted connector descriptor、package/module、upstream source、secret scope、network policy 和 managed env receipt 作为候选；不把 connector installed、MCP health 或 external API reachability 写成 MAS authority。 |

Progress-first 边界固定为：OpenScience advisory、projection、worker、native viewer、connector provisioning、rerun receipt 或 data-flow disclosure 缺失 / 失败 / 超时，不阻断已有 canonical `NextActionEnvelope` / MAS owner-consumed ordinary owner action。只有当前 delta 的 route-required ref 直接涉及 source / data / evidence，或 OpenScience-derived candidate 指出 forbidden write、independent reviewer、publication gate、human gate 这类 MAS hard gate，才允许升级为 typed blocker candidate；正式 typed blocker 仍必须由 MAS owner surface、OPL Stage Transition Authority、independent reviewer / auditor、human gate 或 typed blocker materializer 产出。

## OPL Connect external-skills gap policy

MAS 默认使用外部 `mas-scholar-skills` 单源维护的八个核心专业 Skill：`display`、`tables`、`stats`、`lit`、`write`、`review`、`submit` 和 `data`。这些 Skill 覆盖常规医学论文写作、审稿、图件、文献、统计审阅、表格、投稿准备与临床数据治理；MAS stage 主提示词仍留在 `agent/stages/` 和 `agent/prompts/`，不迁入外部库。

OPL Connect external-skills 只处理罕见、重型或专科科学能力缺口，不作为默认加载层、第二 catalog 或 MAS authority。调用顺序固定为 `search -> inspect -> sync`，并且只在以下触发条件之一成立时使用：

- 用户显式点名工具、数据库、运行时或 specialist，例如 `scanpy`、`pydeseq2`、pathway enrichment、Nextflow、RDKit、PyHealth。
- 八个核心 ScholarSkills 中的某个 Skill 返回 route-back，明确说明当前 work unit 需要核心 Skill 之外的专科能力。
- MAS stage policy 在 current owner delta 上判断八个核心 Skill 无法覆盖所需 ref family、方法学执行或专业审查。
- 需要联网、云计算、外部凭据、第三方数据库、敏感数据路径或组织策略审批时，先走 policy / approval，再决定是否 sync。

external-skills 的输出仍是 refs-only candidate、execution receipt candidate、owner-gate request 或 route-back hint。MAS 不因外部 skill 被 sync、K-Dense 命中、工具 README 存在或 candidate package 生成而写 study truth、paper body、artifact body、publication eval、controller decisions、owner receipt、typed blocker、human gate、submission package 或 `current_package`。K-Dense 可以作为外部能力发现/学习线索，但不能成为 MAS 技能库、stage prompt、currentness 或 authority source。

## K-Dense BYOK 折回 OPL 的读法

K-Dense BYOK 的可复用点不是它的 Pi SDK backend、local web app 或 BYOK runtime，而是它把研究任务组织成“workflow / database / specialist / workspace / cost / human clarification / tool connector / multi-model judgment”的产品形态。MAS 只吸收这些 shape，落到 OPL-owned substrate，并通过 `med_autoscience.external_learning_progress_workers.build_kdense_byok_pattern_advisory`、`med_autoscience.kdense_byok_catalog_surfaces.build_kdense_byok_catalog_surfaces` 和 `med_autoscience.kdense_byok_runtime_surfaces.build_kdense_byok_runtime_surfaces` 发 refs-only 候选，保持 `Codex CLI as OPL harness`、`no Pi runtime dependency`、`refs-only`、`no-authority`：

2026-07-03 closeout 读法：`contracts/kdense_byok_external_intake.json#/repo_native_projection_builders` 是当前 builder 状态锚点。Catalog surfaces 由 `src/med_autoscience/kdense_byok_catalog_surfaces.py` 投影 Stagecraft recipe catalog、Atlas source-ref catalog、Codex specialist roster 和 workspace artifact preview；runtime surfaces 由 `src/med_autoscience/kdense_byok_runtime_surfaces.py` 投影 attempt replay / lab notebook、cost ledger、connector doctor、remote compute receipt schema、human-gate form schema、Console activity / timeline 和 Fusion watch-only briefing。两组 builder 都是 refs-only、advisory-only、nonblocking、fail-open，测试只证明 MAS repo-native projection 和 forbidden-authority 边界，不证明真实 remote execution、真实 connector credentials、真实 OPL App UI、owner receipt、paper progress、publication readiness 或 `current_package`。

| K-Dense pattern | MAS / OPL foldback | Authority boundary |
| --- | --- | --- |
| `web/src/data/workflows.json` 的 workflow templates | 进入 OPL Stagecraft recipe catalog 候选：每条 recipe 只给 stage policy 提供可选步骤、required refs、placeholder schema 和 suggested capability hints。 | recipe 不能成为 stage completion、NextActionEnvelope、paper progress 或 owner route。 |
| `web/src/data/databases.json` 的 database refs | 进入 OPL Atlas / source-ref candidate catalog 候选：database id、url、domain、category 只作为 source discovery 和 policy approval 输入。 | database catalog 不能替代 MAS source readiness verdict、source truth 或 data access approval。 |
| 21 scientific specialists / sub-agent roster | 映射为 Codex specialist roster 与独立 reviewer lanes；只在 MAS 要求 executor / reviewer 分离、citation/statistics/methodology check 或 route-back briefing 时启用。 | specialist report 只是 reviewer/auditor record candidate；MAS owner surface 才能签 owner receipt、typed blocker、quality verdict 或 human gate。 |
| project file tree、preview、bioinformatics readers、LaTeX editor、PDF viewer | 映射为 OPL Workspace / Ledger / Console display pattern：workspace 持文件拓扑，Ledger 持 refs / manifest / checksum，Console 展示 preview / compile diagnostics。 | preview、PDF render、LaTeX compile 和文件存在都不是 artifact authority、publication readiness 或 `current_package` freshness。 |
| `.kady/runs/<session>/costs.jsonl` cost ledger | 映射为 OPL Ledger budget receipts：agent、specialist 和 compute spend 分账，供 Console 展示和 budget guard 读取。 | cost receipt 不能证明研究质量或 progress；预算耗尽默认是 typed route / human decision 输入，不是论文结论。 |
| inline interview form | 映射为 MAS human-gate schema 候选：structured question id、single/multi/text/image answer、recommended option、timeout 和 attachments。 | 表单答案必须经 MAS human gate / owner route 消费后才可改变 study truth、source readiness 或 artifact mutation。 |
| MCP servers 与 Modal compute | 映射为 OPL Connect / Runway policy：Connect 负责 tool trust、secret scope、server health；Runway 负责 remote execution receipt、file-in/out、timeout、cost 和 fail-open / fail-closed。 | 不把外部 MCP、Modal sandbox 或 remote compute 写成 MAS runtime owner、provider attempt authority 或 direct artifact mutation authority。 |
| OpenRouter Fusion | 仅作为 watch-only reviewer briefing pattern：多模型 panel 可启发 methodology critique、literature synthesis 或 claim-support cross-check briefing。 | Fusion 没有 local tools、不可复现且 source 不完整；不能成为 independent reviewer gate、quality verdict、publication readiness 或 owner receipt。 |

## Scientific Capability Registry landing

External-learning 的当前统一落地面是 `scientific_capability_registry` + ScholarSkills owner-consumption，而不是 MAS 私有 selector、第二 backlog 或外部 runtime。外部框架可以进入三类 capability surface：

- `refs_only_advisory_capability`：ARS、AutoSci / OmegaWiki、ARK、ARIS、PaperSpine、PaperOrchestra、Light 等只输出 refs-only advisory / candidate refs，默认 fail-open。
- `scholarskills_module_capability`：图、表、统计、文献、写作、review、投稿和数据治理八类 active 学术能力以 `mas-scholar-skills.<module>` descriptor、required ref families、execution receipt candidate 和 file-materialized package manifest 暴露给 MAS。
- `paper_mission_candidate_package_capability`：`paper-mission package-candidate` 将当前 PaperMission readback 转成 16 个非权威候选文件，包括 `owner_consumption_request.json`、`owner_blocker_packet.json`、`submission_milestone_checklist.json` 与 paper-facing candidate artifacts，用于 owner-consumption-first。

`scholarskills_module_capability` 的 source of truth 是外部 `mas-scholar-skills` repo 的 skill entry 和 module contract。`medical-manuscript-writing`、`medical-manuscript-review`、`medical-figure-design`、`medical-research-lit`、`medical-statistical-review`、`medical-table-design`、`medical-submission-prep` 和 `medical-data-governance` 作为可同步的 professional specialist skill 由该仓库维护。`omics` 没有稳定 MAS 组学专业 workflow 前不作为 active module 暴露；通用 source / external-learning intake 归 OPL Framework 或 MAS stage/source surface，不放进 MAS Scholar Skills 专业 Skill 库占位。MAS 的 `write`、`review`、`figure`、`data/cohort` 等 stage 主提示词 canonical source 仍是本仓 `agent/stages/` + `agent/prompts/`。MAS 只引用外部 source 的 descriptor/readback、authority false flags、required ref families、专业 skill source refs 和 compact review refs，不在本仓维护第二套 ScholarSkills catalog 或第二套专业 skill 正文；`src/med_autoscience/overlay/templates/*.SKILL.md` 与 `.codex/skills/medical-research-*` 是 Codex 自动发现兼容投影，必须保留同步机制，但不能当作 stage 或 specialist source。Display gallery 的跨仓传播只允许 compact review package：PDF gallery、reference、status、quality audit、manifest 和 snapshot；不得把 MAS `outputs/display-pack-gallery/` build workspace、render caches、single-figure PNG/SVG/HTML exports、dependency locks、run-context files 或其他大规模中间产物复制进每个 workspace / quest local install。

这些 landing 的共同 contract 是：stage 主提示词、professional skill、tool/connector 三段默认都保持 no-authority boundary。MAS 可以 `summary` / `inventory` 汇总当前能力面，发现、resolve、invoke readback、消费 refs、生成 owner-gate request 或 owner-blocker packet；MAS 不因这些 refs 直接写 study truth、paper body、artifact body、publication eval、controller decisions、owner receipt、typed blocker、human gate、submission package 或 `current_package`。当 external-learning / ScholarSkills package 缺 required refs、含 truthy authority flag、含 forbidden `written_files` 或 module id mismatch 时，consumer fail closed；当只是缺 advisory 或缺 owner response refs 时，ordinary current owner action fail-open 继续推进。

只有后续 MAS owner surface 返回 owner receipt、quality gate receipt、reviewer receipt、route-back evidence、stable typed blocker、human gate 或 accepted canonical artifact delta，external-learning output 才能从 capability candidate 晋级为真实 paper / study progress。

## 不再走的路径

- 不把 `adopt_contract`、reference intake、design doc、score、ranking、checklist、skill inventory 或 external README 写成 landed。
- 不复制外部 runtime、queue、scheduler、worker residency、memory DB、project DB、router、dashboard、Telegram/webapp service 或 slash skill source。
- 不接入 OpenScience Tauri / Electron / WebUI / OpenCode sidecar / MCP / runtime，不复制 OpenScience skill catalog，不把 `science_artifact` MCP、native viewer、project-local ledger、connector provisioning、rerun receipt 或 artifact graph 写成 MAS study truth、artifact authority、owner receipt、typed blocker、publication gate 或 source readiness verdict。
- 不把 external review score、self-review checklist、tool selector score、observation memory、wiki graph、passport、issue DB 或 citation table 写成 MAS truth、quality verdict、publication readiness、artifact authority、memory accept/reject 或 owner receipt。
- 不为补齐外部 intake 重新制造 full lifecycle preflight、read-model reconcile loop 或每步 checklist gate。
- 不把 external-learning 后续优化写成 MAS 私有 selector / resolver / backlog；hosted selector / resolver 归 OPL Capability Registry，MAS repo 只暴露 `scientific_capability_registry` ABI、refs 消费与 authority 晋级边界。

## 验证门槛

Docs-only 更新至少运行：

```bash
rtk git diff --check
rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs
```

触碰 machine-readable contract、generated surface、action catalog、owner callable、worker/sidecar 或 tests 时，至少补跑对应 focused tests 和：

```bash
rtk make test-meta
rtk scripts/verify.sh
```
