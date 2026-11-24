"""Candidate and claim-scope record normalization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    enum_text,
    exact_keys,
    integer,
    mapping,
    sequence,
    sha256,
    text,
    text_list,
)
from .._record_validation import (
    typed_ref as _typed_ref,
)
from .policy import _CLAIM_CLASSES, _MANUSCRIPT_SECTIONS


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


def _candidate_exact_ref(candidate: Mapping[str, Any]) -> dict[str, Any]:
    member = candidate["candidate_member"]
    return {
        "kind": member["kind"],
        "ref": member["ref"],
        "size_bytes": member["size_bytes"],
        "sha256": member["sha256"],
    }
