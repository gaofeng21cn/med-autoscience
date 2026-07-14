# SciPilot Figure Skill Learning Intake

Status: `owner_surface_and_docs_landed`
Date: `2026-07-05`
Owner: `MedAutoScience Medical Display + Stage-Led Autonomy`
Purpose: 记录 `scipilot-figure-skill` 中可学习的科研数据可视化模式如何折回 MAS 文档层、Stage/Skill/Tool 分工和 no-authority 边界。
State: `reference_only_pattern_mapped; owner_surface_landed; refs_only_sidecar_tool_shape_landed; no_runtime_import; no_authority_import`
Machine boundary: 本文是人读学习记录。它不新增 runtime provider、默认 skill source、tool dependency、renderer contract、publication authority、owner receipt、typed blocker、human gate、current package、submission package 或 paper truth。机器真相仍归 MAS owner surfaces、Display Pack contracts、ScholarSkills source pack、quality gates、runtime/readback 和真实 workspace artifacts。

Landing boundary: 本轮停止条件是把可学习点同时落到 MAS figure contract / workflow packet / Stage quality pack / medical-display docs / ScholarSkills professional skill，并把 SciPilot 可执行小工具优势登记为 MAS refs-only sidecar/tool-shape landing。本文声明的是 non-authority owner-surface、docs/professional-skill、sidecar/tool-shape metadata 和 Display Pack workflow projection landing；不声明导入 SciPilot worker、tool adapter、owner receipt 或 production/runtime authority landing。

## 2026-07-05 Source Evidence

Source of truth: `/tmp/scipilot-figure-skill` at commit `43098ddb9e6a6d142218540c114f9ed38922fc42`.

本轮检查了：

- `SKILL.md` 与 `README.md`：定位为 scientific data visualization advisor，强调先数据剖析、论证目标和图型选择，再绘图。
- `references/chart_selection.md`：用变量类型、论证意图和样本量三轴选择图型。
- `references/data_profiling.md`：把列类型、分组样本量、偏度、缺失、异常和相关性转成画图决策。
- `references/viz_pitfalls.md`：主动拦截均值柱、双 Y 轴、饼图、Y 轴截断、rainbow 色图、一图多论点、乱码、裁切和子图编号错位等高频错误。
- `references/journal_specs.md` 与 `references/publication_checklist.md`：记录最终尺寸、字体、矢量优先、色盲安全、误差说明和投稿前机器检查。
- `references/visual_review.md`：提出 PNG preview -> deterministic layout audit -> AI 读图 -> 回改重渲的视觉自检闭环。
- `references/plot_recipes.md`、`scripts/*.py`、`requirements.txt`：实现基于 matplotlib / seaborn / plotly / pandas / scipy 的 Python 绘图工具链，包含 profile、style、export、layout、visual QA 和 check scripts。
- `LICENSE`：MIT。

## MAS Learning Verdict

`scipilot-figure-skill` 的可学习点不是外部 Python 绘图 runtime，而是“先判断、再作图、再读图修正”的工作纪律。MAS 已有 Display Pack、R/ggplot2-first evidence path、ScholarSkills medical-display source pack、visual audit protocol 和 owner gate；因此本次只吸收 advisor patterns 到 MAS-native owner surfaces，不导入外部 runtime、依赖、脚本或 skill 目录。

