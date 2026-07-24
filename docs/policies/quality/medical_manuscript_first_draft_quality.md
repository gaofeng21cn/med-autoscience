# Medical Manuscript First-Draft Quality Policy

Owner: `MedAutoScience`
Purpose: `Define stable MAS quality, publication, evidence, and reviewer policy boundaries.`
State: `active_policy`
Machine boundary: Human-readable policy only; quality verdicts, publication truth, evidence state, and reviewer receipts remain in MAS authority functions, contracts, artifacts, ledgers, and owner receipts.

## 目标

MAS 的医学论文初稿不能只是研究执行日志、结果汇总或投稿包清单。初稿在生成时就必须是医学期刊可读的 manuscript-shaped prose，并且在写作前绑定研究类型、报告规范、证据边界和读者问题。历史 MDS / DeepScientist 只能作为 stage discipline、fixture 或 provenance 参考，不能作为初稿质量 owner。

## 外部规范基座

- ICMJE Recommendations: manuscript body follows the usual Introduction, Methods, Results, and Discussion logic for original research.
- EQUATOR Network: reporting guideline selection is a pre-draft responsibility, not a post-hoc proofing step.
- TRIPOD / TRIPOD+AI: prediction-model manuscripts must define target population, prediction timepoint, outcome horizon, intended use, predictors, missing data, model specification, validation, calibration, and clinical utility before drafting.
- STROBE: observational manuscripts must define design, setting, participants, variables, data sources, bias, missing data, statistical methods, limitations, and generalizability.

## MAS 合同层

`study_charter.paper_quality_contract.structured_reporting_contract.first_draft_quality_contract` is the upstream owner for first-draft quality. It now carries two mandatory parts:

- `imrad_section_contract`: title, abstract, introduction, methods, results, discussion, and conclusion section purposes.
- `manuscript_native_prose`: prose must be journal-style medical writing, not controller notes, figure/table anchors, author-confirmation placeholders, or work-report question/answer narration.
- `pre_draft_writing_readiness_contract`: first draft writing cannot begin until clinical question, population/design/outcome, display-to-claim map, claim-evidence map, section purpose, reader-flow plan, journal voice, and AI prose-review feedback loop are closed as machine-readable readiness items.
- `first_draft_generation_model`: the writer must start from clinical problem, study design, population, timepoint, outcome, analysis plan, display-to-claim map, and reader-facing contribution; if those inputs are missing, route back before drafting.
- `medical_prose_review_request`: final language polish is a required AI-reviewer loop, not an optional copy-edit. The reviewer must check four axes before a clear verdict: de-internalize workflow/TODO/package language, de-duplicate repeated boundary statements, de-defend limitations and descriptive-study rationale, and remove AI/data-engineering voice such as `analytic surface` or `data surface`.

`medical_quality_operating_system_contract.quality_contract.first_draft_manuscript_quality_contract` projects the same rule with guideline-specific obligations selected from STROBE, TRIPOD, TRIPOD+AI, CONSORT, CONSORT-AI, PRISMA, and RECORD.

