# 医学绘图军火库总览

## 文档定位

本文记录 `med-autoscience` 当前已经沉淀下来的医学绘图与表格能力总账，用于回答四个问题：

1. 现在平台已经正式会做什么图、什么表；
2. 哪些能力已经过真实论文验证；
3. 哪些能力来自外部高水平期刊图例的吸收；
4. 下一次继续扩库时，应以什么边界和口径继续。

本文不是逐项输入契约手册，也不是生成式目录的替代物。

- 具体模板、输入契约、渲染器和质控配置，以 [medical_display_template_catalog.md](./medical_display_template_catalog.md) 为准。
- 论文问题层的长期路线，以 [medical_display_family_roadmap.md](./medical_display_family_roadmap.md) 为准。
- 工程审计层的严格真相，以 [medical_display_audit_guide.md](./medical_display_audit_guide.md) 为准。
- 军火库扩充时间线，以 [medical_display_arsenal_history.md](./medical_display_arsenal_history.md) 为准。
- 模板包化与军火库独立演进架构，以 [medical_display_template_pack_architecture.md](./medical_display_template_pack_architecture.md) 为准。

## 统计口径

本文统计的是“当前已进入 strict registry / template catalog / audited guide 真相面的绘图军火库”，不是任一时刻共享 `main` 工作树上恰好已经吸收完毕的全部代码状态。

当前生效统计口径以 registry / template catalog / audited guide 的一致真相为准，现行库存是 `88`。

`2026-04-07` 的 `31` 模板冻结边界只保留为历史 provenance，用来解释这条主线是如何从首批冻结快照继续扩容到当前库存的。对应历史锚点如下：

- `63cd76a`：`F` 家族干净集成锚点
- `ce129dc`：`F` 家族视觉审计决策面收口锚点
- `474ee02`：`B` 家族最后一个包含实际绘图代码变更的 head
- `3cc2a19`：绘图主线冻结交棒 head
- `9a74154`：`G` 家族首个审计基线
- 历史冻结报告索引（legacy）：`docs/history/omx/README*`

因此，本文记录的是“这条绘图主线现在到底已经会什么”，而不是“当前共享根工作树正好展开到了哪里”。

## 当前总览

- 八大论文家族 `A-H` 已全部完成首个审计基线，当前完成度为 `8/8`。
- 历史冻结快照（仅用于 provenance）为 `31`：
  - 证据型图模板 `24`
  - 插图壳层模板 `2`
  - 表格壳层模板 `5`
- 当前 strict registry / template catalog 工程口径统一为 `88`：
  - 证据型图模板 `76`
  - 插图壳层模板 `7`
  - 表格壳层模板 `5`
