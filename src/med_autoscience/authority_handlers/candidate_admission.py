"""Adjudicate one manifest-bound candidate before manuscript consumption."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._generation_manifest import (
    normalize_generation_manifest,
    source_input_digest,
)
from ._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_text,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)


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


def evaluate_candidate_admission_authority(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deterministic result only for a current MAS adjudicator receipt."""

    try:
        normalized = _normalize_request(request)
    except RequestShapeError as error:
        return _invalid_host_input(str(error))

    currentness_issue = _currentness_issue(normalized)
    if currentness_issue is not None:
        return _finalize(
            normalized,
            status="typed_blocker",
            typed_blocker=currentness_issue,
        )

    gate = normalized["hard_gate"]
    if gate["kind"] == "human_decision":
        return _finalize(
            normalized,
            status="human_gate",
            human_gate=_human_gate(normalized),
        )
    if gate["kind"] in _HARD_GATE_KINDS:
        return _finalize(
            normalized,
            status="typed_blocker",
            typed_blocker=_typed_blocker(normalized),
        )

    identity_admission = _clinical_identity_admission_result(normalized)
    if identity_admission is not None:
        return identity_admission

    verdict = normalized["adjudicator_receipt"]["verdict"]
    if verdict == "route_back":
        return _finalize(
            normalized,
            status="route_back",
            route_back=_route_back(normalized),
        )
    if verdict == "waived":
        return _finalize(
            normalized,
            status="waived",
            waiver=_waiver_result(normalized),
        )
    return _finalize(
        normalized,
        status=verdict,
        disposition_receipt=_disposition_receipt(normalized),
    )


def normalize_candidate_admission_receipt(
    value: Any,
    field: str = "candidate_admission_receipt",
) -> dict[str, Any]:
    """Validate an exact accepted/rejected receipt for downstream consumption."""

    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "mission_identity",
            "adjudicator_refs",
            "currentness_receipt_ref",
            "authority_epoch",
            "generation_id",
            "generation_manifest_ref",
            "source_input_digest",
            "candidate_id",
            "candidate_ref",
            "candidate_size_bytes",
            "evidence_refs",
            "claim_scope",
            "disposition",
            "decision_code",
            "authorizes_manuscript_consumption",
            "authorizes_publication_or_submission",
            "requires_host_exact_byte_persistence",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_candidate_admission_receipt":
        raise RequestShapeError(
            f"{field}.receipt_kind must be mas_candidate_admission_receipt"
        )
    if payload.get("schema_version") != 2 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 2")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")

    disposition = enum_text(
        payload.get("disposition"), f"{field}.disposition", {"accepted", "rejected"}
    )
    decision_code = enum_text(
        payload.get("decision_code"),
        f"{field}.decision_code",
        _ACCEPT_CODES | _REJECT_CODES,
    )
    if disposition == "accepted" and decision_code not in _ACCEPT_CODES:
        raise RequestShapeError(f"{field}.decision_code is not an acceptance code")
    if disposition == "rejected" and decision_code not in _REJECT_CODES:
        raise RequestShapeError(f"{field}.decision_code is not a rejection code")
    expected_authorization = disposition == "accepted"
    if payload.get("authorizes_manuscript_consumption") is not expected_authorization:
        raise RequestShapeError(
            f"{field}.authorizes_manuscript_consumption does not match disposition"
        )
    if payload.get("authorizes_publication_or_submission") is not False:
        raise RequestShapeError(
            f"{field}.authorizes_publication_or_submission must be false"
        )
    if payload.get("requires_host_exact_byte_persistence") is not True:
        raise RequestShapeError(
            f"{field}.requires_host_exact_byte_persistence must be true"
        )

    core = {
        "receipt_kind": "mas_candidate_admission_receipt",
        "schema_version": 2,
        "owner": "MedAutoScience",
        "mission_identity": _normalize_mission(
            payload.get("mission_identity"), f"{field}.mission_identity"
        ),
        "adjudicator_refs": _normalize_adjudicator_refs(
            payload.get("adjudicator_refs"), f"{field}.adjudicator_refs"
        ),
        "currentness_receipt_ref": _exact_ref(
            payload.get("currentness_receipt_ref"),
            f"{field}.currentness_receipt_ref",
            "mas_generation_currentness_receipt",
        ),
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{field}.authority_epoch"
        ),
        "generation_id": text(payload.get("generation_id"), f"{field}.generation_id"),
        "generation_manifest_ref": _exact_ref(
            payload.get("generation_manifest_ref"),
            f"{field}.generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "source_input_digest": _normalize_manifest_member(
            payload.get("source_input_digest"),
            f"{field}.source_input_digest",
            expected_kind="mas_artifact",
            expected_role="source_input_digest",
        ),
        "candidate_id": text(payload.get("candidate_id"), f"{field}.candidate_id"),
        "candidate_ref": _exact_ref(
            payload.get("candidate_ref"),
            f"{field}.candidate_ref",
            "mas_artifact",
        ),
        "candidate_size_bytes": integer(
            payload.get("candidate_size_bytes"), f"{field}.candidate_size_bytes"
        ),
        "evidence_refs": _exact_ref_list(
            payload.get("evidence_refs"),
            f"{field}.evidence_refs",
            "mas_evidence",
            dedupe_size=False,
        ),
        "claim_scope": _normalize_claim_scope(
            payload.get("claim_scope"), f"{field}.claim_scope"
        ),
        "disposition": disposition,
        "decision_code": decision_code,
        "authorizes_manuscript_consumption": expected_authorization,
        "authorizes_publication_or_submission": False,
        "requires_host_exact_byte_persistence": True,
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    if core["candidate_size_bytes"] != core["candidate_ref"]["size_bytes"]:
        raise RequestShapeError(
            f"{field}.candidate_size_bytes does not match candidate_ref"
        )
    receipt_id = text(payload.get("receipt_id"), f"{field}.receipt_id")
    if (
        receipt_id
        != f"mas-candidate-admission:{expected_fingerprint.removeprefix('sha256:')}"
    ):
        raise RequestShapeError(f"{field}.receipt_id does not match canonical receipt")
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_size_bytes does not match canonical receipt"
        )
    if (
        sha256(payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint")
        != expected_fingerprint
    ):
        raise RequestShapeError(
            f"{field}.receipt_fingerprint does not match canonical receipt"
        )
    return {
        **core,
        "receipt_id": receipt_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = mapping(request, "request")
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "adjudicator_context",
            "mission",
            "generation_manifest",
            "generation_manifest_ref",
            "currentness_receipt",
            "candidate",
            "adjudicator_receipt",
            "hard_gate",
        },
        "request",
    )
    if payload.get("surface_kind") != REQUEST_KIND:
        raise RequestShapeError(f"surface_kind must be {REQUEST_KIND}")
    if payload.get("schema_version") != SCHEMA_VERSION or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("schema_version must be integer 2")

    context = _normalize_adjudicator_context(payload.get("adjudicator_context"))
    manifest = normalize_generation_manifest(payload.get("generation_manifest"))
    if manifest["manifest_scope"] != "analysis_generation":
        raise RequestShapeError(
            "candidate admission requires an analysis_generation manifest"
        )
    if manifest["independent_review_receipts"]:
        raise RequestShapeError(
            "candidate admission manifest cannot carry downstream review receipts"
        )
    manifest_ref = _exact_ref(
        payload.get("generation_manifest_ref"),
        "generation_manifest_ref",
        "mas_generation_manifest",
    )
    if (
        manifest_ref["sha256"] != manifest["generation_manifest_sha256"]
        or manifest_ref["size_bytes"] != manifest["generation_manifest_size_bytes"]
    ):
        raise RequestShapeError(
            "generation_manifest_ref size/hash does not match canonical manifest"
        )
    candidate = _normalize_candidate(payload.get("candidate"))
    _validate_manifest_membership(manifest, candidate)
    currentness = _normalize_currentness_receipt(payload.get("currentness_receipt"))
    adjudicator = _normalize_adjudicator_receipt(payload.get("adjudicator_receipt"))

    normalized = {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "adjudicator_context": context,
        "mission": _normalize_mission(payload.get("mission"), "mission"),
        "generation_manifest": manifest,
        "generation_manifest_ref": manifest_ref,
        "currentness_receipt": currentness,
        "candidate": candidate,
        "adjudicator_receipt": adjudicator,
        "hard_gate": _normalize_hard_gate(payload.get("hard_gate")),
    }
    _validate_currentness_receipt_ref(normalized)
    _validate_adjudicator_receipt(normalized)
    return normalized


