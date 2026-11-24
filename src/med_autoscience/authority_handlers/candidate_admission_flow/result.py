"""Candidate-admission result projections and authority identities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import source_input_digest
from .._record_validation import canonical_json_bytes, fingerprint
from .adjudicator import _adjudicator_refs
from .candidate import _candidate_exact_ref
from .policy import _AUTHORITY_BOUNDARY, RESULT_KIND, SCHEMA_VERSION


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
