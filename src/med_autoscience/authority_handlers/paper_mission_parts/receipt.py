"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import (
    EPISTEMIC_AUTHORITY_BOUNDARY,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    REVIEW_LANE_ORDER,
    REVIEW_LANES_BY_SCOPE,
    epistemic_review_dependency_refs,
    first_draft_applicable_ref_fields,
    normalize_generation_manifest,
    require_stage_scope,
    review_scope_member_projection,
    source_input_digest,
)
from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    dedupe,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_sha256,
    optional_text,
    optional_typed_ref as _optional_typed_ref,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)
from ..candidate_admission import normalize_candidate_admission_receipt



def _owner_receipt(request: Mapping[str, Any]) -> dict[str, Any]:
    evidence = request["medical_evidence"]
    reviews = request["generation_manifest"]["independent_review_receipts"]
    currentness = request["review_authority"]["currentness_receipt"]
    selected_build_authority = request["selected_build_currentness_authority"]
    core = {
        "receipt_kind": "mas_paper_mission_owner_receipt",
        "schema_version": 3 if selected_build_authority is not None else 2,
        "owner": "MedAutoScience",
        "mission_identity": dict(request["mission"]),
        "host_refs": _host_refs(request),
        "generation_identity": _generation_identity(request),
        "review_authority_epoch": currentness["authority_epoch"],
        "review_currentness_receipt_ref": dict(
            request["review_authority"]["currentness_receipt_ref"]
        ),
        "accepted_candidate_admissions": [
            {
                "candidate_id": item["receipt"]["candidate_id"],
                "candidate_ref": dict(item["receipt"]["candidate_ref"]),
                "receipt_ref": dict(item["receipt_ref"]),
                "claim_scope": dict(item["receipt"]["claim_scope"]),
            }
            for item in request["candidate_admissions"]
        ],
        "medical_evidence_refs": list(evidence["evidence_refs"]),
        "negative_result_refs": list(evidence["negative_result_refs"]),
        "failed_path_refs": list(evidence["failed_path_refs"]),
        "artifact_lineage_refs": list(evidence["artifact_lineage_refs"]),
        "reproducibility_refs": list(evidence["reproducibility_refs"]),
        "source_readiness_receipt_ref": evidence["source_readiness_receipt_ref"],
        "claim_boundary_ref": evidence["claim_boundary_ref"],
        "professional_skill_receipt_projection": (
            _professional_skill_receipt_projection(request)
        ),
        "independent_review_receipt_refs": [
            dict(item["receipt_ref"]) for item in reviews
        ],
        "revision_consumption": _revision_consumption_projection(request),
        "verdict": "accepted_domain_delta",
        "authorizes_stage_domain_completion": True,
        "authorizes_publication_or_submission": False,
        "requires_host_exact_byte_persistence": True,
    }
    if selected_build_authority is not None:
        core["selected_build_currentness_authority_ref"] = dict(
            selected_build_authority["authority_ref"]
        )
    if request["mission"]["stage_id"] == "finalize_and_publication_handoff":
        core["artifact_projection_transport"] = _artifact_projection_transport(request)
    receipt_fingerprint = fingerprint(core)
    return {
        **core,
        "receipt_id": (
            "mas-paper-mission-owner-receipt:"
            f"{receipt_fingerprint.removeprefix('sha256:')}"
        ),
        "receipt_size_bytes": len(canonical_json_bytes(core)),
        "receipt_fingerprint": receipt_fingerprint,
    }


def _professional_skill_receipt_projection(
    request: Mapping[str, Any],
) -> list[dict[str, Any]]:
    projection = []
    for invocation in request["generation_manifest"].get(
        "professional_skill_invocations", []
    ):
        if invocation["schema_version"] != 2:
            continue
        projection.append(
            {
                "skill_id": invocation["skill_id"],
                "target_id": invocation.get("figure_id"),
                "invocation_ref": dict(invocation["invocation_ref"]),
                "receipt_ref": dict(invocation["receipt_ref"]),
            }
        )
    projection.sort(key=lambda item: (item["skill_id"], item["target_id"] or ""))
    return projection


