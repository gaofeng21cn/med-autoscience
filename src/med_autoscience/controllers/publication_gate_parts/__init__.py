from __future__ import annotations

from . import discovery_and_drift as discovery_and_drift
from . import state_and_reports as state_and_reports
from . import supervisor_and_cli as supervisor_and_cli

discovery_and_drift.__dict__.update({
    "resolve_write_drift_stdout_path": state_and_reports.resolve_write_drift_stdout_path,
    "medical_publication_surface_report_current": state_and_reports.medical_publication_surface_report_current,
    "medical_publication_surface_currentness_anchor": state_and_reports.medical_publication_surface_currentness_anchor,
    "resolve_compile_report_path": state_and_reports.resolve_compile_report_path,
    "_resolve_gate_study_root": state_and_reports._resolve_gate_study_root,
    "resolve_primary_journal_target": state_and_reports.resolve_primary_journal_target,
    "_resolved_optional_path": state_and_reports._resolved_optional_path,
    "_resolve_current_journal_source_manifest_path": state_and_reports._resolve_current_journal_source_manifest_path,
    "resolve_journal_requirement_state": state_and_reports.resolve_journal_requirement_state,
    "resolve_journal_package_state": state_and_reports.resolve_journal_package_state,
    "resolve_primary_anchor": state_and_reports.resolve_primary_anchor,
    "build_gate_state": state_and_reports.build_gate_state,
    "build_gate_report": state_and_reports.build_gate_report,
    "_bundle_stage_is_on_critical_path": state_and_reports._bundle_stage_is_on_critical_path,
    "build_publication_supervisor_state": supervisor_and_cli.build_publication_supervisor_state,
    "extract_publication_supervisor_state": supervisor_and_cli.extract_publication_supervisor_state,
    "render_gate_markdown": supervisor_and_cli.render_gate_markdown,
    "write_gate_files": supervisor_and_cli.write_gate_files,
    "_materialize_publication_eval_latest": supervisor_and_cli._materialize_publication_eval_latest,
    "run_controller": supervisor_and_cli.run_controller,
    "parse_args": supervisor_and_cli.parse_args,
    "main": supervisor_and_cli.main,
})
state_and_reports.__dict__.update({
    "build_publication_supervisor_state": supervisor_and_cli.build_publication_supervisor_state,
    "extract_publication_supervisor_state": supervisor_and_cli.extract_publication_supervisor_state,
    "render_gate_markdown": supervisor_and_cli.render_gate_markdown,
    "write_gate_files": supervisor_and_cli.write_gate_files,
    "_materialize_publication_eval_latest": supervisor_and_cli._materialize_publication_eval_latest,
    "run_controller": supervisor_and_cli.run_controller,
    "parse_args": supervisor_and_cli.parse_args,
    "main": supervisor_and_cli.main,
})