def _normalize_adjudicator_context(value: Any) -> dict[str, Any]:
    field = "adjudicator_context"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "producer_attempt_ref",
            "adjudicator_attempt_ref",
            "candidate_packet_ref",
            "admission_request_ref",
            "adjudicator_receipt_ref",
            "currentness_receipt_ref",
        },
        field,
    )
    normalized = {
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            f"{field}.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "adjudicator_attempt_ref": _typed_ref(
            payload.get("adjudicator_attempt_ref"),
            f"{field}.adjudicator_attempt_ref",
            "opl_stage_attempt",
        ),
        "candidate_packet_ref": _exact_ref(
            payload.get("candidate_packet_ref"),
            f"{field}.candidate_packet_ref",
            "opl_action_output",
        ),
        "admission_request_ref": _exact_ref(
            payload.get("admission_request_ref"),
            f"{field}.admission_request_ref",
            "opl_action_output",
        ),
        "adjudicator_receipt_ref": _exact_ref(
            payload.get("adjudicator_receipt_ref"),
            f"{field}.adjudicator_receipt_ref",
            "mas_candidate_adjudicator_receipt",
        ),
        "currentness_receipt_ref": _exact_ref(
            payload.get("currentness_receipt_ref"),
            f"{field}.currentness_receipt_ref",
            "mas_generation_currentness_receipt",
        ),
    }
    if (
        normalized["producer_attempt_ref"]["ref"]
        == normalized["adjudicator_attempt_ref"]["ref"]
        or normalized["producer_attempt_ref"]["sha256"]
        == normalized["adjudicator_attempt_ref"]["sha256"]
    ):
        raise RequestShapeError(
            "adjudicator attempt must be independent from the candidate producer attempt"
        )
    return normalized


