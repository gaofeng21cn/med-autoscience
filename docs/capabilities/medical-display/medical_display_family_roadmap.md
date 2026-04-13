# Medical Display Family Roadmap

This document is the authoritative long-horizon roadmap for the medical display platform in `med-autoscience`.

Use this file when the question is:

- Which paper-facing evidence families should the platform ultimately cover?
- How should the original `A-H` display families relate to the current audited engineering taxonomy?
- What should count as platform progress after the current anchor-paper figure recovery closes?

For the absorbed baseline program that established first-baseline coverage across `A-H`, see [medical_display_family_baseline_program.md](./medical_display_family_baseline_program.md).

For the strict engineering truth of what is already audited today, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).

For the generated inventory of registered templates, renderers, schemas, and QC profiles, see [medical_display_template_catalog.md](./medical_display_template_catalog.md).

## Why This Roadmap Exists

The display system currently has three valid but different viewpoints:

1. **Paper family**
   - What question is a paper figure or table trying to answer?
2. **Audit family**
   - What engineering contract, renderer path, and QC risks govern this artifact?
3. **Template instance**
   - What exact template, input schema, renderer family, and QC profile implement it?

Those layers serve different purposes. They should not compete for the same role.

This roadmap fixes the split by making the top-level long-horizon target explicit:

- `A-H` is the stable **paper-family roadmap**.
- Audit families remain the **engineering governance layer**.
- Template instances remain the **concrete implementation layer**.

## Operating Principles

### 1. Real papers drive template maturity

The project should not expand by mechanically filling a checklist of every planned template.

Instead, it should expand by:

1. using real paper delivery as the forcing function;
2. turning recurring figure/table needs into audited templates;
3. folding those successful capabilities back into the stable family roadmap.

### 2. Templates protect the lower bound, not cap the upper bound

The purpose of the platform is to prevent low-quality paper figures and tables from slipping through:

- text overlap
- unreadable panel composition
- incorrect default title behavior
- unstable annotation placement
- axis windows that do not fit the effective data domain
- palette drift away from article-level truth

Templates and QC should guarantee a defensible lower bound while still allowing article-level style and figure-level override refinement.

### 3. Contract beats post-hoc repair

Display quality should be expressed through:

- paper-owned inputs
- audited overrides
- renderer contracts
- layout QC
- manuscript-facing validation

It should not rely on last-minute manual nudges, heuristic cleanup, or informal human memory.

### 4. Deterministic lower bound, AI-first upper bound

The platform should separate two kinds of quality work:

1. **Lower-bound protection**
   - owned by templates, input contracts, renderer behavior, layout QC, and manuscript-facing validation;
   - covers failures that should be made deterministic and enforceable, such as missing panel labels, invalid default title behavior, overflow, broken axis contracts, or package/surface inconsistency.
2. **Upper-bound visual refinement**
   - owned by an explicit AI-first visual audit and critique loop;
   - covers paper-facing presentation judgments that are difficult to encode perfectly in advance without overfitting the renderer layer, such as balance, crowding, annotation placement, arrow placement, local readability, or figure-specific composition tradeoffs.

This AI-first layer is not a replacement for audited contracts, and it is not a silent post-processing patch.

It should work like this:

- render the current figure through the audited path;
- let an AI visual-review lane inspect the actual output;
- emit concrete, reviewable critique points;
- revise the renderer / input / override / QC contract where needed;
- rerender and re-audit.

In other words:

- deterministic rules should guard the lower bound;
- AI-first visual critique should help the platform approach a higher paper-facing ceiling.

### 5. Gate clear is not enough

`publication-gate` and `medical-reporting-audit` are necessary but not sufficient.

A paper-facing figure family should only be considered mature when:

- its contract path is audited;
- its QC can catch the known failure modes;
- its outputs survive real-paper visual review.

## Three-Layer Model

### Layer 1: Paper Family

This roadmap uses eight top-level paper families as the stable north star.

These families answer:

- what kind of manuscript question is being answered;
- what kind of evidence is being presented;
- what kinds of displays the platform must eventually support.

### Layer 2: Audit Family

Audit families exist to make engineering truth maintainable.

They group templates by:

- input-shape affinity;
- renderer/layout structure;
- shared QC risk;
- shared materialization and validation paths.

