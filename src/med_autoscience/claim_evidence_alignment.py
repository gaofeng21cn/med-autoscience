from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.policies.medical_publication_surface import (
    validate_claim_evidence_map,
    validate_evidence_ledger,
)

__all__ = ["build_claim_evidence_alignment_gate"]


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list_of_mappings(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _resolve_ref(*, study_root: Path, ref: str | Path) -> Path:
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (study_root / candidate).resolve()


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else None


def _stable_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _blocked_gate(
    *,
    claim_evidence_map_path: Path,
    evidence_ledger_path: Path,
    missing_required_fields: list[str],
    blockers: list[str],
    claims: list[dict[str, Any]] | None = None,
    claim_count: int = 0,
    aligned_claim_count: int = 0,
) -> dict[str, Any]:
    return {
        "surface_kind": "claim_evidence_alignment_gate_v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_claim_evidence_alignment_gate",
        "status": "blocked",
        "input_refs": {
            "claim_evidence_map": str(claim_evidence_map_path),
            "evidence_ledger": str(evidence_ledger_path),
        },
        "claim_count": claim_count,
        "aligned_claim_count": aligned_claim_count,
        "claims": claims or [],
        "fail_closed_when_missing": True,
        "missing_required_fields": missing_required_fields,
        "blockers": blockers,
        "body_included": False,
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
    }


def build_claim_evidence_alignment_gate(
    *,
    study_root: str | Path,
    claim_evidence_map_ref: str | Path,
    evidence_ledger_ref: str | Path,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    claim_evidence_map_path = _resolve_ref(
        study_root=resolved_study_root,
        ref=claim_evidence_map_ref,
    )
    evidence_ledger_path = _resolve_ref(
        study_root=resolved_study_root,
        ref=evidence_ledger_ref,
    )

    missing_required_fields: list[str] = []
    blockers: list[str] = []
    claim_map_payload = _read_json_object(claim_evidence_map_path)
    evidence_ledger_payload = _read_json_object(evidence_ledger_path)
    if claim_map_payload is None:
        missing_required_fields.append("claim_evidence_map")
    if evidence_ledger_payload is None:
        missing_required_fields.append("evidence_ledger")
    if missing_required_fields:
        return _blocked_gate(
            claim_evidence_map_path=claim_evidence_map_path,
            evidence_ledger_path=evidence_ledger_path,
            missing_required_fields=missing_required_fields,
            blockers=[f"{field}_missing_or_invalid" for field in missing_required_fields],
        )

    claim_map_errors = validate_claim_evidence_map(claim_map_payload)
    evidence_ledger_errors = validate_evidence_ledger(evidence_ledger_payload)
    if claim_map_errors:
        missing_required_fields.extend(f"claim_evidence_map:{error}" for error in claim_map_errors)
    if evidence_ledger_errors:
        missing_required_fields.extend(f"evidence_ledger:{error}" for error in evidence_ledger_errors)
    if missing_required_fields:
        return _blocked_gate(
            claim_evidence_map_path=claim_evidence_map_path,
            evidence_ledger_path=evidence_ledger_path,
            missing_required_fields=missing_required_fields,
            blockers=["claim_evidence_alignment_payload_invalid"],
        )

    ledger_claims = {
        _text(claim.get("claim_id")): claim
        for claim in _list_of_mappings(evidence_ledger_payload.get("claims"))
        if _text(claim.get("claim_id"))
    }
    claim_rows: list[dict[str, Any]] = []
    aligned_claim_count = 0
    for claim in _list_of_mappings(claim_map_payload.get("claims")):
        claim_id = _text(claim.get("claim_id"))
        evidence_items = _list_of_mappings(claim.get("evidence_items"))
        evidence_item_refs = _stable_unique([_text(item.get("item_id")) for item in evidence_items])
        support_levels = _stable_unique([_text(item.get("support_level")) for item in evidence_items])
        row: dict[str, Any] = {
            "claim_id": claim_id,
            "status": "aligned",
            "evidence_item_refs": evidence_item_refs,
            "support_levels": support_levels,
        }
        ledger_claim = ledger_claims.get(claim_id)
        if ledger_claim is None:
            row["status"] = "blocked"
            row["defect_stage"] = "claim_id_alignment"
            row["missing_evidence_item_refs"] = evidence_item_refs
            blockers.append(f"{claim_id}_missing_from_evidence_ledger")
            claim_rows.append(row)
            continue

        ledger_evidence_ids = {
            _text(item.get("evidence_id"))
            for item in _list_of_mappings(ledger_claim.get("evidence"))
            if _text(item.get("evidence_id"))
        }
        missing_evidence_item_refs = [item_id for item_id in evidence_item_refs if item_id not in ledger_evidence_ids]
        if missing_evidence_item_refs:
            row["status"] = "blocked"
            row["defect_stage"] = "evidence_id_alignment"
            row["missing_evidence_item_refs"] = missing_evidence_item_refs
            blockers.extend(f"{claim_id}.{item_id}_missing_from_evidence_ledger" for item_id in missing_evidence_item_refs)
        else:
            aligned_claim_count += 1
        claim_rows.append(row)

    status = "ready" if not blockers else "blocked"
    return {
        "surface_kind": "claim_evidence_alignment_gate_v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_claim_evidence_alignment_gate",
        "status": status,
        "input_refs": {
            "claim_evidence_map": str(claim_evidence_map_path),
            "evidence_ledger": str(evidence_ledger_path),
        },
        "claim_count": len(claim_rows),
        "aligned_claim_count": aligned_claim_count,
        "claims": claim_rows,
        "fail_closed_when_missing": True,
        "missing_required_fields": [],
        "blockers": blockers,
        "body_included": False,
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
    }
