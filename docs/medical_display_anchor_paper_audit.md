# Medical Display Anchor Paper Audit

## Purpose

这个文档把当前两篇锚点论文的主文 Figure / Table 资产映射到 `med-autoscience` 已有 audited display surface，用来回答三个问题：

1. 哪些论文资产已经可以直接迁移到正式模板面。
2. 哪些资产只差统一 layout / shell / composite panel 执行层。
3. 哪些资产会反向驱动下一批新增模板。

这里的“有效主文资产”以各 study 的 `manuscript/final/`、`artifacts/final/`、`submission_package/`，以及当前 active quest 的 journal-facing paper package 为准，而不是早期分析草稿或单次运行时中间文件。

## Coverage Labels

- `direct`
  - 当前 audited template / shell 已能承载同一类论文语义，下一步主要是把现有论文资产迁移到正式 schema + materialization + QC + catalog。
- `partial`
  - 现有 audited surface 已覆盖核心语义，但还缺 paper-level composite panel、Figure 1 shell 扩展，或统一 layout 执行层。
- `gap`
  - 当前 audited surface 没有对应模板，必须新增 template / shell 才能稳定接住。

## Portfolio Summary

| Study | Effective Main Package | Direct | Partial | Gap | Recommended Role |
| --- | ---: | ---: | ---: | ---: | --- |
| `001-dm-cvd-mortality-risk` | `7` packaged (`Figure 1-5`, `Table 1-2`) | `6` | `1` | `0` | 第一批迁移验收稿 |
| `003-endocrine-burden-followup` | `5` current-main (`Figure 1-4`, `Table 1`) + `2` current-supplementary (`S1-S2`) | `1` | `2` | `2` current-main | 第一批缺失模板驱动稿 |

结论：

- `001` 应优先作为 audited display surface 的第一批迁移验收稿。
- `003` 应优先作为下一批新增模板和 composite layout 执行层的驱动稿。

## Study 001 Audit

### Trusted Roots

- Workspace root:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk`
- Study root:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk`
- Final submission manifest:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/manuscript/final/submission_manifest.json`
- Final paper bundle manifest:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/artifacts/final/paper_bundle_manifest.json`
- Final delivery manifest:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/manuscript/final/delivery_manifest.json`
- Assembly inventory:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/analysis/clean_room_execution/60_manuscript_assembly/figure_table_manifest.md`

### Current Main-Text Assets

| Asset | Current Theme | Trusted Surface | Audit Mapping | Next Action |
| --- | --- | --- | --- | --- |
| `Table 1` | Baseline characteristics of the formal modeling cohort | `artifacts/final/tables/table1.md` | `direct` -> `table1_baseline_characteristics` | 迁移到正式 table shell，并把当前 paper-facing labels 收紧到 schema contract |
| `Table 2` | Fixed-horizon performance summary of the primary and supportive endpoints | `artifacts/final/tables/table2.md` | `direct` -> `table2_time_to_event_performance_summary` | 迁移到正式 table shell，并把 primary/supportive block 显式化 |
| `Table 3` | Clinical interpretation summary | 仅在 outline / 早期 contract 叙事面出现，未进入 final submission package | `direct` -> `table3_clinical_interpretation_summary` | 不作为当前 submission 阻塞项；待下一轮论文重构时决定是否恢复 |
| `Figure 1` | Cohort flow + endpoint inventory + non-overlapping center split schema | `analysis/.../figure1/figure1_cohort_endpoint_split.{svg,pdf,png}` | `partial` -> `cohort_flow_figure` 核心语义已覆盖，但现有 shell 不足以表达 endpoint inventory + split schema | 扩展 Figure 1 shell，使其能稳定承载 cohort flow、endpoint inventory、split schema 三段式结构 |
| `Figure 2` | Primary endpoint discrimination + grouped 5-year calibration | `manuscript/final/submission_package/figures/figure2.{svg,pdf,png}` | `direct` -> `time_to_event_discrimination_calibration_panel` | 迁移到 audited template，并补 catalog / QC metadata |
| `Figure 3` | 5-year KM risk stratification | `manuscript/final/submission_package/figures/figure3.{svg,pdf,png}` | `direct` -> `kaplan_meier_grouped` | 迁移到 audited template，并固定 risk-group label contract |
| `Figure 4` | 5-year decision curve | `manuscript/final/submission_package/figures/figure4.{svg,pdf,png}` | `direct` -> `time_to_event_decision_curve` | 迁移到 audited template，并固定 horizon-aware label contract |
| `Figure 5` | Internal multicenter generalizability summary | `manuscript/final/submission_package/figures/figure5.{svg,pdf,png}` | `direct` -> `multicenter_generalizability_overview` | 迁移到 audited template，并把 limitation-aware center support 保持在 schema 内 |

