# Medical Manuscript First-Draft Quality Policy

## 目标

MAS/MDS 的医学论文初稿不能只是研究执行日志、结果汇总或投稿包清单。初稿在生成时就必须是医学期刊可读的 manuscript-shaped prose，并且在写作前绑定研究类型、报告规范、证据边界和读者问题。

## 外部规范基座

- ICMJE Recommendations: manuscript body follows the usual Introduction, Methods, Results, and Discussion logic for original research.
- EQUATOR Network: reporting guideline selection is a pre-draft responsibility, not a post-hoc proofing step.
- TRIPOD / TRIPOD+AI: prediction-model manuscripts must define target population, prediction timepoint, outcome horizon, intended use, predictors, missing data, model specification, validation, calibration, and clinical utility before drafting.
- STROBE: observational manuscripts must define design, setting, participants, variables, data sources, bias, missing data, statistical methods, limitations, and generalizability.

## MAS/MDS 合同层

`study_charter.paper_quality_contract.structured_reporting_contract.first_draft_quality_contract` is the upstream owner for first-draft quality. It now carries two mandatory parts:

- `imrad_section_contract`: title, abstract, introduction, methods, results, discussion, and conclusion section purposes.
- `manuscript_native_prose`: prose must be journal-style medical writing, not controller notes, figure/table anchors, author-confirmation placeholders, or work-report question/answer narration.
- `pre_draft_writing_readiness_contract`: first draft writing cannot begin until clinical question, population/design/outcome, display-to-claim map, claim-evidence map, section purpose, reader-flow plan, journal voice, and AI prose-review feedback loop are closed as machine-readable readiness items.
- `first_draft_generation_model`: the writer must start from clinical problem, study design, population, timepoint, outcome, analysis plan, display-to-claim map, and reader-facing contribution; if those inputs are missing, route back before drafting.

`medical_quality_operating_system_contract.quality_contract.first_draft_manuscript_quality_contract` projects the same rule with guideline-specific obligations selected from STROBE, TRIPOD, TRIPOD+AI, CONSORT, CONSORT-AI, PRISMA, and RECORD.

## 003 差异复盘

The user-edited 003 manuscript reads as a medical article because it starts from clinical context, objective, cohort, model validation, results, interpretation, and limitations. The MAS draft drifted toward a work report because internal execution scaffolding was allowed to enter the article body:

- Results were narrated as "The clinical question was ... The answer was ...", preserving the controller's analysis checklist instead of journal prose.
- `Figure and Table Anchors` was emitted as a manuscript section, although it is packaging metadata.
- Declaration placeholders and author-confirmation instructions were mixed into the article body instead of remaining in submission TODO surfaces.
- Figure legends explained what reviewers could identify and what the figure "defines", which is an operations/review framing rather than a reader-facing legend.
- Controller language such as claim boundaries, model protagonist, and manuscript role labels leaked into clinical interpretation.

The durable fix is therefore pre-draft routing plus manuscript-native prose generation, with the gate left as a final safety net.

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
- administrative placeholders belong in submission metadata or TODO surfaces, not in the article body;
- figure legends must explain the display for readers, not describe what reviewers can identify or what the figure itself "defines".

## Gate 角色

`medical_publication_surface` remains a safety net. It blocks work-report residue such as:

- `The first clinical question was ... The answer was ...`
- `Figure and Table Anchors`
- author-confirmation placeholders in the manuscript body
- figure self-explanation paragraphs
- paper-scaffold labels such as `paper protagonist` or `bounded complexity benchmark`

The gate is not the primary writing strategy. The primary strategy is contract-first generation through study charter and quality OS surfaces.