- 截至 `2026-04-20`，post-baseline rolling expansion 已在冻结基线上正式收口五十个 capability cluster：
  - `celltype_signature_heatmap`：把 `D/E/G` 从“仅候选复合图式”推进到第一个 pack 化 `embedding + signature heatmap` 复合模板；
  - `time_to_event_landmark_performance_panel`：把 `A/B` 从“已有 horizon ROC / grouped calibration 组件”推进到正式的 landmark/time-slice discrimination + Brier error + calibration slope 治理模板；
  - `shap_dependence_panel`：把 `F` 从“只会 SHAP summary”推进到正式多 panel dependence + shared colorbar + zero-line governance 的本地解释模板；
  - `time_to_event_threshold_governance_panel`：把 `A/B` 从“已有 decision curve / grouped calibration 组件”推进到正式的 threshold summary cards + grouped survival calibration governance 组合模板；
  - `time_to_event_multihorizon_calibration_panel`：把 `A/B` 从“已有单 horizon grouped calibration / threshold-governance 内嵌校准 panel”推进到正式的 `3/5-year` multi-horizon grouped calibration governance 模板；
  - `clinical_impact_curve_binary`：把 `A` 从“已有 ROC / PR / calibration / decision curve，但缺临床阈值下受影响人数与真阳性人数直接计数图面”推进到正式的 binary clinical-impact lower bound，并复用 `binary_prediction_curve_inputs_v1` 与 `publication_evidence_curve` 把阈值计数语义收进同一审计口径；
  - `genomic_program_governance_summary_panel`：把 `G` 从“已有 pathway-integrated genomic composite”继续推进到正式的 two-panel program-governance lower bound，并把 cross-layer genomic evidence 与 manuscript-facing program verdict/action summary 收进同一 bounded composite contract；
  - `single_cell_atlas_overview_panel`：把 `D/E/G` 从“已有 embedding + signature heatmap”继续推进到正式的 atlas overview baseline，并把 `embedding occupancy + group-wise composition shift + marker/program definition` 一并固化为单一复合模板；
  - `atlas_spatial_bridge_panel`：把 `D/E/G` 从“已有 atlas overview baseline”继续推进到正式的 atlas-to-spatial bridge baseline，并把 `atlas embedding + spatial state topography + region-wise state composition + marker/program heatmap` 一并固化为单一四块式复合模板；
  - `spatial_niche_map_panel`：把 `D/E/G` 从“已有 atlas overview baseline”继续推进到正式的 tissue-coordinate niche composite，并把 `spatial topography + region-wise niche composition + marker/program definition` 一并固化为单一复合模板；
  - `trajectory_progression_panel`：把 `D/E/G` 从“已有 atlas overview + spatial niche baseline”继续推进到正式的 trajectory progression composite，并把 `trajectory embedding + pseudotime-bin branch composition + marker/module kinetics` 一并固化为单一复合模板；
  - `atlas_spatial_trajectory_storyboard_panel`：把 `D/E/G` 从“已有 atlas-spatial-trajectory 分块基线”继续推进到正式的五块式 storyboard baseline，并把 `atlas occupancy + spatial topography + trajectory progression + region-wise state composition + kinetics heatmap` 固化为单一复合模板；
  - `atlas_spatial_trajectory_density_coverage_panel`：把 `D/E/G` 从“已有五块式 storyboard baseline”继续推进到正式的四块式 density/coverage support baseline，并把 `atlas density + spatial coverage topography + trajectory coverage progression + state-by-context support heatmap` 固化为单一 bounded composite contract；
  - `atlas_spatial_trajectory_context_support_panel`：把 `D/E/G` 从“已有四块式 density/coverage support baseline”继续推进到正式的六块式 context-support baseline，并把 `atlas occupancy + spatial state topography + trajectory progression + region-wise state composition + kinetics heatmap + state-by-context support heatmap` 固化为单一 bounded composite contract；
  - `phate_scatter_grouped`：把 `D` 从“PCA / UMAP / t-SNE 三件套”推进到正式包含 `PHATE` 的 grouped manifold baseline，并把 grouped embedding scatter 的 projection family 扩成四投影一致口径；
  - `shap_waterfall_local_explanation_panel`：把 `F` 从“已有 summary + dependence”继续推进到正式 patient-level local explanation baseline，并把 `baseline -> ordered feature contributions -> final prediction` 的 additive path 固化为单一 bounded 模板；
  - `shap_force_like_summary_panel`：把 `F` 从“已有 summary + dependence + waterfall”继续推进到正式 representative-case force-like summary baseline，并把 `baseline marker + positive/negative contribution lanes + prediction marker` 的 bounded explanation path 固化为单一模板；
  - `partial_dependence_ice_panel`：把 `F` 从“已有 summary + dependence + waterfall + force-like”继续推进到正式 bounded `PDP mean + ICE curves` explanation baseline，并把 per-panel reference line/label、shared legend 语义与 `PDP/ICE` 几何 containment 固化为单一模板；
  - `partial_dependence_interaction_contour_panel`：把 `F` 从“已有 bounded PDP/ICE baseline”继续推进到正式 bounded pairwise interaction contour lower bound，并把显式 `x/y grid`、shared colorbar、reference crosshair、observed-support containment 与 panel-level interaction semantics 固化为单一模板；
  - `shap_bar_importance`：把 `F` 从“已有 summary + local explanation”补齐到正式 bounded global importance overview，并把 rank strict order、feature uniqueness、non-negative importance、bar/label/value-label sidecar 关联与 panel containment 固化为单一模板；
  - `shap_signed_importance_panel`：把 `F` 从“已有 bounded global importance overview”继续推进到正式 zero-centered directional importance overview，并把 signed polarity、absolute-magnitude strict order、zero-line side governance、direction labels 与 polarity-aware value-label containment 固化为单一模板；
  - `shap_multicohort_importance_panel`：把 `F` 从“已有 single-cohort global importance overview”继续推进到正式 bounded cross-cohort global importance comparison，并把 shared feature-order governance、panel/cohort identity、per-panel bar/value-label sidecar 关联与 panel-label anchoring 固化为单一模板；
  - `shap_grouped_local_explanation_panel`：把 `F` 从“已有 waterfall / force-like 的单病例局部解释”继续推进到正式 bounded grouped-local comparison，并把 shared feature-order governance、baseline-plus-contribution conservation、zero-centered signed contribution lanes、panel/group identity 与 row-aligned feature/value labels 固化为单一模板；
  - `shap_grouped_decision_path_panel`：把 `F` 从“已有 grouped-local comparison，但仍缺共享 baseline 的双组 cumulative decision path 对照”继续推进到正式 bounded grouped decision-path comparison，并把 shared feature-order、baseline reference line、ordered cumulative segments、prediction marker / label 与两组守恒关系固化为单一模板；
  - `shap_multigroup_decision_path_panel`：把 `F` 从“已有双组 grouped decision-path comparison，但仍缺稳定的三组 manuscript-facing explanation lower bound”继续推进到正式 bounded multigroup decision-path comparison，并把固定三组、共享 baseline、共享 feature-order、单 panel 右侧 legend 与三组守恒关系固化为单一模板；
  - `generalizability_subgroup_composite_panel`：把 `C/H` 从“forest 与 multicenter overview 分散承接子组件”推进到正式的 bounded `generalizability + subgroup interval` 复合模板，并把 cohort-level metric overview、support labels、subgroup interval block 与 outboard label containment 一并固化为单一复合契约；
  - `multivariable_forest`：把 `C` 从“main effects / subgroup effects 两条 forest 基线”推进到正式的 multivariable-model forest lower bound，并把多变量模型主结果表达收回到统一 `forest_effect_inputs_v1` / `publication_forest_plot` 契约；
  - `compact_effect_estimate_panel`：把 `C/H` 从“已有 main/subgroup forest 与 generalizability composite，但仍缺一个收纳多组预设 effect estimate 的紧凑 manuscript-facing 图面”推进到正式的 bounded compact multi-panel 模板，并把 shared reference line、shared row order、bounded panel count 与 outboard row-label containment 固化为单一审计契约；
  - `coefficient_path_panel`：把 `C/H` 从“已有紧凑 effect-estimate lower bound，但仍缺一个能正式表达预设模型步骤下系数方向与幅度稳定性的 manuscript-facing 图面”推进到正式的 bounded coefficient-path + stability-summary 双 panel 模板，并把 declared step coverage、reference-line containment、row-level path geometry、summary-card containment 与 step-legend identity 固化为单一审计契约；
  - `broader_heterogeneity_summary_panel`：把 `C/H` 从“已有 generalizability composite + compact estimate + coefficient-path lower bound，但仍缺一个逐行收口 manuscript verdict 的 comparative summary”推进到正式的 bounded 双 panel 模板，并把 declared slice coverage、slice-kind vocabulary、row-level verdict state、matrix/reference-line containment 与 summary-panel verdict alignment 固化为单一审计契约；
  - `interaction_effect_summary_panel`：把 `C/H` 从“已有 compact estimate、coefficient-path 与 broader heterogeneity，但 modifier-level interaction 仍停留在零散 forest 或正文补充说明里”推进到正式的双 panel 模板，并把 modifier-level interval、interaction p 值、favored subgroup 文字、verdict 受控词表、estimate/reference containment 与 summary-panel verdict alignment 固化为单一审计契约；
  - `design_evidence_composite_shell`：把 `H` 从“已有 fixed 2x2 workflow fact sheet，但仍缺带 workflow ribbon 的 manuscript-facing 设计证据骨架”推进到正式 bounded `workflow ribbon + three summary panels` 壳层，并把 workflow stage、panel-label anchoring、summary-title containment 与 card label/value containment 固化为单一审计契约。
  - `baseline_missingness_qc_panel`：把 `H` 从“已有 workflow/design-evidence shell，但仍缺一张可以同时交代组间平衡、缺失模式与质控摘要的 bounded manuscript-facing 图面”推进到正式的三联壳层，并把 balance threshold、missingness grid 完整性、QC card containment 与固定 `A/B/C` panel 治理固化为单一审计契约。
  - `center_coverage_batch_transportability_panel`：把 `H` 从“已有 baseline-missingness-QC 三联壳层与 multicenter/generalizability baseline，但仍缺一张能同时交代中心覆盖、批次漂移与 transportability boundary 的 bounded manuscript-facing 图面”推进到正式的三联壳层，并把 center-support counts、batch grid 完整性、threshold governance、transportability card containment 与固定 `A/B/C` panel 治理固化为单一审计契约。
  - `transportability_recalibration_governance_panel`：把 `H` 从“已有中心覆盖/批次漂移/transportability 三联壳层，但仍缺一个能正式交代各中心 recalibration 动作是否达标的 manuscript-facing 图面”推进到正式的三联壳层 follow-on，并把 acceptance band、center-level slope / O:E ratio、action row containment 与固定 `A/B/C` panel 治理固化为单一审计契约。
  - `center_transportability_governance_summary_panel`：把 `H` 从“已有 multicenter overview、generalizability composite、center-coverage transportability shell、recalibration-governance shell 与 broader heterogeneity stability summary，但仍缺一张能把中心级 transportability 指标与 manuscript-facing 治理结论直接收束进正文主叙事的 bounded 图面”推进到正式的双 panel 模板，并把 center-level metric interval、verdict 受控词表、support/decision row completeness 与 panel-level narrative containment 固化为单一审计契约。
  - `partial_dependence_interaction_slice_panel`：把 `F` 从“已有 bounded PDP/ICE 与 pairwise interaction contour lower bound”继续推进到正式 higher-order interaction slice 模板，并把固定切片条件、per-panel feature/slice identity、slice-point containment 与 shared legend 语义固化为单一模板；
  - `partial_dependence_subgroup_comparison_panel`：把 `F` 从“已有总体层面的 PDP lower bound”继续推进到正式 subgroup-conditioned partial-dependence 对照模板，并把 subgroup identity、estimate marker / ribbon containment、shared x-domain 与 panel-label anchoring 固化为单一模板；
  - `accumulated_local_effects_panel`：把 `F` 从“已有 PDP 系列，但仍缺对相关特征更稳健的局部效应表达”继续推进到正式 ALE 模板，并把 bin order、bin geometry、local-effect finite contract、zero/reference guide 与 bin containment 固化为单一模板。
  - `feature_response_support_domain_panel`：把 `F` 从“已有 PDP / subgroup / ALE lower bound，但 support-domain、subgroup-legend 与 extrapolation 提醒仍分散在多个模板里”继续推进到正式 support-domain explanation panel，并把 response-curve 区间、support-kind 受控词表、full-domain coverage、reference guide 与 segment/label containment 固化为单一模板；
  - `shap_grouped_local_support_domain_panel`：把 `F` 从“已有 grouped-local comparison 与 support-domain explanation，但还缺正文可直接使用的 explanation scene”继续推进到正式上下两排复合模板，并把 shared local feature order、exactly-two support panels、local/support panel-label 全局唯一性与 support legend title 治理固化为单一模板。
  - `shap_multigroup_decision_path_support_domain_panel`：把 `F` 从“已有三组 decision-path 与 grouped-local + support-domain 两条 lower bound，但缺正文可直接使用的多组 decision-scene”继续推进到正式 `1 + 2` explanation scene，并把 fixed three-group decision order、matched two-panel support domain、decision-to-support feature-order governance 与 support-domain follow-on 复合在同一张 manuscript-facing 模板里。
  - `pathway_enrichment_dotplot_panel`：把 `E/G` 从“已有 GSVA/ssGSEA 热图与 atlas 复合图，但仍缺高频正文 pathway enrichment 图式”继续推进到正式 bounded dotplot 模板，并把 shared pathway order、完整 `panel x pathway` 网格、effect/size 双标尺语义与非负 hit-size 治理固化为单一模板。
  - `omics_volcano_panel`：把 `G` 从“已有 GSVA/ssGSEA 热图与 pathway enrichment dotplot，但仍缺差异表达正文常用的 volcano 主图”继续推进到正式 bounded up-to-two-panel volcano 模板，并把 fold-change/significance threshold、regulation vocabulary、highlight label 治理与 panel-level threshold-guide sidecar 固化为单一模板。
  - `oncoplot_mutation_landscape_panel`：把 `G` 从“已有 GSVA/ssGSEA 热图、pathway enrichment dotplot 与 volcano，但仍缺正式突变格局主图”继续推进到正式 bounded oncoplot 模板，并把 declared sample/gene order、最多三条 annotation track、top burden 与右侧 altered-frequency 侧栏语义固化为单一模板。
  - `cnv_recurrence_summary_panel`：把 `G` 从“已有 GSVA/ssGSEA 热图、pathway enrichment dotplot、volcano 与 oncoplot，但仍缺 copy-number 正文主图”继续推进到正式 bounded CNV summary 模板，并把 declared sample/region order、最多三条 annotation track、top burden 与右侧 gain/loss frequency 侧栏语义固化为单一模板。
  - `genomic_alteration_landscape_panel`：把 `G` 从“已有分开的 oncoplot 与 CNV summary，但仍缺一个正文可直接使用的 mutation-plus-CNV 联合景观主图”继续推进到正式 bounded genomic alteration landscape 模板，并把 declared `gene_order`、declared `sample_order`、最多三条 annotation track、sample-level burden、gene-level alteration frequency 与 dual-state overlay 治理固化为单一模板。
  - `genomic_alteration_consequence_panel`：把 `G` 从“已有 mutation-plus-CNV gene-level landscape，但仍缺 driver-centric transcriptome / proteome consequence follow-on”继续推进到正式 bounded consequence 模板，并把 `driver_gene_order`、`consequence_panel_order`、effect / significance threshold、下游 scatter semantics 与 bounded label containment 固化为单一模板。
  - `genomic_alteration_multiomic_consequence_panel`：把 `G` 从“已有 landscape + transcriptome/proteome consequence follow-on，但仍缺固定三层 multiomic manuscript-facing composite”继续推进到正式 bounded multiomic consequence 模板，并把 `proteome/phosphoproteome/glycoproteome` vocabulary、每层 driver coverage、effect / significance threshold、panel identity 与 bounded label containment 固化为单一模板。
  - `genomic_alteration_pathway_integrated_composite_panel`：把 `G` 从“已有 landscape + 三层 multiomic consequence follow-on，但仍缺把 pathway-level enrichment evidence 收进正文主图的固定复合契约”继续推进到正式 `1 + 3 + 3` pathway-integrated composite 模板，并把 shared `pathway_order`、pathway colorbar / size-scale、三层 omics consequence 与三层 pathway panel identity 一并固化为单一模板。
