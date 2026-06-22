from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


SURFACE_KIND = "mas_paper_mission_candidate_consume_readback"
SCHEMA_VERSION = 1
ALLOWED_OUTCOMES = (
    "accepted_candidate",
    "rejected_candidate",
    "route_back",
    "typed_blocker_required",
    "human_gate_required",
)
FORBIDDEN_AUTHORITY_CLAIMS = (
    "publication_ready",
    "owner_receipt_written",
    "typed_blocker_written",
    "current_package_updated",
)
REQUIRED_NON_DEGRADATION_FIELDS = (
    "source_readiness_refs",
    "quality_auditor_requirement",
    "artifact_authority_boundary",
    "next_owner",
    "resume_condition",
)
FORBIDDEN_WRITE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("publication_eval_latest", ("publication_eval", "latest.json")),
    ("controller_decisions_latest", ("controller_decisions", "latest.json")),
    ("owner_receipt", ("owner_receipt",)),
    ("typed_blocker", ("typed_blocker",)),
    ("human_gate", ("human_gate",)),
    ("current_package", ("current_package",)),
    ("runtime_queue_or_provider_attempt", ("runtime", "queue")),
    ("runtime_queue_or_provider_attempt", ("provider", "attempt")),
    ("paper_body", ("paper", "manuscript")),
    ("paper_body", ("manuscript", "body")),
)


