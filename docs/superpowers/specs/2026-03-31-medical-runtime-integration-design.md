# Medical Runtime Integration Design

Date: `2026-03-31`

## Context

当前 `MedAutoScience` 与 `DeepScientist` 的关系已经比较清楚：

- `MedAutoScience` 是唯一正式研究入口
- `DeepScientist` 是通用 quest runtime
- 医学研究治理、投稿约束、paper-facing contract 应优先放在 `MedAutoScience`

现阶段最主要的缺口，不再是“DeepScientist 会不会跑”，而是“它会不会沿着医学论文可接受的方式持续推进，并且能稳定承接已有医学资产”。

围绕这个问题，已经收敛出三个明确优化目标：

1. 医学论文实验调整
   - 让 runtime 不再只偏向 AI/ML 论文默认实验包，而是显式面向医学论文需要的分析与证据结构。
2. 文献检索源优化
   - 让医学研究不再隐含退化为 arXiv-first，而是具备 PubMed / PMC / DOI 驱动的主文献层。
3. `MedAutoScience` 与 `DeepScientist` 的衔接
   - 让 `DeepScientist` 不再从“几乎空白”的 quest 起步，而是从已有 literature、已有 framing、已有结果、已有 manuscript contract 起步。

这三个目标本质上不是三个孤立功能，而是一条统一的受管研究运行链：

- `MedAutoScience` 先决定医学研究 contract
- `MedAutoScience` 再把已有状态注入 quest
- `DeepScientist` 在该 contract 下推进实验、分析、写作与 review
- `MedAutoScience` 在关键节点提供文献补引、医学审计与交付 gate

## Problem Statement

当前问题不是单点 bug，而是 runtime 语义与医学研究治理之间仍有三处断层：

### 1. Experiment contract mismatch

`DeepScientist` 默认擅长的 follow-up package 更偏：

- 消融
- 鲁棒性
- 普通 error analysis
- benchmark-style comparison

但医学论文通常要求的不是这套默认包，而是与任务 archetype 绑定的 paper package，例如：

- calibration / recalibration
- decision-curve / threshold / utility analysis
- subgroup heterogeneity
- external validation / temporal validation
- gray-zone triage yield
- case-mix transportability
- endpoint provenance caveat
- manuscript-safe reproducibility surface

如果不把这些要求写成一等公民 contract，runtime 就会继续按通用 AI 论文直觉推进。

### 2. Literature source mismatch

当前 `DeepScientist` 原生的一等公民文献接口主要是 arXiv。对医学论文来说，这会带来两个问题：

- 写作和 review 期的主动补引会天然偏 arXiv
- 已有医学文献资产即使存在，也没有被稳定前置为 runtime truth source

因此问题不只是“多接一个搜索源”，而是要建立医学文献层的权威顺序。

### 3. Startup state mismatch

当前 quest 创建时只建立最小骨架，`MedAutoScience` 侧已经存在的资产没有被系统承接：

- 已有 literature
- 已有 protocol / framing
- 已有 baseline notes
- 已有结果与 artifacts
- 已有医学写作 contract

这导致 `DeepScientist` 经常像“新接手的陌生人”一样重新摸索，而不是作为一个连续 runtime 承接已有研究状态。

## User-Level Requirements

本次设计必须满足以下要求：

1. 不以修改 `DeepScientist core` 作为前提
2. 不采用事后兜底、局部稳定化或启发式补救
3. `MedAutoScience` 必须成为医学研究 contract、文献层和 quest 起点的权威入口
4. runtime 必须能持续推进实验、分析、写作、review，而不是只在启动时拿到一句 prompt
5. 医学稿件的交付前审计必须是硬 gate，不是“建议复查”

## Design Goals

### G1. Keep DeepScientist as generic runtime

继续把 `DeepScientist` 视为通用 quest runtime，不把医学论文专有 schema 塞回上游 core。

### G2. Make MedAutoScience the medical truth layer

医学论文实验 contract、文献权威层、startup hydration、submission audit 都由 `MedAutoScience` 主导。

### G3. Raise quest starting state

正式 quest 启动前必须完成 hydration，使 runtime 起点能承接已有工作。

### G4. Close the literature loop during writing and review

不能只做“启动前把文献塞进去”；当 write/review 暴露新的引文缺口时，也要有受管的医学文献补引闭环。

### G5. Use hard gates, not soft hints

关键 contract 不满足时应阻断 route，而不是依赖 prompt 说服或后处理清洗。