- 此前文档里沿用过的早期 rolling headline，不再代表当前严格工程库存；从本轮起统一以 registry / template catalog 真相口径为准。
- 真实由锚点论文 `001/003` 证明过的核心家族是 `A`、`B`、`H`。
- 当前主线状态不应再被理解成“默认停车、显式重开才继续”。
- 更准确的理解是：
  - `A-H` 首个审计基线已完成；
  - 当前进入 rolling hardening / visual audit / paper-driven strengthening；
  - 本文只负责记录能力库存与成熟度，不再承载默认停车治理规则。
- 质量策略固定为两层：
  - 模板、输入契约、渲染器与质控负责保下限；
  - AI 优先的视觉审计负责逼近论文级上限。

## 军火库的三层结构

### 1. 论文家族层

回答的是“论文到底在呈现什么证据问题”。

这层是长期北极星，按 `A-H` 组织：

- `A` 预测性能与决策
- `B` 生存与时间事件
- `C` 效应量与异质性
- `D` 表征结构与数据几何
- `E` 特征模式与矩阵
- `F` 模型解释
- `G` 生物信息与组学证据
- `H` 队列与研究设计证据

### 2. 审计家族层

回答的是“这类图在工程上由什么契约、什么渲染结构、什么质控风险来治理”。

这层的职责是让平台能够稳定维护，而不是把所有图都混成单一目录。

### 3. 模板实例层

回答的是“具体是哪一个模板、哪个输入契约、哪个渲染器、哪个质控配置在工作”。

军火库真正可复用的最小单元，落在这一层。

## 当前军火库全貌

| 论文家族 | 主要回答的问题 | 当前代表模板 | 当前成熟度 | 主要来路 |
| --- | --- | --- | --- | --- |
| `A. 预测性能与决策` | 模型效果、校准、决策阈值与临床可用性 | `roc_curve_binary`、`pr_curve_binary`、`calibration_curve_binary`、`decision_curve_binary`、`clinical_impact_curve_binary`、`binary_calibration_decision_curve_panel`、`time_to_event_decision_curve`、`time_to_event_landmark_performance_panel`、`time_to_event_threshold_governance_panel`、`time_to_event_multihorizon_calibration_panel` | 已形成真实论文证明的核心能力，并已把 `Brier/error-oriented` landmark 治理、threshold summary + grouped survival calibration governance、binary clinical-impact counting，以及 multi-horizon grouped calibration governance 一并提升为正式模板资产 | `001/003` 锚点论文 + `A/B/H` 回归加固 + `Nature Communications` `2021` 动态复发风险 exemplar + `Nature Medicine` / `npj Digital Medicine` `2025` 阈值与校准 exemplar + clinical-impact counting follow-on |
| `B. 生存与时间事件` | 随时间推移的风险分层、累计发生、固定时间点表现与多窗口对比 | `kaplan_meier_grouped`、`cumulative_incidence_grouped`、`time_to_event_discrimination_calibration_panel`、`time_to_event_risk_group_summary`、`time_to_event_stratified_cumulative_incidence_panel`、`time_dependent_roc_comparison_panel`、`time_to_event_landmark_performance_panel`、`time_to_event_threshold_governance_panel`、`time_to_event_multihorizon_calibration_panel` | 当前工程加固最充分、结构最完整的家族之一，并已具备正式 landmark/time-slice performance governance、grouped survival calibration governance 与 multi-horizon grouped calibration governance | `001/003` 锚点论文 + `HTN-AI` 图 3 + `Nature Medicine` 风险论文图 4a/4c + `Nature Communications` `2021` 动态复发风险 exemplar + `Nature Medicine` / `npj Digital Medicine` `2025` 阈值与校准 exemplar |
| `C. 效应量与异质性` | 主效应与亚组效应的区间估计表达 | `forest_effect_main`、`multivariable_forest`、`subgroup_forest`、`generalizability_subgroup_composite_panel`、`compact_effect_estimate_panel`、`coefficient_path_panel`、`broader_heterogeneity_summary_panel`、`interaction_effect_summary_panel` | 已具备首个审计基线，并把 subgroup interval evidence 从单一 forest 扩到 main / multivariable / subgroup 三条 forest lower bound，再补齐 cohort/generalizability overview 的 bounded composite baseline、shared-reference / shared-row-order 的紧凑 effect-estimate lower bound、预设模型步骤下的 coefficient-path stability、逐行 manuscript verdict 收口的 broader heterogeneity summary 合同，以及 modifier-level interaction summary lower bound | 既有森林图契约沉淀 + `JAMA Surgery` `2025` / `npj Digital Medicine` `2026` / `World Psychiatry` `2024` subgroup-generalizability exemplar + multivariable forest concrete follow-on + 真实论文 compact-estimate / coefficient-path / broader-heterogeneity / interaction-summary follow-on 交付需求 |
| `D. 表征结构与数据几何` | 嵌入空间、分群结构、atlas 到空间的状态桥接、tissue-coordinate 空间拓扑、trajectory / manifold 演进与低维投影表达 | `umap_scatter_grouped`、`pca_scatter_grouped`、`tsne_scatter_grouped`、`phate_scatter_grouped`、`celltype_signature_heatmap`、`single_cell_atlas_overview_panel`、`atlas_spatial_bridge_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel`、`atlas_spatial_trajectory_storyboard_panel`、`atlas_spatial_trajectory_density_coverage_panel`、`atlas_spatial_trajectory_context_support_panel` | 已具备首个审计基线，并把 D/E/G baseline 从 grouped embedding 四投影 lower bound 扩到 `embedding + signature heatmap`、`atlas overview`、`atlas-to-spatial bridge`、`spatial niche topography + composition + marker/program`、`trajectory progression + branch composition + kinetics`、五块式 `atlas-spatial-trajectory storyboard`、四块式 `density / coverage` support composite，再推进到六块式 `context-support` baseline | 既有散点与嵌入契约 + `Nature Medicine` `2025` 炎症图谱图 1 + `npj Digital Medicine` `2025` 前列腺 XAI 图 1/2/3/7 + `Genome Research` `2021` / `Nature Communications` `2023` atlas overview exemplar + `Nature Medicine` `2024` / `Nature Medicine` `2025` / `Nature Communications` `2025` atlas-spatial bridge exemplar + `Nature Medicine` `2024` / `Nature Communications` `2025` / `npj Digital Medicine` `2025` spatial niche exemplar + `Nature Biotechnology` `2023` trajectory exemplar + `PHATE` concrete backlog absorb + atlas / spatial / trajectory density / coverage / context-support follow-on 学习 |
| `E. 特征模式与矩阵` | 热图、矩阵对比、相关性、有序性能矩阵、通路富集点图与带 marker/program / kinetics / context-support 解释的复合图 | `heatmap_group_comparison`、`correlation_heatmap`、`clustered_heatmap`、`performance_heatmap`、`pathway_enrichment_dotplot_panel`、`celltype_signature_heatmap`、`single_cell_atlas_overview_panel`、`atlas_spatial_bridge_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel`、`atlas_spatial_trajectory_storyboard_panel`、`atlas_spatial_trajectory_density_coverage_panel`、`atlas_spatial_trajectory_context_support_panel` | 已具备首个审计基线，并开始从独立矩阵扩到带 shared-pathway enrichment dotplot、celltype/program、atlas-spatial 状态桥接、spatial niche、trajectory kinetics、storyboard 叙事、state-by-context support heatmap 与更完整 context-support 复合矩阵的 manuscript-facing 图面 | 通用热图能力 + `Nature Medicine` 风险论文图 4c + 高水平组学论文常见 enrichment dotplot 编排 + atlas/spatial/trajectory exemplar 学习 |
| `F. 模型解释` | 特征归因、解释性摘要与复杂度审计 | `shap_summary_beeswarm`、`shap_bar_importance`、`shap_signed_importance_panel`、`shap_multicohort_importance_panel`、`shap_dependence_panel`、`shap_waterfall_local_explanation_panel`、`shap_force_like_summary_panel`、`shap_grouped_local_explanation_panel`、`shap_grouped_decision_path_panel`、`shap_multigroup_decision_path_panel`、`shap_grouped_local_support_domain_panel`、`shap_multigroup_decision_path_support_domain_panel`、`partial_dependence_ice_panel`、`partial_dependence_interaction_contour_panel`、`partial_dependence_interaction_slice_panel`、`partial_dependence_subgroup_comparison_panel`、`accumulated_local_effects_panel`、`feature_response_support_domain_panel`、`model_complexity_audit_panel` | 已具备首个审计基线，并把 global bar-importance overview、zero-centered signed importance、cross-cohort global importance comparison、dependence、patient-level waterfall、representative-case force-like summary、最多三 panel 的 grouped-local comparison、双组与三组 decision-path comparison、上下两排 grouped-local + support-domain explanation scene、`1 + 2` 的 multigroup decision-path + support-domain explanation scene、bounded PDP+ICE baseline、bounded pairwise interaction contour lower bound，以及 higher-order interaction slice / subgroup comparison / ALE / support-domain follow-on 一并提升为正式 pack 资产；当前剩余主缺口转向 AI-first visual audit 驱动的 annotation / legend 收紧与更高阶 explanation scene 的真实论文扩容 | `001/003` 锚点论文 + `npj Digital Medicine` `2025` SHAP dependence exemplar + `npj Digital Medicine` `2025` UMORSS 图 6 + `JBJS Open Access` `2025` PARITY 图 6A/B + SHAP force plot / bar importance / signed-importance / multicohort importance / grouped-local comparison / grouped decision-path / grouped-local-support-domain explanation scene / 多组 phenotype / subtype explanation scene follow-on + PDP-ICE / ALE 经典解释图式 + `npj Digital Medicine` `2026` pairwise partial-dependence interaction exemplar + support-domain explanation follow-on 实战需求 + `F` 家族视觉审计决策线 |
| `G. 生物信息与组学证据` | 组学打分、差异表达、通路富集、突变格局、拷贝数改变、联合 alteration landscape、driver-centric consequence follow-on、多组学 consequence 复合面板、pathway-integrated genomic composite、program-governance summary，以及程序活性与组学原生热图表达 | `gsva_ssgsea_heatmap`、`pathway_enrichment_dotplot_panel`、`omics_volcano_panel`、`oncoplot_mutation_landscape_panel`、`cnv_recurrence_summary_panel`、`genomic_alteration_landscape_panel`、`genomic_alteration_consequence_panel`、`genomic_alteration_multiomic_consequence_panel`、`genomic_alteration_pathway_integrated_composite_panel`、`genomic_program_governance_summary_panel`、`celltype_signature_heatmap`、`single_cell_atlas_overview_panel`、`atlas_spatial_bridge_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel`、`atlas_spatial_trajectory_storyboard_panel`、`atlas_spatial_trajectory_density_coverage_panel`、`atlas_spatial_trajectory_context_support_panel` | 已建立首个专用审计基线，并把组学/程序证据从单独热图推进到 shared-pathway enrichment dotplot、差异表达 volcano、正式 bounded oncoplot mutation landscape、正式 bounded CNV recurrence summary、正式 bounded mutation-plus-CNV genomic alteration landscape、正式 bounded driver-centric genomic consequence follow-on、正式 bounded三层 multiomic consequence composite、正式 bounded `1 + 3 + 3` pathway-integrated genomic composite、正式 bounded two-panel genomic program-governance summary、atlas occupancy、atlas-spatial 状态桥接、spatial niche composition、trajectory kinetics channel、五块式 storyboard 叙事、四块式 density/coverage support 与六块式 context-support 复合证据面 | 组学原生证据需求 + `Nature Medicine`、`Nature Cancer`、`npj Digital Medicine`、`Nature Communications` 等高水平组学论文常见 enrichment dotplot / volcano / oncoplot / CNV summary / genomic landscape / multi-omics consequence / pathway-integrated composite / program-governance synthesis 编排 + atlas/spatial/trajectory partial-fit 学习 |
| `H. 队列与研究设计证据` | 队列构成、泛化性、研究流程与投稿壳层 | `multicenter_generalizability_overview`、`generalizability_subgroup_composite_panel`、`center_transportability_governance_summary_panel`、`compact_effect_estimate_panel`、`coefficient_path_panel`、`broader_heterogeneity_summary_panel`、`interaction_effect_summary_panel`、`cohort_flow_figure`、`submission_graphical_abstract`、`workflow_fact_sheet_panel`、`design_evidence_composite_shell`、`baseline_missingness_qc_panel`、`center_coverage_batch_transportability_panel`、`transportability_recalibration_governance_panel`、`table1_baseline_characteristics`、`table3_clinical_interpretation_summary` | 已形成真实论文证明的核心能力，并把 multicenter generalizability 继续扩到 cohort-level overview + subgroup robustness 的 bounded composite baseline，再补齐中心级 transportability 指标与 manuscript-facing 治理结论直接收束的 governance summary、shared-reference / shared-row-order 的 compact estimate lower bound、预设模型步骤下的 coefficient-path stability、逐行 manuscript verdict 收口的 broader heterogeneity summary 合同，以及 modifier-level interaction summary lower bound，同时补齐固定 `2x2` 的 workflow fact sheet 壳层、固定 `workflow ribbon + three summary panels` 的 design-evidence composite 下限、第一张可同时交代基线平衡/缺失模式/质控摘要的 bounded manuscript-facing 三联壳层、第一张可同时交代中心覆盖/批次漂移/transportability boundary 的 bounded manuscript-facing 三联壳层，以及第一张可正式交代中心级 recalibration 行动与 acceptance band 是否达标的 follow-on manuscript-facing 壳层 | `001/003` 锚点论文 + 投稿包装需求沉淀 + `JAMA Surgery` `2025` / `npj Digital Medicine` `2026` / `World Psychiatry` `2024` generalizability exemplar + transportability-governance follow-on 交付需求 + compact-estimate / coefficient-path / broader-heterogeneity / interaction-summary follow-on 交付需求 + `H` 家族 manuscript-facing QC shell hardening follow-on |

