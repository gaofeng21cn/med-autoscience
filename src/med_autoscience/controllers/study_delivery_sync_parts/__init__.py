from __future__ import annotations

from . import chunk_01 as chunk_01
from . import chunk_02 as chunk_02
from . import chunk_03 as chunk_03

chunk_01.__dict__.update({
    "_copy_relative_files": chunk_02._copy_relative_files,
    "copy_review_ledger_to_delivery_root": chunk_02.copy_review_ledger_to_delivery_root,
    "_copy_optional_file": chunk_02._copy_optional_file,
    "_copy_optional_tree": chunk_02._copy_optional_tree,
    "_iter_relative_files": chunk_02._iter_relative_files,
    "_draft_handoff_source_relative_paths": chunk_02._draft_handoff_source_relative_paths,
    "_draft_handoff_source_signature": chunk_02._draft_handoff_source_signature,
    "_resolve_submission_source_path": chunk_02._resolve_submission_source_path,
    "_hash_file_bytes": chunk_02._hash_file_bytes,
    "CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS": chunk_02.CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS,
    "CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS": chunk_02.CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS,
    "_submission_source_relative_paths": chunk_02._submission_source_relative_paths,
    "_submission_source_signature": chunk_02._submission_source_signature,
    "_load_json_file": chunk_02._load_json_file,
    "_normalize_projection_json_payload": chunk_02._normalize_projection_json_payload,
    "_submission_projection_file_matches_source": chunk_02._submission_projection_file_matches_source,
    "_submission_projection_matches_source": chunk_02._submission_projection_matches_source,
    "build_draft_handoff_readme": chunk_02.build_draft_handoff_readme,
    "describe_draft_handoff_delivery": chunk_02.describe_draft_handoff_delivery,
    "describe_submission_delivery": chunk_02.describe_submission_delivery,
    "materialize_submission_delivery_stale_notice": chunk_02.materialize_submission_delivery_stale_notice,
    "sync_draft_handoff_delivery": chunk_03.sync_draft_handoff_delivery,
    "sync_general_delivery": chunk_03.sync_general_delivery,
    "sync_journal_specific_delivery": chunk_03.sync_journal_specific_delivery,
    "sync_promoted_journal_delivery": chunk_03.sync_promoted_journal_delivery,
    "sync_study_delivery": chunk_03.sync_study_delivery,
    "parse_args": chunk_03.parse_args,
    "main": chunk_03.main,
})
chunk_02.__dict__.update({
    "sync_draft_handoff_delivery": chunk_03.sync_draft_handoff_delivery,
    "sync_general_delivery": chunk_03.sync_general_delivery,
    "sync_journal_specific_delivery": chunk_03.sync_journal_specific_delivery,
    "sync_promoted_journal_delivery": chunk_03.sync_promoted_journal_delivery,
    "sync_study_delivery": chunk_03.sync_study_delivery,
    "parse_args": chunk_03.parse_args,
    "main": chunk_03.main,
})