## Non-Goals

- 不在本次设计中给 `DeepScientist` 原生新增 `artifact.pubmed(...)`
- 不在本次设计中重写 `DeepScientist` 的 daemon / turn loop / memory core
- 不在本次设计中把所有医学实验逻辑都做成上游 skill patch
- 不把论文质量控制降级成一次性的终稿人工 polish

## Current System Facts

### A. `MedAutoScience` 已经接管了一部分医学写作 surface

这一层已经不只是“文风像医学论文”，而是已经包含：

- `general_medical_journal` 写作 profile
- AMA 引文风格
- 医学 Methods / Results / figure semantics / reproducibility manifest
- manuscript-facing forbidden language 检查
- 医学 review gate

因此，本次设计不需要重复解决“计算机论文腔”的基础问题，而是要把实验、文献和 startup continuity 继续补齐。

### B. `DeepScientist` 已支持 richer startup context

`entry_state_summary`、`review_summary`、`review_materials`、`custom_brief` 会被当成 active runtime context，而不是装饰性 metadata。

这意味着：即便不改上游 core，也可以通过 `MedAutoScience` 把医学资产前置注入 runtime。

### C. `reference_papers` contract 已存在，但仍未形成完整文献层

当前 contract 已支持：

- `url`
- `doi`
- `pmid`
- `pmcid`
- `arxiv_id`
- `pdf_path`

但它主要仍是解析和 overlay 提醒层，尚未形成：

- 文献检索
- 文献归档
- quest hydration
- runtime 中途补引
- manuscript-facing bibliography sync

## Considered Approaches

### Option A. 改 `DeepScientist core`，让它原生学会 PubMed 和医学实验

做法：

- 在上游 runtime 中新增 PubMed 文献接口
- 把医学实验 schema 直接做进 `DeepScientist`
- 让 write/review 原生感知医学期刊要求

优点：

- 运行中自主性最强
- 文献与实验逻辑看起来更“内生”

缺点：

- 改动面大
- 维护成本高
- 与当前仓库“优先通过 profile -> controller -> overlay -> adapter 影响 DeepScientist”的原则冲突

结论：

- 现在不选。

### Option B. 只做终稿后医学审计，运行期保持现状

做法：

- 允许 `DeepScientist` 继续以 arXiv-first 和通用实验默认逻辑运行
- 等它产出一个“可交付版本”后，再由 `MedAutoScience` 做医学审计和返工

优点：

- 接入成本低
- 对现有 runtime 侵入小

缺点：

- 运行期仍会积累错误方向
- 文献和实验路径可能从一开始就偏离医学目标
- 这本质是后处理补救，不符合本项目要求

结论：

- 不接受。

### Option C. 在 `MedAutoScience` 建立 controller-first 的医学研究运行层

做法：

- `MedAutoScience` 编译医学实验 contract
- `MedAutoScience` 建立 PubMed / PMC / DOI 文献层
- `MedAutoScience` 在 quest 启动前做 hydration
- `DeepScientist` 继续负责 generic quest runtime
- `MedAutoScience` 在 write/review 与 finalize 前设置医学审计 gate

优点：

- 与当前架构一致
- 不需要先改 `DeepScientist core`
- 可以在 `MedAutoScience` 层先完整落地一期

缺点：

- 需要新增一组 controller / adapter / durable state
- 写作期补引需要通过 runtime 外围闭环接回 quest

结论：

- 这是本次推荐方案。

## Chosen Design

采用 `Option C`：

把三个优化目标统一设计为一条 `MedAutoScience-managed medical runtime integration` 链路。

核心原则是：

- `DeepScientist` 负责 generic runtime
- `MedAutoScience` 负责医学 contract、文献权威层、startup hydration、交付前 audit

## Why One Integrated Spec

本次采用“一份总设计、分期实施”的组织方式，而不是拆成三份互相引用的 spec。

原因不是这三件事完全相同，而是它们在运行时共享同一条控制链：

- 医学实验 contract 决定需要什么文献与什么 manuscript surface
- 文献层决定 write/review 期能否拿到正确引文与 claim support
- hydration 决定 runtime 是否能从正确起点进入这些 contract

因此，它们适合放在一份统一 spec 中保持边界一致；真正进入 implementation plan 时，再按 phase 和 controller 拆成可独立交付的任务。

## High-Level Architecture

### New runtime phases

正式启动流程从：

- `create -> start`

变为：

