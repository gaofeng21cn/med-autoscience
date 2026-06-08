from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import paper_repair_execution_evidence
from med_autoscience.controllers.domain_action_request_lifecycle import (
    materialize_ai_reviewer_request,
    stable_ai_reviewer_request_path,
)
from med_autoscience.controllers.quality_repair_batch_parts import (
    medical_prose_story_surface,
)
from med_autoscience.controllers.story_surface_work_units import (
    is_story_surface_delta_write_work_unit,
)


SURFACE = "paper_story_repair_executor"
SCHEMA_VERSION = 1
BLOCKER = "manuscript_story_surface_delta_missing"
DM002_STORY_WORK_UNIT = "dm002_same_line_publication_paper_repair"
DEFAULT_DPCC_STORY_WORK_UNIT = medical_prose_story_surface.MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID


def run_story_repair(
    *,
    study_id: str,
    quest_id: str | None = None,
    study_root: str | Path,
    source: str = "med_autoscience",
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_quest_id = quest_id or study_id
    generated_at = _utc_now()
    publication_eval_path = resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = _read_json_object(publication_eval_path)
    quality_batch_path = (
        resolved_study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    )
    quality_batch = _read_json_object(quality_batch_path)
    work_unit_id = _select_story_work_unit_id(
        study_id=study_id,
        publication_eval=publication_eval,
        quality_batch=quality_batch,
        route_context=route_context,
    )
    if work_unit_id is None:
        return _blocked_result(
            generated_at=generated_at,
            study_id=study_id,
            quest_id=resolved_quest_id,
            study_root=resolved_study_root,
            source=source,
            publication_eval=publication_eval,
            quality_batch=quality_batch,
            typed_blocker=BLOCKER,
        )

    try:
        changed_paths = medical_prose_story_surface.materialize_medical_prose_story_surfaces(
            paper_root=resolved_study_root / "paper",
            work_unit_id=work_unit_id,
            source_eval_id=_text(publication_eval.get("eval_id")),
            previous_quality_repair_batch=quality_batch,
            publication_eval_payload=publication_eval,
        )
    except RuntimeError as exc:
        return _blocked_result(
            generated_at=generated_at,
            study_id=study_id,
            quest_id=resolved_quest_id,
            study_root=resolved_study_root,
            source=source,
            publication_eval=publication_eval,
            quality_batch=quality_batch,
            typed_blocker=_text(exc) or BLOCKER,
            work_unit_id=work_unit_id,
        )

    changed_refs = [
        {"path": str(Path(path).expanduser().resolve()), "artifact_role": _artifact_role(Path(path))}
        for path in changed_paths
    ]
    review_ledger_ref = _materialize_review_ledger(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=resolved_quest_id,
        work_unit_id=work_unit_id,
        source_eval_id=_text(publication_eval.get("eval_id")),
        generated_at=generated_at,
    )
    if review_ledger_ref:
        changed_refs.append({"path": review_ledger_ref, "artifact_role": "review_ledger"})
    evidence_ledger_ref = _ensure_evidence_ledger(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=resolved_quest_id,
        work_unit_id=work_unit_id,
        source_eval_id=_text(publication_eval.get("eval_id")),
        generated_at=generated_at,
    )
    if evidence_ledger_ref:
        changed_refs.append({"path": evidence_ledger_ref, "artifact_role": "evidence_ledger"})
    gate_replay_ref = _write_gate_replay_request(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=resolved_quest_id,
        work_unit_id=work_unit_id,
        changed_refs=changed_refs,
        source_eval_id=_text(publication_eval.get("eval_id")),
        generated_at=generated_at,
    )
    ai_request = _write_ai_reviewer_recheck_request(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=resolved_quest_id,
        work_unit_id=work_unit_id,
        gate_replay_ref=gate_replay_ref,
        source_eval_id=_text(publication_eval.get("eval_id")),
        generated_at=generated_at,
    )
    evidence = paper_repair_execution_evidence.build_repair_execution_evidence(
        study_id=study_id,
        quest_id=resolved_quest_id,
        study_root=resolved_study_root,
        repair_work_unit={
            "unit_id": work_unit_id,
            "work_unit_type": "text_repair",
            "owner": "write",
            "source": source,
            "source_eval_id": _text(publication_eval.get("eval_id")),
            "gate_replay_target": "publication_eval/latest.json",
        },
        review_finding={
            "source_eval_id": _text(publication_eval.get("eval_id")),
            "source_quality_repair_batch": str(quality_batch_path) if quality_batch_path.exists() else None,
        },
        source_refs=_source_refs(publication_eval_path, quality_batch_path, quality_batch),
        changed_artifact_refs=changed_refs,
        evidence_ledger_ref=evidence_ledger_ref,
        review_ledger_ref=review_ledger_ref,
        gate_replay_target="publication_eval/latest.json",
        gate_replay_refs=[str(gate_replay_ref)],
        ai_reviewer_recheck_request_ref=ai_request.get("path"),
        previous_quality_repair_batch=quality_batch,
        publication_eval_payload=publication_eval,
    )
    evidence_path = paper_repair_execution_evidence.write_repair_execution_evidence(
        study_root=resolved_study_root,
        evidence=evidence,
    )
    receipt = _owner_receipt(
        generated_at=generated_at,
        study_id=study_id,
        quest_id=resolved_quest_id,
        work_unit_id=work_unit_id,
        execution_status=evidence["status"],
        typed_blocker=None if evidence["progress_delta_candidate"] else _first_blocker(evidence),
        changed_refs=evidence["changed_artifact_refs"],
        evidence_path=evidence_path,
        gate_replay_ref=gate_replay_ref,
        ai_request_ref=ai_request.get("path"),
    )
    receipt_path = _write_owner_receipt(study_root=resolved_study_root, receipt=receipt)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "ok": evidence["progress_delta_candidate"] is True,
        "status": evidence["status"],
        "study_id": study_id,
        "quest_id": resolved_quest_id,
        "work_unit_id": work_unit_id,
        "source_eval_id": _text(publication_eval.get("eval_id")),
        "changed_artifact_refs": evidence["changed_artifact_refs"],
        "repair_execution_evidence": evidence,
        "repair_execution_evidence_ref": str(evidence_path),
        "owner_receipt": receipt,
        "owner_receipt_ref": str(receipt_path),
        "gate_replay_request_ref": str(gate_replay_ref),
        "ai_reviewer_recheck_request_ref": ai_request.get("path"),
        "direct_current_package_write": False,
        "quality_gate_relaxation_allowed": False,
    }