SYNC_STAGES = chunk_01.SYNC_STAGES
FORMAL_PAPER_DELIVERY_RELATIVE_PATHS = chunk_01.FORMAL_PAPER_DELIVERY_RELATIVE_PATHS
utc_now = chunk_01.utc_now
dump_json = chunk_01.dump_json
_normalized_path = chunk_01._normalized_path
_build_ledger_contract_linkage = chunk_01._build_ledger_contract_linkage
build_charter_contract_linkage = chunk_01.build_charter_contract_linkage
write_text = chunk_01.write_text
reset_directory = chunk_01.reset_directory
remove_directory = chunk_01.remove_directory
create_staging_root = chunk_01.create_staging_root
remap_staging_path_string = chunk_01.remap_staging_path_string
remap_staging_file_records = chunk_01.remap_staging_file_records
replace_directory_atomically = chunk_01.replace_directory_atomically
clear_directory_contents = chunk_01.clear_directory_contents
can_sync_study_delivery = chunk_01.can_sync_study_delivery
_resolve_study_owned_paper_context = chunk_01._resolve_study_owned_paper_context
_resolve_delivery_context = chunk_01._resolve_delivery_context
copy_file = chunk_01.copy_file
copy_tree = chunk_01.copy_tree
build_submission_source_root = chunk_01.build_submission_source_root
build_submission_package_readme = chunk_01.build_submission_package_readme
build_general_delivery_readme = chunk_01.build_general_delivery_readme
_submission_delivery_stale_reason_label = chunk_01._submission_delivery_stale_reason_label
build_unavailable_general_delivery_readme = chunk_01.build_unavailable_general_delivery_readme
build_preview_general_delivery_readme = chunk_01.build_preview_general_delivery_readme
build_manuscript_root_readme = chunk_01.build_manuscript_root_readme
build_artifacts_root_readme = chunk_01.build_artifacts_root_readme
build_artifacts_finalize_readme = chunk_01.build_artifacts_finalize_readme
build_unavailable_submission_package_readme = chunk_01.build_unavailable_submission_package_readme
build_submission_package_audit_preview_readme = chunk_01.build_submission_package_audit_preview_readme
build_delivery_surface_roles = chunk_01.build_delivery_surface_roles
build_promoted_delivery_readme = chunk_01.build_promoted_delivery_readme
ensure_manuscript_root_readme = chunk_01.ensure_manuscript_root_readme
resolve_finalize_resume_packet_source = chunk_01.resolve_finalize_resume_packet_source
build_zip_from_directory = chunk_01.build_zip_from_directory
build_authority_source_relative_root = chunk_01.build_authority_source_relative_root
FRONT_MATTER_LABELS = chunk_01.FRONT_MATTER_LABELS
METADATA_CLOSEOUT_LABELS = chunk_01.METADATA_CLOSEOUT_LABELS
_humanize_submission_field = chunk_01._humanize_submission_field
_humanize_metadata_closeout_item = chunk_01._humanize_metadata_closeout_item
_is_pending_submission_item = chunk_01._is_pending_submission_item
build_submission_todo_from_manifest = chunk_01.build_submission_todo_from_manifest
build_current_package_readme = chunk_01.build_current_package_readme
sync_current_package_projection = chunk_01.sync_current_package_projection
annotations = chunk_01.annotations
argparse = chunk_01.argparse
hashlib = chunk_01.hashlib
json = chunk_01.json
shutil = chunk_01.shutil
tempfile = chunk_01.tempfile
zipfile = chunk_01.zipfile
datetime = chunk_01.datetime
timezone = chunk_01.timezone
Path = chunk_01.Path
Any = chunk_01.Any
medical_surface_policy = chunk_01.medical_surface_policy
GENERAL_MEDICAL_JOURNAL_PROFILE = chunk_01.GENERAL_MEDICAL_JOURNAL_PROFILE
is_supported_publication_profile = chunk_01.is_supported_publication_profile
normalize_publication_profile = chunk_01.normalize_publication_profile
read_study_charter = chunk_01.read_study_charter
resolve_study_charter_ref = chunk_01.resolve_study_charter_ref
resolve_paper_root_context = chunk_01.resolve_paper_root_context
_copy_relative_files = chunk_02._copy_relative_files
copy_review_ledger_to_delivery_root = chunk_02.copy_review_ledger_to_delivery_root
_copy_optional_file = chunk_02._copy_optional_file
_copy_optional_tree = chunk_02._copy_optional_tree
_iter_relative_files = chunk_02._iter_relative_files
_draft_handoff_source_relative_paths = chunk_02._draft_handoff_source_relative_paths
_draft_handoff_source_signature = chunk_02._draft_handoff_source_signature
_resolve_submission_source_path = chunk_02._resolve_submission_source_path
_hash_file_bytes = chunk_02._hash_file_bytes
CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS = chunk_02.CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS
CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS = chunk_02.CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS
_submission_source_relative_paths = chunk_02._submission_source_relative_paths
_submission_source_signature = chunk_02._submission_source_signature
_load_json_file = chunk_02._load_json_file
_normalize_projection_json_payload = chunk_02._normalize_projection_json_payload
_submission_projection_file_matches_source = chunk_02._submission_projection_file_matches_source
_submission_projection_matches_source = chunk_02._submission_projection_matches_source
build_draft_handoff_readme = chunk_02.build_draft_handoff_readme
describe_draft_handoff_delivery = chunk_02.describe_draft_handoff_delivery
describe_submission_delivery = chunk_02.describe_submission_delivery
materialize_submission_delivery_stale_notice = chunk_02.materialize_submission_delivery_stale_notice
sync_draft_handoff_delivery = chunk_03.sync_draft_handoff_delivery
sync_general_delivery = chunk_03.sync_general_delivery
sync_journal_specific_delivery = chunk_03.sync_journal_specific_delivery
sync_promoted_journal_delivery = chunk_03.sync_promoted_journal_delivery
sync_study_delivery = chunk_03.sync_study_delivery
parse_args = chunk_03.parse_args
main = chunk_03.main

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
