"""Stable candidate-admission policy values shared by the handler parts."""

REQUEST_KIND = "mas_candidate_admission_authority_request"
RESULT_KIND = "mas_candidate_admission_authority_result"
SCHEMA_VERSION = 2

_HARD_GATE_KINDS = frozenset(
    {
        "medical_safety",
        "source_identity",
        "source_currentness",
        "domain_authority",
        "credential",
        "irreversible_action",
    }
)
_CLAIM_CLASSES = {
    "primary",
    "secondary",
    "post_hoc",
    "exploratory",
    "descriptive",
    "sensitivity",
    "supplementary_only",
    "provenance_only",
}
_MANUSCRIPT_SECTIONS = {
    "abstract",
    "methods",
    "results",
    "discussion",
    "table",
    "figure",
    "supplement",
    "citation_ledger",
    "numeric_trace",
}
_ACCEPT_CODES = {
    "accepted_for_exact_claim_scope",
    "accepted_for_bounded_sensitivity_use",
}
_REJECT_CODES = {
    "rejected_out_of_scope",
    "rejected_unsupported_evidence",
    "rejected_superseded_source",
    "rejected_provenance_only",
}
_ROUTE_CODES = {
    "candidate_evidence_incomplete",
    "candidate_manifest_membership_required",
    "claim_scope_revision_required",
    "source_input_currentness_required",
    "adjudicator_receipt_revision_required",
}
_WAIVER_CODES = {
    "waived_non_material_candidate_gap",
    "waived_duplicate_evidence_record",
    "waived_provenance_only",
}
_ALL_DECISION_CODES = (
    _ACCEPT_CODES | _REJECT_CODES | _ROUTE_CODES | {"waived_with_typed_scope"}
)
_AUTHORITY_BOUNDARY = {
    "owner": "MedAutoScience",
    "handler_role": "validate_manifest_bound_mas_adjudicator_receipt_and_return_exact_authority_result",
    "opl_role": "verify_exact_ref_bytes_inject_typed_records_and_persist_exact_result_bytes",
    "host_proposal_can_authorize_candidate": False,
    "program_originates_medical_acceptance_verdict": False,
    "provider_completion_counts_as_candidate_acceptance": False,
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "spawns_process_or_executor": False,
    "owns_runtime_or_attempt_lifecycle": False,
    "authorizes_publication_or_submission": False,
}
