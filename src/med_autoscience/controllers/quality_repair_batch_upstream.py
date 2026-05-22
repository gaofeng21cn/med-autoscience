from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers import domain_action_requests
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS,
)
from med_autoscience.controllers.medical_prose_story_surface_parts.eval_bound_currentness import (
    eval_bound_current_story_delta_source_basis,
)
from med_autoscience.controllers.quality_repair_batch_parts import medical_prose_story_surface


_REVIEW_LEDGER_RELATIVE_PATH = Path("review") / "review_ledger.json"
_MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS = medical_prose_story_surface.MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _write_json_if_changed(path: Path, payload: Mapping[str, Any]) -> bool:
    rendered = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def _source_fingerprint(
    *,
    work_unit_id: str,
    source_eval_id: str | None,
    gate_report: Mapping[str, Any],
    current_manuscript_basis: Mapping[str, Any] | None = None,
) -> str:
    payload = {
        "work_unit_id": work_unit_id,
        "source_eval_id": source_eval_id,
        "gate_fingerprint": _text(gate_report.get("gate_fingerprint")),
        "blockers": [
            str(item).strip()
            for item in (gate_report.get("blockers") or [])
            if str(item).strip()
        ],
        "medical_publication_surface_named_blockers": [
            str(item).strip()
            for item in (gate_report.get("medical_publication_surface_named_blockers") or [])
            if str(item).strip()
        ],
        "current_manuscript_basis": dict(current_manuscript_basis)
        if isinstance(current_manuscript_basis, Mapping)
        else {},
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _repair_receipt(
    *,
    study_id: str,
    quest_id: str,
    work_unit_id: str,
    source_eval_id: str | None,
    source_fingerprint: str,
) -> dict[str, Any]:
    return {
        "receipt_id": (
            f"quality-repair-batch::{study_id}::{quest_id}::{work_unit_id}::"
            f"{source_fingerprint.removeprefix('sha256:')[:16]}"
        ),
        "controller": "quality_repair_batch",
        "work_unit_id": work_unit_id,
        "source_eval_id": source_eval_id,
        "source_fingerprint": source_fingerprint,
        "authority": "controller_owned_repair_receipt",
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
    }


def _append_receipt(payload: dict[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    receipts = [
        dict(item)
        for item in (updated.get("controller_repair_receipts") or [])
        if isinstance(item, Mapping)
    ]
    receipt_id = _text(receipt.get("receipt_id"))
    if receipt_id and not any(_text(item.get("receipt_id")) == receipt_id for item in receipts):
        receipts.append(dict(receipt))
    updated["controller_repair_receipts"] = receipts
    return updated


def _materialize_review_ledger(
    *,
    paper_root: Path,
    receipt: Mapping[str, Any],
    work_unit_id: str,
) -> dict[str, Any]:
    path = paper_root / _REVIEW_LEDGER_RELATIVE_PATH
    payload = _read_json_object(path)
    concerns = [
        dict(item)
        for item in (payload.get("concerns") or [])
        if isinstance(item, Mapping)
    ]
    concern_id = f"controller-{work_unit_id}"
    if not any(_text(item.get("concern_id")) == concern_id for item in concerns):
        concerns.append(
            {
                "concern_id": concern_id,
                "reviewer_id": "MAS/controller",
                "summary": (
                    "Controller materialized reviewer-first repair evidence and routed the paper "
                    "back to AI reviewer recheck without mutating submission packages."
                ),
                "severity": "major",
                "status": "resolved",
                "owner_action": "ai_reviewer_recheck_requested",
                "revision_links": [
                    {
                        "revision_id": _text(receipt.get("receipt_id")) or concern_id,
                        "revision_log_path": (paper_root / "evidence_ledger.json").as_posix(),
                    }
                ],
            }
        )
    updated = {
        **payload,
        "schema_version": 1,
        "status": "closed",
        "concerns": concerns,
    }
    updated = _append_receipt(updated, receipt)
    changed = _write_json_if_changed(path, updated)
    return {
        "path": str(path.resolve()),
        "changed": changed,
    }


def _update_claim_and_evidence_surfaces(
    *,
    paper_root: Path,
    receipt: Mapping[str, Any],
) -> list[str]:
    changed_paths: list[str] = []
    for relpath in (Path("claim_evidence_map.json"), Path("evidence_ledger.json")):
        path = paper_root / relpath
        payload = _read_json_object(path)
        if not payload:
            continue
        updated = _append_receipt(payload, receipt)
        if _write_json_if_changed(path, updated):
            changed_paths.append(str(path.resolve()))
    return changed_paths


def _materialize_medical_prose_story_surfaces(
    *,
    paper_root: Path,
    work_unit_id: str,
    source_eval_id: str | None,
    previous_quality_repair_batch: Mapping[str, Any] | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> list[str]:
    return medical_prose_story_surface.materialize_medical_prose_story_surfaces(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
        previous_quality_repair_batch=previous_quality_repair_batch,
        publication_eval_payload=publication_eval_payload,
    )

def _materialize_ai_reviewer_request(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    source_fingerprint: str,
    gate_report: Mapping[str, Any],
) -> dict[str, Any]:
    input_refs = domain_action_request_lifecycle.default_ai_reviewer_request_input_refs(
        study_root=study_root,
    )
    medical_prose_review = _mapping(input_refs.get("medical_prose_review"))
    fallback_medical_prose_review_path = study_root / "paper" / "medical_prose_review.json"
    if medical_prose_review.get("present") is False and fallback_medical_prose_review_path.exists():
        medical_prose_review.update(
            {
                "path": str(fallback_medical_prose_review_path.resolve()),
                "relative_path": "paper/medical_prose_review.json",
                "present": True,
                "valid": True,
            }
        )
        input_refs["medical_prose_review"] = medical_prose_review
    workflow_state = {
        "quality_authority": {
            "owner": "mechanical_projection",
            "state": "review_required",
        },
        "route_back": {
            "required": True,
            "target": "ai_reviewer",
            "reason": "Controller-owned paper repair produced canonical evidence delta requiring AI reviewer recheck.",
        },
        "input_refs": input_refs,
        "blockers": [
            str(item).strip()
            for item in (gate_report.get("blockers") or [])
            if str(item).strip()
        ],
    }
    packet = domain_action_requests.build_ai_reviewer_publication_eval_request(
        study_id=study_id,
        quest_id=quest_id,
        source_surface="quality_repair_batch",
        workflow_state=workflow_state,
        input_refs=input_refs,
    )
    packet["source_fingerprint"] = source_fingerprint
    return domain_action_request_lifecycle.materialize_ai_reviewer_request(
        study_root=study_root,
        packet=packet,
    )


def run_upstream_paper_repair_unit(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    gate_report: Mapping[str, Any],
    work_unit_id: str | None,
    source_eval_id: str | None,
    previous_quality_repair_batch: Mapping[str, Any] | None = None,
    publication_eval_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    resolved_work_unit_id = _text(work_unit_id)
    if resolved_work_unit_id not in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS:
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    paper_root = resolved_study_root / "paper"
    if not paper_root.exists():
        return {
            "unit_id": resolved_work_unit_id,
            "label": "Materialize controller-owned upstream paper repair surfaces",
            "parallel_safe": False,
            "status": "missing",
            "result": {
                "status": "blocked_missing_paper_root",
                "paper_root": str(paper_root),
            },
        }

    current_manuscript_basis = eval_bound_current_story_delta_source_basis(
        paper_root=paper_root,
        work_unit_id=resolved_work_unit_id,
        medical_prose_write_repair_work_unit_id=medical_prose_story_surface.MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID,
        manuscript_story_surface_relative_paths=medical_prose_story_surface.MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS,
        contains_forbidden_manuscript_terms=medical_prose_story_surface._contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        publication_eval_payload=publication_eval_payload,
    )
    source_fingerprint = _source_fingerprint(
        work_unit_id=resolved_work_unit_id,
        source_eval_id=source_eval_id,
        gate_report=gate_report,
        current_manuscript_basis=current_manuscript_basis,
    )
    receipt = _repair_receipt(
        study_id=study_id,
        quest_id=quest_id,
        work_unit_id=resolved_work_unit_id,
        source_eval_id=source_eval_id,
        source_fingerprint=source_fingerprint,
    )
    changed_refs = _update_claim_and_evidence_surfaces(paper_root=paper_root, receipt=receipt)
    changed_refs.extend(
        _materialize_medical_prose_story_surfaces(
            paper_root=paper_root,
            work_unit_id=resolved_work_unit_id,
            source_eval_id=source_eval_id,
            previous_quality_repair_batch=previous_quality_repair_batch,
            publication_eval_payload=publication_eval_payload,
        )
    )
    review_ledger = _materialize_review_ledger(
        paper_root=paper_root,
        receipt=receipt,
        work_unit_id=resolved_work_unit_id,
    )
    if review_ledger["changed"]:
        changed_refs.append(review_ledger["path"])
    ai_request = _materialize_ai_reviewer_request(
        study_id=study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        source_fingerprint=source_fingerprint,
        gate_report=gate_report,
    )
    canonical_refs = [
        str(path.resolve())
        for path in (
            *(paper_root / relative_path for relative_path in _MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS),
            paper_root / "claim_evidence_map.json",
            paper_root / "evidence_ledger.json",
            paper_root / _REVIEW_LEDGER_RELATIVE_PATH,
        )
        if path.exists()
    ]
    status = "updated" if changed_refs else "already_current"
    return {
        "unit_id": resolved_work_unit_id,
        "label": "Materialize controller-owned upstream paper repair surfaces",
        "parallel_safe": False,
        "status": status,
        "result": {
            "status": status,
            "work_unit_id": resolved_work_unit_id,
            "source_fingerprint": source_fingerprint,
            "changed_artifact_refs": changed_refs,
            "canonical_artifact_refs": canonical_refs,
            "ai_reviewer_recheck_request_ref": ai_request.get("path"),
            "quality_gate_relaxation_allowed": False,
            "current_package_write_allowed": False,
        },
    }