def _select_story_work_unit_id(
    *,
    study_id: str,
    publication_eval: Mapping[str, Any],
    quality_batch: Mapping[str, Any],
    route_context: Mapping[str, Any] | None,
) -> str | None:
    for candidate in _candidate_work_unit_ids(route_context):
        if is_story_surface_delta_write_work_unit(candidate):
            return _normalize_story_work_unit_id(study_id=study_id, work_unit_id=candidate)
    for candidate in _candidate_work_unit_ids(quality_batch):
        if is_story_surface_delta_write_work_unit(candidate):
            return _normalize_story_work_unit_id(study_id=study_id, work_unit_id=candidate)
    for candidate in _publication_eval_work_unit_ids(publication_eval):
        if is_story_surface_delta_write_work_unit(candidate):
            return _normalize_story_work_unit_id(study_id=study_id, work_unit_id=candidate)
    return None


def _normalize_story_work_unit_id(*, study_id: str, work_unit_id: str) -> str:
    if study_id.startswith("002-") and work_unit_id in {"manuscript_story_repair", DEFAULT_DPCC_STORY_WORK_UNIT}:
        return DM002_STORY_WORK_UNIT
    return work_unit_id


def _publication_eval_work_unit_ids(publication_eval: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for action in _mappings(publication_eval.get("recommended_actions")):
        result.extend(_candidate_work_unit_ids(action))
        for work_unit in _mappings(action.get("blocking_work_units")):
            result.extend(_candidate_work_unit_ids(work_unit))
    return _dedupe_text(result)


def _candidate_work_unit_ids(payload: object) -> list[str]:
    mapping = _mapping(payload)
    candidates: list[str] = []
    for key in ("unit_id", "work_unit_id", "next_work_unit", "materialized_work_unit_id"):
        value = mapping.get(key)
        if isinstance(value, Mapping):
            candidates.extend(_candidate_work_unit_ids(value))
        elif text := _text(value):
            candidates.append(text)
    for key in ("owner_route", "source_refs", "prompt_contract", "source_action"):
        value = mapping.get(key)
        if isinstance(value, Mapping):
            candidates.extend(_candidate_work_unit_ids(value))
    return _dedupe_text(candidates)


def _materialize_review_ledger(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    work_unit_id: str,
    source_eval_id: str | None,
    generated_at: str,
) -> str:
    path = study_root / "paper" / "review" / "review_ledger.json"
    payload = _read_json_object(path)
    concerns = _mappings(payload.get("concerns"))
    concern_id = f"{work_unit_id}::story_delta"
    if not any(_text(item.get("concern_id")) == concern_id for item in concerns):
        concerns.append(
            {
                "concern_id": concern_id,
                "reviewer_id": SURFACE,
                "summary": "Canonical manuscript story surface was repaired for the current publication evaluation.",
                "severity": "major",
                "status": "resolved",
                "owner_action": "ai_reviewer_recheck_requested",
                "source_eval_id": source_eval_id,
                "resolved_at": generated_at,
            }
        )
    payload.update(
        {
            "schema_version": 1,
            "status": "closed",
            "study_id": study_id,
            "quest_id": quest_id,
            "updated_at": generated_at,
            "reviews_count": len(concerns),
            "concerns": concerns,
        }
    )
    _write_json(path, payload)
    return str(path.resolve())


def _ensure_evidence_ledger(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    work_unit_id: str,
    source_eval_id: str | None,
    generated_at: str,
) -> str:
    path = study_root / "paper" / "evidence_ledger.json"
    payload = _read_json_object(path)
    claim_evidence_map = _read_json_object(study_root / "paper" / "claim_evidence_map.json")
    claims = _evidence_claims_from_claim_map(claim_evidence_map)
    updates = _mappings(payload.get("evidence_updates"))
    update_id = f"{work_unit_id}::story_surface_delta"
    if not any(_text(item.get("update_id")) == update_id for item in updates):
        updates.append(
            {
                "update_id": update_id,
                "study_id": study_id,
                "quest_id": quest_id,
                "work_unit_id": work_unit_id,
                "source_eval_id": source_eval_id,
                "updated_at": generated_at,
                "summary": (
                    "Canonical draft and review manuscript were regenerated from current paper owner surfaces."
                ),
                "source_refs": [
                    "paper/draft.md",
                    "paper/build/review_manuscript.md",
                    "paper/claim_evidence_map.json",
                ],
            }
        )
    payload.update(
        {
            "schema_version": 1,
            "status": "updated",
            "study_id": study_id,
            "quest_id": quest_id,
            "updated_at": generated_at,
            "evidence_updates": updates,
        }
    )
    if claims:
        payload["claims"] = claims
    _write_json(path, payload)
    return str(path.resolve())


def _evidence_claims_from_claim_map(claim_evidence_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for claim in _mappings(claim_evidence_map.get("claims")):
        claim_id = _text(claim.get("claim_id"))
        statement = _text(claim.get("statement")) or _text(claim.get("claim_text"))
        evidence_items = _mappings(claim.get("evidence_items"))
        if claim_id is None or statement is None or not evidence_items:
            continue
        evidence = [
            _ledger_evidence_item_from_claim_item(evidence_item)
            for evidence_item in evidence_items
            if _text(evidence_item.get("item_id")) is not None
        ]
        if not evidence:
            continue
        claims.append(
            {
                "claim_id": claim_id,
                "statement": statement,
                "status": _text(claim.get("status")) or "supported_with_limitations",
                "submission_scope": _text(claim.get("paper_role")) or "main_text",
                "evidence": evidence,
                "gaps": [
                    {
                        "gap_id": f"{claim_id}::story_repair_gate_recheck",
                        "description": "Claim evidence was aligned for reviewer and publication-gate replay.",
                        "submission_impact": "requires_ai_reviewer_recheck",
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": f"{claim_id}::ai_reviewer_recheck",
                        "priority": "required",
                        "description": "Re-run AI reviewer and publication gate against the aligned manuscript package.",
                    }
                ],
            }
        )
    return claims


def _ledger_evidence_item_from_claim_item(evidence_item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": _text(evidence_item.get("item_id")),
        "kind": _text(evidence_item.get("kind")) or _text(evidence_item.get("evidence_kind")) or "paper_evidence",
        "source_paths": [
            text
            for text in (_text(item) for item in (evidence_item.get("source_paths") or []))
            if text
        ],
        "support_level": _text(evidence_item.get("support_level")) or "supporting",
        "summary": _text(evidence_item.get("summary")) or "Claim-map evidence item carried into evidence ledger.",
    }


def _write_gate_replay_request(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    work_unit_id: str,
    changed_refs: Iterable[Mapping[str, Any]],
    source_eval_id: str | None,
    generated_at: str,
) -> Path:
    path = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    _write_json(
        path,
        {
            "surface": "paper_story_repair_gate_replay_request",
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "study_id": study_id,
            "quest_id": quest_id,
            "work_unit_id": work_unit_id,
            "source_eval_id": source_eval_id,
            "target": "publication_eval/latest.json",
            "changed_artifact_refs": [dict(ref) for ref in changed_refs],
            "direct_current_package_write": False,
        },
    )
    return path


def _write_ai_reviewer_recheck_request(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    work_unit_id: str,
    gate_replay_ref: Path,
    source_eval_id: str | None,
    generated_at: str,
) -> dict[str, Any]:
    packet = {
        "surface": "domain_action_request",
        "schema_version": SCHEMA_VERSION,
        "request_id": f"ai-reviewer-recheck::{study_id}::{work_unit_id}",
        "request_kind": "return_to_ai_reviewer_workflow",
        "request_owner": "ai_reviewer",
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": quest_id,
        "repair_work_unit": {
            "unit_id": work_unit_id,
            "source_eval_id": source_eval_id,
        },
        "required_output": {"path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "gate_replay_request_ref": str(gate_replay_ref),
        "request_lifecycle": {"state": "requested", "assigned_to": "ai_reviewer"},
    }
    return materialize_ai_reviewer_request(study_root=study_root, packet=packet)


def _blocked_result(
    *,
    generated_at: str,
    study_id: str,
    quest_id: str,
    study_root: Path,
    source: str,
    publication_eval: Mapping[str, Any],
    quality_batch: Mapping[str, Any],
    typed_blocker: str,
    work_unit_id: str | None = None,
) -> dict[str, Any]:
    evidence = paper_repair_execution_evidence.build_repair_execution_evidence(
        study_id=study_id,
        quest_id=quest_id,
        study_root=study_root,
        repair_work_unit={
            "unit_id": work_unit_id or "manuscript_story_repair",
            "work_unit_type": "text_repair",
            "owner": "write",
            "source": source,
            "source_eval_id": _text(publication_eval.get("eval_id")),
        },
        review_finding={
            "source_eval_id": _text(publication_eval.get("eval_id")),
            "typed_blocker": typed_blocker,
        },
        source_refs=_source_refs(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
            quality_batch,
        ),
        changed_artifact_refs=[],
    )
    evidence["retryable"] = True
    evidence_path = paper_repair_execution_evidence.write_repair_execution_evidence(
        study_root=study_root,
        evidence=evidence,
    )
    receipt = _owner_receipt(
        generated_at=generated_at,
        study_id=study_id,
        quest_id=quest_id,
        work_unit_id=work_unit_id or "manuscript_story_repair",
        execution_status="blocked",
        typed_blocker=typed_blocker,
        changed_refs=[],
        evidence_path=evidence_path,
        gate_replay_ref=None,
        ai_request_ref=None,
    )
    receipt_path = _write_owner_receipt(study_root=study_root, receipt=receipt)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "status": "blocked",
        "study_id": study_id,
        "quest_id": quest_id,
        "work_unit_id": work_unit_id,
        "typed_blocker": typed_blocker,
        "changed_artifact_refs": [],
        "repair_execution_evidence": evidence,
        "repair_execution_evidence_ref": str(evidence_path),
        "owner_receipt": receipt,
        "owner_receipt_ref": str(receipt_path),
    }


def _owner_receipt(
    *,
    generated_at: str,
    study_id: str,
    quest_id: str,
    work_unit_id: str,
    execution_status: str,
    typed_blocker: str | None,
    changed_refs: list[Mapping[str, Any]],
    evidence_path: Path,
    gate_replay_ref: Path | None,
    ai_request_ref: object | None,
) -> dict[str, Any]:
    return {
        "surface": "paper_story_repair_owner_receipt",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "accepted": typed_blocker is None,
        "study_id": study_id,
        "quest_id": quest_id,
        "work_unit_id": work_unit_id,
        "execution_status": execution_status,
        "typed_blocker": typed_blocker,
        "blocked_reason": typed_blocker,
        "canonical_artifact_delta_refs": [dict(ref) for ref in changed_refs],
        "repair_execution_evidence_ref": str(evidence_path),
        "gate_replay_request_ref": str(gate_replay_ref) if gate_replay_ref is not None else None,
        "ai_reviewer_recheck_request_ref": _text(ai_request_ref),
        "direct_current_package_write": False,
        "quality_authorized": False,
        "submission_authorized": False,
    }


def _write_owner_receipt(*, study_root: Path, receipt: Mapping[str, Any]) -> Path:
    digest = hashlib.sha256(str(receipt.get("work_unit_id") or "story_repair").encode("utf-8")).hexdigest()[:20]
    path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / f"{digest}.json"
    _write_json(path, receipt)
    _write_json(study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json", receipt)
    return path


def _source_refs(publication_eval_path: Path, quality_batch_path: Path, quality_batch: Mapping[str, Any]) -> list[str]:
    refs = [str(publication_eval_path.resolve())]
    if quality_batch_path.exists():
        refs.append(str(quality_batch_path.resolve()))
    if ref := _text(quality_batch.get("repair_execution_evidence_path")):
        refs.append(ref)
    return refs


def _artifact_role(path: Path) -> str:
    text = path.as_posix()
    if text.endswith("draft.md") or text.endswith("build/review_manuscript.md"):
        return "canonical_manuscript_story_surface"
    if text.endswith("review_ledger.json"):
        return "review_ledger"
    if text.endswith("evidence_ledger.json"):
        return "evidence_ledger"
    return "canonical_paper_artifact"


def _first_blocker(evidence: Mapping[str, Any]) -> str | None:
    blockers = [item for item in (_text(item) for item in evidence.get("blockers") or []) if item]
    return blockers[0] if blockers else None


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _dedupe_text(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = ["run_story_repair"]
