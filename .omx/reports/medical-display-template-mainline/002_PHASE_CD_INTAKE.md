# 002 Phase C/D promotion intake

## Scope

This note captures the exact blockers and formal promotion path for study `002-early-residual-risk` from the current partially managed state into the mainline reporting/publication surface. Scope is limited to the managed quest bound by `studies/002-early-residual-risk/runtime_binding.yaml` (`quest_id: 002-early-residual-risk-managed-20260402`) plus the legacy paper bundle currently holding the only concrete Phase C/D assets.

## Verified current state

### Study truth anchors

- `studies/002-early-residual-risk/protocol.md` keeps the study on the binary `removal_rate` endpoint, with working semantics `1 = GTR`, `0 = non-GTR`, and paper-facing phrasing `early residual / non-GTR risk`.
- `studies/002-early-residual-risk/protocol.md` and `studies/002-early-residual-risk/notes/clinical_metadata_packet.md` both say the `v2026-03-31` authoritative freeze requires rerunning the paper-facing path from the updated `357` first-surgery cohort, not the earlier `354` accepted-manuscript slice.
- `studies/002-early-residual-risk/runtime_binding.yaml` binds the study to the managed quest root `/Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk-managed-20260402`.

### Managed quest audit state

Command used:

```bash
uv run python -m med_autoscience.cli medical-reporting-audit \
  --quest-root /Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk-managed-20260402
```

Observed report:

- report: `/Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk-managed-20260402/artifacts/reports/medical_reporting_audit/2026-04-05T034413Z.json`
- status: `blocked`
- blockers:
  - `missing_display_registry`
  - `missing_figure1_shell`
  - `missing_cohort_flow`
  - `missing_table1_shell`
  - `missing_baseline_characteristics_schema`
  - `missing_reporting_guideline_checklist`

The managed paper root currently contains only:

- `paper/medical_analysis_contract.json`
- `paper/medical_reporting_contract.json`
- `paper/reference_coverage_report.json`
- `paper/references.bib`

It does **not** yet contain `publication_style_profile.json`, `display_overrides.json`, `display_registry.json`, shell JSONs, stub inputs, figure/table catalogs, or `paper_bundle_manifest.json`.

### Legacy publication-surface state

The managed quest cannot currently drive `medical-publication-surface` because `paper_bundle_manifest.json` is missing, so the usable evidence comes from the legacy paper bundle under:

- `/Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk/.ds/worktrees/paper-run-1cbaa7ed/paper`

Command used:

```bash
uv run python -m med_autoscience.cli medical-publication-surface \
  --quest-root /Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk \
  --daemon-url ''
```

Observed report:

- report: `/Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk/artifacts/reports/medical_publication_surface/2026-04-05T034602Z.json`
- status: `blocked`
- blockers:
  - `forbidden_manuscript_terms_present`
  - `figure_catalog_missing_or_incomplete`
  - `table_catalog_missing_or_incomplete`
  - `methods_implementation_manifest_missing_or_incomplete`
  - `results_narrative_map_missing_or_incomplete`
  - `figure_semantics_manifest_missing_or_incomplete`
  - `derived_analysis_manifest_missing_or_incomplete`
  - `manuscript_safe_reproducibility_supplement_missing_or_incomplete`
  - `endpoint_provenance_note_missing_or_unapplied`
  - `undefined_methodology_labels_present`

The legacy bundle already carries publication-facing assets that the managed quest lacks:

- `paper_bundle_manifest.json`
- `publication_style_profile.json`
- `display_overrides.json`
- `display_registry.json`
- `cohort_flow.json`
- `figures/figure_catalog.json`
- `tables/table_catalog.json`
- `derived/study_design_cohort_flow.json`

But the legacy `figure_catalog.json` and `table_catalog.json` are still pre-mainline: `F2/F3/F4/T2/T3` all have `template_id`, `renderer_family`, `input_schema_id`, `qc_profile`, and `qc_result` unset, so they cannot satisfy `medical_publication_surface`.

## The main mismatch to resolve

`002` is blocked not because the study truth is wrong, but because the managed path currently resolves only the minimal binary reporting surface:

- `paper/medical_reporting_contract.json` currently requires only `cohort_flow_figure` and `table1_baseline_characteristics`.
- `src/med_autoscience/policies/medical_reporting_contract.py` only auto-expands to the richer `F2/F3/F4/T2` display plan for the **time-to-event** branch, not for the binary early-residual branch.
- `paper/medical_analysis_contract.json` is still generic for binary prediction work and does not itself project the Phase C/D publication bundle.

Important correction: **do not flip `002` to `endpoint_type = time_to_event` just to unlock richer displays.** The study truth in `protocol.md` and `clinical_metadata_packet.md` is still the binary early residual / non-GTR endpoint. The correct move is to promote the already-registered binary Phase C/D surfaces that exist in:

- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/controllers/_medical_display_surface_support.py`
- `src/med_autoscience/controllers/publication_shell_sync.py`
- `tests/test_quest_hydration.py`
- `tests/test_publication_shell_sync.py`
- `tests/test_display_surface_materialization.py`

## Exact contract files to add or tighten

### Managed quest paper root: add immediately

At `/Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk-managed-20260402/paper` add:

1. `publication_style_profile.json`
2. `display_overrides.json`
3. `display_registry.json`
4. `reporting_guideline_checklist.json`
5. `paper_bundle_manifest.json`
6. `cohort_flow.json`
7. `baseline_characteristics_schema.json`
8. `risk_layering_monotonic_inputs.json`
9. `binary_calibration_decision_curve_panel_inputs.json`
10. `model_complexity_audit_panel_inputs.json`
11. `performance_summary_table_generic.json`
12. `grouped_risk_event_summary_table.json`
13. `figures/figure_catalog.json`
14. `tables/table_catalog.json`
15. `figures/<display_id>.shell.json` for each bound figure
16. `tables/<display_id>.shell.json` for each bound table
17. `methods_implementation_manifest.json`
18. `results_narrative_map.json`
19. `figure_semantics_manifest.json`
20. `derived_analysis_manifest.json`
21. `manuscript_safe_reproducibility_supplement.json`
22. `endpoint_provenance_note.md`

### Managed quest paper root: tighten immediately

1. `medical_reporting_contract.json`
   - keep `endpoint_type: "binary"`
   - keep `reporting_guideline_family: "TRIPOD"`
   - expand `display_registry_required`, `required_table_shells`, `required_evidence_templates`, and especially `display_shell_plan`
   - formalize the binary Phase C/D bindings listed below
2. `medical_analysis_contract.json`
   - keep `endpoint_type: "binary"`
   - ensure the reporting items used by publication gating are actually projected into the managed paper root, especially `derived_analysis_manifest.json`

### Repo-level contract/policy files to tighten if the goal is automatic regeneration instead of one-off paper edits

1. `src/med_autoscience/policies/medical_reporting_contract.py`
   - add a binary early-residual Phase C/D branch so `resolve_medical_reporting_contract()` emits the richer display plan directly for `002`
2. `src/med_autoscience/controllers/medical_reporting_contract.py`
   - surface the richer binary plan in resolved contract summaries once policy supports it
3. `src/med_autoscience/controllers/medical_analysis_contract.py`
   - only if we want the binary branch to project stronger publication-facing reporting items automatically

Without those repo-level changes, `002` can still be promoted by tightening the managed `paper/medical_reporting_contract.json` directly and then re-running hydration/sync/materialization.

## Exact formal F2/F3/F4/T2/T3 requirements

### Supported mainline mapping (already covered by hydration/sync/materialization tests)

The existing mainline binary Phase C/D path is exercised by:

- `tests/test_quest_hydration.py::test_run_quest_hydration_supports_phase_c_and_phase_d_display_plan`
- `tests/test_publication_shell_sync.py::test_run_publication_shell_sync_writes_phase_c_and_phase_d_inputs_when_bound`
- `tests/test_display_surface_materialization.py` binary/table materialization cases

Use the following formal mapping for `002`:

| Catalog id | requirement_key | Formal template / shell | Required input schema | Renderer / QC | Recommended role in 002 |
|---|---|---|---|---|---|
| `F2` | `risk_layering_monotonic_bars` | evidence figure `risk_layering_monotonic_bars` | `risk_layering_monotonic_inputs_v1` | `python` / `publication_risk_layering_bars` | risk stratification / monotonic layering summary |
| `F3` | `binary_calibration_decision_curve_panel` | evidence figure `binary_calibration_decision_curve_panel` | `binary_calibration_decision_curve_panel_inputs_v1` | `python` / `publication_binary_calibration_decision_curve` | calibration + decision-curve utility panel |
| `F4` | `model_complexity_audit_panel` | evidence figure `model_complexity_audit_panel` | `model_complexity_audit_panel_inputs_v1` | `python` / `publication_model_complexity_audit` | coefficient / importance / model-stability audit |
| `T2` | `performance_summary_table_generic` | table shell `performance_summary_table_generic` | `performance_summary_table_generic_v1` | `publication_table_performance` | comparative model metrics table |
| `T3` | `grouped_risk_event_summary_table` | table shell `grouped_risk_event_summary_table` | `grouped_risk_event_summary_table_v1` | `publication_table_interpretation` | bounded risk-group / event summary table |

### Exact `display_registry.json` bindings to add

A stable binary Phase C/D registry for `002` should add at least these entries (display_id strings may vary, but the requirement keys and catalog ids must stay aligned):

```json
[
  {"display_id":"cohort_flow","display_kind":"figure","requirement_key":"cohort_flow_figure","catalog_id":"F1"},
  {"display_id":"baseline_characteristics","display_kind":"table","requirement_key":"table1_baseline_characteristics","catalog_id":"T1"},
  {"display_id":"risk_layering","display_kind":"figure","requirement_key":"risk_layering_monotonic_bars","catalog_id":"F2"},
  {"display_id":"calibration_decision","display_kind":"figure","requirement_key":"binary_calibration_decision_curve_panel","catalog_id":"F3"},
  {"display_id":"model_audit","display_kind":"figure","requirement_key":"model_complexity_audit_panel","catalog_id":"F4"},
  {"display_id":"performance_summary","display_kind":"table","requirement_key":"performance_summary_table_generic","catalog_id":"T2"},
  {"display_id":"risk_event_summary","display_kind":"table","requirement_key":"grouped_risk_event_summary_table","catalog_id":"T3"}
]
```

Each entry must also carry a `shell_path`, because `quest_hydration.py` writes the registry in that form and `startup_hydration_validation.py` expects the corresponding shell JSONs to exist.

### Exact figure/table catalog expectations after materialization

`medical_publication_surface.py` and `tests/test_display_surface_materialization.py` make the catalog requirements explicit.

For `F2/F3/F4`, `figure_catalog.json` entries must end up with at least:

- `figure_id`
- `title`
- `caption`
- `paper_role`
- `template_id`
- `renderer_family`
- `input_schema_id`
- `qc_profile`
- `qc_result`
- export or asset paths that resolve under the paper root

For `T2/T3`, `table_catalog.json` entries must end up with at least:

- `table_id`
- `title`
- `caption`
- `table_shell_id`
- `input_schema_id`
- `qc_profile`
- `qc_result`
- markdown/csv asset paths under the paper root

The current legacy `F2/F3/F4/T2/T3` entries fail exactly here: they point to static manuscript assets but do not declare the registered template/shell metadata or QC results.

### How the current legacy 002 figures/tables should be interpreted

The legacy bundle is not one-to-one with the formal mainline binary surfaces:

- current legacy `F2` mixes calibration, decision-curve, and risk-tertile content in one composite figure
- current legacy `F3` is closest to the formal `model_complexity_audit_panel`
- current legacy `F4` mixes threshold examples and risk-group deployment framing that should largely be decomposed into the formal `F3` decision panel plus `T3` grouped-risk table

Therefore the safest mainline promotion is:

1. map the **legacy story** onto the **registered binary surfaces** above, not onto the old composite figure boundaries;
2. accept that the current legacy `F4` does **not** have a 1:1 registered binary figure template today;
3. only add a new binary threshold/deployment figure template if preserving the exact old `F4` layout is a hard requirement.

## Controller and hydration touchpoints

### Contract resolution / policy layer

- `src/med_autoscience/controllers/medical_reporting_contract.py`
- `src/med_autoscience/policies/medical_reporting_contract.py`
- `src/med_autoscience/controllers/medical_analysis_contract.py`
- `src/med_autoscience/policies/medical_analysis_contract.py`

These files currently explain why `002` resolves only to `F1/T1` by default: the richer automatic `display_shell_plan` exists only in the time-to-event policy branch.

### Hydration / stub seeding layer

- `src/med_autoscience/controllers/quest_hydration.py`
- `src/med_autoscience/controllers/_medical_display_surface_support.py`
- `src/med_autoscience/controllers/startup_hydration_validation.py`
- `src/med_autoscience/publication_display_contract.py`

These are the exact files that will:

1. write `medical_analysis_contract.json` and `medical_reporting_contract.json`
2. seed `display_registry.json`
3. seed the figure/table shell JSONs
4. seed `publication_style_profile.json` and `display_overrides.json`
5. seed the binary Phase C/D stub payloads once the display plan includes the required keys
6. fail startup if those files are missing or invalid

### Materialization / migration layer

- `src/med_autoscience/controllers/publication_shell_sync.py`
- `src/med_autoscience/controllers/display_surface_materialization.py`
- `src/med_autoscience/controllers/medical_reporting_audit.py`
- `src/med_autoscience/controllers/medical_publication_surface.py`
- `src/med_autoscience/runtime_protocol/paper_artifacts.py`

These are the operational gates:

1. `publication_shell_sync.py` already knows how to translate binary Phase C/D sources into:
   - `risk_layering_monotonic_inputs.json`
   - `binary_calibration_decision_curve_panel_inputs.json`
   - `model_complexity_audit_panel_inputs.json`
   - `performance_summary_table_generic.json`
   - `grouped_risk_event_summary_table.json`
2. `display_surface_materialization.py` renders those inputs and writes the registered catalog metadata/QC outputs.
3. `medical_reporting_audit.py` blocks before that surface exists.
4. `medical_publication_surface.py` blocks until the catalogs and publication manifests are complete.
5. `paper_artifacts.resolve_latest_paper_root()` requires `paper_bundle_manifest.json`, which is why the managed quest currently cannot even run the publication gate cleanly.

## How `study_design_cohort_flow.json`, `protocol.md`, and `clinical_metadata_packet.md` should feed the formal path

### 1. `derived/study_design_cohort_flow.json`

Current evidence:

- legacy `paper/derived/study_design_cohort_flow.json` already encodes the `409 -> 357 -> 357` cohort progression
- legacy `paper/cohort_flow.json` already shows how that truth becomes the formal `cohort_flow_figure` shell payload

Required mainline projection:

1. normalize `study_design_cohort_flow.json` into the managed study-facing source expected by sync/hydration (`study_root/paper/derived/cohort_flow.json`, or an equivalent adapter output)
2. derive managed `paper/cohort_flow.json` from that normalized cohort-flow truth
3. keep the `357` cohort counts synchronized with `baseline_characteristics_schema.json`, figure captions, table captions, and `derived_analysis_manifest.json`

### 2. `protocol.md`

`protocol.md` should be the authority for:

- keeping `endpoint_type = binary`
- locking the manuscript-facing endpoint wording to `early residual / non-GTR risk`
- documenting that any continued paper-facing run must start from the `357`-patient `v2026-03-31` cohort

Required mainline projection:

- its endpoint semantics should be copied into `medical_analysis_contract.json`, `medical_reporting_contract.json`, and especially `endpoint_provenance_note.md`
- any automatic contract-generation path for `002` should read protocol-derived semantics before choosing the display plan

### 3. `notes/clinical_metadata_packet.md`

`clinical_metadata_packet.md` should be the authority for:

- `357` total primary-cohort patients
- `57` non-GTR events and `300` GTR cases in the current freeze
- the statement that three `removal_rate` values were restored in the current freeze
- the 3-month MRI definition of GTR vs non-GTR

Required mainline projection:

- use it to populate the cohort-flow counts and wording
- use it to populate `endpoint_provenance_note.md`
- use it to validate every manuscript-facing count in `T1/T2/T3`, figure captions, and `results_narrative_map.json`
- use it as the durable source when regenerating `derived_analysis_manifest.json`

There is currently no evidence in the repo that these truth-anchor files are read directly by a dedicated `002` adapter, so today they must be projected through hydration payload generation and/or a small study-specific intake adapter before the formal path can consume them.

## Minimal implementation sequence

1. Keep `002` on the binary endpoint contract from `protocol.md`; do not switch it to time-to-event.
2. Tighten managed `paper/medical_reporting_contract.json` so its `display_shell_plan` binds `F1/F2/F3/F4/T1/T2/T3` using the registered binary Phase C/D requirement keys above.
3. Seed or hydrate the missing files via `quest_hydration.py` conventions:
   - `display_registry.json`
   - shell JSONs
   - stub inputs
   - `publication_style_profile.json`
   - `display_overrides.json`
4. Normalize `study_design_cohort_flow.json` plus `protocol.md` / `clinical_metadata_packet.md` into managed cohort-flow and endpoint-provenance artifacts.
5. Run `publication_shell_sync.py` on the binary Phase C/D bindings so managed `F2/F3/F4/T2/T3` input JSONs are populated from actual 002 artifacts.
6. Run `display_surface_materialization.py` so the catalogs gain `template_id`, `renderer_family`, `input_schema_id`, `qc_profile`, and `qc_result`.
7. Add the publication-gate manifests (`methods_implementation_manifest.json`, `results_narrative_map.json`, `figure_semantics_manifest.json`, `derived_analysis_manifest.json`, `manuscript_safe_reproducibility_supplement.json`, `endpoint_provenance_note.md`) and `paper_bundle_manifest.json`.
8. Re-run:

```bash
uv run python -m med_autoscience.cli medical-reporting-audit \
  --quest-root /Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk-managed-20260402

uv run python -m med_autoscience.cli medical-publication-surface \
  --quest-root /Users/gaofeng/workspace/Yang/NF-PitNET/ops/med-deepscientist/runtime/quests/002-early-residual-risk-managed-20260402 \
  --daemon-url ''
```

## Bottom line

`002` already has enough study truth and enough mainline binary display infrastructure to promote Phase C/D formally. The blocker is the missing managed-paper contract surface: today the managed quest still resolves only the minimal `F1/T1` binary path, while the only concrete Phase C/D evidence remains stranded in a legacy bundle whose catalogs are not yet registered/QC-backed. The safest path is to promote `002` through the existing binary Phase C/D templates and tables already covered by hydration, sync, and materialization tests, while keeping the study on its true binary early-residual endpoint.
