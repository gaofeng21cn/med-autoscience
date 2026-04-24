from __future__ import annotations

from . import staging_and_sources as staging_and_sources
from . import delivery_descriptions as delivery_descriptions
from . import sync_orchestration as sync_orchestration

staging_and_sources.__dict__.update({
    "_copy_relative_files": delivery_descriptions._copy_relative_files,
    "copy_review_ledger_to_delivery_root": delivery_descriptions.copy_review_ledger_to_delivery_root,
    "_copy_optional_file": delivery_descriptions._copy_optional_file,
    "_copy_optional_tree": delivery_descriptions._copy_optional_tree,
    "_iter_relative_files": delivery_descriptions._iter_relative_files,
    "_draft_handoff_source_relative_paths": delivery_descriptions._draft_handoff_source_relative_paths,
    "_draft_handoff_source_signature": delivery_descriptions._draft_handoff_source_signature,
    "_resolve_submission_source_path": delivery_descriptions._resolve_submission_source_path,
    "_hash_file_bytes": delivery_descriptions._hash_file_bytes,
    "CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS": delivery_descriptions.CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS,
    "CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS": delivery_descriptions.CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS,
    "_submission_source_relative_paths": delivery_descriptions._submission_source_relative_paths,
    "_submission_source_signature": delivery_descriptions._submission_source_signature,
    "_load_json_file": delivery_descriptions._load_json_file,
    "_normalize_projection_json_payload": delivery_descriptions._normalize_projection_json_payload,
    "_submission_projection_file_matches_source": delivery_descriptions._submission_projection_file_matches_source,
    "_submission_projection_matches_source": delivery_descriptions._submission_projection_matches_source,
    "build_draft_handoff_readme": delivery_descriptions.build_draft_handoff_readme,
    "describe_draft_handoff_delivery": delivery_descriptions.describe_draft_handoff_delivery,
    "describe_submission_delivery": delivery_descriptions.describe_submission_delivery,
    "materialize_submission_delivery_stale_notice": delivery_descriptions.materialize_submission_delivery_stale_notice,
    "sync_draft_handoff_delivery": sync_orchestration.sync_draft_handoff_delivery,
    "sync_general_delivery": sync_orchestration.sync_general_delivery,
    "sync_journal_specific_delivery": sync_orchestration.sync_journal_specific_delivery,
    "sync_promoted_journal_delivery": sync_orchestration.sync_promoted_journal_delivery,
    "sync_study_delivery": sync_orchestration.sync_study_delivery,
    "parse_args": sync_orchestration.parse_args,
    "main": sync_orchestration.main,
})
delivery_descriptions.__dict__.update({
    "sync_draft_handoff_delivery": sync_orchestration.sync_draft_handoff_delivery,
    "sync_general_delivery": sync_orchestration.sync_general_delivery,
    "sync_journal_specific_delivery": sync_orchestration.sync_journal_specific_delivery,
    "sync_promoted_journal_delivery": sync_orchestration.sync_promoted_journal_delivery,
    "sync_study_delivery": sync_orchestration.sync_study_delivery,
    "parse_args": sync_orchestration.parse_args,
    "main": sync_orchestration.main,
})