- `create_only -> hydrate -> validate -> start_or_resume`

### New responsibility split

#### `MedAutoScience`

负责：

- study-level medical analysis contract
- literature source federation and ranking
- quest hydration
- hydration validation
- runtime review follow-up routing
- medical manuscript audit

#### `DeepScientist`

负责：

- quest creation
- daemon loop
- stage routing
- durable quest memory
- generic experiment / analysis / write / review execution

## Design Part I: Medical Analysis Contract

### Why

要解决“医学论文实验调整”问题，不能继续依赖 overlay 里零散的文字提醒，而要把医学论文所需实验结构提升为 controller-first contract。

### New contract

新增 study-level `medical_analysis_contract`，由 `MedAutoScience` 根据任务 archetype、submission target、endpoint type 与数据准备度编译生成。

### Core fields

最少包含：

- `study_archetype`
- `primary_claim_family`
- `endpoint_type`
- `validation_expectation`
- `required_analysis_packages`
- `required_reporting_items`
- `reporting_guideline_family`
- `required_reporting_checklists`
- `population_accounting_contract`
- `forbidden_default_routes`
- `minimum_manuscript_surfaces`

### Required analysis packages

该 contract 不是抽象标签，而是要给出结构化 analysis package。例如：

#### `clinical_classifier`

- discrimination metrics
- calibration assessment
- threshold / utility analysis
- subgroup heterogeneity
- clinically interpretable risk grouping
- external or temporal validation when feasible

#### `external_validation_model_update`

- baseline model registry
- transportability assessment
- recalibration / model update
- case-mix comparison
- decision impact before and after update

#### `gray_zone_triage`

- triage-zone definition
- rule-in / rule-out / gray-zone yield
- unsafe case review
- resource or workflow consequence

### Forbidden defaults

contract 还要明确哪些“通用 AI follow-up”不能被误当成医学论文主证据。例如：

- 只有消融，没有 calibration / utility
- 只有 benchmark 表格，没有 subgroup / transportability
- 只有 figure-by-figure narration，没有 clinical answer

### Structured medical manuscript evidence package

`medical_analysis_contract` 不能只描述“做哪些分析”，还必须显式描述这些分析如何被投射为医学稿件可接受的证据包。

这意味着以下内容必须从 prompt / overlay 提醒提升为一等结构化 schema，而不是留到终稿时再靠人工补表：

- `cohort flow`
- `baseline characteristics`
- reporting guideline checklist

### First-class schemas

建议把这部分设计成与 `medical_analysis_contract` 并列但紧耦合的 `medical_reporting_contract`，至少包含：

- `reporting_guideline_family`
  - 例如 `TRIPOD`、`STROBE`、`CONSORT`
- `cohort_flow_required`
- `baseline_characteristics_required`
- `population_accounting_rules`
- `table_shell_requirements`
- `required_reporting_items`
- `manuscript_section_requirements`

### Cohort flow contract

`cohort flow` 不能只是一张后画出来的图，而应有结构化 truth source。

建议新增：

- `paper/cohort_flow.json`
- `paper/cohort_flow.md`
- `paper/figures/cohort_flow_figure_spec.json`

最少表达：

- source population
- inclusion steps
- exclusion steps
- 每一步的计数变化
- analysis population
- missingness-related排除或不可评估样本
- train / validation / test 或 derivation / validation population 的关系

这个 schema 的目标不是“生成一张好看的流程图”，而是保证稿件中所有人口统计与样本数叙述都可回溯到同一个 participant accounting truth source。

### Baseline characteristics contract

`baseline characteristics` 也不能只靠 `Table 1` 文本拼接。

建议新增：

- `paper/baseline_characteristics_schema.json`
- `paper/tables/table1_baseline_characteristics.json`
- `paper/tables/table1_baseline_characteristics.md`

最少表达：

- baseline table 适用的人群定义
- 分层方式或比较组定义
- 变量清单与变量角色
- 连续变量与分类变量的汇总方式
- 缺失值展示规则
- 单位、取值重编码与医学可读标签
- 是否允许组间显著性检验及其依据

这层 schema 的重点是：让 `Table 1` 成为 manuscript-safe 的结构化证据面，而不是最后阶段从数据框随手导出一张表。

### Reporting guideline checklist contract

`TRIPOD / STROBE / CONSORT` 这类 guideline 不能只留在 overlay 文字里。

建议新增：

- `paper/reporting_guideline_checklist.json`
- `paper/reporting_guideline_checklist.md`