## 各家族已完成模板清单（人话版）

下面这一节回答的是：

- 每个论文家族现在到底已经模板化了哪些图或表；
- 这些图表在论文里通常拿来回答什么问题；
- 哪些模板虽然工程上只有一个，但会同时服务多个家族。

统计说明：

- 这里按“论文问题归属”统计，不按去重后的模板总数统计；
- 同一个模板如果同时服务多个家族，会在多个家族里重复出现；
- 所以下面各家族的小计相加，会大于当前军火库总数 `88`。

### A. 预测性能与决策类

当前已覆盖 `17` 个模板归属。

- `ROC 曲线（二分类）`
  用途：看模型在不同阈值下区分阳性和阴性的能力，是最基础的判别力图。
- `PR 曲线（二分类）`
  用途：在阳性样本较少时，看模型的查准率和召回率，比 ROC 更适合不平衡数据。
- `校准曲线（二分类）`
  用途：看模型报出来的风险值是否接近真实发生率，回答“这个概率能不能信”。
- `决策曲线（二分类）`
  用途：看模型在不同临床阈值下有没有净获益，回答“用了它到底值不值”。
- `临床影响曲线（二分类）`
  用途：直接看不同阈值下会被判为高风险的人数，以及其中真正会发生事件的人数，回答“这个阈值落到临床后会影响多少人、抓到多少真阳性”。
- `二分类校准 + 决策复合面板`
  用途：把“概率准不准”和“临床上有没有用”放在同一个图里，一次性看完整。
- `时间依赖 ROC（单时间点）`
  用途：看某个固定随访时间点上的判别力，比如 1 年、3 年或 5 年。
- `时间依赖 ROC 对比面板`
  用途：把多个时间点或多个队列的 ROC 放在一起比较，回答“什么时候最好、在哪个队列表现更稳”。
- `landmark 表现汇总面板`
  用途：把多个 landmark 时间窗的判别力、误差和校准斜率放在一起，回答“模型在不同随访窗口是否稳定”。
- `时间事件阈值治理面板`
  用途：把阈值选择、风险分层和生存校准放在一起，回答“阈值怎么选、分层后是否真的有意义”。
- `多时间点分组校准面板`
  用途：把 3 年、5 年等多个时间点的分组校准并列展示，回答“模型在不同预测窗口上准不准”。
- `时间事件判别 + 分组校准面板`
  用途：把生存模型的判别力和分组校准放在一起，适合做正式外部验证图。
- `时间事件决策曲线`
  用途：看生存模型在固定预测窗口上的临床净获益。
- `投稿图形摘要`
  用途：把研究问题、队列、核心结果压缩成一张投稿摘要图，服务于论文封面级入口表达。
- `时间事件性能汇总表`
  用途：用表格集中汇总 C-index、AUC、Brier 等关键指标，适合正文或补充材料。
- `临床解释汇总表`
  用途：把风险分层、阈值含义和临床解释写成规范表格，方便论文直接引用。
- `通用性能汇总表`
  用途：把多个模型、多个队列或多个实验设置的性能放在一张通用表里。

### B. 生存与时间事件类

当前已覆盖 `16` 个模板归属。

- `单调风险分层柱图`
  用途：把低危、中危、高危等分层按顺序摆开，直接看事件数、风险率是否随分层单调变化。
- `时间依赖 ROC（单时间点）`
  用途：看生存模型在某个具体随访时间点上的判别力。
- `时间依赖 ROC 对比面板`
  用途：并排比较多个随访时间点或多个队列的 ROC。
- `landmark 表现汇总面板`
  用途：对比不同 landmark 时间窗的判别力、误差和校准，适合动态预测任务。
- `时间事件阈值治理面板`
  用途：把生存阈值、风险分层和校准结果一起呈现，适合临床使用场景。
- `多时间点分组校准面板`
  用途：看多个预测时间窗下的分组校准情况。
- `Kaplan-Meier 分组生存曲线`
  用途：最经典的生存曲线，用来看不同组的生存概率是否分开。
- `分组累计发生曲线`
  用途：当终点更适合看累计发生率而不是生存率时，用来比较不同组的事件累积。
- `分层累计发生复合面板`
  用途：把不同分层或不同终点的累计发生率放在同一张图中系统比较。
- `性能热图`
  用途：把不同时间窗、不同队列、不同指标的表现做成矩阵热图，一眼看全局。
- `时间事件判别 + 分组校准面板`
  用途：适合做正式验证图，兼顾“分得开”和“报得准”。
- `风险组汇总图`
  用途：把每个风险组的病例数、事件数、绝对风险等核心信息做成简洁面板。