| pattern | disposition | MAS foldback | landing status | authority boundary |
| --- | --- | --- | --- | --- |
| 数据剖析先于图型选择 | `adapt` | 进入 Stage / medical-display 的 figure-purpose brief 读法，并落到 `plot_selection_quality_floor`：先确认 claim、comparison、sample size、distribution、missingness、grouping 和 source refs，再选图。 | `owner_surface_landed` | 不运行外部 `profile_data.py`，不写 source readiness，不替代 analysis owner。 |
| 图型选择三轴：变量类型、论证意图、样本量 | `adapt` | 进入 MAS figure intent / workflow packet：purpose-first，不按模板名或视觉偏好选图。 | `owner_surface_landed` | 不新增 standalone chart selector，不阻断 canonical owner action。 |
| 主动拦截 bad chart choices | `adopt_as_quality_lens` | 进入 QA gates、figure contract 和 Stage quality pack：均值柱掩盖分布、双 Y 轴、饼图、Y 轴截断、rainbow、分类折线、一图多论点等作为 visual / semantic critique candidates。 | `contract_projection_landed` | finding 只能成为 review note、route-back candidate 或 typed blocker candidate；正式 blocker 仍由 MAS owner surface 产出。 |
| 最终尺寸、矢量优先、字体、灰度/色盲、误差说明 | `adapt` | 落到专业 skill / medical-display 指南 / workflow packet 的 publication-form QA 口径；MAS 已有 display lock、style profile、visual audit 和 PDF 实物复核。 | `professional_skill_and_docs_landed` | 不以外部 checklist 签 publication readiness。 |
| PNG preview + 程序布局审计 + AI 读图闭环 | `adapt` | 对齐现有 `paper/figure_visual_audit_receipt.json` 和 Visual Audit Protocol，并在 workflow packet 中拆出 `qa_split`。 | `owner_surface_landed` | 不用外部 visual_qa 替代 MAS visual audit receipt、owner receipt 或 publication gate。 |
| `profile_data.py` / `chart_selection.md` advisor shape | `adapt_as_refs_only_sidecar_tool_shape` | 映射为 `figure_advisor_probe`：读取 current figure brief、claim/data refs、data profile refs、样本量/分布/缺失/异常/分组 refs，输出 plot-selection rationale 与 warning refs。 | `refs_only_sidecar_tool_shape_landed` | 不运行 SciPilot 脚本，不导入 pandas/scipy/matplotlib 依赖；输出只能进入 figure brief、Stage quality pack、review note、route-back hint 或 typed blocker candidate。 |
| `check_figure.py` / `export_figure.py` export lint shape | `adapt_as_refs_only_sidecar_tool_shape` | 映射为 `figure_export_lint`：读取 rendered artifact refs、layout/display lock、export/profile refs，检查 DPI、最终尺寸、字体嵌入、JPEG 禁用、SVG 位图嵌入、CJK 字体和负号风险。 | `refs_only_sidecar_tool_shape_landed` | 不替代 Display Pack renderer、visual audit receipt、owner receipt、publication gate、submission readiness 或 PDF 实物验收。 |
| Python matplotlib / seaborn / plotly scripts | `reject_runtime_import` | SciPilot scripts 只作为上述两个 tool-shape 的 provenance，不作为 MAS runnable dependency。 | `reject` | 不导入依赖，不新增 SciPilot runtime，不改变 R/ggplot2-first evidence path。 |
| 外部 skill 作为默认 figure skill source | `reject` | MAS stage prompt 仍归本仓，professional skill / display source pack 归 `mas-scholar-skills`。 | `reject` | 不复制 SciPilot skill、prompt、scripts 或 requirements，不作为 default skill pack。 |
| 外部 runtime / graceful fallback behavior | `reject` | MAS 不接受外部 plotting runtime 或 optional dependency fallback 作为 paper progress substrate。 | `reject` | 不导入外部 runner、provider、queue、runtime、currentness 或 authority。 |

## Foldback By Layer

| MAS layer | What to learn | What not to import |
| --- | --- | --- |
| MAS base / runtime | 只保留 progress-first 与 no-authority 读法；已采纳模式折入 `contracts/capability_map.json`、medical figure catalog 与 ScholarSkills，本文保存 source commit 和 adopt/reject provenance。 | 不新增 scheduler、默认 advisory scan、SciPilot Python plotting runtime、scripts import 或 dependency import。 |
| MAS Stage | 在 `figure_evidence_contract_pack` 与 `scipilot_visualization_advisor_ref_floor` 中要求 figure question、variable/sample-size refs、plot-selection rationale、warning ref、deterministic QC ref、AI visual review ref。 | 不把 SciPilot 选图建议写成 owner route 或 hard gate。 |
| Professional skill | `medical-figure-design` 已把“advisor-first、主动拦截、投稿形式 QA、AI 读图闭环”作为 refs-only 教学和 reviewer lens。 | 不复制 SciPilot Skill 正文，不把它变成第二套 ScholarSkills catalog。 |
| Tool / pack | `figure_advisor_probe` 和 `figure_export_lint` 可以作为 MAS/OPL refs-only sidecar/tool-shape：只输出 advisory refs、warning refs、missing route-required refs 或 typed blocker candidate，不写 authority surface。 | 当前不接入 matplotlib / seaborn / plotly scripts，不修改 Display Pack source pack，不把 lint pass 写成 publication readiness。 |

## Refs-Only Sidecar Tool Shapes

| tool shape | SciPilot provenance | MAS owner-surface mapping | output boundary | fail-open policy |
| --- | --- | --- | --- | --- |
| `figure_advisor_probe` | `scripts/profile_data.py`、`references/data_profiling.md`、`references/chart_selection.md`、`references/viz_pitfalls.md` | Display Pack `figure_intent` / `figure_workflow_packet`、Stage `scipilot_visualization_advisor_ref_floor`、ScholarSkills `medical-figure-design` critique refs | data profile refs、plot-selection rationale、small-n / skew / missingness / grouping / misleading-chart warning refs、route-back hint 或 typed blocker candidate | 缺 probe、probe timeout 或非 route-required ref 缺失默认 fail-open；只有 claim/data/source/evidence ref 是当前 route-required 且影响 hard gate 时才升级 candidate。 |
| `figure_export_lint` | `scripts/check_figure.py`、`scripts/export_figure.py`、`references/publication_checklist.md`、`references/journal_specs.md` | Display Pack export/QC refs、layout sidecar / display lock、visual audit protocol、publication manifest refs preservation | DPI/final-size/font/JPEG/SVG-raster/CJK/negative-sign warning refs、export-QA note、route-back hint 或 typed blocker candidate | lint 缺失、失败、低置信或超时不阻断 ordinary progress；lint pass 不签 visual-audit clear、owner receipt、publication readiness、submission readiness 或 PDF 实物验收。 |