def consume_paper_mission_candidate(candidate: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    payload, manifest_input = _load_candidate_payload(candidate)
    base = _base_payload(payload)
    if manifest_input is not None:
        base["candidate_manifest_input"] = manifest_input

    if manifest_input is not None and manifest_input.get("loaded") is not True:
        return {
            **base,
            "status": "route_back",
            "selected_outcome": "route_back",
            "consume_result": _consume_result("route_back"),
            "accepted_candidate": None,
            "route_back": {
                "candidate_id": base["candidate_id"],
                "reason_code": "candidate_manifest_unreadable",
                "next_owner": "mission_executor",
                "resume_condition": "supply a readable JSON object candidate manifest",
            },
            "next_owner": "mission_executor",
            "resume_condition": "supply a readable JSON object candidate manifest",
        }

    claim_violations = _forbidden_claim_violations(payload)
    if claim_violations:
        return {
            **base,
            "status": "rejected_candidate",
            "selected_outcome": "rejected_candidate",
            "consume_result": _consume_result("rejected_candidate"),
            "accepted_candidate": None,
            "rejected_candidate": {
                "candidate_id": base["candidate_id"],
                "reason_code": "forbidden_authority_claim",
                "violations": claim_violations,
                "next_owner": "mission_executor",
                "resume_condition": (
                    "remove forbidden authority claims and resubmit as a refs-only candidate"
                ),
            },
        }

    forbidden_paths = _forbidden_write_path_matches(payload)
    if forbidden_paths:
        return {
            **base,
            "status": "route_back",
            "selected_outcome": "route_back",
            "consume_result": _consume_result("route_back"),
            "accepted_candidate": None,
            "route_back": {
                "candidate_id": base["candidate_id"],
                "reason_code": "forbidden_authority_write_path",
                "forbidden_write_path_matches": forbidden_paths,
                "next_owner": "mission_executor",
                "resume_condition": (
                    "remove forbidden authority write paths and resubmit as refs-only candidate"
                ),
            },
            "forbidden_write_path_matches": forbidden_paths,
            "next_owner": "mission_executor",
            "resume_condition": (
                "remove forbidden authority write paths and resubmit as refs-only candidate"
            ),
        }

    missing_fields = _missing_required_fields(payload)
    if missing_fields:
        return {
            **base,
            "status": "route_back",
            "selected_outcome": "route_back",
            "consume_result": _consume_result("route_back"),
            "accepted_candidate": None,
            "route_back": {
                "candidate_id": base["candidate_id"],
                "reason_code": "missing_required_non_degradation_refs",
                "missing_fields": missing_fields,
                "next_owner": "mission_executor",
                "resume_condition": "supply missing mission authority refs and resubmit",
            },
            "next_owner": "mission_executor",
            "resume_condition": "supply missing mission authority refs and resubmit",
        }

    requested_outcome = _requested_outcome(payload)
    if requested_outcome == "human_gate_required":
        return {
            **base,
            "status": "human_gate_required",
            "selected_outcome": "human_gate_required",
            "consume_result": _consume_result("human_gate_required"),
            "accepted_candidate": None,
            "human_gate_required": _human_gate_payload(payload),
        }
    if requested_outcome == "typed_blocker_required":
        return {
            **base,
            "status": "typed_blocker_required",
            "selected_outcome": "typed_blocker_required",
            "consume_result": _consume_result("typed_blocker_required"),
            "accepted_candidate": None,
            "typed_blocker_required": _typed_blocker_payload(payload),
        }
    if requested_outcome == "route_back":
        return {
            **base,
            "status": "route_back",
            "selected_outcome": "route_back",
            "consume_result": _consume_result("route_back"),
            "accepted_candidate": None,
            "route_back": {
                "candidate_id": base["candidate_id"],
                "reason_code": _text(payload.get("route_back_reason_code"))
                or "candidate_requested_route_back",
                "next_owner": "mission_executor",
                "resume_condition": _text(payload.get("route_back_resume_condition"))
                or "mission executor revises the candidate and resubmits",
            },
            "next_owner": "mission_executor",
            "resume_condition": _text(payload.get("route_back_resume_condition"))
            or "mission executor revises the candidate and resubmits",
        }
    if requested_outcome == "rejected_candidate":
        return {
            **base,
            "status": "rejected_candidate",
            "selected_outcome": "rejected_candidate",
            "consume_result": _consume_result("rejected_candidate"),
            "accepted_candidate": None,
            "rejected_candidate": {
                "candidate_id": base["candidate_id"],
                "reason_code": _text(payload.get("rejection_reason_code"))
                or "candidate_requested_rejection",
                "next_owner": "mission_executor",
                "resume_condition": _text(payload.get("rejection_resume_condition"))
                or "mission executor submits a corrected candidate",
            },
        }

    return {
        **base,
        "status": "accepted_candidate",
        "selected_outcome": "accepted_candidate",
        "consume_result": _consume_result("accepted_candidate"),
        "accepted_candidate": {
            "candidate_id": base["candidate_id"],
            "mission_id": base["mission_id"],
            "study_id": base["study_id"],
            "candidate_manifest_ref": _text(payload.get("candidate_manifest_ref")),
            "candidate_artifact_refs": _text_list(payload.get("candidate_artifact_refs")),
            "authority_materialized": False,
        },
    }


def _base_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": _text(payload.get("candidate_id")) or "unknown_candidate",
        "mission_id": _text(payload.get("mission_id")) or "unknown_mission",
        "study_id": _text(payload.get("study_id")) or "unknown_study",
        "allowed_outcomes": list(ALLOWED_OUTCOMES),
        "candidate_is_authority": False,
        "source_readiness_refs": _text_list(payload.get("source_readiness_refs")),
        "quality_auditor_requirement": _mapping(payload.get("quality_auditor_requirement")),
        "artifact_authority_boundary": _artifact_authority_boundary(payload),
        "next_owner": _text(payload.get("next_owner")) or "mas_authority_kernel",
        "resume_condition": _text(payload.get("resume_condition"))
        or "accepted mission candidate awaits MAS authority consumption",
        "write_plan": _no_write_plan(),
        "forbidden_authority_writes": _forbidden_authority_writes(),
        "authority_boundary": _authority_boundary(),
    }


def _consume_result(outcome: str) -> dict[str, Any]:
    status_by_outcome = {
        "accepted_candidate": "accepted",
        "rejected_candidate": "rejected",
        "route_back": "route_back",
        "typed_blocker_required": "typed_blocker",
        "human_gate_required": "human_gate",
    }
    return {
        "status": status_by_outcome[outcome],
        "outcome": outcome,
        "authority_materialized": False,
    }