- `时间事件决策曲线`
  用途：回答“在某个预测时间窗上，模型是否真的能帮临床做更好的决策”。
- `时间事件性能汇总表`
  用途：规范汇总多个生存分析指标，方便正文或补充材料引用。
- `分组风险事件汇总表`
  用途：按风险组汇总病例数、事件数和风险展示，服务于论文正文解释。

### C. 效应量与异质性类

当前已覆盖 `8` 个模板归属。

- `主效应森林图`
  用途：展示主要变量或主要模型结果的效应量和置信区间。
- `多变量森林图`
  用途：展示多变量模型里各变量调整后的效应量和置信区间，回答“控制协变量后，主结果还剩多大、方向是否稳定”。
- `亚组森林图`
  用途：展示不同亚组里的效应量是否一致，回答“异质性大不大”。
- `泛化性 + 亚组复合面板`
  用途：把总体泛化表现和亚组效应量放到同一张图里，回答“整体能用、局部稳不稳”。
- `紧凑效应量面板`
  用途：把多个预设调整规格、模型版本或 cohort 定义下的效应量并排收进一张紧凑多 panel 图里，回答“方向是否一致、量级是否接近、区间是否仍然可读”。
- `系数路径面板`
  用途：把同一批预设变量在 unadjusted、adjusted、sensitivity 等模型步骤下的系数方向与幅度变化收进一张双 panel 图里，左侧看 path，右侧看稳定性摘要，回答“哪些效应方向稳定、哪些在调整后衰减、哪些值得进正文或附录”。
- `交互效应汇总面板`
  用途：把 modifier-level interaction estimate、置信区间、favored subgroup 提示和 interaction P 值收进一张双 panel 图里，回答“哪些交互值得正文强调、哪些只是提示性信号、哪些目前证据不足”。

### D. 表征结构与数据几何类

当前已覆盖 `12` 个模板归属。

- `UMAP 分组散点图`
  用途：把样本压到二维空间里，看不同组是否形成清晰结构。
- `PCA 分组散点图`
  用途：看数据的主成分结构，适合做最基础的几何分布展示。
- `t-SNE 分组散点图`
  用途：更强调局部邻域结构，适合看复杂数据的聚类分布。
- `PHATE 分组散点图`
  用途：强调连续状态转变与流形演进，适合看轨迹感更强的结构分布。
- `细胞类型嵌入 + 签名热图`
  用途：把低维嵌入和 marker/program 热图绑在一起，既看结构，也看生物学含义。
- `单细胞图谱总览面板`
  用途：把图谱嵌入、群体组成变化和 marker/program 定义做成一张总览图。
- `atlas-spatial bridge 面板`
  用途：把 atlas 里的状态结构、真实组织空间里的状态定位、区域组成变化和 marker/program 定义绑成一张四块式桥接图，回答“图谱里看到的状态，能不能在空间里和组成差异上对得上”。
- `空间 niche 地图面板`
  用途：把组织空间位置、niche 组成和 marker/program 信息同时展示出来。
- `轨迹进展面板`
  用途：把轨迹嵌入、伪时间组成变化和 marker/module 动态放在一起，看过程如何演进。
- `atlas-spatial-trajectory storyboard 面板`
  用途：把 atlas、空间拓扑、轨迹进展、区域组成与程序动力学绑成一张五块式叙事图，回答“同一状态结构能否同时在图谱、空间和演进过程中被连续解释”。
- `atlas-spatial-trajectory density / coverage 面板`
  用途：把 atlas 密度、空间覆盖、轨迹覆盖和状态-上下文支持热图绑成一张四块式合同图，回答“同一状态在 atlas / tissue / progression 三个上下文里到底覆盖到哪里、支持有多强”。
- `atlas-spatial-trajectory context-support 面板`
  用途：把 atlas 占据度、空间状态拓扑、轨迹进展、区域状态组成、程序动力学和状态-上下文支持热图绑成一张六联 manuscript-facing 图，回答“同一状态结构在 atlas、空间、轨迹、区域组成和程序支持层面能否形成连续、互相印证的证据链”。

### E. 特征模式与矩阵类

当前已覆盖 `13` 个模板归属。

- `分组比较热图`
  用途：把多个组在多个特征上的高低模式直接做成热图比较。
- `性能热图`
  用途：把模型、指标、时间窗或队列的表现做成矩阵，适合做全局总结。
- `相关性热图`
  用途：看变量之间的相关结构，适合探索性分析和补充材料。
- `聚类热图`
  用途：在已有排序基础上展示样本或特征的块状结构。
- `通路富集点图面板`
  用途：把通路富集方向、效应强度和命中规模压缩进一张正文点图里，适合并列比较 transcriptome / proteome 或不同组学层的 pathway 证据。
- `细胞类型嵌入 + 签名热图`
  用途：兼具矩阵模式和图谱结构表达，是 D/E/G 的交叉模板。
- `单细胞图谱总览面板`
  用途：其中的组成矩阵和 marker/program 模块，属于典型矩阵型证据。
- `atlas-spatial bridge 面板`
  用途：其中的区域组成条带和 marker/program 热图，把 atlas 状态与空间分布之间的桥接证据压缩成一张矩阵驱动的复合图。
- `空间 niche 地图面板`
  用途：其中的区域组成和 marker/program 模块，也属于矩阵型表达。
- `轨迹进展面板`
  用途：其中的 kinetics 模块本质上也是矩阵型证据表达。
- `atlas-spatial-trajectory storyboard 面板`
  用途：其中的组成条带和 kinetics 热图，把 atlas / spatial / trajectory 三条证据链压缩成单一 storyboard 里的矩阵驱动复合表达。
- `atlas-spatial-trajectory density / coverage 面板`
  用途：其中的 state-by-context support heatmap 直接把 atlas / spatial / trajectory 三个上下文里的支持强度压成一张矩阵型证据图。
- `atlas-spatial-trajectory context-support 面板`
  用途：其中的区域组成、程序动力学和 state-by-context support heatmap 一起构成更完整的矩阵驱动复合证据，适合把 atlas / spatial / trajectory 三条链条压成一张正式论文图。

### F. 模型解释类

当前已覆盖 `20` 个模板归属。

- `模型复杂度审计面板`
  用途：展示模型规模、复杂度、特征数或治理边界，回答“这个模型是不是太重、太复杂”。
- `SHAP beeswarm 总览图`
  用途：看全局哪些特征最重要，以及它们对预测方向的总体影响。
- `SHAP 条形重要性图`
  用途：把全局重要性做成更规整的条形图，适合论文正文。
- `SHAP 带方向的重要性图`
  用途：不仅看重要性大小，还看它更偏向推高风险还是降低风险。
- `SHAP 多队列重要性对比图`
  用途：看不同队列里，重要特征排序是否一致。
- `SHAP dependence 面板`
  用途：看某个特征取值变化时，模型输出如何变化。
- `SHAP waterfall 局部解释图`
  用途：解释单个病例的预测值是如何被各个特征一步步推上去或拉下来的。
- `SHAP force-like 摘要图`
  用途：把局部解释压缩成更适合论文展示的“推拉”结构图。
- `SHAP 分组局部解释对比图`
  用途：把两组或多组代表性病例的局部解释并排对比。
- `SHAP 分组决策路径图`
  用途：看不同组的特征是如何沿着一条累计路径共同把预测值推到最终结果。
- `SHAP 多组决策路径图`
  用途：把三组共享 baseline 的累计决策路径放到一张图里，适合正文直接比较不同 phenotype 或 subtype 的预测形成机制。
- `SHAP grouped-local + support-domain 复合面板`
  用途：上排对比代表性局部解释，下排补充对应特征的响应曲线和支持区间，适合论文一张图同时回答“为什么判成这样”和“这个解释在什么数据域里站得住”。
- `SHAP 多组决策路径 + support-domain 复合面板`
  用途：上排用三组共享 baseline 的 cumulative decision path 直接比较不同 phenotype 或 subtype 的预测形成机制，下排用两个 matched support-domain panel 交代关键特征的响应曲线、参考值与支持区间，适合论文一张图同时回答“为什么三组会拉开”和“这些解释在什么数据域里成立”。
- `PDP + ICE 面板`
  用途：同时看平均边际效应和个体曲线，回答“总体趋势”和“个体差异”。
- `二元交互 PDP 等高线图`
  用途：看两个特征一起变化时，模型响应面如何变化。
- `高阶交互切片 PDP 面板`
  用途：在固定住某个交互条件后，看另一个特征的响应曲线如何变化，适合解释“在不同背景下，同一特征为什么反应不一样”。
- `亚组对照 PDP 面板`
  用途：把不同亚组的边际响应曲线并排比较，回答“这个特征的作用方式在不同人群里是否一致”。
- `ALE 局部效应面板`
  用途：在特征相关性较强时，更稳健地展示局部效应变化，回答“某个区间内，特征变化到底把预测往哪个方向推了多少”。
- `support-domain explanation 面板`
  用途：单独交代某个特征的响应曲线、参考值和数据支持区间，适合补充说明 extrapolation 风险与 subgroup/bin 覆盖边界。

### G. 生物信息与组学证据类

当前已覆盖 `15` 个模板归属。

- `GSVA / ssGSEA 热图`
  用途：展示通路、基因集或程序活性在不同样本/分组中的变化。
- `通路富集点图面板`
  用途：把 pathway enrichment 的方向、强度和 hit count 放到一张正文可直接使用的组学总结图里，适合并列比较不同 omics 层或不同 panel 的富集结果。