## Difference From Nature-Skills Figure Absorption

Nature-Skills figure absorption 已经在 MAS 中承接为 `figure_contract_policy`、`figure_workflow_packet`、composition recipes、publication polish policy 和 Display Pack QA gates。它学习的是 contract-first figure brief、page-level organization、backend/export discipline、render-inspect-revise 和 Nature-style figure production workflow。

SciPilot 的补位不同：

- Nature-Skills 偏 `figure contract / page organization / backend-export QA`；SciPilot 偏 `data profiling / chart-choice advisor / bad-chart interception / publication-form self-check`。
- Nature-Skills 的重点是把 paper figure workflow 变成 MAS-native contracts；SciPilot 的重点是防止 agent 在进入 renderer 前选错图或忽略样本量、分布、色盲、字体和导出检查。
- Nature-Skills 曾有 backend gate；MAS 明确改造成 progress-first，不因 backend 未选而停。SciPilot 也不能把“先问用户论证目标”变成阻塞 gate；agent 应优先从 current owner delta、paper context、claim/data refs 推断，只有 route-required evidence 缺失才形成 owner question 或 typed blocker candidate。
- 两者都不进入 MAS runtime、default skill source、publication authority 或 owner receipt。

## Progress-First Boundary

SciPilot-derived checklist 是 acceleration layer，不是 admission layer。

- 若 MAS 已有 current owner action、claim/data refs 和 Display Pack route，缺 `figure_advisor_probe` / `figure_export_lint` 不阻断 render / audit / owner handoff。
- 若图型选择或导出 lint 缺少 route-required source/data/evidence/export refs，只能生成 route-back hint 或 typed blocker candidate；正式 blocker 必须由 MAS owner surface、independent reviewer/auditor、human gate 或 typed blocker materializer 产出。
- AI/VLM 或人读 visual finding 不能修改 claim、data、statistics、artifact authority、paper body、publication eval、controller decisions、owner receipt、human gate、current package 或 submission package。
- 外部脚本检查通过，只能说明外部脚本检查通过；不能证明 MAS visual audit clear、publication readiness、submission readiness 或 paper closure。

## Learning Landing Audit

| Item | Pattern | Local owner surface | Target landing | Status | Completion | Fresh evidence | Missing refs | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Source capture | Commit-bound upstream inspection | this reference | Record source commit and inspected files | `done` | `100%` | source refs listed above | none | none |
| Classification | adopt / adapt / watch / reject | capability map + ScholarSkills | Map each pattern to MAS Stage / professional skill / hosted tool | `done` | `100%` | current capability refs | none | none |
| MAS base owner surface | Plot-selection floor, bad-chart warnings, QA split | figure contract / workflow packet / QA gates | Expose consumable refs without authority | `done` | `100%` | `figure_contract_policy`, `build_figure_workflow_packet`, `qa_gates.json` | no worker/tool adapter by design | none |
| Stage quality pack | Figure evidence ref floor | `stage_quality_contract/pack_data.py` | Add `scipilot_visualization_advisor_ref_floor` | `done` | `100%` | Stage contract tests | none | none |
| Professional skill | Figure advisor discipline | `mas-scholar-skills/skills/medical-figure-design/SKILL.md` | refs-only critique and QA language | `done` | `100%` | ScholarSkills skill/contract checks | repo-wide ScholarSkills verify has unrelated display-pack descriptor residual | keep residual separate |
| Refs-only sidecar tool shape | `figure_advisor_probe` / `figure_export_lint` metadata and Display Pack workflow projection | MAS runtime / Display Pack / Stage quality pack | Map SciPilot executable-tool advantages without importing scripts/dependencies | `done` | `100%` | `build_figure_advisor_probe` / `build_figure_export_lint`, sidecar/tool-shape rows in adoption contract, focused Display Pack tests | no SciPilot script import by design | code-side sidecar may consume these refs-only shapes only under no-authority / fail-open boundary |
| Runtime / dependency import | External Python stack and scripts | MAS runtime / ScholarSkills / OPL Pack | Reject SciPilot runtime import | `done` | `100%` | reject rows in adoption contract and this file | no runtime dependency by design | revisit only with explicit owner request |

## Current Claim

可声明：`scipilot-figure-skill` 的学习结论已按 MAS docs taxonomy、figure contract / workflow packet、Stage quality pack、ScholarSkills `medical-figure-design` refs-only skill，以及 `figure_advisor_probe` / `figure_export_lint` refs-only Display Pack workflow projection 折回；它是 non-authority advisor-quality / export-lint-quality landing。

不可声明：SciPilot 已成为 MAS dependency、runtime provider、default skill source、Display Pack renderer、quality gate、owner receipt、publication authority、submission readiness authority 或 paper progress evidence。
