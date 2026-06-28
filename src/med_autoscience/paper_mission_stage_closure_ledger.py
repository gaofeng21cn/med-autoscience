from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


PAPER_MISSION_STAGE_CLOSURE_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_stage_closure"
)


def write_paper_mission_stage_closure_decision(
    *,
    output_root: Path,
    study_id: str,
    decision: Mapping[str, Any],
    source_readback: Mapping[str, Any],
    source: str,
    forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    study_root = output_root.expanduser().resolve() / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    normalized = paper_mission_stage_closure_decision_record(
        study_id=study_id,
        decision=decision,
        source_readback=source_readback,
        source=source,
        forbidden_authority_writes=forbidden_authority_writes,
        forbidden_authority_claims=forbidden_authority_claims,
    )
    output_ref = study_root / "stage_closure_decision.json"
    text = json.dumps(normalized, ensure_ascii=False, indent=2) + "\n"
    output_ref.write_text(text, encoding="utf-8")
    return {
        "mode": "stage_closure_terminalizer_decision",
        "output_root": str(study_root),
        "written_files": [str(output_ref)],
        "file_sha256": {
            str(output_ref): hashlib.sha256(text.encode("utf-8")).hexdigest()
        },
        "stage_closure_decision_ref": str(output_ref),
        "stage_closure_outcome": _mapping(normalized.get("outcome")).get("kind"),
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "forbidden_authority_writes": list(forbidden_authority_writes),
    }


def paper_mission_stage_closure_decision_record(
    *,
    study_id: str,
    decision: Mapping[str, Any],
    source_readback: Mapping[str, Any],
    source: str,
    forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    transaction = _mapping(source_readback.get("paper_mission_transaction"))
    payload = {
        **dict(decision),
        "surface_kind": "mas_stage_closure_decision",
        "schema_version": 1,
        "source": source,
        "study_id": study_id,
        "mission_id": _first_text(
            source_readback.get("mission_id"),
            transaction.get("mission_id"),
        ),
        "paper_mission_transaction_ref": _first_text(
            transaction.get("transaction_id"),
            source_readback.get("paper_mission_transaction_ref"),
        ),
        "source_consume_candidate_status": _text(
            source_readback.get("consume_candidate_status")
        ),
        "source_transaction_state": _text(source_readback.get("transaction_state")),
        "source_ref": _first_text(
            source_readback.get("source_ref"),
            source_readback.get("materialized_mission_ref"),
        ),
        "authority_materialized": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "counts_as_stage_closure_terminalizer_evidence": True,
        "counts_as_owner_receipt": False,
        "counts_as_typed_blocker": False,
        "counts_as_human_gate": False,
        "counts_as_current_package": False,
        "counts_as_runtime_truth": False,
        "can_claim_paper_progress": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": {
            "surface_role": "stage_closure_terminalizer_decision_record",
            "authority_materialized": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_submission_ready_package": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "forbidden_authority_writes": list(forbidden_authority_writes),
    }
    return _compact(payload)


def latest_paper_mission_stage_closure_decision_readback(
    *,
    workspace_root: Path,
    study_id: str,
    transaction_ref: str | None = None,
) -> dict[str, Any] | None:
    ledger_root = workspace_root.expanduser().resolve() / PAPER_MISSION_STAGE_CLOSURE_RELPATH
    if not ledger_root.exists():
        return None
    candidates: list[tuple[float, str, dict[str, Any]]] = []
    for decision_ref in ledger_root.glob(f"**/{study_id}/stage_closure_decision.json"):
        payload = _valid_stage_closure_decision_readback(
            decision_ref=decision_ref,
            study_id=study_id,
            transaction_ref=transaction_ref,
        )
        if payload is None:
            continue
        try:
            mtime = decision_ref.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append((mtime, str(decision_ref), payload))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def _valid_stage_closure_decision_readback(
    *,
    decision_ref: Path,
    study_id: str,
    transaction_ref: str | None,
) -> dict[str, Any] | None:
    payload = _read_json_object(decision_ref)
    if payload.get("surface_kind") != "mas_stage_closure_decision":
        return None
    if _text(payload.get("study_id")) != study_id:
        return None
    if transaction_ref and _text(payload.get("paper_mission_transaction_ref")) != transaction_ref:
        return None
    if payload.get("counts_as_stage_closure_terminalizer_evidence") is not True:
        return None
    if any(
        payload.get(flag) is True
        for flag in (
            "authority_materialized",
            "writes_authority",
            "writes_runtime",
            "writes_yang_authority",
            "counts_as_owner_receipt",
            "counts_as_typed_blocker",
            "counts_as_human_gate",
            "counts_as_current_package",
            "counts_as_runtime_truth",
            "can_claim_paper_progress",
            "can_claim_submission_ready",
            "can_claim_publication_ready",
            "can_claim_runtime_ready",
        )
    ):
        return None
    boundary = _mapping(payload.get("authority_boundary"))
    if any(
        boundary.get(flag) is True
        for flag in (
            "writes_owner_receipt",
            "writes_typed_blocker",
            "writes_human_gate",
            "writes_current_package",
            "writes_submission_ready_package",
            "writes_runtime_queue_or_provider_attempt",
        )
    ):
        return None
    return {
        **payload,
        "terminalizer_decision_ref": _text(payload.get("decision_ref")),
        "decision_ref": str(decision_ref),
        "source_ref": str(decision_ref),
        "source_surface_kind": "paper_mission_stage_closure_ledger",
        "projection_status": "terminalizer_outcome_observed",
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _first_text(*values: Any) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _compact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}