An audit family may be finer-grained than a paper family.

### Layer 3: Template Instance

Template instances are the concrete artifacts:

- template ID
- input schema
- renderer family
- QC profile
- export contract

Every template instance should ultimately be mappable upward to both:

- one or more paper families;
- one audit family.

## Current Paper-Proven Baseline (001/003)

The current audited inventory is broader than the subset already proven against real papers.

As of the `001/003` anchor-paper hardening line, the first paper-proven baseline is:

- Paper families: `A. Predictive Performance and Decision`, `B. Survival and Time-to-Event`, `H. Cohort and Study Design Evidence`
- Audit families: `Clinical Utility`, `Time-to-Event`, `Generalizability`, `Publication Shells / Tables`
- Template instances:
  - `binary_calibration_decision_curve_panel`
  - `time_to_event_discrimination_calibration_panel`
  - `time_to_event_risk_group_summary`
  - `time_to_event_decision_curve`
  - `multicenter_generalizability_overview`
  - `submission_graphical_abstract`

This baseline is not “the whole platform,” but it is the first set of families that has survived all of the following together:

- audited materialization and packaging;
- focused regression coverage;
- fresh paper-owned final figure QA.

Therefore the first cross-paper golden regression lane should stay centered on the failure modes already exposed by those real papers:

- title policy and no-title defaults;
- annotation placement inside the intended panel blank zone;
- panel-label and header-band anchoring;
- grouped-separation monotonicity and spread readability for ordered risk summaries;
- landmark/time-slice title, caption, and annotation semantics for horizon evidence;
- graphical-abstract arrow-lane placement;
- calibration axis-window fit;
- legend title/label semantics and tick-label readability in multicenter/generalizability layouts.

## Roadmap Families

The roadmap families below are the current top-level target model. This is the authoritative planning view for long-horizon display work.

### A. 预测性能与决策类

Paper question:

- 模型效果如何？
- 是否达到可用于临床决策或阈值判断的证据强度？

Representative displays:

- ROC
- PR
- calibration
- decision curve
- calibration + decision composite panel
- threshold summary
- lift/gain
- time-dependent AUC
- Brier curve

Primary mapped audit families:

- `Prediction Performance`
- `Clinical Utility`

Current roadmap status:

- `paper-proven core / expanding`

Current audited anchors:

- `roc_curve_binary`
- `pr_curve_binary`
- `calibration_curve_binary`
- `decision_curve_binary`
- `binary_calibration_decision_curve_panel`
- `time_to_event_decision_curve`
- `time_to_event_landmark_performance_panel`
- `time_to_event_threshold_governance_panel`
- `time_to_event_multihorizon_calibration_panel`

Current gap direction:

- lift/gain style views
- denser threshold governance beyond the first audited threshold-summary + grouped-calibration slice
- broader survival-calibration governance beyond the current grouped dumbbell + multi-horizon grouped-calibration slices
- stronger presentation QC around title policy, annotation layout, and multi-panel semantics

### B. 生存与时间事件类

Paper question:

- 随时间推移的风险、事件差异、风险分层与固定时间点表现如何？

Representative displays:

- Kaplan-Meier
- cumulative incidence
- hazard-related curves
- landmark/time-slice performance
- survival calibration
- grouped event-risk summary

Primary mapped audit families:

- `Time-to-Event`
- parts of `Clinical Utility`

Current roadmap status:

- `paper-proven core / expanding`

Current audited anchors:

- `kaplan_meier_grouped`
- `cumulative_incidence_grouped`
- `time_dependent_roc_horizon`
- `time_dependent_roc_comparison_panel`
- `time_to_event_landmark_performance_panel`
- `time_to_event_multihorizon_calibration_panel`
- `time_to_event_threshold_governance_panel`
- `time_to_event_discrimination_calibration_panel`
- `time_to_event_risk_group_summary`
- `risk_layering_monotonic_bars`
- `time_to_event_decision_curve`

Current gap direction:

- richer survival calibration governance beyond the first grouped threshold-governance + multi-horizon calibration slices
- broader time-slice variants beyond the current landmark summary panel
- stricter axis-window and grouped-separation QC for real paper outputs

### C. 效应量与异质性类

Paper question:

- 主效应有多大？
- 亚组是否一致？
- 变量方向如何？

Representative displays:

- forest plots
- subgroup forest
- interaction plots
- OR/HR coefficient views
- meta-style effect views

Primary mapped audit families:

- `Effect Estimate`

Current roadmap status:

- `partial / expanding`

Current audited anchors:

- `forest_effect_main`
- `subgroup_forest`
- `generalizability_subgroup_composite_panel`

Current gap direction:

- interaction-effect displays
- coefficient-path / compact estimate panels
- broader heterogeneous effect summaries beyond the first bounded generalizability + subgroup composite baseline

### D. 表征结构与数据几何类

Paper question:

- 数据在表征空间里长什么样？
- 分群是否分开？
- 结构层面的分布特征如何？

Representative displays:

- PCA
- UMAP
- t-SNE
- PHATE
- cluster maps
- embedding scatter
- trajectory / manifold overlays

Primary mapped audit families:

- `Data Geometry`

Current roadmap status:

- `paper-proven core / expanding`

Current audited anchors:

- `umap_scatter_grouped`
- `pca_scatter_grouped`
- `tsne_scatter_grouped`
- `celltype_signature_heatmap`
- `single_cell_atlas_overview_panel`
- `spatial_niche_map_panel`
- `trajectory_progression_panel`

Current gap direction:

- PHATE and richer manifold overlays beyond the current atlas + spatial-niche + trajectory baseline
- richer density/coverage annotation beyond occupancy / tissue topography + composition + marker/program overview
- stronger crowding / labeling / legend QC for atlas-style, spatial, and trajectory publication-facing composites

### E. 特征模式与矩阵类

Paper question:

- 变量在样本、分组、时间维度上的模式是什么？

Representative displays:

- heatmap
- correlation heatmap
- clustered heatmap
- expression matrix heatmap
- attention/importances heatmap
- missingness map

Primary mapped audit families:

- `Matrix Pattern`

Current roadmap status:

- `partial / expanding`

Current audited anchors:

- `heatmap_group_comparison`
- `performance_heatmap`
- `correlation_heatmap`
- `clustered_heatmap`
- `celltype_signature_heatmap`
- `single_cell_atlas_overview_panel`
- `spatial_niche_map_panel`
- `trajectory_progression_panel`

Current gap direction:

- missingness and QC-oriented matrices
- attention/importances matrix displays
- celltype/program/kinetics composite matrices beyond the current atlas / spatial-niche / trajectory baseline
- omics-oriented matrix surfaces with manuscript-facing annotation control

### F. 模型解释类

Paper question:

- 模型依赖哪些特征？
- 为什么做出这样的预测？

Representative displays:

- SHAP beeswarm
- dependence
- waterfall
- force-like summary
- grouped local explanation
- grouped decision path
- PDP
- ICE
- feature importance
- signed feature importance

Primary mapped audit families:

- `Model Explanation`
- parts of `Model Audit`

Current roadmap status:

- `partial / expanding`

Current audited anchors:

- `shap_summary_beeswarm`
- `shap_bar_importance`
- `shap_signed_importance_panel`
- `shap_multicohort_importance_panel`
- `shap_dependence_panel`
- `shap_waterfall_local_explanation_panel`
- `shap_force_like_summary_panel`
- `shap_grouped_local_explanation_panel`
- `shap_grouped_decision_path_panel`
- `partial_dependence_ice_panel`
- `partial_dependence_interaction_contour_panel`

Current gap direction:

- richer partial-dependence variants beyond the current summary + bar-importance + signed bar-importance + multicohort bar-importance + dependence + waterfall + force-like + grouped-local + grouped decision-path + bounded PDP/ICE baseline + bounded pairwise interaction-contour lower bound
- more complex grouped-local / decision-path scenes only when real paper demand proves the current two-group shared-baseline lower bound should expand
- stronger explanation-panel readability and annotation contracts

### G. 生物信息与组学证据类

Paper question:

- 差异表达、通路富集、组学结构、突变格局是什么？

Representative displays:

- volcano
- enrichment dot/bar
- GSEA running score
- oncoplot
- violin/box by gene set
- GSVA/ssGSEA heatmap
- CNV summary
- mutation landscape

Primary mapped audit families:

- `Matrix Pattern`
- `Data Geometry`
- future omics-specific audit families as needed

Current roadmap status:

- `paper-proven core / expanding`

Current audited anchors:

- `gsva_ssgsea_heatmap`
- `celltype_signature_heatmap`
- `single_cell_atlas_overview_panel`
- `spatial_niche_map_panel`
- `trajectory_progression_panel`

Current gap direction:

- expand from GSVA-only heatmaps into structured celltype/program composite omics panels where real paper demand is already explicit
- atlas overview baseline has now extended from embedding+signature into occupancy + composition + marker/program, then into tissue-coordinate niche topography + composition + marker/program, and now further into trajectory progression + branch composition + marker/module kinetics; larger multi-view omics composites remain follow-on slices
- expand beyond the first omics-native baseline into volcano, enrichment, oncoplot, and mutation-landscape families as real paper demand appears
- strengthen manuscript-facing legend, annotation, and local readability contracts for omics-specific matrices and atlas composites without pretending shared neighboring templates already solve the whole family

### H. 队列与研究设计证据类

Paper question:

- 样本来源、纳排、分层、基线差异、数据质量、泛化边界如何？

Representative displays:

- cohort attrition
- data split flow
- baseline balance plots
- missing-data pattern
- QC plots
- batch-effect plots
- transportability / center coverage

Primary mapped audit families:

- `Generalizability`
- `Publication Shells / Tables`
- parts of `Model Audit`

Current roadmap status:

- `partial`

Current audited anchors:

- `cohort_flow_figure`
- `submission_graphical_abstract`
- `table1_baseline_characteristics`
- `table2_time_to_event_performance_summary`
- `table3_clinical_interpretation_summary`
- `multicenter_generalizability_overview`
- `generalizability_subgroup_composite_panel`

Current gap direction:

- baseline balance plots
- missingness maps
- explicit QC/batch-effect display families
- broader design-evidence shells beyond current paper tables and the first bounded generalizability + subgroup composite baseline

## Cross-Cutting Audit Families

Two current audit families should be treated as cross-cutting engineering governance rather than top-level roadmap competitors.

### Model Audit

Purpose:

- capture model coherence, bounded complexity, and stability views that may support multiple paper families.

Typical paper-family alignment:

- `F. 模型解释类`
- `H. 队列与研究设计证据类`
- sometimes `A. 预测性能与决策类`

### Publication Shells / Tables

Purpose:

- govern how paper-facing shells and tables land in the audited submission surface.

Typical paper-family alignment:

- most strongly `H. 队列与研究设计证据类`
- but also supports families `A-C` when tables summarize performance or interpretation

## What Counts As Progress

The platform should report progress on three separate axes:

### 1. Roadmap progress

- Which `A-H` families have meaningful paper-proven coverage?

### 1b. Completion-program progress

- Which `A-H` families have crossed the current target of **first audited baseline coverage**?
- Which families are still missing even one dedicated end-to-end audited baseline?

### 2. Audit progress

- Which audit families have stable contracts, QC, and materialization paths?

### 3. Inventory progress

- How many audited templates, shells, and tables are registered today?

No single count should be used as a substitute for all three.

In particular:

- a family can remain `partial` at the roadmap level;
- while already satisfying the current completion-program baseline threshold;
- and still needing later hardening and visual-review work.

## Execution Order After Current Figure QA Recovery

The next long-horizon sequence should be:

1. finish the current real-paper figure recovery blockers;
2. keep `A-H` as the stable north star;
3. expand through real paper needs rather than isolated checklist work;
4. fold each proven template and QC improvement back into:
   - this roadmap;
   - the audit guide;
   - the generated catalog;
5. build cross-paper golden regressions so lower-bound failures stop recurring;
6. keep an explicit AI-first visual audit lane for paper-facing refinement where deterministic QC still cannot express the right critique with sufficient fidelity.

## Governance Rule

If these docs appear to disagree:

1. this roadmap defines the **top-level platform target**;
2. [medical_display_audit_guide.md](./medical_display_audit_guide.md) defines the **strict engineering audited truth**;
3. [medical_display_template_catalog.md](./medical_display_template_catalog.md) defines the **current generated inventory**.

That division of responsibility is intentional and should be preserved.