- `组学 volcano 面板`
  用途：把差异表达的 fold-change、显著性阈值与重点基因标注压缩成一张正文可直接使用的 volcano 主图，适合并列比较两组条件、两个 omics 层或两个 cohort 的差异模式。
- `oncoplot 突变景观面板`
  用途：把样本级突变事件、顶栏突变负荷、侧边 altered frequency 与 cohort 注释整合进同一张正文主图，适合回答“哪些基因常突变、哪些样本突变更重、这些变化和临床注释是否同步”。
- `CNV recurrence summary 面板`
  用途：把样本级 CNV burden、区域级 gain/loss 频率、CNV matrix 与 cohort 注释压缩成一张正文可直接使用的 copy-number 主图，适合回答“哪些区域反复 gain/loss、哪些样本负荷更高、这些变化和关键注释是否同步”。
- `genomic alteration landscape 面板`
  用途：把 mutation 与 CNV 联合景观、顶栏负荷、侧边 alteration frequency 和 cohort 注释整合进同一张正文主图，适合回答“哪些基因在不同 alteration 层面同时异常、这些异常在样本维度上如何分布”。
- `genomic alteration consequence 面板`
  用途：把 gene-level alteration landscape 继续接到 transcriptome / proteome consequence 散点面板上，适合回答“关键 driver alteration 是否真的带来下游分子层的方向性后果，以及这种后果是否跨 omics 一致”。
- `genomic program governance 汇总面板`
  用途：把 cross-layer genomic evidence、program priority、主导 driver/pathway、verdict 和建议 action 收进同一张 manuscript-facing 两联图里，适合回答“哪些程序在多层组学里形成收敛证据、当前优先级是什么、下一步治理动作是什么”。
- `细胞类型嵌入 + 签名热图`
  用途：把单细胞或组学程序的结构和分子特征放到同一张图里。
- `单细胞图谱总览面板`
  用途：适合展示 atlas 级别的组学全局结构和程序差异。
- `atlas-spatial bridge 面板`
  用途：适合把 atlas 状态、空间定位和 marker/program 证据桥接起来，回答“同一组学状态是否真的落在特定空间区域与组成变化上”。
- `空间 niche 地图面板`
  用途：把空间组织学与组学程序表达结合起来。
- `轨迹进展面板`
  用途：展示沿轨迹演进过程中，组学模块如何动态变化。
- `atlas-spatial-trajectory storyboard 面板`
  用途：把 atlas、空间与轨迹三条组学叙事链放进同一张 storyboard 图里，适合做高层次整合性组学证据总结。
- `atlas-spatial-trajectory density / coverage 面板`
  用途：把 atlas / spatial / trajectory 三个上下文里的状态支持度放进同一张矩阵驱动复合图里，适合做更聚焦的整合性组学 coverage 证据总结。
- `atlas-spatial-trajectory context-support 面板`
  用途：把 atlas 状态结构、空间定位、轨迹进展、区域组成、程序动力学和上下文支持度一起放进同一张六联复合图里，适合做更完整的整合性组学主图。

### H. 队列与研究设计证据类

当前已覆盖 `19` 个模板归属。

- `模型复杂度审计面板`
  用途：当论文需要交代模型方法学边界时，这张图可以作为研究设计补充证据。
- `泛化性 + 亚组复合面板`
  用途：把总体泛化能力和关键亚组稳健性放在一张图里。
- `紧凑效应量面板`
  用途：把几个预设调整规格或 cohort 定义下的 OR/HR / effect estimate 收进一张紧凑 manuscript-facing 图面，适合在研究设计或稳健性位置快速交代结果是否方向一致。
- `系数路径面板`
  用途：把同一批预设变量在多个模型步骤下的系数路径和稳定性摘要一起呈现，适合在研究设计、稳健性或 appendix-facing summary 位置正式交代“调整前后效果是否保持稳定”。
- `交互效应汇总面板`
  用途：把预设修饰因素的 interaction estimate、favored subgroup 和 verdict summary 收在一张双 panel 图里，适合在研究设计、稳健性或正文方法学补充位置正式交代“哪些交互结论可信、哪些只属于提示性异质性信号”。
- `多中心泛化总览图`
  用途：看不同中心、不同外部队列的表现是否稳定，回答“能不能迁移”。
- `中心 transportability 治理汇总面板`
  用途：把各中心的关键 transportability 指标区间与治理结论收在一张双 panel 图里，适合正文直接回答“哪些中心表现稳定、哪些中心需要限制解释或继续重校准”。
- `队列流程图`
  用途：规范展示筛选、纳排、分析集形成过程，是方法学论文的标配图。
- `投稿图形摘要`
  用途：服务投稿入口，把研究问题、队列、方法和核心结果压成一张摘要图。
- `workflow fact sheet`
  用途：用固定 `2x2` 结构，把队列、终点、模型流程和验证边界做成规整的研究摘要图。
- `design-evidence composite shell`
  用途：用 `workflow ribbon + three summary panels` 的结构，把研究流程和关键设计证据做成一张更完整的稿件级骨架图。
- `基线平衡-缺失-质控三联面板`
  用途：一张图里同时交代组间基线平衡、缺失模式和数据质量下限，适合放在方法学、队列质量或补充材料入口位置。
- `中心覆盖-批次漂移-transportability 三联面板`
  用途：一张图里同时交代各中心样本支持度、批次/队列差异热图和 transportability boundary，适合放在多中心泛化、数据可迁移性或补充材料入口位置。
- `transportability recalibration governance 面板`
  用途：把各中心 recalibration 后的 slope、O:E ratio 和建议动作写成一张正式图面，适合回答“哪些中心已经校准到可接受区间、哪些中心需要继续重校准或限制解释范围”。
- `基线特征表（Table 1）`
  用途：规范展示各组的基线人口学与临床特征。
- `时间事件性能汇总表（Table 2）`
  用途：把多时间点 C-index、AUC、Brier 等关键结果整理成规范表格，适合在方法学或结果部分集中引用。
- `临床解释汇总表（Table 3）`
  用途：把风险分层解释、临床使用建议和结论摘要化，方便正文直接引用。

## 已被真实论文证明的核心能力

当前真正经过真实论文交付、而不只是“目录里存在”的核心能力，主要集中在 `001/003` 锚点论文暴露过的失败模式上。

已经被正式吸收进军火库下限保护的关键能力包括：

- 默认不把 `figure title` 直接画进图面，而是让标题策略服从稿件表达面；
- 注释文本需要落在预期空白区域内，而不是只要画出来就算通过；
- `panel label` 与 `header band` 必须稳定锚定，不能漂移；
- 有顺序含义的风险分层摘要，必须同时满足顺序、单调性与可读性；
- 时间窗、多窗口、多时间片证据需要显式写入结构，而不是靠图例或自由拼接暗示；
- 图形摘要的箭头通道、泛化性图的图例标题与标签、坐标窗与有效数据域之间的关系，都已经进入正式下限治理。

这意味着军火库的价值不只是“会画”，而是“知道哪些地方最容易把论文图画坏，并且已经把一部分坏法做成了确定性的下限防线”。

## 外部高水平期刊图例吸收情况

### 已经正式吸收进军火库的外部锚点

