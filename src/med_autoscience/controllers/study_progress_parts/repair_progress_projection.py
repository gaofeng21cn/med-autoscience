from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


EVIDENCE_RELATIVE_PATH = Path("artifacts/controller/repair_execution_evidence/latest.json")
RECEIPT_RELATIVE_PATH = Path("artifacts/controller/repair_execution_receipts/latest.json")
QUALITY_REPAIR_BATCH_RELATIVE_PATH = Path("artifacts/controller/quality_repair_batch/latest.json")


def build_repair_progress_projection(*, study_root: Path) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    evidence_path = root / EVIDENCE_RELATIVE_PATH
    receipt_path = root / RECEIPT_RELATIVE_PATH
    quality_batch_path = root / QUALITY_REPAIR_BATCH_RELATIVE_PATH
    evidence = _read_json_object(evidence_path)
    receipt = _read_json_object(receipt_path)
    quality_batch = _read_json_object(quality_batch_path)
    quality_identity = _quality_batch_work_unit_identity(quality_batch)
    changed_refs = _progress_changed_refs(evidence=evidence, receipt=receipt)
    accepted = _accepted_progress_receipt(receipt=receipt) or _accepted_quality_batch_owner_result(
        quality_batch=quality_batch,
        quality_batch_path=quality_batch_path,
        evidence=evidence,
        evidence_path=evidence_path,
    )
    progress_delta_candidate = _progress_delta_candidate(evidence=evidence)
    paper_delta_observed = bool(changed_refs) and progress_delta_candidate and accepted
    owner_receipt_ref = str(receipt_path) if receipt else str(quality_batch_path) if accepted and quality_batch else None
    return {
        "surface_kind": "repair_progress_projection",
        "schema_version": 1,
        "source": "mas_owner_repair_execution_evidence",
        "study_root": str(root),
        "paper_delta_observed": paper_delta_observed,
        "progress_delta_candidate": progress_delta_candidate,
        "accepted_owner_receipt": accepted,
        "status": "progress_delta_observed" if paper_delta_observed else "not_observed",
        "work_unit_id": _text(_mapping(evidence.get("repair_work_unit")).get("unit_id"))
        or _text(receipt.get("work_unit_id"))
        or _text(quality_identity.get("work_unit_id")),
        "work_unit_fingerprint": _text(quality_identity.get("work_unit_fingerprint"))
        or _text(receipt.get("work_unit_fingerprint")),
        "action_fingerprint": _text(quality_identity.get("work_unit_fingerprint"))
        or _text(receipt.get("action_fingerprint")),
        "source_fingerprint": _text(evidence.get("source_fingerprint")),
        "source_eval_id": _text(_mapping(evidence.get("repair_work_unit")).get("source_eval_id"))
        or _text(_mapping(evidence.get("review_finding")).get("source_eval_id")),
        "repair_execution_evidence_ref": str(evidence_path) if evidence else None,
        "owner_receipt_ref": owner_receipt_ref,
        "gate_replay_refs": _dedupe(
            [
                *_ref_items(evidence.get("gate_replay_refs")),
                _text(receipt.get("gate_replay_request_ref")),
            ]
        ),
        "gate_replay_done": evidence.get("gate_replay_done") is True,
        "ai_reviewer_recheck_required": evidence.get("ai_reviewer_recheck_required") is True,
        "ai_reviewer_recheck_done": evidence.get("ai_reviewer_recheck_done") is True,
        "ai_reviewer_recheck_request_ref": _text(evidence.get("ai_reviewer_recheck_request_ref"))
        or _text(receipt.get("ai_reviewer_recheck_request_ref")),
        "changed_artifact_refs": changed_refs,
        "authority_boundary": {
            "projection_only": True,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
            "can_write_current_package": False,
        },
    }


def _progress_delta_candidate(*, evidence: Mapping[str, Any]) -> bool:
    if evidence.get("progress_delta_candidate") is not True:
        return False
    delta = _mapping(evidence.get("canonical_artifact_delta"))
    return delta.get("meaningful_artifact_delta") is True


def _accepted_progress_receipt(*, receipt: Mapping[str, Any]) -> bool:
    if not receipt:
        return False
    if receipt.get("accepted") is not True:
        return False
    if receipt.get("direct_current_package_write") is True:
        return False
    if receipt.get("quality_authorized") is True or receipt.get("submission_authorized") is True:
        return False
    return _text(receipt.get("typed_blocker")) is None and _text(receipt.get("blocked_reason")) is None


def _accepted_quality_batch_owner_result(
    *,
    quality_batch: Mapping[str, Any],
    quality_batch_path: Path,
    evidence: Mapping[str, Any],
    evidence_path: Path,
) -> bool:
    if not quality_batch:
        return False
    if quality_batch.get("ok") is not True:
        return False
    if _text(quality_batch.get("status")) not in {"executed", "handoff_ready"}:
        return False
    if _text(quality_batch.get("typed_blocker")) is not None:
        return False
    if _text(quality_batch.get("blocked_reason")) is not None:
        return False
    if not _quality_batch_refs_current_evidence(
        quality_batch=quality_batch,
        quality_batch_path=quality_batch_path,
        evidence=evidence,
        evidence_path=evidence_path,
    ):
        return False
    if evidence.get("quality_authorized") is True or evidence.get("submission_authorized") is True:
        return False
    if evidence.get("current_package_write_authorized") is True:
        return False
    blockers = [item for item in _ref_items(evidence.get("blockers")) if item]
    if blockers:
        return False
    return _quality_batch_authority_allows_owner_receipt(quality_batch)


