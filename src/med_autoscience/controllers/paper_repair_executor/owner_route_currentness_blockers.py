from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from med_autoscience.controllers import paper_repair_execution_evidence


OWNER_ROUTE_CURRENTNESS_BLOCKERS = {
    "owner_route_stale",
    "owner_route_next_owner_mismatch",
    "owner_route_currentness_basis_missing",
}


@dataclass(frozen=True)
class CurrentnessBlockerMaterialization:
    evidence_path: Path
    receipt_fields: Mapping[str, Any]
    result_fields: Mapping[str, Any]


def materialize(
    study_id: str,
    quest_id: str,
    study_root: Path,
    repair_work_unit: Mapping[str, Any],
    owner_result: Mapping[str, Any],
    typed_blocker: str | None,
    evidence_path: Path,
) -> CurrentnessBlockerMaterialization:
    if typed_blocker not in OWNER_ROUTE_CURRENTNESS_BLOCKERS:
        return CurrentnessBlockerMaterialization(
            evidence_path=evidence_path,
            receipt_fields={},
            result_fields={},
        )
    evidence_payload = _read_evidence(evidence_path)
    if not isinstance(evidence_payload, dict):
        evidence_payload = paper_repair_execution_evidence.build_repair_execution_evidence(
            study_id=study_id,
            quest_id=quest_id,
            study_root=study_root,
            repair_work_unit=repair_work_unit,
            review_finding={
                "surface": "paper_repair_executor",
                "blocked_reason": typed_blocker,
                "owner_result": dict(owner_result),
            },
            source_refs=repair_work_unit.get("source_refs") or [],
            changed_artifact_refs=[],
        )
        evidence_path = paper_repair_execution_evidence.write_repair_execution_evidence(
            study_root=study_root,
            evidence=evidence_payload,
        )
    evidence_payload["retryable"] = False
    _write_json(evidence_path, evidence_payload)
    return CurrentnessBlockerMaterialization(
        evidence_path=evidence_path,
        receipt_fields={"retryable": False},
        result_fields={"retryable": False, "repair_execution_evidence": evidence_payload},
    )


def _read_evidence(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = ["materialize"]
