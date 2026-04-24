from __future__ import annotations

from . import chunk_01 as chunk_01
from . import chunk_02 as chunk_02
from . import chunk_03 as chunk_03

chunk_01.__dict__.update({
    "resolve_write_drift_stdout_path": chunk_02.resolve_write_drift_stdout_path,
    "medical_publication_surface_report_current": chunk_02.medical_publication_surface_report_current,
    "medical_publication_surface_currentness_anchor": chunk_02.medical_publication_surface_currentness_anchor,
    "resolve_compile_report_path": chunk_02.resolve_compile_report_path,
    "_resolve_gate_study_root": chunk_02._resolve_gate_study_root,
    "resolve_primary_journal_target": chunk_02.resolve_primary_journal_target,
    "_resolved_optional_path": chunk_02._resolved_optional_path,
    "_resolve_current_journal_source_manifest_path": chunk_02._resolve_current_journal_source_manifest_path,
    "resolve_journal_requirement_state": chunk_02.resolve_journal_requirement_state,
    "resolve_journal_package_state": chunk_02.resolve_journal_package_state,
    "resolve_primary_anchor": chunk_02.resolve_primary_anchor,
    "build_gate_state": chunk_02.build_gate_state,
    "build_gate_report": chunk_02.build_gate_report,
    "_bundle_stage_is_on_critical_path": chunk_02._bundle_stage_is_on_critical_path,
    "build_publication_supervisor_state": chunk_03.build_publication_supervisor_state,
    "extract_publication_supervisor_state": chunk_03.extract_publication_supervisor_state,
    "render_gate_markdown": chunk_03.render_gate_markdown,
    "write_gate_files": chunk_03.write_gate_files,
    "_materialize_publication_eval_latest": chunk_03._materialize_publication_eval_latest,
    "run_controller": chunk_03.run_controller,
    "parse_args": chunk_03.parse_args,
    "main": chunk_03.main,
})
chunk_02.__dict__.update({
    "build_publication_supervisor_state": chunk_03.build_publication_supervisor_state,
    "extract_publication_supervisor_state": chunk_03.extract_publication_supervisor_state,
    "render_gate_markdown": chunk_03.render_gate_markdown,
    "write_gate_files": chunk_03.write_gate_files,
    "_materialize_publication_eval_latest": chunk_03._materialize_publication_eval_latest,
    "run_controller": chunk_03.run_controller,
    "parse_args": chunk_03.parse_args,
    "main": chunk_03.main,
})

