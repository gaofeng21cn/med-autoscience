from __future__ import annotations

from .publication_gate_parts import (
    PUBLICATION_SUPERVISOR_KEYS,
    _NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS,
    _BUNDLE_STAGE_ONLY_BLOCKERS,
    _MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS,
    _MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS,
    _MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS,
    _MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS,
    _MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES,
    _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES,
    _append_unique,
    GateState,
    utc_now,
    load_json,
    dump_json,
    _non_empty_text,
    _normalized_blocker_set,
    find_latest,
    find_latest_parseable_json,
    _normalize_medical_surface_paper_root,
    _medical_surface_report_matches_paper_root,
    _medical_surface_report_matches_study_root,
    find_latest_gate_report,
    find_latest_medical_publication_surface_report,
    _write_drift_text_surfaces,
    detect_write_drift,
    _paper_line_open_supplementary_count,
    _paper_line_recommended_action,
    _paper_line_blocking_reasons,
    _paper_line_requires_required_supplementary,
    _medical_publication_surface_named_blockers,
    _medical_publication_surface_expectation_gaps,
    _medical_publication_surface_route_back_recommendation,
    _medical_publication_surface_stage_note,
    _dedupe_resolved_paths,
    _bundle_manifest_branch,
    _paper_line_branch,
    _projected_bundle_manifest_path,
    _resolve_worktree_bundle_manifest_by_branch,
    resolve_bundle_authority_paper_root,
    resolve_submission_checklist_path,
    load_submission_checklist,
    resolve_submission_minimal_manifest,
    resolve_submission_minimal_output_paths,
    classify_deliverables,
    resolve_paper_root,
    collect_manuscript_surface_paths,
    detect_manuscript_terminology_violations,
    _load_catalog_entries,
    active_manuscript_figure_count,
    active_main_text_figure_count,
    infer_submission_publication_profile,
    collect_submission_surface_qc_failures,
    gate_allows_write,
    annotations,
    argparse,
    import_module,
    json,
    re,
    dataclass,
    datetime,
    timezone,
    Path,
    Any,
    journal_package_controller,
    study_delivery_sync,
    submission_minimal,
    describe_journal_submission_package,
    journal_requirements_json_path,
    load_journal_requirements,
    slugify_journal_name,
    publication_gate_policy,
    paper_artifacts,
    quest_state,
    resolve_paper_root_context,
    user_message,
    runtime_protocol_report_store,
    resolve_write_drift_stdout_path,
    medical_publication_surface_report_current,
    medical_publication_surface_currentness_anchor,
    resolve_compile_report_path,
    _resolve_gate_study_root,
    resolve_primary_journal_target,
    _resolved_optional_path,
    _resolve_current_journal_source_manifest_path,
    resolve_journal_requirement_state,
    resolve_journal_package_state,
    resolve_primary_anchor,
    build_gate_state,
    build_gate_report,
    _bundle_stage_is_on_critical_path,
    build_publication_supervisor_state,
    extract_publication_supervisor_state,
    render_gate_markdown,
    write_gate_files,
    _materialize_publication_eval_latest,
    run_controller,
    parse_args,
    main,
    __all__,
)
from .publication_gate_parts import discovery_and_drift as discovery_and_drift
from .publication_gate_parts import state_and_reports as state_and_reports
from .publication_gate_parts import supervisor_and_cli as supervisor_and_cli

import sys
from types import ModuleType
from typing import Any as _Any

_DECLARED_NAMES = ('PUBLICATION_SUPERVISOR_KEYS', '_NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS', '_BUNDLE_STAGE_ONLY_BLOCKERS', '_MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS', '_MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS', '_MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS', '_MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS', '_MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES', '_DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES', '_append_unique', 'GateState', 'utc_now', 'load_json', 'dump_json', '_non_empty_text', '_normalized_blocker_set', 'find_latest', 'find_latest_parseable_json', '_normalize_medical_surface_paper_root', '_medical_surface_report_matches_paper_root', '_medical_surface_report_matches_study_root', 'find_latest_gate_report', 'find_latest_medical_publication_surface_report', '_write_drift_text_surfaces', 'detect_write_drift', '_paper_line_open_supplementary_count', '_paper_line_recommended_action', '_paper_line_blocking_reasons', '_paper_line_requires_required_supplementary', '_medical_publication_surface_named_blockers', '_medical_publication_surface_expectation_gaps', '_medical_publication_surface_route_back_recommendation', '_medical_publication_surface_stage_note', '_dedupe_resolved_paths', '_bundle_manifest_branch', '_paper_line_branch', '_projected_bundle_manifest_path', '_resolve_worktree_bundle_manifest_by_branch', 'resolve_bundle_authority_paper_root', 'resolve_submission_checklist_path', 'load_submission_checklist', 'resolve_submission_minimal_manifest', 'resolve_submission_minimal_output_paths', 'classify_deliverables', 'resolve_paper_root', 'collect_manuscript_surface_paths', 'detect_manuscript_terminology_violations', '_load_catalog_entries', 'active_manuscript_figure_count', 'active_main_text_figure_count', 'infer_submission_publication_profile', 'collect_submission_surface_qc_failures', 'gate_allows_write', 'resolve_write_drift_stdout_path', 'medical_publication_surface_report_current', 'medical_publication_surface_currentness_anchor', 'resolve_compile_report_path', '_resolve_gate_study_root', 'resolve_primary_journal_target', '_resolved_optional_path', '_resolve_current_journal_source_manifest_path', 'resolve_journal_requirement_state', 'resolve_journal_package_state', 'resolve_primary_anchor', 'build_gate_state', 'build_gate_report', '_bundle_stage_is_on_critical_path', 'build_publication_supervisor_state', 'extract_publication_supervisor_state', 'render_gate_markdown', 'write_gate_files', '_materialize_publication_eval_latest', 'run_controller', 'parse_args', 'main',)


def _split_chunks() -> tuple[ModuleType, ...]:
    return tuple(
        value
        for name, value in globals().items()
        if isinstance(value, ModuleType) and name in {'discovery_and_drift', 'state_and_reports', 'supervisor_and_cli'} # and isinstance(value, ModuleType)
    )


def _restore_declaring_module() -> None:
    module_name = __name__
    for name in _DECLARED_NAMES:
        value = globals().get(name)
        if isinstance(value, type) or callable(value):
            if getattr(value, "__module__", None) != module_name:
                try:
                    value.__module__ = module_name
                except (AttributeError, TypeError):
                    pass


class _SplitModule(ModuleType):
    def __setattr__(self, name: str, value: _Any) -> None:
        super().__setattr__(name, value)
        for chunk in _split_chunks():
            if hasattr(chunk, name):
                setattr(chunk, name, value)


_restore_declaring_module()
sys.modules[__name__].__class__ = _SplitModule