| 来源 | 吸收的结构能力 | 提升到的论文家族 / 模板 |
| --- | --- | --- |
| `HTN-AI` 图 3 | 把单一累计发生曲线提升为显式多分层、多面板累计发生率契约 | `B` / `time_to_event_stratified_cumulative_incidence_panel` |
| `Nature Medicine` 风险论文图 4a | 把单时间窗 ROC 提升为显式多窗口、多面板 ROC 契约 | `A/B` / `time_dependent_roc_comparison_panel` |
| `Nature Medicine` 风险论文图 4c | 把泛化热图提升为有顺序、有指标语义、有数值边界的性能热图契约 | `B/E` / `performance_heatmap` |
| `Nature Communications` `2021` ctDNA 动态复发风险研究 | 把 forward landmark windows 的 discrimination、Brier error 与 calibration slope 从自由拼图提升为统一治理的三联 summary 契约 | `A/B` / `time_to_event_landmark_performance_panel` |
| `Nature Medicine` `2025` 结直肠手术 AI 决策支持论文图 4a-d + `npj Digital Medicine` `2025` RCC / 胃癌预后论文图 2/5 | 把 threshold summary cards、grouped survival calibration governance、risk-group operating review 从论文现场组合图提升为正式 pack 模板契约 | `A/B` / `time_to_event_threshold_governance_panel` |
| `Nature Medicine` `2025` 结直肠手术 AI 决策支持论文图 4a-d 与 `npj Digital Medicine` `2025` RCC / 胃癌预后论文图 2/5 所体现的多 horizon 校准叙事 | 把 `3/5-year` 并列 grouped calibration governance 从单 horizon dumbbell / 组合图内嵌局部能力提升为正式 multi-horizon 校准模板，并把 horizon strict order、panel identity 与 calibration point fail-closed 一并固定 | `A/B` / `time_to_event_multihorizon_calibration_panel` |
| `Nature Medicine` `2025` 炎症图谱图 1 + `npj Digital Medicine` `2025` 前列腺 XAI 图 1/2/3/7 | 把单独的 embedding scatter 与矩阵热图提升为显式耦合的 `celltype/program` 复合图式，并把 `score_method`、行列完备性、legend/colorbar 锚定做成确定性约束 | `D/E/G` / `celltype_signature_heatmap` |
| `Genome Research` `2021` tumor immune atlas 图 2 + `Nature Communications` `2023` integrated TME mapping 图 3 | 把 repeated atlas partial-fit 学到的 `embedding occupancy + group-wise composition shift + marker/signature definition` 固化为单一 atlas overview composite，并把 composition 完整性、state vocabulary 对齐、heatmap 网格完备性与 panel-level readability 做成正式契约 | `D/E/G` / `single_cell_atlas_overview_panel` |
| `Nature Medicine` `2024` spatial niche exemplar + `Nature Medicine` `2025` atlas-state bridge exemplar + `Nature Communications` `2025` spatial atlas exemplar | 把 atlas 里的状态结构、组织空间里的状态定位、region-wise state composition 与 marker/program definition 统一成单一四块式 bridge composite，并把 atlas/spatial state vocabulary 对齐、region composition 完整性、heatmap 网格完备性与四个 panel label 锚定做成正式契约 | `D/E/G` / `atlas_spatial_bridge_panel` |
| `Nature Medicine` `2024` spatial niche exemplar + `Nature Communications` `2025` spatial atlas exemplar + `npj Digital Medicine` `2025` tissue-organization exemplar + `Nature Communications` `2023` TME mapping 图 3 | 把 tissue-coordinate niche localization、region-wise niche composition 与 marker/program definition 从多篇论文里的现场复合图提升为统一的 spatial niche composite，并把 niche vocabulary 对齐、composition 完整性、heatmap 网格完备性与 panel-label anchoring 做成正式契约 | `D/E/G` / `spatial_niche_map_panel` |
| `Nature Biotechnology` `2023` trajectory exemplar | 把 trajectory / manifold 里的 branch progression、pseudotime-bin composition 与 marker/module kinetics 从论文现场多块拼图提升为统一的 trajectory progression composite，并把 branch vocabulary、pseudotime bins、branch-weight completeness 与 kinetics heatmap 网格做成正式契约 | `D/E/G` / `trajectory_progression_panel` |
| `Nature Medicine` `2024` spatial niche exemplar + `Nature Communications` `2025` spatial atlas exemplar + `Nature Biotechnology` `2023` trajectory exemplar | 把 atlas、空间与轨迹三条已经分开审计的证据链继续上提为五块式 storyboard composite，并把共享 state vocabulary、branch/bin 治理、composition 完整性、kinetics heatmap 网格与五个 panel label 锚定做成正式契约 | `D/E/G` / `atlas_spatial_trajectory_storyboard_panel` |
| `Nature Medicine` `2024` spatial niche exemplar + `Nature Communications` `2025` spatial atlas exemplar + `Nature Biotechnology` `2023` trajectory exemplar + density / coverage follow-on real-paper demand | 把 atlas、空间与轨迹三条已经分开审计的证据链继续收束成四块式 density / coverage support composite，并把共享 state vocabulary、region/branch 受控语义、context-kind 治理与 state-by-context support heatmap 完整网格做成正式契约 | `D/E/G` / `atlas_spatial_trajectory_density_coverage_panel` |
| `Nature Medicine` `2024` spatial niche exemplar + `Nature Communications` `2025` spatial atlas exemplar + `Nature Biotechnology` `2023` trajectory exemplar + context-support follow-on real-paper demand | 把 atlas、空间与轨迹三条已经收束到 density / coverage support baseline 的证据链继续推进到六联 context-support composite，并把 atlas occupancy、spatial state topography、trajectory progression、region-wise state composition、kinetics heatmap 与 state-by-context support heatmap 一并收进单一 bounded manuscript-facing 契约 | `D/E/G` / `atlas_spatial_trajectory_context_support_panel` |
| `Nature Medicine` / `Nature Cancer` / `npj Digital Medicine` 等高水平组学论文常见 volcano 编排 + 真实正文差异组学交付需求 | 把差异表达结果从自由散点图提升为正式 bounded up-to-two-panel volcano 契约；固定 fold-change 阈值、显著性阈值、`upregulated/downregulated/background` 受控词表、highlight label 与 threshold-guide sidecar 治理 | `G` / `omics_volcano_panel` |
| `Nature Medicine` / `Nature Cancer` / `npj Digital Medicine` 等高水平组学论文常见 oncoplot 编排 + 真实正文突变景观交付需求 | 把突变景观结果从自由拼接图提升为正式 bounded oncoplot 契约；固定 declared `gene_order`、declared `sample_order`、最多三条 annotation track、top burden 与右侧 altered-frequency 侧栏语义 | `G` / `oncoplot_mutation_landscape_panel` |
| `Nature Medicine` / `Nature Cancer` / `npj Digital Medicine` 等高水平组学论文常见 CNV summary 编排 + 真实正文 copy-number 主图交付需求 | 把 copy-number gain/loss summary 从自由拼接图提升为正式 bounded CNV recurrence 契约；固定 declared `sample_order`、declared `region_order`、最多三条 annotation track、top burden 与右侧 gain/loss frequency 侧栏语义 | `G` / `cnv_recurrence_summary_panel` |
| `Nature Medicine` / `Nature Cancer` / `npj Digital Medicine` 等高水平组学论文常见 mutation + CNV landscape 编排 + 真实正文联合 alteration 主图交付需求 | 把分开的 mutation oncoplot 与 CNV summary 收束成正式 bounded mutation-plus-CNV genomic landscape 契约；固定 declared `gene_order`、declared `sample_order`、最多三条 annotation track、top burden、右侧 gene-level alteration frequency、dual-state overlay 与 vocabulary 治理 | `G` / `genomic_alteration_landscape_panel` |
| `Nature Medicine` / `Nature Cancer` / `npj Digital Medicine` 等高水平组学论文常见 driver-gene consequence 编排 + 真实正文 transcriptome / proteome follow-on 交付需求 | 把 gene-level genomic landscape 继续上提为正式 bounded driver-centric consequence 契约；固定 `driver_gene_order`、`consequence_panel_order`、effect / significance threshold、transcriptome / proteome scatter panel 与 consequence legend 语义 | `G` / `genomic_alteration_consequence_panel` |
| `Nature Communications` `2025` driver mutation to proteome/phosphoproteome/glycoproteome consequence 编排 + 真实正文 multiomic follow-on 交付需求 | 把 landscape + driver-centric consequence 继续上提为正式 bounded三层 multiomic consequence 契约；固定 `proteome/phosphoproteome/glycoproteome` vocabulary、每层 driver coverage、effect / significance threshold、panel identity 与 consequence label containment | `G` / `genomic_alteration_multiomic_consequence_panel` |
| `Nature Communications` `2025` driver mutation后 pathway-level enrichment 编排 + 真实正文 broader genomic composite 交付需求 | 把 landscape + 三层 multiomic consequence 再继续上提为正式 bounded `1 + 3 + 3` pathway-integrated composite 契约；固定 shared `pathway_order`、pathway colorbar / size-scale、`proteome/phosphoproteome/glycoproteome` 双层 consequence/pathway panel identity 与 composite panel-label anchoring | `G` / `genomic_alteration_pathway_integrated_composite_panel` |
| `Nature Cancer` / `Nature Communications` / `npj Digital Medicine` 等高水平组学论文常见 program-governance synthesis 编排 + 当前 broader genomic composite backlog sweep | 把 pathway-integrated composite 继续上提为正式 bounded two-panel genomic program governance summary 契约；固定五层 `layer_order`、program priority / verdict / action 受控词表、cross-layer support coverage、主导 driver/pathway 摘要与 manuscript-facing governance table-like summary 语义 | `G` / `genomic_program_governance_summary_panel` |
| `npj Digital Medicine` `2025` 前列腺 XAI SHAP dependence 图面 | 把论文现场局部 dependence explanation 提升为正式多 panel SHAP dependence 契约，并把 shared colorbar、panel label 与 zero-line 变成可审计下限 | `F` / `shap_dependence_panel` |
| `npj Digital Medicine` `2025` UMORSS ovarian workflow 图 6 + `JBJS Open Access` `2025` PARITY bone tumor explanation 图 6A/B | 把 patient-level SHAP explanation 从“单篇论文现场插图”提升为正式 waterfall 模板；固定 `baseline -> ordered contributions -> final prediction` additive path、case/panel 唯一性、贡献方向一致性与预测值守恒约束 | `F` / `shap_waterfall_local_explanation_panel` |
| `真实解释型论文交付需求 + SHAP force plot 经典解释图式` | 把代表性病例的局部解释从 waterfall 再推进到 bounded force-like summary；固定 `baseline marker -> positive/negative directional lanes -> prediction marker` 的 panel 内表达，并把标签 containment、方向一致性与排序守恒做成正式契约 | `F` / `shap_force_like_summary_panel` |
| `真实解释型论文交付需求 + PDP / ICE 经典解释图式` | 把按特征展开的 marginal response 与 individual trajectory explanation 从候选概念提升为正式 bounded multi-panel 模板；固定 `PDP mean + ICE curves`、per-panel reference line/label、shared legend 语义以及 panel 内几何 containment 契约 | `F` / `partial_dependence_ice_panel` |
| `npj Digital Medicine` `2026` pairwise partial-dependence interaction exemplar + `Nature Communications` `2020` pairwise PDP / interaction reasoning exemplar | 把 pairwise partial-dependence interaction 从论文现场的 3D / pairwise scene 提炼成更适合投稿审计的二维 contour lower bound；固定显式 `x_grid/y_grid`、`response_grid` 维度一致性、reference crosshair、shared colorbar 与 observed-support containment 契约 | `F` / `partial_dependence_interaction_contour_panel` |
| `真实解释型论文交付需求 + SHAP bar importance 经典解释图式` | 把全局特征重要性总览从“解释章节常见但未正式入库的补位图式”提升为正式 bounded 单 panel 模板；固定 feature unique、rank strict order、importance non-negative finite、bar/value-label 关联与 panel containment 契约 | `F` / `shap_bar_importance` |
| `真实解释型论文交付需求 + SHAP signed importance / divergent bar 经典解释图式` | 把方向性全局特征重要性总览提升为正式 zero-centered 单 panel 模板；固定 signed polarity、absolute-magnitude strict order、negative/positive direction labels、zero-line side governance 与 polarity-aware value-label containment 契约 | `F` / `shap_signed_importance_panel` |
| `真实解释型论文交付需求 + multi-cohort global importance comparison 经典解释图式` | 把跨 cohort 的全局特征重要性对照从“候选 follow-on”提升为正式 bounded multi-panel 模板；固定 panel/cohort identity、shared feature-order governance、per-panel rank strict order、bar/value-label 关联与 panel-label anchoring 契约 | `F` / `shap_multicohort_importance_panel` |
| `真实解释型论文交付需求 + grouped local explanation comparison 经典解释图式` | 把 grouped local explanation comparison 从“已有 waterfall / force-like 但仍缺跨 panel 比较”的 follow-on 候选提升为正式 bounded multi-panel 模板；固定 panel/group identity、shared feature-order governance、baseline-plus-contribution conservation、zero-centered signed contribution lanes 与 row-aligned feature/value labels 契约 | `F` / `shap_grouped_local_explanation_panel` |
| `真实解释型论文交付需求 + SHAP decision plot / grouped decision-path 经典解释图式` | 把 grouped decision-path comparison 从“已有 grouped-local 但仍缺共享 baseline 的 cumulative decision path 对照”的 follow-on 候选提升为正式 bounded 单 panel 模板；固定 shared feature-order、baseline reference line、ordered cumulative segments、prediction marker/label 与两组守恒关系契约 | `F` / `shap_grouped_decision_path_panel` |
| `真实解释型论文交付需求 + 多组 phenotype / subtype explanation manuscript-facing 对照需求` | 把三组共享 baseline 的 cumulative decision path 对照从“已有双组模板的外推需求”提升为正式 bounded 单 panel 模板；固定 exactly-three groups、shared feature-order、baseline reference line、右侧 legend 治理、prediction marker/label containment 与三组守恒关系契约 | `F` / `shap_multigroup_decision_path_panel` |
| `JAMA Surgery` `2025` multicenter surgical transfusion risk 图 2A/B + `npj Digital Medicine` `2026` postcranioplasty multicenter cohort 图 3/4/5 + `World Psychiatry` `2024` UHR 1000+ 图 2 | 把 subgroup interval 与 generalizability overview 从“forest + multicenter panels 各自独立”提升为固定两块式 composite；同时把 cohort/support completeness、subgroup interval fail-closed、legend 语义与 outboard label containment 做成正式契约 | `C/H` / `generalizability_subgroup_composite_panel` |
| `真实论文 compact-estimate / coefficient-path / broader-heterogeneity / interaction-summary follow-on 交付需求 + bounded lower-bound hardening` | 先把多个预设 estimate slices 从论文现场并排 forest / 补充说明收敛成共享 reference line、共享 row order 的紧凑多 panel effect-estimate 图面，再把预设模型步骤下的 coefficient direction / magnitude stability 收束成 bounded `path + summary` manuscript-facing 合同，进一步上提到逐行 manuscript verdict 收口的 broader heterogeneity summary，最后补齐 modifier-level interaction estimate、interaction P 值与 favored subgroup narration 的正式双 panel lower bound；同时把 panel count、panel identity、interval containment、step coverage、slice vocabulary、modifier verdict vocabulary 与 summary-panel alignment 做成正式契约 | `C/H` / `compact_effect_estimate_panel`、`coefficient_path_panel`、`broader_heterogeneity_summary_panel`、`interaction_effect_summary_panel` |