PUBLICATION_SUPERVISOR_KEYS = chunk_01.PUBLICATION_SUPERVISOR_KEYS
_NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS = chunk_01._NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS
_BUNDLE_STAGE_ONLY_BLOCKERS = chunk_01._BUNDLE_STAGE_ONLY_BLOCKERS
_MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS = chunk_01._MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS
_MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS = chunk_01._MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS
_MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS = chunk_01._MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS
_MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS = chunk_01._MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS
_MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES = chunk_01._MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES
_DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES = chunk_01._DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES
_append_unique = chunk_01._append_unique
GateState = chunk_01.GateState
utc_now = chunk_01.utc_now
load_json = chunk_01.load_json
dump_json = chunk_01.dump_json
_non_empty_text = chunk_01._non_empty_text
_normalized_blocker_set = chunk_01._normalized_blocker_set
find_latest = chunk_01.find_latest
find_latest_parseable_json = chunk_01.find_latest_parseable_json
_normalize_medical_surface_paper_root = chunk_01._normalize_medical_surface_paper_root
_medical_surface_report_matches_paper_root = chunk_01._medical_surface_report_matches_paper_root
_medical_surface_report_matches_study_root = chunk_01._medical_surface_report_matches_study_root
find_latest_gate_report = chunk_01.find_latest_gate_report
find_latest_medical_publication_surface_report = chunk_01.find_latest_medical_publication_surface_report
_write_drift_text_surfaces = chunk_01._write_drift_text_surfaces
detect_write_drift = chunk_01.detect_write_drift
_paper_line_open_supplementary_count = chunk_01._paper_line_open_supplementary_count
_paper_line_recommended_action = chunk_01._paper_line_recommended_action
_paper_line_blocking_reasons = chunk_01._paper_line_blocking_reasons
_paper_line_requires_required_supplementary = chunk_01._paper_line_requires_required_supplementary
_medical_publication_surface_named_blockers = chunk_01._medical_publication_surface_named_blockers
_medical_publication_surface_expectation_gaps = chunk_01._medical_publication_surface_expectation_gaps
_medical_publication_surface_route_back_recommendation = chunk_01._medical_publication_surface_route_back_recommendation
_medical_publication_surface_stage_note = chunk_01._medical_publication_surface_stage_note
_dedupe_resolved_paths = chunk_01._dedupe_resolved_paths
_bundle_manifest_branch = chunk_01._bundle_manifest_branch
_paper_line_branch = chunk_01._paper_line_branch
_projected_bundle_manifest_path = chunk_01._projected_bundle_manifest_path
_resolve_worktree_bundle_manifest_by_branch = chunk_01._resolve_worktree_bundle_manifest_by_branch
resolve_bundle_authority_paper_root = chunk_01.resolve_bundle_authority_paper_root
resolve_submission_checklist_path = chunk_01.resolve_submission_checklist_path
load_submission_checklist = chunk_01.load_submission_checklist
resolve_submission_minimal_manifest = chunk_01.resolve_submission_minimal_manifest
resolve_submission_minimal_output_paths = chunk_01.resolve_submission_minimal_output_paths
classify_deliverables = chunk_01.classify_deliverables
resolve_paper_root = chunk_01.resolve_paper_root
collect_manuscript_surface_paths = chunk_01.collect_manuscript_surface_paths
detect_manuscript_terminology_violations = chunk_01.detect_manuscript_terminology_violations
_load_catalog_entries = chunk_01._load_catalog_entries
active_manuscript_figure_count = chunk_01.active_manuscript_figure_count
active_main_text_figure_count = chunk_01.active_main_text_figure_count
infer_submission_publication_profile = chunk_01.infer_submission_publication_profile
collect_submission_surface_qc_failures = chunk_01.collect_submission_surface_qc_failures
gate_allows_write = chunk_01.gate_allows_write
annotations = chunk_01.annotations
argparse = chunk_01.argparse
import_module = chunk_01.import_module
json = chunk_01.json
re = chunk_01.re
dataclass = chunk_01.dataclass
datetime = chunk_01.datetime
timezone = chunk_01.timezone
Path = chunk_01.Path
Any = chunk_01.Any
journal_package_controller = chunk_01.journal_package_controller
study_delivery_sync = chunk_01.study_delivery_sync
submission_minimal = chunk_01.submission_minimal
describe_journal_submission_package = chunk_01.describe_journal_submission_package
journal_requirements_json_path = chunk_01.journal_requirements_json_path
load_journal_requirements = chunk_01.load_journal_requirements
slugify_journal_name = chunk_01.slugify_journal_name
publication_gate_policy = chunk_01.publication_gate_policy
paper_artifacts = chunk_01.paper_artifacts
quest_state = chunk_01.quest_state
resolve_paper_root_context = chunk_01.resolve_paper_root_context
user_message = chunk_01.user_message
runtime_protocol_report_store = chunk_01.runtime_protocol_report_store
resolve_write_drift_stdout_path = chunk_02.resolve_write_drift_stdout_path
medical_publication_surface_report_current = chunk_02.medical_publication_surface_report_current
medical_publication_surface_currentness_anchor = chunk_02.medical_publication_surface_currentness_anchor
resolve_compile_report_path = chunk_02.resolve_compile_report_path
_resolve_gate_study_root = chunk_02._resolve_gate_study_root
resolve_primary_journal_target = chunk_02.resolve_primary_journal_target
_resolved_optional_path = chunk_02._resolved_optional_path
_resolve_current_journal_source_manifest_path = chunk_02._resolve_current_journal_source_manifest_path
resolve_journal_requirement_state = chunk_02.resolve_journal_requirement_state
resolve_journal_package_state = chunk_02.resolve_journal_package_state
resolve_primary_anchor = chunk_02.resolve_primary_anchor
build_gate_state = chunk_02.build_gate_state
build_gate_report = chunk_02.build_gate_report
_bundle_stage_is_on_critical_path = chunk_02._bundle_stage_is_on_critical_path
build_publication_supervisor_state = chunk_03.build_publication_supervisor_state
extract_publication_supervisor_state = chunk_03.extract_publication_supervisor_state
render_gate_markdown = chunk_03.render_gate_markdown
write_gate_files = chunk_03.write_gate_files
_materialize_publication_eval_latest = chunk_03._materialize_publication_eval_latest
run_controller = chunk_03.run_controller
parse_args = chunk_03.parse_args
main = chunk_03.main

__all__ = [
    "PUBLICATION_SUPERVISOR_KEYS",
    "GateState",
    "utc_now",
    "load_json",
    "dump_json",
    "find_latest",
    "find_latest_parseable_json",
    "find_latest_gate_report",
    "find_latest_medical_publication_surface_report",
    "detect_write_drift",
    "resolve_bundle_authority_paper_root",
    "resolve_submission_checklist_path",
    "load_submission_checklist",
    "resolve_submission_minimal_manifest",
    "resolve_submission_minimal_output_paths",
    "classify_deliverables",
    "resolve_paper_root",
    "collect_manuscript_surface_paths",
    "detect_manuscript_terminology_violations",
    "active_manuscript_figure_count",
    "active_main_text_figure_count",
    "infer_submission_publication_profile",
    "collect_submission_surface_qc_failures",
    "gate_allows_write",
    "resolve_write_drift_stdout_path",
    "medical_publication_surface_report_current",
    "medical_publication_surface_currentness_anchor",
    "resolve_compile_report_path",
    "resolve_primary_journal_target",
    "resolve_journal_requirement_state",
    "resolve_journal_package_state",
    "resolve_primary_anchor",
    "build_gate_state",
    "build_gate_report",
    "build_publication_supervisor_state",
    "extract_publication_supervisor_state",
    "render_gate_markdown",
    "write_gate_files",
    "run_controller",
    "parse_args",
    "main",
]