最少表达：

- guideline family
- checklist item id
- requiredness
- manuscript coverage status
- evidence path
- unresolved gap

这使得 runtime 在 write/review 期能够明确知道：

- 哪些稿件要求已经满足
- 哪些只是写了几句像样的话，但并没有证据锚点
- 哪些项目缺失到必须回退补分析或补文献

### Design principle

这里的关键不是“多几个表单”，而是把医学稿件常见证据包从自由 prose 提升为可校验、可 hydration、可 audit 的 quest state。

### Runtime consumption

该 contract 通过三种方式进入 runtime：

1. 扩充 `startup_contract`
2. hydration 后写入 quest-local durable files
3. overlay 在相关 stage 把它当作必须遵守的 truth source

### Durable files

建议新增：

- `paper/medical_analysis_contract.json`
- `paper/medical_reporting_contract.json`
- `paper/paper_experiment_matrix.json`
- `paper/derived_analysis_manifest.json`
- `paper/cohort_flow.json`
- `paper/baseline_characteristics_schema.json`
- `paper/reporting_guideline_checklist.json`
- `memory/knowledge/active-user-requirements.md`

## Design Part II: Medical Literature Layer

### Why

要解决“文献检索源优化”问题，重点不是让 runtime 拥有更多 search prompt，而是让 quest 在医学文献层面有清晰的权威顺序。

### Source authority order

医学论文默认文献权威顺序设为：

1. user-provided or workspace-local papers
2. PubMed / PMID metadata
3. PMC full text when available
4. DOI-resolved publisher metadata
5. arXiv as supplementary or method-neighbor source

这意味着：

- arXiv 不再是医学稿件的默认主源
- PubMed / PMC 成为医学 literature 的默认主层

### New literature adapters

新增 `MedAutoScience` adapters：

- `pubmed_adapter`
- `pmc_adapter`
- `doi_metadata_adapter`
- `literature_federation_adapter`

这些 adapter 负责：

- 查询
- metadata 归一化
- ID 对齐
- source ranking
- evidence provenance

### Literature normalization model

新增统一 literature record，最少包含：

- `record_id`
- `title`
- `authors`
- `year`
- `journal`
- `doi`
- `pmid`
- `pmcid`
- `arxiv_id`
- `abstract`
- `full_text_availability`
- `source_priority`
- `citation_payload`
- `local_asset_paths`
- `relevance_role`
- `claim_support_scope`

### Runtime injection

文献层通过两条路径进入 quest：

#### Path A. startup hydration

启动前把已有文献资产写入 quest：

- `literature/imported/records.jsonl`
- `literature/pubmed/records.jsonl`
- `literature/pubmed/search_reports/*.json`
- `paper/references.bib`
- `paper/related_work_map.md`
- `paper/reference_coverage_report.json`

#### Path B. writing/review follow-up loop

当 write/review 暴露引文缺口时，由 `MedAutoScience` 文献 controller 接管：

1. 读取 review 缺口
2. 调用 PubMed / PMC / DOI 检索
3. 产出新的 literature package
4. 重新 hydration 到 quest
5. 允许 runtime 继续 write/review

### Not changing upstream core

这一层的设计重点是：

- 不要求 `DeepScientist` 原生去 PubMed 搜
- 但要保证它在运行时能消费 PubMed 资产
- 同时把运行中的引文缺口闭环拉回 `MedAutoScience`

## Design Part III: Quest Hydration and Startup Contract Expansion

### Why

要解决“MedAutoScience 与 DeepScientist 的衔接”问题，核心不是让 quest 创建时多写几句 summary，而是建立正式 hydration phase。

### New controller

新增 `quest_hydration_controller`。

职责：

- 收集 study 当前已有资产
- 编译 startup extension
- 写入 quest-local durable state
- 生成 hydration report
- 在不满足 contract 时阻断 start

### Hydration inputs

最少包括：

- study payload
- reference papers
- current paper URLs / local PDFs
- existing result artifacts
- existing review notes
- study archetype
- journal shortlist
- medical analysis contract
- manuscript surface state

### Hydration writes

建议写入 quest 的资产包括：