### 已观察、仍在候选池中的高价值素材

以下素材已经进入绘图主线视野，但当前仍不计入“已正式落地的新增军火库能力”。其中 atlas exemplar 暴露出的 `embedding + signature heatmap`、`embedding + composition + marker/program overview`、`atlas embedding + spatial state topography + region-wise state composition + marker/program heatmap`、`atlas / spatial / trajectory density-coverage support contract` 与 `atlas / spatial / trajectory context-support composite`，spatial exemplar 暴露出的 `tissue-coordinate niche topography + region-wise niche composition + marker/program definition`，以及 trajectory exemplar 暴露出的 `trajectory progression + pseudotime-bin branch composition + marker/module kinetics`，已分别正式入库为 `celltype_signature_heatmap`、`single_cell_atlas_overview_panel`、`atlas_spatial_bridge_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel`、`atlas_spatial_trajectory_density_coverage_panel` 与 `atlas_spatial_trajectory_context_support_panel`；更大 atlas / spatial / trajectory 多视图变体仍留在候选池中：

- `Cancer Cell` `2022` 肾脏图谱类图面：
  - 价值：总体嵌入 + 主要细胞类型热图 + 空间上下文；
  - 可能提升：`D/E/G`；
  - 当前状态：已作为外部范例候选归档。
- `Lancet Digital Health` 多癌种风险图 2：
  - 价值：风险表达与泛化表达的稿件级组合方式；
  - 可能提升：`A/H`；
  - 当前状态：保留为低优先级候选。

## 当前军火库的边界

### 1. 军火库不是模板数量竞赛

军火库的目标是提升论文交付能力，而不是机械堆模板数量。

一个模板只有在以下条件同时满足时，才算真正进入军火库：

- 已注册；
- 有正式输入契约；
- 有渲染路径；
- 有质控路径；
- 能通过稿件包装与投稿输出验证；
- 最好还能被真实论文图面验证过。

### 2. 下限与上限必须分开治理

模板与质控负责保下限，但它们不应该假装自己已经覆盖了全部视觉判断。

真正的论文级上限，仍然依赖 AI 优先的视觉审计与再修订闭环：

1. 先按审计路径出图；
2. 再看真实图像；
3. 明确指出具体问题；
4. 再把可复用的问题沉淀回模板、契约、渲染器或质控。

### 3. 当前仍不计入“已成熟完成”的部分

以下方向已经有价值，但当前不应被误写成“军火库已经完整具备”：

- `F` 家族虽已从 `shap_summary_beeswarm` 扩到 `shap_bar_importance`、`shap_signed_importance_panel`、`shap_multicohort_importance_panel`、`shap_dependence_panel`、`shap_waterfall_local_explanation_panel`、`shap_force_like_summary_panel`、`shap_grouped_local_explanation_panel`、`shap_grouped_decision_path_panel`、`shap_multigroup_decision_path_panel`、`shap_grouped_local_support_domain_panel`、`shap_multigroup_decision_path_support_domain_panel`、`partial_dependence_ice_panel`、`partial_dependence_interaction_contour_panel`、`partial_dependence_interaction_slice_panel`、`partial_dependence_subgroup_comparison_panel`、`accumulated_local_effects_panel` 与 `feature_response_support_domain_panel`，但 annotation / legend 治理与更高阶 explanation scene 仍需继续滚动 hardening；
- `C/H` 虽已从 `subgroup_forest` / `multicenter_generalizability_overview` 扩到 `generalizability_subgroup_composite_panel`、`compact_effect_estimate_panel`、`coefficient_path_panel`、`broader_heterogeneity_summary_panel` 与 `interaction_effect_summary_panel`，并补齐 workflow / design-evidence / baseline-missingness-QC shells、center-coverage / batch-shift / transportability 三联壳层与 recalibration-governance follow-on，但 calibration appendix 与更高层 transportability synthesis 仍在后续扩容范围内；
- `D/E/G` 更大 atlas / spatial / trajectory 复合图谱结构；`single_cell_atlas_overview_panel`、`atlas_spatial_bridge_panel`、`spatial_niche_map_panel`、`trajectory_progression_panel`、`atlas_spatial_trajectory_storyboard_panel`、`atlas_spatial_trajectory_density_coverage_panel` 与 `atlas_spatial_trajectory_context_support_panel` 已把 baseline 扩到 occupancy / atlas-spatial bridge / spatial topography / progression / storyboard / density-coverage support / context-support，但 atlas / spatial / trajectory 平台仍在继续扩库；
- `G/E` 已形成 `GSVA/ssGSEA 热图 + pathway enrichment dotplot + omics volcano + bounded oncoplot + bounded CNV summary + bounded genomic alteration landscape + bounded genomic alteration consequence + bounded三层 multiomic consequence + bounded pathway-integrated composite + bounded genomic program governance summary` 十基线，后续扩容重点转向超出当前 program-governance lower bound 的更高阶 genomic-governance scene 与更复杂的 enrichment 组合图；
- 仅在外部范例中观察到、但还没形成正式模板与回归套件的高级图式。

## 后续维护规则

后续每次军火库扩充，至少要同步更新两份文档：

1. 本文：更新当前总览、家族全貌与已吸收能力；
2. [medical_display_arsenal_history.md](./medical_display_arsenal_history.md)：追加时间、来源、学到的结构、提升到的家族或模板。

这样做的目的，是让“现在会什么”和“怎么学会的”始终保持分离但一致。