def _load_candidate_payload(
    candidate: Mapping[str, Any] | str | Path,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if isinstance(candidate, Mapping):
        return dict(candidate), None
    path = Path(candidate).expanduser().resolve()
    manifest_input: dict[str, Any] = {
        "path": str(path),
        "loaded": False,
        "mode": "read_only_json_manifest",
    }
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        manifest_input["error"] = exc.__class__.__name__
        return {}, manifest_input
    if not isinstance(loaded, Mapping):
        manifest_input["error"] = "manifest_root_not_object"
        return {}, manifest_input
    manifest_input["loaded"] = True
    return dict(loaded), manifest_input


def _artifact_authority_boundary(payload: Mapping[str, Any]) -> dict[str, Any]:
    boundary = _mapping(payload.get("artifact_authority_boundary"))
    return {
        **boundary,
        "artifact_authority_owner": _text(boundary.get("artifact_authority_owner"))
        or "MedAutoScience",
        "candidate_is_authority": False,
        "can_update_current_package": False,
        "can_write_paper_body": False,
        "can_authorize_artifact_authority": False,
    }


def _forbidden_claim_violations(payload: Mapping[str, Any]) -> list[str]:
    return [field for field in FORBIDDEN_AUTHORITY_CLAIMS if payload.get(field) is True]


def _forbidden_write_path_matches(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    paths = _text_list(payload.get("authority_write_paths"))
    paths.extend(_text_list(payload.get("proposed_write_paths")))
    paths.extend(_text_list(payload.get("write_paths")))
    matches: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw_path in paths:
        normalized = _normalized_path(raw_path)
        for category, parts in FORBIDDEN_WRITE_PATTERNS:
            if _path_matches(normalized, parts):
                key = (category, raw_path)
                if key in seen:
                    continue
                seen.add(key)
                matches.append({"category": category, "path": raw_path})
    return matches


def _missing_required_fields(payload: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_NON_DEGRADATION_FIELDS:
        value = payload.get(field)
        if field == "source_readiness_refs":
            if not _text_list(value):
                missing.append(field)
        elif field in {"quality_auditor_requirement", "artifact_authority_boundary"}:
            if not _mapping(value):
                missing.append(field)
        elif _text(value) is None:
            missing.append(field)
    return missing


def _requested_outcome(payload: Mapping[str, Any]) -> str:
    requested = _text(payload.get("requested_outcome")) or "accepted_candidate"
    return requested if requested in ALLOWED_OUTCOMES else "route_back"


def _human_gate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    request = _mapping(payload.get("human_gate_request"))
    return {
        "candidate_id": _text(payload.get("candidate_id")) or "unknown_candidate",
        "materialized": False,
        "decision_packet_ref": _text(request.get("decision_packet_ref")),
        "next_owner": _text(request.get("next_owner")) or "human_owner",
        "resume_condition": _text(request.get("resume_condition"))
        or "human decision ref is returned to MAS authority kernel",
    }


def _typed_blocker_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    request = _mapping(payload.get("typed_blocker_request"))
    return {
        "candidate_id": _text(payload.get("candidate_id")) or "unknown_candidate",
        "materialized": False,
        "blocker_id": _text(request.get("blocker_id")),
        "blocker_ref": _text(request.get("blocker_ref")),
        "next_owner": _text(request.get("next_owner")) or "mas_authority_kernel",
        "resume_condition": _text(request.get("resume_condition"))
        or "MAS authority kernel records or rejects the typed blocker request",
    }


def _no_write_plan() -> dict[str, Any]:
    return {
        "mode": "readback_only",
        "written_files": [],
        "can_write_publication_eval_latest": False,
        "can_write_controller_decisions_latest": False,
        "can_write_owner_receipts": False,
        "can_write_typed_blockers": False,
        "can_write_human_gate_authority_records": False,
        "can_write_current_package": False,
        "can_write_paper_body": False,
        "can_write_runtime_queues_or_provider_attempts": False,
    }


def _forbidden_authority_writes() -> dict[str, bool]:
    return {
        "publication_eval_latest": True,
        "controller_decisions_latest": True,
        "owner_receipts": True,
        "typed_blockers": True,
        "human_gate_authority_records": True,
        "current_package": True,
        "paper_body": True,
        "runtime_queues_or_provider_attempts": True,
    }


def _authority_boundary() -> dict[str, bool | str]:
    return {
        "surface_role": "paper_mission_candidate_consume_readback_only",
        "candidate_can_satisfy_publication_ready": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_current_package": False,
        "can_write_paper_body": False,
        "can_write_runtime_queue_or_provider_attempt": False,
        "can_authorize_publication_ready": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_artifact_authority": False,
    }


def _normalized_path(value: str) -> str:
    path = Path(value).as_posix().lower()
    return path.replace("\\", "/")


def _path_matches(path: str, parts: tuple[str, ...]) -> bool:
    position = 0
    for part in parts:
        found = path.find(part, position)
        if found < 0:
            return False
        position = found + len(part)
    return True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        items: Sequence[object] = [value]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        items = value
    else:
        items = []
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _text(item)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ALLOWED_OUTCOMES",
    "FORBIDDEN_AUTHORITY_CLAIMS",
    "SURFACE_KIND",
    "consume_paper_mission_candidate",
]