- `memory/knowledge/active-user-requirements.md`
- `memory/knowledge/study_framing_summary.md`
- `literature/imported/records.jsonl`
- `literature/pubmed/records.jsonl`
- `paper/references.bib`
- `paper/related_work_map.md`
- `paper/paper_experiment_matrix.md`
- `paper/paper_experiment_matrix.json`
- `paper/medical_analysis_contract.json`
- `paper/medical_reporting_contract.json`
- `paper/cohort_flow.json`
- `paper/cohort_flow.md`
- `paper/baseline_characteristics_schema.json`
- `paper/tables/table1_baseline_characteristics.json`
- `paper/reporting_guideline_checklist.json`
- `paper/methods_implementation_manifest.json`
- `paper/derived_analysis_manifest.json`
- `artifacts/reports/startup/hydration_report.json`

### Startup contract expansion

在现有 `startup_contract` 基础上，建议新增或强化以下字段：

- `reference_papers`
- `medical_analysis_contract_summary`
- `medical_reporting_contract_summary`
- `reporting_guideline_family`
- `entry_state_summary` expanded
- `review_summary`
- `review_materials`
- `custom_brief` expanded
- `runtime_reentry_gate.required_paths`
- `literature_state_summary`
- `hydration_report_path`

### Validation

Hydration 之后必须执行 `startup_hydration_validation`，至少验证：

- quest 关键文件是否已落盘
- reference papers 是否可解析
- bibliography 是否已生成
- medical analysis contract 是否存在
- medical reporting contract 是否存在
- `cohort_flow` schema 是否存在且计数可解释
- `baseline characteristics` schema 是否存在
- reporting guideline checklist 是否已 bootstrap
- manuscript minimal surfaces 是否满足最小起点

验证失败时，`start_or_resume` 必须被阻断。

## Design Part IV: Medical Manuscript Audit Loop

### Why

如果只做 startup hydration，而不做交付前医学审计，runtime 仍可能在运行中逐渐偏离医学论文要求。

### Position

医学审计不是一次性的终稿润色，而是正式的 runtime gate。

### Audit timing

至少在两个节点触发：

1. write/review 期发现文献或 manuscript contract 缺口时
2. finalize / delivery 前

### Audit scope

审计最少覆盖：

- 现有引用是否真的支撑当前 claim
- 是否缺失关键医学文献、指南、经典 comparator、近年强相关研究
- Methods contract 是否完整
- Results narration 是否按 clinical question 组织
- endpoint caveat 是否显式投射到 manuscript surface
- medical analysis contract 是否真的被转化为 paper-facing evidence package
- `cohort flow` 的 participant accounting 是否前后一致
- `baseline characteristics` 是否真正对应 manuscript 主分析人群
- `TRIPOD / STROBE / CONSORT` checklist 是否有 evidence-backed coverage，而不是仅有措辞覆盖

### Outputs

新增医学审计 durable outputs：

- `paper/review/medical_literature_audit.md`
- `paper/review/reference_gap_report.json`
- `paper/review/medical_contract_audit.json`
- `paper/review/reporting_guideline_audit.json`
- `paper/review/population_accounting_audit.json`
- `artifacts/reports/medical_runtime/medical_audit_report.json`

### Gate semantics

审计不通过时，允许的下一步只有：

- literature supplementation
- contract completion
- manuscript rewrite
- targeted follow-up analysis

不允许直接 finalize。

## End-to-End Flow

### Phase 0. Study readiness

`MedAutoScience` 完成：

- submission target resolution
- study archetype resolution
- medical analysis contract compilation
- medical reporting contract compilation
- reference paper resolution

### Phase 1. Quest creation

调用 `DeepScientist` `create_only`，只建立最小 quest 骨架。

### Phase 2. Quest hydration

`MedAutoScience` 执行：

- literature hydration
- analysis contract hydration
- reporting contract hydration
- manuscript surface bootstrap
- state summary generation

### Phase 3. Hydration validation

如果 hydration 不完整，阻断启动。

### Phase 4. Runtime execution

`DeepScientist` 在 richer quest state 下推进：

- intake-audit
- experiment
- analysis-campaign
- write
- review

### Phase 5. Writing/review follow-up

若暴露文献或 manuscript 缺口：

- 由 `MedAutoScience` 接管医学文献补引与 contract 修复
- 然后再把更新结果写回 quest

### Phase 6. Final medical audit

delivery 之前，必须通过医学审计 gate。

## Controller Set

建议新增或扩展以下 controller：

- `medical_analysis_contract_controller`
- `medical_reporting_contract_controller`
- `literature_hydration_controller`
- `pubmed_literature_controller`
- `quest_hydration_controller`
- `startup_hydration_validation_controller`
- `medical_literature_audit_controller`
- `medical_reporting_audit_controller`

