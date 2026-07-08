from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


BLOCKED_REASON = "claim_evidence_alignment_required"
OWNER_CALLABLE_SURFACE = "quality_repair_batch.run_quality_repair_batch"
REQUIRED_INPUT_SURFACE = "paper/claim_evidence_map.json + paper/evidence_ledger.json"
ERROR_MARKER = "claim_evidence_alignment"


def blocker_from_workflow_exception(*, study_root: Path, error: str) -> dict[str, Any] | None:
    if ERROR_MARKER not in error:
        return None
    claim_alignment = _extract_claim_alignment(study_root=study_root)
    return {
        "surface_kind": "claim_evidence_alignment_dispatch_blocker",
        "authority_source_signature": "ai_reviewer_publication_eval_workflow",
        "blocked_reason": BLOCKED_REASON,
        "currentness_error": error,
        "claim_evidence_alignment": claim_alignment,
        "missing_evidence_item_refs": _missing_evidence_item_refs(claim_alignment),
        "quality_verdict_written": False,
        "submission_package_regenerated": False,
        "next_owner": "write",
        "next_required_actions": ["run_quality_repair_batch", "return_to_ai_reviewer_workflow"],
        "required_input_surface": REQUIRED_INPUT_SURFACE,
        "owner_callable_surface": OWNER_CALLABLE_SURFACE,
    }


def _extract_claim_alignment(*, study_root: Path) -> dict[str, Any]:
    try:
        from med_autoscience.claim_evidence_alignment import build_claim_evidence_alignment_gate

        return build_claim_evidence_alignment_gate(
            study_root=study_root,
            claim_evidence_map_ref="paper/claim_evidence_map.json",
            evidence_ledger_ref="paper/evidence_ledger.json",
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "surface_kind": "claim_evidence_alignment_gate_v1",
            "status": "blocked",
            "blockers": ["claim_evidence_alignment_gate_unavailable"],
            "error": str(exc),
            "input_refs": {
                "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
                "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
            },
        }


def _missing_evidence_item_refs(claim_alignment: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    claims = claim_alignment.get("claims")
    if not isinstance(claims, list):
        return refs
    for claim in claims:
        if not isinstance(claim, Mapping):
            continue
        refs.extend(str(item) for item in claim.get("missing_evidence_item_refs") or [] if str(item or "").strip())
    return list(dict.fromkeys(refs))


__all__ = [
    "BLOCKED_REASON",
    "OWNER_CALLABLE_SURFACE",
    "REQUIRED_INPUT_SURFACE",
    "blocker_from_workflow_exception",
]