def _revision_consumption_projection(request: Mapping[str, Any]) -> dict[str, Any]:
    binding = request["revision_consumption"]
    receipt = binding["consumption_receipt"]
    return {
        "surface_kind": "mas_revision_consumption_owner_projection",
        "schema_version": 1,
        "consumption_receipt_ref": dict(binding["consumption_receipt_ref"]),
        "applicability": receipt["applicability"],
        "revision_intake_refs": [
            dict(item) for item in receipt["revision_intake_refs"]
        ],
        "opl_review_receipt_ref": (
            dict(receipt["opl_review_receipt_ref"])
            if receipt["opl_review_receipt_ref"] is not None
            else None
        ),
        "opl_finding_lineage": (
            dict(receipt["opl_finding_lineage"])
            if receipt["opl_finding_lineage"] is not None
            else None
        ),
        "finding_closures": [dict(item) for item in receipt["finding_closures"]],
        "consumed_revision_refs": [
            dict(item) for item in receipt["consumed_revision_refs"]
        ],
        "authority_boundary": dict(receipt["authority_boundary"]),
    }


def _artifact_projection_transport(request: Mapping[str, Any]) -> dict[str, Any]:
    manifest = request["generation_manifest"]
    required_roles = (
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
        "submission_projection_manifest",
    )
    members = {
        role: next(item for item in manifest["artifacts"] if item["role"] == role)
        for role in required_roles
    }
    return {
        "surface_kind": "mas_artifact_projection_transport_authorization",
        "schema_version": 1,
        "transport_owner": "One Person Lab",
        "transport_action_id": "opl_pack_materialize_artifact_projection",
        "request_contract_ref": (
            "contracts/opl-framework/"
            "artifact-projection-materialization-request.schema.json"
        ),
        "receipt_contract_ref": (
            "contracts/opl-framework/"
            "artifact-projection-materialization-receipt.schema.json"
        ),
        "generation_id": manifest["generation_id"],
        "generation_manifest_ref": dict(request["generation_manifest_ref"]),
        "projection_manifest_ref": _generation_artifact_identity(
            members["submission_projection_manifest"]
        ),
        "generation_bound_truth_members": [
            _generation_artifact_identity(members[role])
            for role in (
                "submission_status",
                "publication_evaluation",
                "next_action_envelope",
            )
        ],
        "target_role": "study_submission_root",
        "completion_marker_paths": [
            "STATUS.json",
            "audit/submission_manifest.json",
        ],
        "opl_request_domain_authorization": {
            "owner": "MedAutoScience",
            "ref_source": "owner_receipt.receipt_id",
            "scope": "artifact_projection_only",
            "artifact_body_write_authorized": True,
            "authorizes_quality_publication_or_submission": False,
        },
        "source_tree_must_match_projection_manifest": True,
        "atomic_tree_switch_required": True,
        "transport_can_write_domain_truth": False,
    }


def _generation_artifact_identity(member: Mapping[str, Any]) -> dict[str, Any]:
    """Project a manifest member onto the stable transport-v1 artifact ABI."""

    return {name: member[name] for name in ("role", "ref", "size_bytes", "sha256")}


def _host_refs(request: Mapping[str, Any]) -> dict[str, Any]:
    host = request["host_context"]
    return {
        "run_ref": dict(host["run_ref"]),
        "producer_attempt_ref": dict(host["producer_attempt_ref"]),
        "output_ref": dict(host["output_ref"]),
    }


def _generation_identity(request: Mapping[str, Any]) -> dict[str, Any]:
    manifest = request["generation_manifest"]
    authority = request["review_authority"]
    return {
        "generation_id": manifest["generation_id"],
        "manifest_scope": manifest["manifest_scope"],
        "generation_manifest_ref": dict(request["generation_manifest_ref"]),
        "review_authority_epoch": authority["currentness_receipt"]["authority_epoch"],
        "review_request_ref": dict(authority["review_request_ref"]),
    }