## Durable State Surfaces

建议统一形成以下 paper-facing and runtime-facing surfaces：

- `paper/medical_analysis_contract.json`
- `paper/medical_reporting_contract.json`
- `paper/paper_experiment_matrix.md`
- `paper/paper_experiment_matrix.json`
- `paper/cohort_flow.json`
- `paper/cohort_flow.md`
- `paper/figures/cohort_flow_figure_spec.json`
- `paper/baseline_characteristics_schema.json`
- `paper/tables/table1_baseline_characteristics.json`
- `paper/tables/table1_baseline_characteristics.md`
- `paper/reporting_guideline_checklist.json`
- `paper/reporting_guideline_checklist.md`
- `paper/references.bib`
- `paper/related_work_map.md`
- `paper/reference_coverage_report.json`
- `paper/review/medical_literature_audit.md`
- `paper/review/reference_gap_report.json`
- `paper/review/medical_contract_audit.json`
- `paper/review/reporting_guideline_audit.json`
- `paper/review/population_accounting_audit.json`
- `literature/imported/records.jsonl`
- `literature/pubmed/records.jsonl`
- `literature/pubmed/search_reports/*.json`
- `artifacts/reports/startup/hydration_report.json`
- `artifacts/reports/medical_runtime/medical_audit_report.json`

## Failure Policy

本设计明确拒绝以下路径：

- 只靠 prompt 提醒而没有结构化 contract
- 只在终稿后做一次性人工式医学补救
- 继续让 quest 从空目录近似重新开始
- 继续把 arXiv 当作医学稿件的默认主文献层
- 让 write/review 发现引文缺口后仍然只能在 runtime 内部自行漂移
- 把 `cohort flow`、`baseline characteristics`、reporting checklist 继续留在自由文本或最终手工补件阶段

## Risks and Mitigations

### Risk 1. Hydration 写太多，quest 变重

处理方式：

- 区分 `summary surfaces` 与 `full literature payload`
- 让关键 summary 进入 startup contract
- 让完整 records 落到 quest 文件面

### Risk 2. 文献层过宽，source ranking 不稳定

处理方式：

- 明确 source authority order
- 所有 record 都保留 source provenance
- manuscript-facing bibliography 只从受管 normalized records 导出

### Risk 3. Runtime 与 controller 循环过多

处理方式：

- 只在特定 gate 触发 controller-side supplementation
- 不把每次 search 都搬回 controller
- 把 write/review 期补引视为结构化 follow-up route，而不是任意打断

## Phasing

### Phase 1

优先落地：

- `medical_analysis_contract`
- `medical_reporting_contract`
- `quest_hydration_controller`
- `startup_contract` 扩容
- `PubMed / PMC / DOI literature adapter`

目标：

- 让 runtime 起点、主文献层和医学稿件基础 evidence package 先正确起来

### Phase 2

继续落地：

- write/review 期文献补引闭环
- reference coverage report
- medical literature audit controller
- `cohort_flow / baseline_characteristics / reporting_guideline_checklist` audit
- participant accounting 与 manuscript population consistency gate

目标：

- 让运行中的文献治理和医学稿件结构化证据审计闭环起来

### Phase 3

继续补强：

- venue-specific reporting guideline variants
- 更细粒度的 arm-level / temporal / external-validation population accounting
- `TRIPOD / STROBE / CONSORT` 的条目级 journal-family 适配

目标：

- 把更细粒度、期刊家族相关的医学 schema 继续下沉为更强 gate

## Acceptance Criteria

当以下条件同时成立时，本设计可视为成功：

1. 任何正式启动的 quest 都不是从空白医学状态起步
2. 医学 study 的主文献层默认不再是 arXiv-first
3. write/review 暴露文献缺口时，系统存在受管补引闭环
4. runtime follow-up 不再默认退化为通用 AI 论文实验包
5. `cohort flow`、`baseline characteristics`、reporting guideline checklist 已经成为 quest 内的一等结构化 state
6. delivery 之前存在明确且可阻断的医学审计 gate

## Recommended Next Step

下一步不应直接开写代码，而应基于本设计写一份 implementation plan，按以下顺序拆任务：

1. `medical_analysis_contract + medical_reporting_contract + startup_contract expansion`
2. `quest_hydration_controller + hydration validation`
3. `PubMed / PMC / DOI literature adapters`
4. `writing/review literature supplementation loop`
5. `medical literature audit + reporting guideline gate`