`artifacts/agent_lab/medical_manuscript_quality/latest_suite.json#/tasks/0/mechanism_evolution_inputs/first_draft_quality_route_back_checklist` 是 Agent Lab / OMA 可消费的 route-back regression surface。它必须把“是否像高质量医学论文初稿”拆成可执行项，而不是只报告 blocked：Methods reproducibility、Results numeric estimates and uncertainty、formal medical figures/tables、Abstract hard metrics and uncertainty、result-driven non-defensive Discussion、runtime/internal QA language purge, and claim-evidence alignment. 每个项目必须带 blocker、route_target、owner、next_work_units、evidence_refs 和 expected_repair_result。该 checklist 只能触发 MAS repo patch / owner route-back regression，不能授权 publication quality、submission readiness、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal/` 或 `manuscript/current_package/` 写入。

## 003 差异复盘

The user-edited 003 manuscript reads as a medical article because it starts from clinical context, objective, cohort, model validation, results, interpretation, and limitations. The MAS draft drifted toward a work report because internal execution scaffolding was allowed to enter the article body:

- Results were narrated as "The clinical question was ... The answer was ...", preserving the controller's analysis checklist instead of journal prose.
- `Figure and Table Anchors` was emitted as a manuscript section, although it is packaging metadata.
- Objective author facts were previously handled as defensive manuscript prose
  or detached submission notes. The corrected model preserves the ideal article
  structure, inserts only the minimum local `[AUTHOR INPUT: ...]` annotation,
  and derives the submission To-Do surface from one registry.
- Figure legends explained what reviewers could identify and what the figure "defines", which is an operations/review framing rather than a reader-facing legend.
- Controller language such as claim boundaries, model protagonist, and manuscript role labels leaked into clinical interpretation.

The durable fix is therefore pre-draft routing plus manuscript-native prose generation, with the gate left as a final safety net.

## 2026-05-16 DPCC 003 平台缺陷复盘

DPCC 003 暴露的不是单篇返修 intake 缺失，而是初稿前质量授权链路曾缺少一段硬门槛。当前 MAS 已把 phenotype / treatment-gap observational paper 的结构化报告合同接入初稿前 owner surface：

- `study_charter` 与 `medical_reporting_contract` 必须为 `clinical_subtype_reconstruction` / `phenotype_real_world_treatment_gap` 物化 phenotype derivation、recorded treatment-gap、baseline characteristics 和 data-quality reporting obligations。
- `pre_draft_quality_runtime` 在授权 first full draft 前读取 charter-owned structured reporting checklist；未闭合时 `full_drafting_authorized=false`，并 route back 到 `pre_draft_writing_readiness`。
- `medical_reporting_audit` 与 `medical_publication_surface` 继续作为后置 safety net，防止 checklist closure 漂移或交付物把内部控制语言带入正文。
- Agent Lab medical manuscript quality suite 还必须把 DPCC 003 这类交付物反馈转成 study-family-specific regression target，让 OMA/opl-meta-agent patch MAS repo 时看到 phenotype / treatment-gap 目标，而不是复用 DM002 external-validation target。

新的平台要求是：phenotype / treatment-gap paper 的以下项目必须在 first full draft 前成为 machine-readable blocker，而不是交付后的审稿式补救项：

- phenotype derivation: assignment method, clinical domains/features, rules or algorithm, class-count rationale, reproducibility / new-patient assignment, analysis-plan or prespecification status;
- treatment gap: numerator, denominator, eligibility, time window, medication data source, interpretation label / non-causal guardrail;
- baseline table: total population, phenotype columns, denominators, missingness, core clinical variables, units, comparison or balance statistics;
- data quality: source record checks, plausibility checks, diagnostic-variable ascertainment, adult/known-age applicability sensitivity, variable missingness, semantic field checks, attrition denominators, claim impact or downgrade.

`pre_draft_quality_runtime_state.readiness.full_drafting_authorized` must stay false until these checklist blockers are closed or explicitly routed back. AI reviewer remains the quality owner for publishability and medical-journal prose; the structured checklist is a deterministic pre-draft blocker, not a substitute subjective reviewer.

## 初稿生成门槛

Before a first full draft is treated as generated:

- reporting-guideline family must be resolved;
- section-level contract must be available to the writer;
- clinical question, target population, timepoint, outcome horizon, analysis plan, and display-to-claim map must be available before main text generation;
- claim-evidence mapping and display-to-claim mapping must be closed before Results prose is generated;
- controller checklists, run logs, progress prose, generic completion checklists, and packaging metadata cannot authorize manuscript-body quality;
- if verified evidence surfaces support a stronger paper shape, MAS routes back to bounded analysis or an analysis campaign instead of writing a light descriptive first draft;
- results narrative must answer clinical findings directly, then cite figures/tables as support;
- limitations must be written as clinical interpretation, not as claim-boundary/controller language;
- registry and observational manuscripts should state denominator, source, causal, prognostic, and treatment-response boundaries in compact clinical language; they must not repeat long defensive disclaimer lists across Abstract, Methods, Results, Discussion, and legends;
- objective facts available to the author, institution, data owner, or
  submission owner use a minimum local `[AUTHOR INPUT: ...]` annotation at the
  exact manuscript location where the final fact belongs; all such annotations
  are registered once and projected into the submission To-Do list;
- scientific evidence gaps must never be disguised as author-input annotations;
  they route back, constrain the claim, become a scientific limitation, or are
  omitted;
- terms such as `analytic surface` and `data surface` should be rewritten as analytic cohort, analytic dataset, registry dataset, measured fields, or available measurements;
- figure legends must explain the display for readers, not describe what reviewers can identify or what the figure itself "defines".
- internal correction provenance, debug history, and preprocessing repair history must not become the title, objective, Results, Discussion opening, conclusion, novelty claim, or figure-legend story. Corrected preprocessing definitions belong in Methods or table notes only when needed for reproducibility; the article body should report the final analysis estimates as the clean scientific story.

### 描述性表型 / treatment-gap 初稿门槛

这类稿件不能只写成“分成若干组并报告各组比例”。first full draft 前必须回答描述性 atlas 的医学发现问题：这些表型是否揭示了可审计的临床负担、记录用药覆盖、轨迹或服务差异模式。

以下内容缺失时，默认 route back 到 bounded analysis-campaign、figure/table repair、write 或 decision，而不是生成轻描述初稿：

- discovery contract：一句话写清 phenotype atlas 揭示的医学/服务复核模式，而不是只列 class count；
- hierarchy rationale：说明规则层级顺序的医学复核依据、未单列领域的处理依据、new-patient assignment 规则和 prespecification 状态；
- burden-medication discordance：至少有一个 phenotype x burden x recorded medication-coverage matrix，或明确 waiver；
- exact gap definitions：每个 gap 指标必须有 numerator、denominator、eligibility、time/index window、medication source、class mapping 和 non-causal interpretation label；
- medication-record sensitivity：当 medication record 不完整时，必须规划或完成 medication-field-present / any-recorded-medication sensitivity；否则只能写 documentation-sensitive review signal；
- diagnostic ascertainment：当 uncontrolled disease、hypertension、dyslipidemia、complication burden 或 phenotype assignment 来自结构化字段时，必须物化诊断/测量变量 ascertainment table；
- variable quality atlas：phenotype-defining variables 的 missingness、plausibility、semantic field checks 和 claim impact 必须进入 table 或 supplement；
- site/trajectory robustness：如果稿件要有“医学发现感”，优先检查 site-level variation、transition category、calendar-year / threshold / adult-known-age / age sensitivity；不要用 p-value pile-up 替代稳健性；
- unsupported evidence gap：calendar-year、repeated-visit、site variance 或中心差异没有当前证据时，必须成为 analysis-campaign gap 或 typed waiver，不能写成 Results 发现；
- service-priority contrast：gap 结果必须区分 rate、count 和 service-priority burden，避免把高比例小人群与低比例大人群混成同一结论；
- figure argument：cohort flow、phenotype/gap matrix、transition/site display 和 gap rate/count display 必须服务中心医学论点，rate 和 count 不得混成一个不可解释图；
- figure/table terminology and retention：Figure/Table、main/supplementary、rate/count、gap/coverage/review-signal 等术语必须一致；补充表图不能因主文压缩被静默丢弃，应保留在 supplement 或记录 typed blocker；
- terminology guardrail：没有 guideline-specific eligibility、contraindication、age/eGFR target 和 citation contract 时，不得把 recorded gap 写成 guideline nonadherence；优先用 recorded medication-coverage gap、treatment-review signal、burden-medication discordance。

### 预测模型外部验证初稿门槛

这类稿件不能只是一组 C-index / calibration 指标摘要。first full draft 前必须把以下内容作为 pre-draft blocker 或已闭合 evidence surface：

- source model：模型来源、完整公式或系数表、变量编码、单位转换、5 年 baseline survival / absolute-risk extraction；
- validation cohort：数据年份、纳排、疾病定义、结局随访、5 年状态构建、删失/KM/IPCW 或二分类处理依据、缺失与 complete-case 策略；
- survey policy：NHANES 等复杂抽样数据必须写清 unweighted 边界，并在需要时规划 survey-weighted sensitivity；
- tables：Table 1 队列对比、Table 2 性能指标、按风险组/十分位的 grouped calibration table 必须有明确 shell、denominator、uncertainty 和 source refs；
- figures：development risk-bin occupancy 与 validation self-quantile calibration 不得混画；若 validation cohort 全落入 development low-risk bin，必须把 occupancy collapse 和 within-validation ranking 分开展示；
- calibration interpretation：极端 calibration slope、窄预测风险范围、O:E mismatch 必须解释为 risk-scale compression / baseline-risk mismatch / support mismatch 等受限解释，不能写成可部署绝对风险；
- decision curve：没有 verified threshold range、net-benefit calculation、calibration basis 和 clinical action scenario 时，不得保留主图 DCA，也不得在 Methods/Results 外包装成 clinical utility。

## Gate 角色

`medical_publication_surface` remains a safety net. It blocks work-report residue such as:

- `The first clinical question was ... The answer was ...`
- `Figure and Table Anchors`
- author-confirmation placeholders in the manuscript body
- figure self-explanation paragraphs
- paper-scaffold labels such as `paper protagonist` or `bounded complexity benchmark`
- paper-facing figure layout sidecars with invalid normalized box geometry or overlapping text boxes
- reference databases that are substantially larger than the manuscript's cited reference footprint

The gate is not the primary writing strategy. The primary strategy is contract-first generation through study charter and quality OS surfaces.

## Reporting Closure Consumption

`medical_reporting_audit` and `medical_publication_surface` must consume closed reporting truth surfaces before applying structured reporting blockers:

- `paper/reporting_guideline_checklist.json` can close structured reporting checklist items only when the overall checklist and the mapped guideline domain are explicitly closed and have evidence refs.
- Unsupported domain IDs, open statuses, or missing evidence do not clear structured reporting blockers.
- `paper/table_figure_claim_map.json` can close the claim-to-display blocker only when it contains at least one claim with a table or figure reference.
- This is a strict truth-surface bridge, not a legacy compatibility layer: stale placeholders inside `medical_reporting_contract.structured_reporting_contract` must not override newer closed guideline and claim-map surfaces.

## Finalize 授权边界

初稿或修复稿进入 bundle/finalize 阶段前，MAS 必须同时满足交付 gate 与 AI reviewer 稿件质量闭合。`publication_gate` clear 只能说明机械完整性、证据投影或交付面阻塞已经清掉；它不能替代医学期刊论文质量判断。

因此，`current_required_action=continue_bundle_stage` 或 `complete_bundle_stage` 时：

- `medical_journal_prose_quality.status=ready` 才能继续进入 `finalize`；
- `ready` 必须来自当前 AI reviewer request / manuscript 快照，`request_digest`、`manuscript_ref` 与 `manuscript_digest` 必须能在 reviewer trace 中对齐；
- AI reviewer clear verdict 必须包含 IMRAD 关键段落诊断和代表性改写证据，不能只给概括性通过语；
- `current_package_freshness.source_eval_id` 必须匹配当前 AI reviewer publication eval，旧 human-facing package 不能被新的质量标签隐式授权；
- 缺少 `medical_prose_review_status` 时按 `underdefined` 处理；
- `underdefined`、`partial` 或 `blocked` 必须 route back 到同一论文线 `review`，由 AI reviewer 关闭 manuscript-native prose quality；
- 不得新增“脚本检查论文是否完整 / 是否像医学论文”的质量授权门。程序化检查只允许成为 evidence snippets、mechanical safety flags 或投影 blocker，不能成为主观稿件质量 owner。
