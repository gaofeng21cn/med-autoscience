# Display Pack Renderer 分层与 R/ggplot2 迁移评估

Owner: `MedAutoScience Medical Display`
Purpose: `display_pack_renderer_topology_and_migration_assessment`
State: `active_plan`
Machine boundary: 本文是人读结构评估和迁移计划。机器真相继续归 `display-packs/**/display_pack.toml`、`display-packs/**/templates/*/template.toml`、renderer source、`contracts/display-pack-contract.v2.json`、E2E runtime、tests、真实 paper artifacts、visual-audit receipt、owner receipt 和 publication gate。

## 当前结论

`R/ggplot2-first` 的方向是对的，但当前 core pack 还没有完成模板层迁移。

当前 `fenggaolab.org.medical-display-core` 的真实 inventory 是：

| 口径 | 数量 | 当前真实状态 |
| --- | ---: | --- |
| Evidence figure template descriptor | 84 | 已在 `templates/*/template.toml` 注册。 |
| `renderer_family = "r_ggplot2"` | 22 | 已有 R/ggplot2 内核，但通过 `python_plugin` 调 `r_renderer.py`，再临时写 R script 并调用 `Rscript`。 |
| `renderer_family = "python"` | 62 | Python renderer，主要是 matplotlib / pack-local layout code。 |
| `execution_mode = "subprocess"` | 0 | Runtime 协议已落地，core pack 模板尚未迁移。 |
| 模板目录内 `render.R` | 0 | 还没有 template-local R subprocess entrypoint。 |

因此，现状应读作：**22 个 evidence templates 已经有 R/ggplot2 绘图能力，但治理上仍是 Python plugin 二等路径；`subprocess` runtime 已经让它们可以升级为一等路径。**

## 结构问题

当前结构把三个概念混在了一起：

| 概念 | 应表达的事实 | 当前问题 |
| --- | --- | --- |
| `renderer_family` | 图由什么生态绘制，例如 `r_ggplot2` / `python`。 | 22 个模板标为 `r_ggplot2`，但调用路径仍是 Python plugin。 |
| `execution_mode` | MAS runtime 如何调用 renderer，例如 `subprocess` / `python_plugin`。 | 84 个 evidence templates 全部是 `python_plugin`，无法从 descriptor 上直接看出一等 R entrypoint。 |
| `entrypoint` | 模板自己的稳定入口。 | R 模板共享一个 Python entrypoint，真实 R script 藏在 `r_renderer.py` 字符串里。 |

这会带来三个维护成本：

1. 管理者看到 `r_ggplot2`，但无法直接检查 `render.R`、R package dependency、R sidecar schema 或 R-level golden。
2. R 模板和 Python 模板都挤在 Python plugin 生命周期里，后续 lock、audit、cache、distribution 很难按真实 runtime 分账。
3. 新增 R 模板时容易继续复制 Python wrapper，而不是使用一等 `subprocess` 合同。

## 建议目标结构

目标不是把所有图硬改成 R，而是让每个模板的 **绘图生态** 和 **执行入口** 一致、可审计、可替换。

推荐结构：

```text
display-packs/fenggaolab.org.medical-display-core/
  display_pack.toml
  templates/
    <template_id>/
      template.toml
      render.R                 # R/ggplot2 subprocess 模板的一等入口
      example_input.json       # 可选，最小输入
      goldens/                 # 可选，template-local regression assets
  src/
    fenggaolab_org_medical_display_core/
      evidence_figures/        # Python plugin templates
    rlib/
      medicaldisplaycore/      # R shared helpers，不能替代 template-local entrypoint
```

模板 descriptor 规则：

| 模板类型 | `renderer_family` | `execution_mode` | `entrypoint` |
| --- | --- | --- | --- |
| 一等 R 模板 | `r_ggplot2` | `subprocess` | `Rscript render.R --request {request_json}` |
| Python 模板 | `python` | `python_plugin` | `fenggaolab_org_medical_display_core...:render_python_evidence_figure` |
| 迁移过渡模板 | `r_ggplot2` | `python_plugin` | 只允许短期存在，并在 migration ledger 标注。 |

