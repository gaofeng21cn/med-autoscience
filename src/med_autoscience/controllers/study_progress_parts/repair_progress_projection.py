from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


EVIDENCE_RELATIVE_PATH = Path("artifacts/controller/repair_execution_evidence/latest.json")
RECEIPT_RELATIVE_PATH = Path("artifacts/controller/repair_execution_receipts/latest.json")


def build_repair_progress_projection(*, study_root: Path) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    evidence_path = root / EVIDENCE_RELATIVE_PATH
    receipt_path = root / RECEIPT_RELATIVE_PATH
    evidence = _read_json_object(evidence_path)
    receipt = _read_json_object(receipt_path)
    changed_refs = _progress_changed_refs(evidence=evidence, receipt=receipt)
    accepted = _accepted_progress_receipt(receipt=receipt)
    progress_delta_candidate = _progress_delta_candidate(evidence=evidence)
    paper_delta_observed = bool(changed_refs) and progress_delta_candidate and accepted
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
        or _text(receipt.get("work_unit_id")),
        "source_fingerprint": _text(evidence.get("source_fingerprint")),
        "source_eval_id": _text(_mapping(evidence.get("repair_work_unit")).get("source_eval_id"))
        or _text(_mapping(evidence.get("review_finding")).get("source_eval_id")),
        "repair_execution_evidence_ref": str(evidence_path) if evidence else None,
        "owner_receipt_ref": str(receipt_path) if receipt else None,
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