PUBLICATION_SUPERVISOR_KEYS = discovery_and_drift.PUBLICATION_SUPERVISOR_KEYS
_NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS = discovery_and_drift._NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS
_BUNDLE_STAGE_ONLY_BLOCKERS = discovery_and_drift._BUNDLE_STAGE_ONLY_BLOCKERS
_MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS = discovery_and_drift._MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS
_MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS = discovery_and_drift._MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS
_MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS = discovery_and_drift._MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS
_MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS = discovery_and_drift._MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS
_MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES = discovery_and_drift._MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES
_DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES = discovery_and_drift._DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES
_append_unique = discovery_and_drift._append_unique
GateState = discovery_and_drift.GateState
utc_now = discovery_and_drift.utc_now
load_json = discovery_and_drift.load_json
dump_json = discovery_and_drift.dump_json
_non_empty_text = discovery_and_drift._non_empty_text
_normalized_blocker_set = discovery_and_drift._normalized_blocker_set
find_latest = discovery_and_drift.find_latest
find_latest_parseable_json = discovery_and_drift.find_latest_parseable_json
_normalize_medical_surface_paper_root = discovery_and_drift._normalize_medical_surface_paper_root
_medical_surface_report_matches_paper_root = discovery_and_drift._medical_surface_report_matches_paper_root
_medical_surface_report_matches_study_root = discovery_and_drift._medical_surface_report_matches_study_root
find_latest_gate_report = discovery_and_drift.find_latest_gate_report
find_latest_medical_publication_surface_report = discovery_and_drift.find_latest_medical_publication_surface_report
_write_drift_text_surfaces = discovery_and_drift._write_drift_text_surfaces
detect_write_drift = discovery_and_drift.detect_write_drift
_paper_line_open_supplementary_count = discovery_and_drift._paper_line_open_supplementary_count
_paper_line_recommended_action = discovery_and_drift._paper_line_recommended_action
_paper_line_blocking_reasons = discovery_and_drift._paper_line_blocking_reasons
_paper_line_requires_required_supplementary = discovery_and_drift._paper_line_requires_required_supplementary
_medical_publication_surface_named_blockers = discovery_and_drift._medical_publication_surface_named_blockers
_medical_publication_surface_expectation_gaps = discovery_and_drift._medical_publication_surface_expectation_gaps
_medical_publication_surface_route_back_recommendation = discovery_and_drift._medical_publication_surface_route_back_recommendation
_medical_publication_surface_stage_note = discovery_and_drift._medical_publication_surface_stage_note
_dedupe_resolved_paths = discovery_and_drift._dedupe_resolved_paths
_bundle_manifest_branch = discovery_and_drift._bundle_manifest_branch
_paper_line_branch = discovery_and_drift._paper_line_branch
_projected_bundle_manifest_path = discovery_and_drift._projected_bundle_manifest_path
_resolve_worktree_bundle_manifest_by_branch = discovery_and_drift._resolve_worktree_bundle_manifest_by_branch
resolve_bundle_authority_paper_root = discovery_and_drift.resolve_bundle_authority_paper_root
resolve_submission_checklist_path = discovery_and_drift.resolve_submission_checklist_path
load_submission_checklist = discovery_and_drift.load_submission_checklist
resolve_submission_minimal_manifest = discovery_and_drift.resolve_submission_minimal_manifest
resolve_submission_minimal_output_paths = discovery_and_drift.resolve_submission_minimal_output_paths
classify_deliverables = discovery_and_drift.classify_deliverables
resolve_paper_root = discovery_and_drift.resolve_paper_root
collect_manuscript_surface_paths = discovery_and_drift.collect_manuscript_surface_paths
detect_manuscript_terminology_violations = discovery_and_drift.detect_manuscript_terminology_violations
_load_catalog_entries = discovery_and_drift._load_catalog_entries
active_manuscript_figure_count = discovery_and_drift.active_manuscript_figure_count
active_main_text_figure_count = discovery_and_drift.active_main_text_figure_count
infer_submission_publication_profile = discovery_and_drift.infer_submission_publication_profile
collect_submission_surface_qc_failures = discovery_and_drift.collect_submission_surface_qc_failures
gate_allows_write = discovery_and_drift.gate_allows_write
annotations = discovery_and_drift.annotations
argparse = discovery_and_drift.argparse
import_module = discovery_and_drift.import_module
json = discovery_and_drift.json
re = discovery_and_drift.re
dataclass = discovery_and_drift.dataclass
datetime = discovery_and_drift.datetime
timezone = discovery_and_drift.timezone
Path = discovery_and_drift.Path
Any = discovery_and_drift.Any
journal_package_controller = discovery_and_drift.journal_package_controller
study_delivery_sync = discovery_and_drift.study_delivery_sync
submission_minimal = discovery_and_drift.submission_minimal
describe_journal_submission_package = discovery_and_drift.describe_journal_submission_package
journal_requirements_json_path = discovery_and_drift.journal_requirements_json_path
load_journal_requirements = discovery_and_drift.load_journal_requirements
slugify_journal_name = discovery_and_drift.slugify_journal_name
publication_gate_policy = discovery_and_drift.publication_gate_policy
paper_artifacts = discovery_and_drift.paper_artifacts
quest_state = discovery_and_drift.quest_state
resolve_paper_root_context = discovery_and_drift.resolve_paper_root_context
user_message = discovery_and_drift.user_message
runtime_protocol_report_store = discovery_and_drift.runtime_protocol_report_store
resolve_write_drift_stdout_path = state_and_reports.resolve_write_drift_stdout_path
medical_publication_surface_report_current = state_and_reports.medical_publication_surface_report_current
medical_publication_surface_currentness_anchor = state_and_reports.medical_publication_surface_currentness_anchor
resolve_compile_report_path = state_and_reports.resolve_compile_report_path
_resolve_gate_study_root = state_and_reports._resolve_gate_study_root
resolve_primary_journal_target = state_and_reports.resolve_primary_journal_target
_resolved_optional_path = state_and_reports._resolved_optional_path
_resolve_current_journal_source_manifest_path = state_and_reports._resolve_current_journal_source_manifest_path
resolve_journal_requirement_state = state_and_reports.resolve_journal_requirement_state
resolve_journal_package_state = state_and_reports.resolve_journal_package_state
resolve_primary_anchor = state_and_reports.resolve_primary_anchor
build_gate_state = state_and_reports.build_gate_state
build_gate_report = state_and_reports.build_gate_report
_bundle_stage_is_on_critical_path = state_and_reports._bundle_stage_is_on_critical_path
build_publication_supervisor_state = supervisor_and_cli.build_publication_supervisor_state
extract_publication_supervisor_state = supervisor_and_cli.extract_publication_supervisor_state
render_gate_markdown = supervisor_and_cli.render_gate_markdown
write_gate_files = supervisor_and_cli.write_gate_files
_materialize_publication_eval_latest = supervisor_and_cli._materialize_publication_eval_latest
run_controller = supervisor_and_cli.run_controller
parse_args = supervisor_and_cli.parse_args
main = supervisor_and_cli.main

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
