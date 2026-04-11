# Medical Display Anchor Paper Audit

## Purpose

这个文档记录 `medical-display-anchor-paper-closure` 的当前真相：

1. 两篇锚点论文当前的 manuscript-facing authority surface 是什么。
2. 哪些 display contract 已经在真实论文 source surface 落地。
3. 还有哪些问题仍属于 display 线本身，哪些已经转为下游 submission-surface 管理问题。

## Visual QA Boundary

- `paper/` root is the authority surface for both `001` and `003`.
- `paper/figures/generated/` is the authority image surface for fresh visual QA.
- `paper/figures/*.shell.json` and `paper/tables/*.shell.json` stay as study-owned contracts; they are not the retrieval target for the latest rendered deliverable.
- `paper/submission_minimal/` is the fixed submission-package lookup path that should stay continuously refreshed for handoff and retrieval.
- `manuscript/` is the only human-facing final-delivery mirror.
- `artifacts/` is reserved for machine-generated auxiliary/finalization evidence and should not duplicate figure/table retrieval.
- obsolete top-level rendered residues (for example `paper/figures/Figure*.png|pdf` or `paper/tables/Table*.md|csv` once the catalogs already point at `generated/`) should be cleaned instead of remaining as ambiguous pseudo-authority surfaces.
- 审计原则保持两层：
  1. 正式 renderer / schema / QC contract 负责视觉下限；
  2. fresh generated images + AI-first visual review 负责把论文呈现质量继续拉到 manuscript-facing 上限。
- 因此，manifest / gate clear 只能说明 contract surface clear；真实 final figure quality 仍必须回到 fresh images 复核。

## Current Closure Summary

| Study | Authoritative source surface | Current audited coverage | Fresh verification status |
| --- | --- | --- | --- |
| `001-dm-cvd-mortality-risk` | study-owned `paper/` root | `GA1`, `F1-F5`, `T1-T3` 已进入 audited contract | `materialize` clear；`export-submission-minimal` clear；catalog/submission 对账 clear；runtime `medical-reporting-audit` / `publication-gate` clear |
| `003-endocrine-burden-followup` | study-owned `paper/` root | `F1-F4`, `T1-T3` 已进入 audited contract | `materialize` clear；`export-submission-minimal` clear；catalog/submission 对账 clear；runtime `medical-reporting-audit` / `medical-publication-surface` / `publication-gate` clear |

## Fresh Conclusions

1. `001` 已不再缺失 study-owned `paper/` root。
   - 当前长期 authority surface 是：
     - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/paper`
   - `manuscript` 现在是唯一人用 final delivery mirror；`artifacts/` 仅保留辅助 evidence，不再充当图表 mirror。
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
5. `003` 当前不再存在 active submission-surface blocker。
   - runtime quest 中 legacy `paper/submission_pituitary` 已通过正式 `archived_reference_only` contract 收口为 historical reference surface；
   - archived contract 已收紧为：只能指向同一 `paper_root` 内、且属于 formal managed submission surface roots 的 `submission_manifest.json`；
   - active managed submission surface 仍是 audited `paper/submission_minimal`。

## Study 001

### Authority Surface

- Study root:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk`
- Authoritative paper root:
  - `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/001-dm-cvd-mortality-risk/paper`
- Delivery mirrors:
  - `manuscript/submission_manifest.json`
  - `manuscript/delivery_manifest.json`
  - `artifacts/`（仅在 finalize/runtime 需要 auxiliary evidence 时使用）
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
  - `manuscript/submission_manifest.json`
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
  - `medical-publication-surface`: `clear`
  - `publication-gate`: `clear`
    - legacy `paper/submission_pituitary` 现已是 archived reference-only surface，不再作为 unmanaged blocker。
    - archived contract 不接受 paper 外部或非 managed root 的伪目标 manifest。

## Cross-Paper Regression Evidence

- repo targeted regression:
  - `uv run pytest tests/test_runtime_protocol_paper_artifacts.py tests/test_figure_renderer_contract.py tests/test_time_to_event_direct_migration.py tests/test_display_layout_qc.py tests/test_display_surface_materialization.py tests/test_medical_publication_surface.py tests/test_display_schema_contract.py tests/test_medical_reporting_contract.py tests/test_medical_reporting_audit.py tests/test_medical_startup_contract_support.py tests/test_quest_hydration.py tests/test_startup_hydration_validation.py tests/test_submission_minimal_display_surface.py tests/test_publication_gate.py -q`
  - result: `171 passed`
- cross-paper paper-root verification:
  - `001 paper root` fresh `materialize-display-surface` clear
  - `003 paper root` fresh `materialize-display-surface` clear
  - `001 paper root` fresh `export-submission-minimal` clear
  - `003 paper root` fresh `export-submission-minimal` clear
  - `001 runtime quest` fresh `medical-reporting-audit / medical-publication-surface / publication-gate` clear
  - `003 runtime quest` fresh `medical-reporting-audit / medical-publication-surface / publication-gate` clear

## Decision Boundary After Closure Audit

- 不要再把 `001/003` 作为“继续补 display template gap”的依据。
- `medical-display-anchor-paper-closure` 当前已完成：
  - anchor-paper truth reset
  - authority closure
  - paper-owned backfill
  - final-figure quality recovery
  - `003` legacy submission surface normalization
  - cross-paper regenerate / submission verification
- 只有在新的 authority / truth conflict、figure-level QA reopen、或新增 anchor-paper scope 出现时才需要重新打开。