def _quality_batch_refs_current_evidence(
    *,
    quality_batch: Mapping[str, Any],
    quality_batch_path: Path,
    evidence: Mapping[str, Any],
    evidence_path: Path,
) -> bool:
    if not evidence:
        return False
    evidence_ref = _text(quality_batch.get("repair_execution_evidence_path"))
    if evidence_ref is None:
        return False
    if Path(evidence_ref).expanduser().resolve() != evidence_path:
        return False
    source_eval_id = _text(quality_batch.get("source_eval_id"))
    evidence_eval_id = _text(_mapping(evidence.get("repair_work_unit")).get("source_eval_id")) or _text(
        _mapping(evidence.get("review_finding")).get("source_eval_id")
    )
    return source_eval_id is not None and evidence_eval_id is not None and source_eval_id == evidence_eval_id


def _quality_batch_authority_allows_owner_receipt(quality_batch: Mapping[str, Any]) -> bool:
    route_gate = _mapping(quality_batch.get("authority_route_gate"))
    if not route_gate:
        return False
    if route_gate.get("authorized") is not True or route_gate.get("allowed") is not True:
        return False
    controller_gate = _mapping(route_gate.get("controller_route_gate"))
    if controller_gate and controller_gate.get("authorized") is False:
        return False
    return True


def _quality_batch_work_unit_identity(quality_batch: Mapping[str, Any]) -> dict[str, Any]:
    gate_batch = _mapping(quality_batch.get("gate_clearing_batch"))
    controller_gate = _mapping(_mapping(quality_batch.get("authority_route_gate")).get("controller_route_gate"))
    controller_ref = _mapping(_mapping(quality_batch.get("authority_route_gate")).get("controller_repair_authorization_ref"))
    selected_work_unit = _mapping(gate_batch.get("selected_publication_work_unit"))
    current_work_unit = _mapping(gate_batch.get("current_publication_work_unit"))
    currentness = _mapping(gate_batch.get("work_unit_currentness"))
    return {
        key: value
        for key, value in {
            "work_unit_id": _text(gate_batch.get("work_unit_id"))
            or _text(controller_gate.get("work_unit_id"))
            or _text(controller_ref.get("work_unit_id"))
            or _text(selected_work_unit.get("unit_id"))
            or _text(current_work_unit.get("unit_id")),
            "work_unit_fingerprint": _text(gate_batch.get("source_work_unit_fingerprint"))
            or _text(gate_batch.get("work_unit_fingerprint"))
            or _text(currentness.get("current_work_unit_fingerprint"))
            or _text(currentness.get("explicit_work_unit_fingerprint"))
            or _text(controller_gate.get("work_unit_fingerprint"))
            or _text(controller_ref.get("work_unit_fingerprint")),
        }.items()
        if value is not None
    }


def _progress_changed_refs(
    *,
    evidence: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    refs.extend(_artifact_refs(evidence.get("changed_artifact_refs")))
    refs.extend(_artifact_refs(_mapping(evidence.get("canonical_artifact_delta")).get("artifact_refs")))
    refs.extend(_artifact_refs(receipt.get("canonical_artifact_delta_refs")))
    return _dedupe_ref_payloads(refs)


def _artifact_refs(value: object) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in _mappings(value):
        path = _text(item.get("path")) or _text(item.get("ref"))
        if path is None or not _paper_delta_ref_is_current_truth(path):
            continue
        result.append(
            {
                key: value
                for key, value in {
                    "path": path,
                    "artifact_role": _text(item.get("artifact_role")) or _text(item.get("role")),
                }.items()
                if value is not None
            }
        )
    return result


def _paper_delta_ref_is_current_truth(ref: str) -> bool:
    normalized = ref.strip().replace("\\", "/")
    if not normalized:
        return False
    if "/runtime/quests/" in normalized:
        return False
    if "/archive/" in normalized or "/_archive/" in normalized:
        return False
    return any(
        marker in normalized
        for marker in (
            "/paper/draft.md",
            "/paper/build/review_manuscript.md",
            "/paper/claim_evidence_map.json",
            "/paper/evidence_ledger.json",
            "/paper/review/",
            "/paper/tables/",
            "/paper/figures/",
            "paper/draft.md",
            "paper/build/review_manuscript.md",
            "paper/claim_evidence_map.json",
            "paper/evidence_ledger.json",
            "paper/review/",
            "paper/tables/",
            "paper/figures/",
        )
    )


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _dedupe_ref_payloads(refs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ref in refs:
        path = _text(ref.get("path"))
        if path is None or path in seen:
            continue
        seen.add(path)
        result.append(dict(ref))
    return result


def _ref_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if isinstance(value, Mapping):
        return [text for item in value.values() if (text := _text(item)) is not None]
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _dedupe(items: Iterable[str | None]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["build_repair_progress_projection"]