新增治理面：

- `renderer_inventory`：由 `template.toml` 生成，统计 `kind`、`renderer_family`、`execution_mode`、entrypoint 和 migration status。
- `r_subprocess_contract`：R renderer 必须读取 `{request_json}`，写出 PNG/PDF/layout sidecar，stdout/stderr 由 MAS runtime 收集。
- `migration_ledger`：记录每个模板的 `current_mode`、`target_mode`、R package candidates、迁移难度、golden/QC 要求和不迁理由。
- `dependency_profile`：R 包依赖进入 pack-level profile，不能散落在脚本注释里。

## R 生态证据

R/ggplot2 适合作为医学 evidence figure 默认路线，原因不是偏好，而是成熟生态覆盖面：

- `ggplot2` 官方定位就是基于 Grammar of Graphics 的声明式图形系统，能把 data、aesthetic、geom、scale、facet、theme 分层管理；其扩展生态也是长期稳定入口。[ggplot2](https://ggplot2.tidyverse.org/)
- 生存曲线和 risk table 有 `survminer::ggsurvplot()`，支持 stratified survival curves、facet/group/combine、risk table、p value、confidence interval 和 ggsci palette。[survminer ggsurvplot](https://rpkgs.datanovia.com/survminer/reference/ggsurvplot.html)
- ROC 有 `pROC::ggroc()`，可从 ROC object/list 初始化 ggplot object，并继续叠加 theme/layers。[pROC ggroc](https://search.r-project.org/CRAN/refmans/pROC/html/ggroc.html)
- Decision curve 有 `dcurves`，目标就是 model evaluation 的 decision curve analysis。[dcurves](https://www.danieldsjoberg.com/dcurves/)
- 复杂热图和多注释矩阵图有 Bioconductor `ComplexHeatmap`，适合多组学、annotation-rich heatmap 和 matrix pattern。[ComplexHeatmap](https://www.bioconductor.org/packages/release/bioc/html/ComplexHeatmap.html)
- 森林图有 `forestploter` 这类 R 包，支持多列 CI、分组和主题化编辑。[forestploter](https://adayim.r-universe.dev/forestploter)
- SHAP 可视化有 `shapviz`，覆盖 importance、beeswarm、dependence、interaction、waterfall 和 force plots。[shapviz](https://cran.r-project.org/package%3Dshapviz)
- 医学期刊和科学图配色有 `ggsci`，覆盖 NPG、NEJM、Lancet、JAMA、BMJ、JCO 等 palette。[ggsci](https://nanx.me/ggsci/)
- 文本避让可用 `ggrepel`；火山图可用 `EnhancedVolcano`；富集 dotplot 可用 `enrichplot`；肿瘤 oncoplot 可用 `maftools`。这些不必全部成为 runtime dependency，但足以证明很多 Python 手写模板可迁到成熟 R pattern。[ggrepel](https://ggrepel.slowkow.com/) [EnhancedVolcano](https://bioconductor.posit.co/packages/3.19/bioc/html/EnhancedVolcano.html) [enrichplot dotplot](https://rdrr.io/bioc/enrichplot/man/dotplot.html) [maftools oncoplot](https://rdrr.io/bioc/maftools/man/oncoplot.html)

## 迁移优先级

### P0：先把已有 22 个 R/ggplot2 模板升成一等 subprocess

这些模板已有 `renderer_family = "r_ggplot2"`，迁移成本最低，收益最大。目标是把共享 `r_renderer.py` 中的 R 代码拆成 template-local `render.R` + shared R helper。

| 模板族 | 模板 | 推荐 R 基座 |
| --- | --- | --- |
| Binary performance curves | `roc_curve_binary`, `pr_curve_binary`, `calibration_curve_binary` | `ggplot2`, `pROC`, `ggsci`, calibration helper |
| Decision / clinical utility | `decision_curve_binary`, `clinical_impact_curve_binary` | `dcurves` / controlled ggplot implementation |
| Survival curves | `kaplan_meier_grouped`, `cumulative_incidence_grouped`, `time_dependent_roc_horizon` | `survminer`, `timeROC`, `riskRegression`, `ggplot2` |
| Embedding scatter | `umap_scatter_grouped`, `pca_scatter_grouped`, `phate_scatter_grouped`, `tsne_scatter_grouped`, `diffusion_map_scatter_grouped` | `ggplot2`, `ggrepel`, `ggsci` |
| Heatmap / matrix | `heatmap_group_comparison`, `performance_heatmap`, `confusion_matrix_heatmap_binary`, `correlation_heatmap`, `clustered_heatmap`, `gsva_ssgsea_heatmap` | `ComplexHeatmap` for complex layouts; `ggplot2::geom_tile` for simple matrices |
| Forest plot | `forest_effect_main`, `subgroup_forest`, `multivariable_forest` | `forestploter` / controlled ggplot forest helper |

P0 验收标准：

- 22 个模板的 `execution_mode` 改为 `subprocess`；
- 每个模板目录有 `render.R` 或明确的 local wrapper；
- E2E runtime 直接调用 `Rscript render.R --request {request_json}`；
- PNG/PDF/layout sidecar、stdout/stderr refs、QC、visual-audit receipt、publication manifest 和 display lock 继续闭合；
- 删除或 tombstone `r_renderer.py` 中对应的 R script 字符串桥接。

### P1：优先迁移现有 Python 里 R 生态明显更成熟的模板

这些模板现在是 Python，但医学论文和 R 生态已有成熟惯例，适合优先做 R/ggplot2 subprocess 版本。迁移时可以保留 Python 旧实现作为 comparison baseline，直到 golden 和 visual audit 稳定。

| 图类 | 当前 Python 模板 | 迁移理由 |
| --- | --- | --- |
| Time-to-event composite | `time_dependent_roc_comparison_panel`, `time_to_event_discrimination_calibration_panel`, `time_to_event_landmark_performance_panel`, `time_to_event_multihorizon_calibration_panel`, `time_to_event_risk_group_summary`, `time_to_event_stratified_cumulative_incidence_panel`, `time_to_event_decision_curve`, `time_to_event_threshold_governance_panel` | R 侧 survival / time-dependent ROC / calibration / DCA 生态更成熟；医学论文读者也更熟悉这类图面。 |
| Clinical utility composite | `binary_calibration_decision_curve_panel` | 可用 ggplot2 + dcurves / calibration helpers 形成更标准的多面板图。 |
| Effect estimate / heterogeneity | `compact_effect_estimate_panel`, `broader_heterogeneity_summary_panel`, `interaction_effect_summary_panel`, `generalizability_subgroup_composite_panel` | forest/dot/interval 图在 R 中更容易做期刊化 theme、CI 标注和分组 facet。 |
| Model complexity / coefficient path | `coefficient_path_panel`, `model_complexity_audit_panel` | ggplot2 对 path / regularization / model diagnostics 的表达更自然。 |
| Omics volcano / enrichment / matrix | `omics_volcano_panel`, `pathway_enrichment_dotplot_panel`, `celltype_marker_dotplot_panel`, `cnv_recurrence_summary_panel`, `genomic_program_governance_summary_panel` | EnhancedVolcano、enrichplot、ComplexHeatmap、ggplot2 dotplot 生态成熟。 |
| Oncoplot / genomic alteration | `oncoplot_mutation_landscape_panel`, `genomic_alteration_landscape_panel`, `genomic_alteration_consequence_panel`, `genomic_alteration_multiomic_consequence_panel`, `genomic_alteration_pathway_integrated_composite_panel` | maftools / ComplexHeatmap 在癌症基因组图中更接近社区惯例。 |
| SHAP standard plots | `shap_summary_beeswarm`, `shap_bar_importance`, `shap_dependence_panel`, `shap_waterfall_local_explanation_panel`, `shap_force_like_summary_panel`, `shap_multicohort_importance_panel` | `shapviz` 已覆盖常见 SHAP 图，适合作为 R 版本候选。 |

### P2：保留 Python 或做双栈的模板

这些模板不是不能用 R，而是当前 Python 实现更像 custom layout engine、multi-panel storyboard 或 MAS-specific support-domain artifact。强行迁 R 会增加风险。

| 图类 | 模板 | 建议 |
| --- | --- | --- |
| Atlas / spatial / trajectory storyboard | `atlas_spatial_bridge_panel`, `single_cell_atlas_overview_panel`, `spatial_niche_map_panel`, `trajectory_progression_panel`, `atlas_spatial_trajectory_storyboard_panel`, `atlas_spatial_trajectory_density_coverage_panel`, `atlas_spatial_trajectory_context_support_panel`, `atlas_spatial_trajectory_multimanifold_context_support_panel` | 先保留 Python；等 reference bundle 和真实 paper demand 明确后再决定是否用 ggplot2 / Seurat / ComplexHeatmap 重做。 |
| SHAP support-domain composites | `feature_response_support_domain_panel`, `shap_grouped_local_support_domain_panel`, `shap_multigroup_decision_path_support_domain_panel`, `shap_signed_importance_local_support_domain_panel` | 这是 MAS-specific composite，不先迁；可抽出局部 ggplot2 panel。 |
| DPCC / descriptive paper-specific figures | `phenotype_gap_structure_figure`, `site_held_out_stability_figure`, `treatment_gap_alignment_figure`, `treatment_shift_alignment_figure`, `practical_factor_dot_figure`, `preferred_class_sensitivity_figure` | 先按真实 paper artifact 和 visual audit 决定，不因 renderer policy 迁移。 |
| Custom explanation panels | `partial_dependence_ice_panel`, `partial_dependence_interaction_contour_panel`, `partial_dependence_interaction_slice_panel`, `partial_dependence_subgroup_comparison_panel`, `accumulated_local_effects_panel`, `shap_grouped_decision_path_panel`, `shap_multigroup_decision_path_panel`, `shap_grouped_local_explanation_panel`, `shap_signed_importance_panel` | 可做 R candidate，但不进入第一批；先看是否已有 stable input schema 和 golden demand。 |

## 实施顺序

1. **结构护栏**：生成 renderer inventory，并把 `r_ggplot2 + python_plugin` 标成 `legacy_bridge`，避免继续误写成已完成 subprocess migration。
2. **P0 迁移**：22 个现有 R/ggplot2 模板迁到 `execution_mode = "subprocess"`，每个模板有 local `render.R`，共享 helper 下沉到 R helper library。
3. **P0 验证**：每个图类至少一个 focused E2E fixture，覆盖 request JSON、PNG/PDF/layout sidecar、QC、stdout/stderr refs 和 display lock。
4. **P1 候选双栈**：为 time-to-event composite、forest/effect、omics/SHAP 标准图先落 R candidate，不直接删除 Python。
5. **Visual audit 决策**：同输入生成 Python/R 两版，用 visual-audit receipt 和 golden diff 决定 promotion。
6. **退役桥接**：当 P0/P1 稳定后，删除 `r_renderer.py` 的内嵌 R source 桥接；Python plugin 只服务真实 Python templates。

## 验收口径

不能再用“R/ggplot2-first subprocess renderer landed”表示 core pack 已迁移。准确口径是：

- runtime 协议：`landed`；
- core pack 现有 R templates：`legacy_bridge_to_be_migrated`；
- core pack subprocess R templates：当前 `0`，P0 目标 `22`；
- Python-to-R 候选迁移：按 P1/P2 分层推进；
- publication readiness：仍必须走 deterministic render、QC、visual audit、owner receipt / publication gate。

