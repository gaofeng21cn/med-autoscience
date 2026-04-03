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
- `003` 最适合作为下一批缺失模板的需求真相源。

## Cross-Paper Priority Reset

### Phase A: First Migration Pack From Existing Audited Surface

优先从 `001` 开始，把以下资产接入 audited display surface：

1. `Table 1` -> `table1_baseline_characteristics`
2. `Table 2` -> `table2_time_to_event_performance_summary`
3. `Figure 2` -> `time_to_event_discrimination_calibration_panel`
4. `Figure 3` -> `kaplan_meier_grouped`
5. `Figure 4` -> `time_to_event_decision_curve`
6. `Figure 5` -> `multicenter_generalizability_overview`

理由：

- 这些都是 `direct` 映射。
- 它们能最快把现有 audited catalog 从“模板存在”推进到“真实论文已复用”。
- 完成后可以立刻验证 catalog、materialization、QC、publication surface 是否真能承接真实论文主文。
- `Table 3` 作为后续增强项保留，不纳入这一轮首批迁移完成判据。

### Phase B: Unified Figure 1 Shell Upgrade

`001 Figure 1` 与 `003 Figure 1` 应共用一条 Figure 1 shell 升级线：

- 保留 cohort flow 的严格数字约束。
- 正式纳入 endpoint inventory。
- 正式纳入 split schema 或 score-construction sidecar。
- 不允许依赖 renderer 临时避让或排版后修补。

### Phase C: Template Additions Driven By Study 003

`003` 应优先驱动下面 5 类新增模板：

1. `risk_layering_monotonic_bars`
2. `binary_calibration_decision_curve_panel`
3. `model_complexity_audit_panel`
4. `performance_summary_table_generic`
5. `grouped_risk_event_summary_table`

前 3 项直接决定 `003` 当前主文能否稳定迁移；后 2 项主要服务当前 supplementary table 与 study-owned transport package。

## Immediate Recommendation

下一轮实现顺序建议固定为：

1. 完成 `001` 的 direct migration pack。
2. 升级统一 Figure 1 shell，使其同时服务 `001` 与 `003`。
3. 以 `003` 为锚点补齐 risk layering、composite curve panel、complexity audit、generic performance table、risk event table。

只有在这三步完成之后，“40 个模板”的扩展数字才真正开始对应到真实论文交付，而不是 catalog 层的名义扩容。