### Study 001 Migration Judgment

- `001` 的主文面已经高度接近当前 audited catalog。
- 当前 final submission manifest 里，`Figure 1-5` 与 `Table 1-2` 都还没有挂上 `template_id`、`input_schema_id`、`qc_profile`，说明它们仍是“已物化但未接入 audited display surface”的历史资产。
- `001` 的第一轮迁移重点不是发明新模板，而是把已有主文资产系统性接入现有模板面。
- `Table 3` 在当前 final submission 里并不是有效资产，应视为后续增强项，而不是当前迁移阻塞项。
- `001` 的 `delivery_manifest.json` 仍保留旧 `quest_id`，但 source paths 实际已经指向 reentry quest；后续做 migration provenance 时应以 source paths 和 `runtime_binding.yaml` 为准。

## Study 003 Audit

### Trusted Roots

- Workspace root:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET`
- Study root:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup`
- Study-owned paper figure catalog:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/paper/figures/figure_catalog.json`
- Study-owned paper table catalog:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/paper/tables/table_catalog.json`
- Figure storyboard:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/paper/figure_storyboard.md`
- Final submission manifest:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/manuscript/final/submission_manifest.json`
- Current journal-facing Pituitary package:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/003-endocrine-burden-followup-managed-20260402/paper/submission_pituitary/submission_manifest.json`
- Current supplementary tables:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/003-endocrine-burden-followup-managed-20260402/paper/supplementary_tables.md`

### Current Main-Text Assets

| Asset | Current Theme | Trusted Surface | Audit Mapping | Next Action |
| --- | --- | --- | --- | --- |
| `Table 1` | Cohort characteristics at the 3-month postoperative landmark | `paper/tables/Table1.{csv,md}` and `artifacts/final/tables/Table1.{csv,md}` | `direct` -> `table1_baseline_characteristics` | 迁移到正式 table shell |
| `Supplementary Table S1` | Unified repeated nested validation results across candidate models | `paper/supplementary_tables.md` 与 `paper/tables/Table2.{csv,md}` | `gap` | 新增通用 performance summary table shell；当前 journal-facing 角色是补充表，不是主文表 |
| `Supplementary Table S2` | Event rates across the simple-score and grouped-risk surfaces | `paper/supplementary_tables.md` 与 `paper/tables/Table3.{csv,md}` | `gap` | 新增 grouped risk event summary table shell；当前 journal-facing 角色是补充表，不是主文表 |
| `Figure 1` | Study schema and simple score construction | `paper/figures/Figure1_study_schema_and_score_construction.{pdf,png}` | `partial` -> `cohort_flow_figure` 只覆盖 cohort restriction，尚不覆盖 score formula + grouped rule | 扩展 Figure 1 shell，使其能承载 study schema 与 scoring rule |
| `Figure 2` | Monotonic risk layering of the 3-month endocrine burden score | `paper/figures/Figure2_monotonic_risk_layering.{pdf,png}` | `gap` | 新增 monotonic risk layering figure template |
| `Figure 3` | Calibration and decision-curve comparison of the candidate packages | `paper/figures/Figure3_calibration_and_decision_curve.{pdf,png}` | `partial` -> 已有 `calibration_curve_binary` + `decision_curve_binary`，但缺统一双 panel audited template | 新增 composite panel 执行层或正式组合模板 |
| `Figure 4` | Unified model comparison and added-value assessment of model complexity | `paper/figures/Figure4_unified_validation_and_complexity_audit.{pdf,png}` | `gap` | 新增 model comparison + complexity audit composite template |