SYNC_STAGES = staging_and_sources.SYNC_STAGES
FORMAL_PAPER_DELIVERY_RELATIVE_PATHS = staging_and_sources.FORMAL_PAPER_DELIVERY_RELATIVE_PATHS
utc_now = staging_and_sources.utc_now
dump_json = staging_and_sources.dump_json
_normalized_path = staging_and_sources._normalized_path
_build_ledger_contract_linkage = staging_and_sources._build_ledger_contract_linkage
build_charter_contract_linkage = staging_and_sources.build_charter_contract_linkage
write_text = staging_and_sources.write_text
reset_directory = staging_and_sources.reset_directory
remove_directory = staging_and_sources.remove_directory
create_staging_root = staging_and_sources.create_staging_root
remap_staging_path_string = staging_and_sources.remap_staging_path_string
remap_staging_file_records = staging_and_sources.remap_staging_file_records
replace_directory_atomically = staging_and_sources.replace_directory_atomically
clear_directory_contents = staging_and_sources.clear_directory_contents
can_sync_study_delivery = staging_and_sources.can_sync_study_delivery
_resolve_study_owned_paper_context = staging_and_sources._resolve_study_owned_paper_context
_resolve_delivery_context = staging_and_sources._resolve_delivery_context
copy_file = staging_and_sources.copy_file
copy_tree = staging_and_sources.copy_tree
build_submission_source_root = staging_and_sources.build_submission_source_root
build_submission_package_readme = staging_and_sources.build_submission_package_readme
build_general_delivery_readme = staging_and_sources.build_general_delivery_readme
_submission_delivery_stale_reason_label = staging_and_sources._submission_delivery_stale_reason_label
build_unavailable_general_delivery_readme = staging_and_sources.build_unavailable_general_delivery_readme
build_preview_general_delivery_readme = staging_and_sources.build_preview_general_delivery_readme
build_manuscript_root_readme = staging_and_sources.build_manuscript_root_readme
build_artifacts_root_readme = staging_and_sources.build_artifacts_root_readme
build_artifacts_finalize_readme = staging_and_sources.build_artifacts_finalize_readme
build_unavailable_submission_package_readme = staging_and_sources.build_unavailable_submission_package_readme
build_submission_package_audit_preview_readme = staging_and_sources.build_submission_package_audit_preview_readme
build_delivery_surface_roles = staging_and_sources.build_delivery_surface_roles
build_promoted_delivery_readme = staging_and_sources.build_promoted_delivery_readme
ensure_manuscript_root_readme = staging_and_sources.ensure_manuscript_root_readme
resolve_finalize_resume_packet_source = staging_and_sources.resolve_finalize_resume_packet_source
build_zip_from_directory = staging_and_sources.build_zip_from_directory
build_authority_source_relative_root = staging_and_sources.build_authority_source_relative_root
FRONT_MATTER_LABELS = staging_and_sources.FRONT_MATTER_LABELS
METADATA_CLOSEOUT_LABELS = staging_and_sources.METADATA_CLOSEOUT_LABELS
_humanize_submission_field = staging_and_sources._humanize_submission_field
_humanize_metadata_closeout_item = staging_and_sources._humanize_metadata_closeout_item
_is_pending_submission_item = staging_and_sources._is_pending_submission_item
build_submission_todo_from_manifest = staging_and_sources.build_submission_todo_from_manifest
build_current_package_readme = staging_and_sources.build_current_package_readme
sync_current_package_projection = staging_and_sources.sync_current_package_projection
annotations = staging_and_sources.annotations
argparse = staging_and_sources.argparse
hashlib = staging_and_sources.hashlib
json = staging_and_sources.json
shutil = staging_and_sources.shutil
tempfile = staging_and_sources.tempfile
zipfile = staging_and_sources.zipfile
datetime = staging_and_sources.datetime
timezone = staging_and_sources.timezone
Path = staging_and_sources.Path
Any = staging_and_sources.Any
medical_surface_policy = staging_and_sources.medical_surface_policy
GENERAL_MEDICAL_JOURNAL_PROFILE = staging_and_sources.GENERAL_MEDICAL_JOURNAL_PROFILE
is_supported_publication_profile = staging_and_sources.is_supported_publication_profile
normalize_publication_profile = staging_and_sources.normalize_publication_profile
read_study_charter = staging_and_sources.read_study_charter
resolve_study_charter_ref = staging_and_sources.resolve_study_charter_ref
resolve_paper_root_context = staging_and_sources.resolve_paper_root_context
_copy_relative_files = delivery_descriptions._copy_relative_files
copy_review_ledger_to_delivery_root = delivery_descriptions.copy_review_ledger_to_delivery_root
_copy_optional_file = delivery_descriptions._copy_optional_file
_copy_optional_tree = delivery_descriptions._copy_optional_tree
_iter_relative_files = delivery_descriptions._iter_relative_files
_draft_handoff_source_relative_paths = delivery_descriptions._draft_handoff_source_relative_paths
_draft_handoff_source_signature = delivery_descriptions._draft_handoff_source_signature
_resolve_submission_source_path = delivery_descriptions._resolve_submission_source_path
_hash_file_bytes = delivery_descriptions._hash_file_bytes
CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS = delivery_descriptions.CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS
CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS = delivery_descriptions.CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS
_submission_source_relative_paths = delivery_descriptions._submission_source_relative_paths
_submission_source_signature = delivery_descriptions._submission_source_signature
_load_json_file = delivery_descriptions._load_json_file
_normalize_projection_json_payload = delivery_descriptions._normalize_projection_json_payload
_submission_projection_file_matches_source = delivery_descriptions._submission_projection_file_matches_source
_submission_projection_matches_source = delivery_descriptions._submission_projection_matches_source
build_draft_handoff_readme = delivery_descriptions.build_draft_handoff_readme
describe_draft_handoff_delivery = delivery_descriptions.describe_draft_handoff_delivery
describe_submission_delivery = delivery_descriptions.describe_submission_delivery
materialize_submission_delivery_stale_notice = delivery_descriptions.materialize_submission_delivery_stale_notice
sync_draft_handoff_delivery = sync_orchestration.sync_draft_handoff_delivery
sync_general_delivery = sync_orchestration.sync_general_delivery
sync_journal_specific_delivery = sync_orchestration.sync_journal_specific_delivery
sync_promoted_journal_delivery = sync_orchestration.sync_promoted_journal_delivery
sync_study_delivery = sync_orchestration.sync_study_delivery
parse_args = sync_orchestration.parse_args
main = sync_orchestration.main

__all__ = [
    "SYNC_STAGES",
    "FORMAL_PAPER_DELIVERY_RELATIVE_PATHS",
    "utc_now",
    "dump_json",
    "build_charter_contract_linkage",
    "write_text",
    "reset_directory",
    "remove_directory",
    "create_staging_root",
    "remap_staging_path_string",
    "remap_staging_file_records",
    "replace_directory_atomically",
    "clear_directory_contents",
    "can_sync_study_delivery",
    "copy_file",
    "copy_tree",
    "build_submission_source_root",
    "build_submission_package_readme",
    "build_general_delivery_readme",
    "build_unavailable_general_delivery_readme",
    "build_preview_general_delivery_readme",
    "build_manuscript_root_readme",
    "build_artifacts_root_readme",
    "build_artifacts_finalize_readme",
    "build_unavailable_submission_package_readme",
    "build_submission_package_audit_preview_readme",
    "build_delivery_surface_roles",
    "build_promoted_delivery_readme",
    "ensure_manuscript_root_readme",
    "resolve_finalize_resume_packet_source",
    "build_zip_from_directory",
    "build_authority_source_relative_root",
    "FRONT_MATTER_LABELS",
    "METADATA_CLOSEOUT_LABELS",
    "build_submission_todo_from_manifest",
    "build_current_package_readme",
    "sync_current_package_projection",
    "copy_review_ledger_to_delivery_root",
    "CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS",
    "CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS",
    "build_draft_handoff_readme",
    "describe_draft_handoff_delivery",
    "describe_submission_delivery",
    "materialize_submission_delivery_stale_notice",
    "sync_draft_handoff_delivery",
    "sync_general_delivery",
    "sync_journal_specific_delivery",
    "sync_promoted_journal_delivery",
    "sync_study_delivery",
    "parse_args",
    "main",
]