def _normalize_mission(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"program_id", "study_id", "mission_id", "stage_id", "stage_goal_ref"},
        field,
    )
    return {
        "program_id": text(payload.get("program_id"), f"{field}.program_id"),
        "study_id": text(payload.get("study_id"), f"{field}.study_id"),
        "mission_id": text(payload.get("mission_id"), f"{field}.mission_id"),
        "stage_id": text(payload.get("stage_id"), f"{field}.stage_id"),
        "stage_goal_ref": _typed_ref(
            payload.get("stage_goal_ref"), f"{field}.stage_goal_ref", "mas_stage_goal"
        ),
    }


def _normalize_candidate(value: Any) -> dict[str, Any]:
    field = "candidate"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"candidate_id", "candidate_member", "evidence_members", "claim_scope"},
        field,
    )
    evidence = [
        _normalize_manifest_member(
            item,
            f"{field}.evidence_members[{index}]",
            expected_kind="mas_evidence",
            expected_role="evidence_record",
        )
        for index, item in enumerate(
            sequence(payload.get("evidence_members"), f"{field}.evidence_members")
        )
    ]
    identities = [(item["ref"], item["sha256"]) for item in evidence]
    if not evidence:
        raise RequestShapeError("candidate.evidence_members must not be empty")
    if len(identities) != len(set(identities)):
        raise RequestShapeError("candidate.evidence_members contains duplicates")
    return {
        "candidate_id": text(payload.get("candidate_id"), "candidate.candidate_id"),
        "candidate_member": _normalize_manifest_member(
            payload.get("candidate_member"),
            "candidate.candidate_member",
            expected_kind="mas_artifact",
            expected_role="candidate_artifact",
        ),
        "evidence_members": evidence,
        "claim_scope": _normalize_claim_scope(
            payload.get("claim_scope"), "candidate.claim_scope"
        ),
    }


def _normalize_claim_scope(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "claim_classes",
            "claim_ids",
            "permitted_sections",
            "required_disclosures",
            "prohibited_claims",
            "sensitivity_only",
            "supplementary_only",
            "abstract_headline_allowed",
        },
        field,
    )
    classes = [
        enum_text(item, f"{field}.claim_classes[{index}]", _CLAIM_CLASSES)
        for index, item in enumerate(
            sequence(payload.get("claim_classes"), f"{field}.claim_classes")
        )
    ]
    sections = [
        enum_text(item, f"{field}.permitted_sections[{index}]", _MANUSCRIPT_SECTIONS)
        for index, item in enumerate(
            sequence(payload.get("permitted_sections"), f"{field}.permitted_sections")
        )
    ]
    if not classes or len(classes) != len(set(classes)):
        raise RequestShapeError(f"{field}.claim_classes must be non-empty and unique")
    if len(sections) != len(set(sections)):
        raise RequestShapeError(f"{field}.permitted_sections contains duplicates")
    booleans: dict[str, bool] = {}
    for name in (
        "sensitivity_only",
        "supplementary_only",
        "abstract_headline_allowed",
    ):
        current = payload.get(name)
        if not isinstance(current, bool):
            raise RequestShapeError(f"{field}.{name} must be boolean")
        booleans[name] = current
    return {
        "claim_classes": classes,
        "claim_ids": text_list(payload.get("claim_ids"), f"{field}.claim_ids"),
        "permitted_sections": sections,
        "required_disclosures": text_list(
            payload.get("required_disclosures"), f"{field}.required_disclosures"
        ),
        "prohibited_claims": text_list(
            payload.get("prohibited_claims"), f"{field}.prohibited_claims"
        ),
        **booleans,
    }


def _normalize_manifest_member(
    value: Any,
    field: str,
    *,
    expected_kind: str,
    expected_role: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"kind", "role", "ref", "size_bytes", "sha256"}, field)
    kind = text(payload.get("kind"), f"{field}.kind")
    if kind != expected_kind:
        raise RequestShapeError(f"{field}.kind must be {expected_kind}")
    role = text(payload.get("role"), f"{field}.role")
    if role != expected_role:
        raise RequestShapeError(f"{field}.role must be {expected_role}")
    return {
        "kind": kind,
        "role": role,
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }


def _validate_manifest_membership(
    manifest: Mapping[str, Any], candidate: Mapping[str, Any]
) -> None:
    inventory = {
        (item["role"], item["ref"], item["size_bytes"], item["sha256"])
        for item in manifest["artifacts"]
    }
    members = [candidate["candidate_member"], *candidate["evidence_members"]]
    missing = [
        item["ref"]
        for item in members
        if (item["role"], item["ref"], item["size_bytes"], item["sha256"])
        not in inventory
    ]
    if missing:
        raise RequestShapeError(
            "candidate members are absent from the exact generation manifest: "
            + ", ".join(missing)
        )


