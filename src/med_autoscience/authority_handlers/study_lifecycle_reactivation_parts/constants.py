"""Shared constants for the study lifecycle reactivation authority."""

from __future__ import annotations

import re


REQUEST_KIND = "mas_study_lifecycle_reactivation_authority_request"
RESULT_KIND = "mas_study_lifecycle_reactivation_authority_result"
SCHEMA_VERSION = 1
HOST_CAPABILITY_ID = "opl_domain_artifact_cas_materialization.v1"

_LIFECYCLE_STATES = {"active", "paused", "delivered_paused", "stopped"}
_INACTIVE_STATES = {"paused", "delivered_paused", "stopped"}
_REQUIRED_TARGET_ROLES = {
    "study_lifecycle_current",
    "workspace_lifecycle_latest",
    "workspace_index",
    "submission_status",
}
_OPTIONAL_TARGET_ROLES = {
    "publication_current_package_status",
    "stage_index",
    "workspace_latest_status",
    "workspace_studies_index",
}
_PUBLIC_STAGE_ACTION_IDS = {
    "direction_and_route_selection",
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
}
_TARGET_ROLE_ORDER = (
    "study_lifecycle_current",
    "workspace_lifecycle_latest",
    "workspace_index",
    "workspace_studies_index",
    "workspace_latest_status",
    "submission_status",
    "publication_current_package_status",
    "stage_index",
)
_AUTHORITY_BOUNDARY = {
    "owner": "MedAutoScience",
    "handler_role": "authorize_exact_inactive_study_reactivation_and_cas_materialization",
    "opl_role": "persist_exact_handler_result_and_journal_all_or_rollback_authorized_json_bytes",
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "spawns_process_or_executor": False,
    "owns_runtime_or_attempt_lifecycle": False,
    "selects_scientific_stage": False,
    "authorizes_publication_or_submission": False,
    "provider_completion_is_domain_completion": False,
    "public_action": False,
}
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
