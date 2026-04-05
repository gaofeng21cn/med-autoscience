# Medical Display Anchor Paper Audit

## Purpose

这个文档记录 `medical-display-anchor-paper-closure` 的当前真相：

1. 两篇锚点论文当前的 manuscript-facing authority surface 是什么。
2. 哪些 display contract 已经在真实论文 source surface 落地。
3. 还有哪些问题仍属于 display 线本身，哪些已经转为下游 submission-surface 管理问题。

## Current Closure Summary

| Study | Authoritative source surface | Current audited coverage | Fresh verification status |
| --- | --- | --- | --- |
| `001-dm-cvd-mortality-risk` | study-owned `paper/` root | `GA1`, `F1-F5`, `T1-T3` 已进入 audited contract | `materialize` clear；`export-submission-minimal` clear；catalog/submission 对账 clear；runtime `medical-reporting-audit` / `publication-gate` clear |
| `003-endocrine-burden-followup` | study-owned `paper/` root | `F1-F4`, `T1-T3` 已进入 audited contract | `materialize` clear；`export-submission-minimal` clear；catalog/submission 对账 clear；runtime `medical-reporting-audit` clear；`publication-gate` 仅剩 legacy `paper/submission_pituitary` blocker |

## Fresh Conclusions

1. `001` 已不再缺失 study-owned `paper/` root。
   - 当前长期 authority surface 是：
     - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/paper`
   - `manuscript/final` 与 `artifacts/final` 现在应视为 delivery mirror，而不是唯一 authority。
2. `003` 已不再存在“F2/F3/F4 与 T2/T3 仍是模板 gap”的旧判断。
   - audited 主线现在正式包含：
     - `risk_layering_monotonic_bars`
     - `binary_calibration_decision_curve_panel`
     - `model_complexity_audit_panel`
     - `performance_summary_table_generic`
     - `grouped_risk_event_summary_table`
3. `003` 的 study-owned `paper/figures/figure_catalog.json`、`paper/tables/table_catalog.json`、input JSON 与 manifest 面已经回填到 audited truth。
4. Figure 1 当前不再是模板缺口判断源。
   - `001` 与 `003` 的 `F1 cohort_flow_figure` 都已在真实 submission 面稳定存在。
   - `001` 旧 audited sidecar role `full_right` 已由正式 materializer alias 收口到 `wide_top`，不是 paper-local patch。
5. 当前剩余问题不再是 display template vocabulary，而是 `003` runtime quest 里 legacy `paper/submission_pituitary` 仍被 `publication-gate` 视为 unmanaged submission surface。

## Study 001

### Authority Surface

- Study root:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk`
- Authoritative paper root:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/paper`
- Delivery mirrors:
  - `manuscript/final/submission_manifest.json`
  - `manuscript/final/delivery_manifest.json`
  - `artifacts/final/`
- Runtime audited quest root:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/med-deepscientist/runtime/quests/001-dm-cvd-mortality-risk-reentry-20260331`

### Fresh Verification

- `paper/` root 已具备 audited paper bundle inputs、catalog、generated assets、`paper_bundle_manifest.json`、`build/compile_report.json`。
- fresh `materialize-display-surface` 结果：
  - figures: `F1-F5`
  - tables: `T1-T2`
  - `T3` 继续作为现存 audited markdown asset 被 submission/export 消费。
- fresh `export-submission-minimal` clear。
- fresh 对账结果：
  - `paper/figures/figure_catalog.json` 与 final `submission_manifest.json` contract fields 一致。
  - `paper/tables/table_catalog.json` 与 final `submission_manifest.json` contract fields 一致。
  - `paper/submission_minimal/submission_manifest.json` 与 final `submission_manifest.json` figure/table ids、template/table shell ids、`input_schema_id`、`qc_profile`、`qc_result.status` 一致。
- runtime verification：
  - `medical-reporting-audit`: `clear`
  - `publication-gate`: `clear`

## Study 003

### Authority Surface

- Study root:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup`
- Authoritative paper root:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/paper`
- Delivery mirror:
  - `manuscript/final/submission_manifest.json`
- Runtime audited quest root:
  - `/Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/003-endocrine-burden-followup-managed-20260402`

### Fresh Verification

- `paper/` root 已具备 audited catalogs、input JSON、generated assets、`paper_bundle_manifest.json`、`build/compile_report.json`。
- fresh `materialize-display-surface` 结果：
  - figures: `F1-F4`
  - tables: `T1-T3`
- fresh `export-submission-minimal` clear。
  - 正式补齐了 `submission_minimal` 对 manuscript-shaped `draft.md`（H1 title + H2 sections，无 front matter）的支持。
  - `submission_minimal/manuscript_submission.md` 现在正确写出：
    - 真标题
    - `bibliography: ../references.bib`
    - 正文 `Materials and Methods` 内容，而不是误抓 abstract subsection。
- fresh 对账结果：
  - `paper/figures/figure_catalog.json` 与 final `submission_manifest.json` contract fields 一致。
  - `paper/tables/table_catalog.json` 与 final `submission_manifest.json` contract fields 一致。
  - `paper/submission_minimal/submission_manifest.json` 与 final `submission_manifest.json` figure/table ids、template/table shell ids、`input_schema_id`、`qc_profile`、`qc_result.status` 一致。
- runtime verification：
  - `medical-reporting-audit`: `clear`
  - `publication-gate`: `blocked`
    - blocker: `unmanaged_submission_surface_present`
    - cause: legacy `paper/submission_pituitary` journal package 仍位于 unmanaged root；这已经不是 display template gap，而是 submission-surface normalization 问题。

## Cross-Paper Regression Evidence

- repo targeted regression:
  - `uv run pytest tests/test_display_surface_materialization.py tests/test_display_registry.py tests/test_display_schema_contract.py tests/test_medical_publication_surface.py tests/test_submission_minimal.py tests/test_submission_minimal_display_surface.py -q`
  - result: `94 passed`
- cross-paper paper-root verification:
  - `001 paper root` fresh `materialize-display-surface` clear
  - `003 paper root` fresh `materialize-display-surface` clear
  - `001 paper root` fresh `export-submission-minimal` clear
  - `003 paper root` fresh `export-submission-minimal` clear

## Decision Boundary After Closure Audit

- 不要再把 `001/003` 作为“继续补 display template gap”的依据。
- 如果下一步继续推进，这条线真正剩下的是：
  - 是否要把 `003` runtime quest 的 legacy `submission_pituitary` 归档/迁移到 managed submission surface。
- 在这一步之前，display 主线本身已经完成 anchor-paper truth reset、authority closure、paper-owned backfill，以及 cross-paper regenerate / submission verification。