### Study 003 Migration Judgment

- `003` 当前真正的期刊主文面是 `Figure 1-4 + Table 1`，而不是 study-owned transport package 里的 `Table 1-3`。
- `Table 2` / `Table 3` 仍是真实有效资产，但当前 journal-facing 角色已经下沉为 `Supplementary Table S1` / `Supplementary Table S2`。
- `003` 的主文面并不是“渲染质量差”，而是大部分资产本身就还没有进入当前 audited template vocabulary。
- `003` 的价值在于把临床医学论文里一批真实高频、但目前 catalog 缺失的图表类型具体化，而不是强行把现有模板套上去。
- `003` 驱动的 `Phase C / Phase D` 缺口现已进入正式主线；当前 blocker 已从模板缺口转移到 reporting / publication 合同面。
- `003` 现阶段最重要的价值不再是继续催生新模板，而是验证正式 gate 能否清掉真实 paper root 的 reporting / manuscript blocker。

## Cross-Paper Priority Reset

### Completed Mainline Intake

以下工作已不再是“下一轮提案”，而是当前主线已完成的前置事实：

- `003` 驱动的 3 个 evidence figure template 已进入正式主线：
  - `risk_layering_monotonic_bars`
  - `binary_calibration_decision_curve_panel`
  - `model_complexity_audit_panel`
- `003` 驱动的 2 个 table shell 已进入正式主线：
  - `performance_summary_table_generic`
  - `grouped_risk_event_summary_table`
- `001` / `002` / `003` 的当前 live paper root 已完成相应 display surface 重物化与 QC 复核。

### Current Priority A: `003` Reporting / Publication Gate Tighten

`003` 当前优先清关项应切换为：

- reporting audit：
  - `reporting_guideline_checklist.json`
- publication surface：
  - `methods_implementation_manifest.json`
  - `results_narrative_map.json`
  - `figure_semantics_manifest.json`
  - `derived_analysis_manifest.json`
  - `manuscript_safe_reproducibility_supplement.json`
  - `endpoint_provenance_note.md`
  - forbidden manuscript terms

这一阶段的判断标准不再是“模板有没有”，而是“正式 contract / controller / manuscript-facing truth 是否闭合”。

### Current Priority B: `001` Submission Companion Contract Tighten

`001` 当前 publication surface 仍被两类 contract 缺口阻塞：

- `submission_graphical_abstract` 尚未正式注册
- `figure_semantics_manifest.json` 中 `GA1` 使用 `submission_companion` renderer semantics，但正式 validator 仍只接受当前主线 renderer family

这说明 `001` 的下一步重点不是 display template 扩容，而是 submission companion / graphical abstract 正式合同化。

### Current Priority C: `002` Real-Study `Phase C / Phase D` Promotion

`002` 当前仍只有 Figure 1 主线化。要把 `Phase C / Phase D` 真正推进到真实课题，需要补齐：

- `medical_analysis_contract.json`
- `medical_reporting_contract.json`
- `publication_style_profile.json`
- `display_overrides.json`
- 真实 `study_design_cohort_flow.json` / `notes/clinical_metadata_packet.md` 的 controller consumer 路径

## Immediate Recommendation

当前建议固定顺序为：

1. 先把 `003` 的 reporting / publication gate blocker 分成“可正式自动化吸收”与“必须依赖真实 paper truth”两类，并优先收紧正式 controller 能直接承接的部分。
2. 再把 `001` 的 `submission_graphical_abstract` / `submission_companion` 缺口定义为下一条 publication-facing contract tighten。
3. 最后回到 `002`，把 `Phase C / Phase D` 升级进真实课题 controller 主线。

只有在这三步完成之后，继续扩模板才真正对应真实论文交付，而不是 catalog 层的名义扩容。