def _normalize_currentness_receipt(value: Any) -> dict[str, Any]:
    field = "currentness_receipt"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_epoch",
            "current_generation_id",
            "authority_role",
            "current_generation_manifest_ref",
            "current_admission_request_ref",
            "current_adjudicator_receipt_ref",
            "superseded_generation_ids",
            "superseded_request_refs",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_generation_currentness_receipt":
        raise RequestShapeError(
            "currentness_receipt.receipt_kind must be mas_generation_currentness_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("currentness_receipt.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError("currentness_receipt.owner must be MedAutoScience")
    if payload.get("authority_role") != "generation_currentness_owner":
        raise RequestShapeError(
            "currentness_receipt.authority_role must be generation_currentness_owner"
        )
    generations = text_list(
        payload.get("superseded_generation_ids"),
        "currentness_receipt.superseded_generation_ids",
    )
    superseded_refs = _exact_ref_list(
        payload.get("superseded_request_refs"),
        "currentness_receipt.superseded_request_refs",
        "opl_action_output",
        dedupe_size=False,
    )
    core = {
        "receipt_kind": "mas_generation_currentness_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "generation_currentness_owner",
        "authority_epoch": text(
            payload.get("authority_epoch"), "currentness_receipt.authority_epoch"
        ),
        "current_generation_id": text(
            payload.get("current_generation_id"),
            "currentness_receipt.current_generation_id",
        ),
        "current_generation_manifest_ref": _exact_ref(
            payload.get("current_generation_manifest_ref"),
            "currentness_receipt.current_generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "current_admission_request_ref": _exact_ref(
            payload.get("current_admission_request_ref"),
            "currentness_receipt.current_admission_request_ref",
            "opl_action_output",
        ),
        "current_adjudicator_receipt_ref": _exact_ref(
            payload.get("current_adjudicator_receipt_ref"),
            "currentness_receipt.current_adjudicator_receipt_ref",
            "mas_candidate_adjudicator_receipt",
        ),
        "superseded_generation_ids": generations,
        "superseded_request_refs": superseded_refs,
    }
    return _validate_embedded_receipt(
        payload,
        core,
        field=field,
        id_prefix="mas-generation-currentness",
    )


def _normalize_adjudicator_receipt(value: Any) -> dict[str, Any]:
    field = "adjudicator_receipt"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_role",
            "authority_epoch",
            "producer_attempt_ref",
            "adjudicator_attempt_ref",
            "candidate_packet_ref",
            "admission_request_ref",
            "generation_id",
            "generation_manifest_ref",
            "candidate_id",
            "candidate_ref",
            "evidence_refs",
            "claim_scope",
            "candidate_record_sha256",
            "verdict",
            "decision_code",
            "next_owner",
            "resume_condition",
            "waiver",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_candidate_adjudicator_receipt":
        raise RequestShapeError(
            "adjudicator_receipt.receipt_kind must be mas_candidate_adjudicator_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("adjudicator_receipt.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError("adjudicator_receipt.owner must be MedAutoScience")
    if payload.get("authority_role") != "independent_medical_adjudicator":
        raise RequestShapeError(
            "adjudicator_receipt.authority_role must be independent_medical_adjudicator"
        )
    verdict = enum_text(
        payload.get("verdict"),
        "adjudicator_receipt.verdict",
        {"accepted", "rejected", "route_back", "waived"},
    )
    decision_code = enum_text(
        payload.get("decision_code"),
        "adjudicator_receipt.decision_code",
        _ALL_DECISION_CODES,
    )
    next_owner = optional_text(
        payload.get("next_owner"), "adjudicator_receipt.next_owner"
    )
    resume_condition = optional_text(
        payload.get("resume_condition"), "adjudicator_receipt.resume_condition"
    )
    waiver = _normalize_waiver(payload.get("waiver"), "adjudicator_receipt.waiver")
    if verdict == "accepted" and decision_code not in _ACCEPT_CODES:
        raise RequestShapeError(
            "accepted adjudicator receipt requires an acceptance code"
        )
    if verdict == "rejected" and decision_code not in _REJECT_CODES:
        raise RequestShapeError(
            "rejected adjudicator receipt requires a rejection code"
        )
    if verdict == "route_back" and decision_code not in _ROUTE_CODES:
        raise RequestShapeError(
            "route-back adjudicator receipt requires a typed route code"
        )
    if verdict == "waived" and decision_code != "waived_with_typed_scope":
        raise RequestShapeError(
            "waived adjudicator receipt requires waived_with_typed_scope"
        )
    if verdict == "route_back":
        if next_owner is None or resume_condition is None or waiver is not None:
            raise RequestShapeError(
                "route-back adjudicator receipt requires next_owner/resume_condition and no waiver"
            )
    elif verdict == "waived":
        if waiver is None or next_owner is not None or resume_condition is not None:
            raise RequestShapeError(
                "waived adjudicator receipt requires one typed waiver and no route fields"
            )
    elif any(
        (next_owner is not None, resume_condition is not None, waiver is not None)
    ):
        raise RequestShapeError(
            "accepted/rejected adjudicator receipt cannot carry route or waiver fields"
        )
    core = {
        "receipt_kind": "mas_candidate_adjudicator_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "independent_medical_adjudicator",
        "authority_epoch": text(
            payload.get("authority_epoch"), "adjudicator_receipt.authority_epoch"
        ),
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            "adjudicator_receipt.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "adjudicator_attempt_ref": _typed_ref(
            payload.get("adjudicator_attempt_ref"),
            "adjudicator_receipt.adjudicator_attempt_ref",
            "opl_stage_attempt",
        ),
        "candidate_packet_ref": _exact_ref(
            payload.get("candidate_packet_ref"),
            "adjudicator_receipt.candidate_packet_ref",
            "opl_action_output",
        ),
        "admission_request_ref": _exact_ref(
            payload.get("admission_request_ref"),
            "adjudicator_receipt.admission_request_ref",
            "opl_action_output",
        ),
        "generation_id": text(
            payload.get("generation_id"), "adjudicator_receipt.generation_id"
        ),
        "generation_manifest_ref": _exact_ref(
            payload.get("generation_manifest_ref"),
            "adjudicator_receipt.generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "candidate_id": text(
            payload.get("candidate_id"), "adjudicator_receipt.candidate_id"
        ),
        "candidate_ref": _exact_ref(
            payload.get("candidate_ref"),
            "adjudicator_receipt.candidate_ref",
            "mas_artifact",
        ),
        "evidence_refs": _exact_ref_list(
            payload.get("evidence_refs"),
            "adjudicator_receipt.evidence_refs",
            "mas_evidence",
            dedupe_size=False,
        ),
        "claim_scope": _normalize_claim_scope(
            payload.get("claim_scope"), "adjudicator_receipt.claim_scope"
        ),
        "candidate_record_sha256": sha256(
            payload.get("candidate_record_sha256"),
            "adjudicator_receipt.candidate_record_sha256",
        ),
        "verdict": verdict,
        "decision_code": decision_code,
        "next_owner": next_owner,
        "resume_condition": resume_condition,
        "waiver": waiver,
    }
    return _validate_embedded_receipt(
        payload,
        core,
        field=field,
        id_prefix="mas-candidate-adjudicator",
    )


def _normalize_waiver(value: Any, field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "waiver_kind",
            "waiver_code",
            "scope",
            "evidence_refs",
            "expires_on_generation_change",
            "authorizes_manuscript_consumption",
        },
        field,
    )
    if payload.get("waiver_kind") != "mas_candidate_admission_waiver":
        raise RequestShapeError(
            f"{field}.waiver_kind must be mas_candidate_admission_waiver"
        )
    if payload.get("expires_on_generation_change") is not True:
        raise RequestShapeError(f"{field}.expires_on_generation_change must be true")
    if payload.get("authorizes_manuscript_consumption") is not False:
        raise RequestShapeError(
            f"{field}.authorizes_manuscript_consumption must be false"
        )
    refs = _typed_ref_list(
        payload.get("evidence_refs"), f"{field}.evidence_refs", "mas_evidence"
    )
    if not refs:
        raise RequestShapeError(f"{field}.evidence_refs must not be empty")
    return {
        "waiver_kind": "mas_candidate_admission_waiver",
        "waiver_code": enum_text(
            payload.get("waiver_code"), f"{field}.waiver_code", _WAIVER_CODES
        ),
        "scope": enum_text(
            payload.get("scope"),
            f"{field}.scope",
            {"candidate_record_only", "provenance_only", "quality_debt_only"},
        ),
        "evidence_refs": refs,
        "expires_on_generation_change": True,
        "authorizes_manuscript_consumption": False,
    }


