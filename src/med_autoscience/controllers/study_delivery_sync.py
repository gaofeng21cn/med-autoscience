from __future__ import annotations

from .study_delivery_sync_parts import (
    SYNC_STAGES,
    FORMAL_PAPER_DELIVERY_RELATIVE_PATHS,
    utc_now,
    dump_json,
    _normalized_path,
    _build_ledger_contract_linkage,
    build_charter_contract_linkage,
    write_text,
    reset_directory,
    remove_directory,
    create_staging_root,
    remap_staging_path_string,
    remap_staging_file_records,
    replace_directory_atomically,
    clear_directory_contents,
    can_sync_study_delivery,
    _resolve_study_owned_paper_context,
    _resolve_delivery_context,
    copy_file,
    copy_tree,
    build_submission_source_root,
    build_submission_package_readme,
    build_general_delivery_readme,
    _submission_delivery_stale_reason_label,
    build_unavailable_general_delivery_readme,
    build_preview_general_delivery_readme,
    build_manuscript_root_readme,
    build_artifacts_root_readme,
    build_artifacts_finalize_readme,
    build_unavailable_submission_package_readme,
    build_submission_package_audit_preview_readme,
    build_delivery_surface_roles,
    build_promoted_delivery_readme,
    ensure_manuscript_root_readme,
    resolve_finalize_resume_packet_source,
    build_zip_from_directory,
    build_authority_source_relative_root,
    FRONT_MATTER_LABELS,
    METADATA_CLOSEOUT_LABELS,
    _humanize_submission_field,
    _humanize_metadata_closeout_item,
    _is_pending_submission_item,
    build_submission_todo_from_manifest,
    build_current_package_readme,
    sync_current_package_projection,
    annotations,
    argparse,
    hashlib,
    json,
    shutil,
    tempfile,
    zipfile,
    datetime,
    timezone,
    Path,
    Any,
    medical_surface_policy,
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
    read_study_charter,
    resolve_study_charter_ref,
    resolve_paper_root_context,
    _copy_relative_files,
    copy_review_ledger_to_delivery_root,
    _copy_optional_file,
    _copy_optional_tree,
    _iter_relative_files,
    _draft_handoff_source_relative_paths,
    _draft_handoff_source_signature,
    _resolve_submission_source_path,
    _hash_file_bytes,
    CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS,
    CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS,
    _submission_source_relative_paths,
    _submission_source_signature,
    _load_json_file,
    _normalize_projection_json_payload,
    _submission_projection_file_matches_source,
    _submission_projection_matches_source,
    build_draft_handoff_readme,
    describe_draft_handoff_delivery,
    describe_submission_delivery,
    materialize_submission_delivery_stale_notice,
    sync_draft_handoff_delivery,
    sync_general_delivery,
    sync_journal_specific_delivery,
    sync_promoted_journal_delivery,
    sync_study_delivery,
    parse_args,
    main,
    __all__,
)
from .study_delivery_sync_parts import chunk_01 as chunk_01
from .study_delivery_sync_parts import chunk_02 as chunk_02
from .study_delivery_sync_parts import chunk_03 as chunk_03

import sys
from types import ModuleType
from typing import Any as _Any

_DECLARED_NAMES = ('SYNC_STAGES', 'FORMAL_PAPER_DELIVERY_RELATIVE_PATHS', 'utc_now', 'dump_json', '_normalized_path', '_build_ledger_contract_linkage', 'build_charter_contract_linkage', 'write_text', 'reset_directory', 'remove_directory', 'create_staging_root', 'remap_staging_path_string', 'remap_staging_file_records', 'replace_directory_atomically', 'clear_directory_contents', 'can_sync_study_delivery', '_resolve_study_owned_paper_context', '_resolve_delivery_context', 'copy_file', 'copy_tree', 'build_submission_source_root', 'build_submission_package_readme', 'build_general_delivery_readme', '_submission_delivery_stale_reason_label', 'build_unavailable_general_delivery_readme', 'build_preview_general_delivery_readme', 'build_manuscript_root_readme', 'build_artifacts_root_readme', 'build_artifacts_finalize_readme', 'build_unavailable_submission_package_readme', 'build_submission_package_audit_preview_readme', 'build_delivery_surface_roles', 'build_promoted_delivery_readme', 'ensure_manuscript_root_readme', 'resolve_finalize_resume_packet_source', 'build_zip_from_directory', 'build_authority_source_relative_root', 'FRONT_MATTER_LABELS', 'METADATA_CLOSEOUT_LABELS', '_humanize_submission_field', '_humanize_metadata_closeout_item', '_is_pending_submission_item', 'build_submission_todo_from_manifest', 'build_current_package_readme', 'sync_current_package_projection', '_copy_relative_files', 'copy_review_ledger_to_delivery_root', '_copy_optional_file', '_copy_optional_tree', '_iter_relative_files', '_draft_handoff_source_relative_paths', '_draft_handoff_source_signature', '_resolve_submission_source_path', '_hash_file_bytes', 'CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS', 'CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS', '_submission_source_relative_paths', '_submission_source_signature', '_load_json_file', '_normalize_projection_json_payload', '_submission_projection_file_matches_source', '_submission_projection_matches_source', 'build_draft_handoff_readme', 'describe_draft_handoff_delivery', 'describe_submission_delivery', 'materialize_submission_delivery_stale_notice', 'sync_draft_handoff_delivery', 'sync_general_delivery', 'sync_journal_specific_delivery', 'sync_promoted_journal_delivery', 'sync_study_delivery', 'parse_args', 'main',)


def _split_chunks() -> tuple[ModuleType, ...]:
    return tuple(
        value
        for name, value in globals().items()
        if name.startswith("chunk_") and isinstance(value, ModuleType)
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