def _validate_embedded_receipt(
    payload: Mapping[str, Any],
    core: dict[str, Any],
    *,
    field: str,
    id_prefix: str,
) -> dict[str, Any]:
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = f"{id_prefix}:{expected_fingerprint.removeprefix('sha256:')}"
    if text(payload.get("receipt_id"), f"{field}.receipt_id") != expected_id:
        raise RequestShapeError(f"{field}.receipt_id does not match canonical receipt")
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_size_bytes does not match canonical receipt"
        )
    if (
        sha256(payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint")
        != expected_fingerprint
    ):
        raise RequestShapeError(
            f"{field}.receipt_fingerprint does not match canonical receipt"
        )
    return {
        **core,
        "receipt_id": expected_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _validate_currentness_receipt_ref(request: Mapping[str, Any]) -> None:
    receipt = request["currentness_receipt"]
    receipt_ref = request["adjudicator_context"]["currentness_receipt_ref"]
    if (
        receipt_ref["ref"] != receipt["receipt_id"]
        or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
        or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
    ):
        raise RequestShapeError(
            "currentness_receipt_ref size/hash does not match currentness_receipt"
        )
    if (
        receipt["current_adjudicator_receipt_ref"]
        != request["adjudicator_context"]["adjudicator_receipt_ref"]
    ):
        raise RequestShapeError(
            "currentness_receipt does not authorize the supplied adjudicator receipt"
        )


def _validate_adjudicator_receipt(request: Mapping[str, Any]) -> None:
    context = request["adjudicator_context"]
    manifest = request["generation_manifest"]
    currentness = request["currentness_receipt"]
    candidate = request["candidate"]
    receipt = request["adjudicator_receipt"]
    receipt_ref = context["adjudicator_receipt_ref"]
    if (
        receipt_ref["ref"] != receipt["receipt_id"]
        or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
        or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
    ):
        raise RequestShapeError(
            "adjudicator_receipt_ref size/hash does not match adjudicator_receipt"
        )
    comparisons = {
        "authority_epoch": (
            receipt["authority_epoch"],
            currentness["authority_epoch"],
        ),
        "adjudicator_attempt_ref": (
            receipt["adjudicator_attempt_ref"],
            context["adjudicator_attempt_ref"],
        ),
        "producer_attempt_ref": (
            receipt["producer_attempt_ref"],
            context["producer_attempt_ref"],
        ),
        "candidate_packet_ref": (
            receipt["candidate_packet_ref"],
            context["candidate_packet_ref"],
        ),
        "admission_request_ref": (
            receipt["admission_request_ref"],
            context["admission_request_ref"],
        ),
        "generation_id": (receipt["generation_id"], manifest["generation_id"]),
        "generation_manifest_ref": (
            receipt["generation_manifest_ref"],
            request["generation_manifest_ref"],
        ),
        "candidate_id": (
            receipt["candidate_id"],
            candidate["candidate_id"],
        ),
        "candidate_ref": (
            receipt["candidate_ref"],
            _candidate_exact_ref(candidate),
        ),
        "evidence_refs": (
            receipt["evidence_refs"],
            [
                {
                    "kind": item["kind"],
                    "ref": item["ref"],
                    "size_bytes": item["size_bytes"],
                    "sha256": item["sha256"],
                }
                for item in candidate["evidence_members"]
            ],
        ),
        "claim_scope": (
            receipt["claim_scope"],
            candidate["claim_scope"],
        ),
        "candidate_record_sha256": (
            receipt["candidate_record_sha256"],
            fingerprint(candidate),
        ),
    }
    mismatches = [name for name, (left, right) in comparisons.items() if left != right]
    if mismatches:
        raise RequestShapeError(
            "adjudicator_receipt is not bound to current exact records: "
            + ", ".join(mismatches)
        )
    if receipt["verdict"] == "accepted":
        scope = candidate["claim_scope"]
        if not scope["claim_ids"] or not scope["permitted_sections"]:
            raise RequestShapeError(
                "accepted adjudicator receipt requires claim_ids and permitted_sections"
            )
        if (
            receipt["decision_code"] == "accepted_for_bounded_sensitivity_use"
            and not scope["sensitivity_only"]
        ):
            raise RequestShapeError(
                "bounded-sensitivity acceptance requires sensitivity_only claim scope"
            )
        if scope["sensitivity_only"] and scope["abstract_headline_allowed"]:
            raise RequestShapeError(
                "sensitivity-only claim scope cannot allow an abstract headline"
            )


def _currentness_issue(request: Mapping[str, Any]) -> dict[str, Any] | None:
    context = request["adjudicator_context"]
    manifest = request["generation_manifest"]
    currentness = request["currentness_receipt"]
    request_identity = (
        context["admission_request_ref"]["ref"],
        context["admission_request_ref"]["size_bytes"],
        context["admission_request_ref"]["sha256"],
    )
    superseded_requests = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in currentness["superseded_request_refs"]
    }
    stale = any(
        (
            currentness["current_generation_id"] != manifest["generation_id"],
            currentness["current_generation_manifest_ref"]
            != request["generation_manifest_ref"],
            currentness["current_admission_request_ref"]
            != context["admission_request_ref"],
            manifest["generation_id"] in currentness["superseded_generation_ids"],
            request_identity in superseded_requests,
        )
    )
    if not stale:
        return None
    return {
        "gate_kind": "source_currentness",
        "reason_code": "superseded_candidate_admission_request",
        "evidence_refs": [
            {
                "kind": context["currentness_receipt_ref"]["kind"],
                "ref": context["currentness_receipt_ref"]["ref"],
                "sha256": context["currentness_receipt_ref"]["sha256"],
            }
        ],
        "next_owner": "mas_generation_currentness_owner",
        "resume_condition": (
            "supply the current generation, admission request, and fresh MAS adjudicator receipt"
        ),
        "authorizes_manuscript_consumption": False,
        "requires_host_exact_byte_persistence": True,
    }


def _disposition_receipt(request: Mapping[str, Any]) -> dict[str, Any]:
    candidate = request["candidate"]
    member = candidate["candidate_member"]
    adjudicator = request["adjudicator_receipt"]
    source = source_input_digest(request["generation_manifest"])
    core = {
        "receipt_kind": "mas_candidate_admission_receipt",
        "schema_version": 2,
        "owner": "MedAutoScience",
        "mission_identity": dict(request["mission"]),
        "adjudicator_refs": _adjudicator_refs(request),
        "currentness_receipt_ref": dict(
            request["adjudicator_context"]["currentness_receipt_ref"]
        ),
        "authority_epoch": request["currentness_receipt"]["authority_epoch"],
        "generation_id": request["generation_manifest"]["generation_id"],
        "generation_manifest_ref": dict(request["generation_manifest_ref"]),
        "source_input_digest": {
            "kind": "mas_artifact",
            **source,
        },
        "candidate_id": candidate["candidate_id"],
        "candidate_ref": {
            "kind": member["kind"],
            "ref": member["ref"],
            "size_bytes": member["size_bytes"],
            "sha256": member["sha256"],
        },
        "candidate_size_bytes": member["size_bytes"],
        "evidence_refs": [
            {
                "kind": item["kind"],
                "ref": item["ref"],
                "size_bytes": item["size_bytes"],
                "sha256": item["sha256"],
            }
            for item in candidate["evidence_members"]
        ],
        "claim_scope": dict(candidate["claim_scope"]),
        "disposition": adjudicator["verdict"],
        "decision_code": adjudicator["decision_code"],
        "authorizes_manuscript_consumption": adjudicator["verdict"] == "accepted",
        "authorizes_publication_or_submission": False,
        "requires_host_exact_byte_persistence": True,
    }
    receipt_fingerprint = fingerprint(core)
    return {
        **core,
        "receipt_id": (
            f"mas-candidate-admission:{receipt_fingerprint.removeprefix('sha256:')}"
        ),
        "receipt_size_bytes": len(canonical_json_bytes(core)),
        "receipt_fingerprint": receipt_fingerprint,
    }


def _route_back(request: Mapping[str, Any]) -> dict[str, Any]:
    candidate = request["candidate"]
    adjudicator = request["adjudicator_receipt"]
    return {
        "route_code": adjudicator["decision_code"],
        "candidate_id": candidate["candidate_id"],
        "candidate_ref": _candidate_exact_ref(candidate),
        "next_owner": adjudicator["next_owner"],
        "resume_condition": adjudicator["resume_condition"],
        "authorizes_manuscript_consumption": False,
        "requires_host_exact_byte_persistence": True,
    }


def _clinical_identity_admission_result(
    request: Mapping[str, Any],
) -> dict[str, Any] | None:
    manifest = request["generation_manifest"]
    if manifest["schema_version"] != 2:
        return None
    admission = manifest.get("clinical_analysis_identity_admission")
    if admission is None:
        if not any(
            item["role"] == "clinical_analysis_input_identity"
            for item in manifest["artifacts"]
        ):
            return None
        return _finalize(
            request,
            status="route_back",
            route_back={
                "route_code": "candidate_evidence_incomplete",
                "candidate_id": request["candidate"]["candidate_id"],
                "candidate_ref": _candidate_exact_ref(request["candidate"]),
                "next_owner": "baseline_and_evidence_setup",
                "resume_condition": (
                    "materialize and adjudicate the exact clinical analysis input "
                    "identity before candidate admission"
                ),
                "authorizes_manuscript_consumption": False,
                "requires_host_exact_byte_persistence": True,
            },
        )
    if admission["status"] == "adjudicator_required":
        return None
    reason_code = admission["reason_codes"][0]
    resume_condition = "; ".join(admission["unresolved_items"])
    if admission["status"] == "open_human_gate":
        return _finalize(
            request,
            status="human_gate",
            human_gate={
                "gate_kind": "human_decision",
                "reason_code": reason_code,
                "evidence_refs": list(admission["human_gate_refs"]),
                "next_owner": admission["next_owner"],
                "resume_condition": resume_condition,
                "authorizes_manuscript_consumption": False,
                "requires_host_exact_byte_persistence": True,
            },
        )
    return _finalize(
        request,
        status="route_back",
        route_back={
            "route_code": "candidate_evidence_incomplete",
            "candidate_id": request["candidate"]["candidate_id"],
            "candidate_ref": _candidate_exact_ref(request["candidate"]),
            "next_owner": admission["next_owner"],
            "resume_condition": resume_condition,
            "authorizes_manuscript_consumption": False,
            "requires_host_exact_byte_persistence": True,
        },
    )


def _waiver_result(request: Mapping[str, Any]) -> dict[str, Any]:
    candidate = request["candidate"]
    waiver = request["adjudicator_receipt"]["waiver"]
    return {
        **dict(waiver),
        "candidate_id": candidate["candidate_id"],
        "candidate_ref": _candidate_exact_ref(candidate),
        "requires_host_exact_byte_persistence": True,
    }


def _typed_blocker(request: Mapping[str, Any]) -> dict[str, Any]:
    gate = request["hard_gate"]
    return {
        "gate_kind": gate["kind"],
        "reason_code": gate["reason_code"],
        "evidence_refs": list(gate["evidence_refs"]),
        "next_owner": gate["next_owner"],
        "resume_condition": gate["resume_condition"],
        "authorizes_manuscript_consumption": False,
        "requires_host_exact_byte_persistence": True,
    }


def _human_gate(request: Mapping[str, Any]) -> dict[str, Any]:
    gate = request["hard_gate"]
    return {
        "gate_kind": "human_decision",
        "reason_code": gate["reason_code"],
        "evidence_refs": list(gate["evidence_refs"]),
        "next_owner": gate["next_owner"],
        "resume_condition": gate["resume_condition"],
        "authorizes_manuscript_consumption": False,
        "requires_host_exact_byte_persistence": True,
    }


def _finalize(
    request: Mapping[str, Any],
    *,
    status: str,
    disposition_receipt: Mapping[str, Any] | None = None,
    route_back: Mapping[str, Any] | None = None,
    waiver: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    human_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "mission_identity": dict(request["mission"]),
        "generation_context": _generation_context(request),
        "candidate_ref": _candidate_exact_ref(request["candidate"]),
        "disposition_receipt": (
            dict(disposition_receipt) if disposition_receipt is not None else None
        ),
        "route_back": dict(route_back) if route_back is not None else None,
        "waiver": dict(waiver) if waiver is not None else None,
        "typed_blocker": dict(typed_blocker) if typed_blocker is not None else None,
        "human_gate": dict(human_gate) if human_gate is not None else None,
        "error": None,
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    return _with_decision_identity(core)


def _invalid_host_input(detail: str) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "invalid_host_input",
        "mission_identity": None,
        "generation_context": None,
        "candidate_ref": None,
        "disposition_receipt": None,
        "route_back": None,
        "waiver": None,
        "typed_blocker": None,
        "human_gate": None,
        "error": {"code": "invalid_host_input", "detail": detail},
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    return _with_decision_identity(core)


def _with_decision_identity(core: Mapping[str, Any]) -> dict[str, Any]:
    decision_fingerprint = fingerprint(core)
    return {
        **core,
        "decision_id": (
            f"mas-candidate-admission:{decision_fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": decision_fingerprint,
    }


def _generation_context(request: Mapping[str, Any]) -> dict[str, Any]:
    manifest = request["generation_manifest"]
    source = source_input_digest(manifest)
    return {
        "generation_id": manifest["generation_id"],
        "generation_manifest_ref": dict(request["generation_manifest_ref"]),
        "source_input_digest": {"kind": "mas_artifact", **source},
        "authority_epoch": request["currentness_receipt"]["authority_epoch"],
    }


def _candidate_exact_ref(candidate: Mapping[str, Any]) -> dict[str, Any]:
    member = candidate["candidate_member"]
    return {
        "kind": member["kind"],
        "ref": member["ref"],
        "size_bytes": member["size_bytes"],
        "sha256": member["sha256"],
    }


def _adjudicator_refs(request: Mapping[str, Any]) -> dict[str, Any]:
    context = request["adjudicator_context"]
    return {
        "producer_attempt_ref": dict(context["producer_attempt_ref"]),
        "adjudicator_attempt_ref": dict(context["adjudicator_attempt_ref"]),
        "candidate_packet_ref": dict(context["candidate_packet_ref"]),
        "admission_request_ref": dict(context["admission_request_ref"]),
        "adjudicator_receipt_ref": dict(context["adjudicator_receipt_ref"]),
    }


def _normalize_adjudicator_refs(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "producer_attempt_ref",
            "adjudicator_attempt_ref",
            "candidate_packet_ref",
            "admission_request_ref",
            "adjudicator_receipt_ref",
        },
        field,
    )
    return {
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            f"{field}.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "adjudicator_attempt_ref": _typed_ref(
            payload.get("adjudicator_attempt_ref"),
            f"{field}.adjudicator_attempt_ref",
            "opl_stage_attempt",
        ),
        "candidate_packet_ref": _exact_ref(
            payload.get("candidate_packet_ref"),
            f"{field}.candidate_packet_ref",
            "opl_action_output",
        ),
        "admission_request_ref": _exact_ref(
            payload.get("admission_request_ref"),
            f"{field}.admission_request_ref",
            "opl_action_output",
        ),
        "adjudicator_receipt_ref": _exact_ref(
            payload.get("adjudicator_receipt_ref"),
            f"{field}.adjudicator_receipt_ref",
            "mas_candidate_adjudicator_receipt",
        ),
    }


def _normalize_hard_gate(value: Any) -> dict[str, Any]:
    field = "hard_gate"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"kind", "reason_code", "evidence_refs", "next_owner", "resume_condition"},
        field,
    )
    kind = enum_text(
        payload.get("kind"),
        "hard_gate.kind",
        {"none", "human_decision", *_HARD_GATE_KINDS},
    )
    normalized = {
        "kind": kind,
        "reason_code": optional_text(
            payload.get("reason_code"), "hard_gate.reason_code"
        ),
        "evidence_refs": _typed_ref_list(
            payload.get("evidence_refs"), "hard_gate.evidence_refs", "mas_gate_evidence"
        ),
        "next_owner": optional_text(payload.get("next_owner"), "hard_gate.next_owner"),
        "resume_condition": optional_text(
            payload.get("resume_condition"), "hard_gate.resume_condition"
        ),
    }
    if kind == "none":
        if any(
            (
                normalized["reason_code"] is not None,
                bool(normalized["evidence_refs"]),
                normalized["next_owner"] is not None,
                normalized["resume_condition"] is not None,
            )
        ):
            raise RequestShapeError("hard_gate.kind none requires an empty gate record")
        return normalized
    missing = [
        name
        for name in ("reason_code", "next_owner", "resume_condition")
        if normalized[name] is None
    ]
    if not normalized["evidence_refs"]:
        missing.append("evidence_refs")
    if missing:
        raise RequestShapeError("hard gate missing: " + ", ".join(missing))
    return normalized


__all__ = [
    "evaluate_candidate_admission_authority",
    "normalize_candidate_admission_receipt",
]
