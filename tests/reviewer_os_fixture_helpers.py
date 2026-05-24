from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def ready_claim_evidence_alignment_gate(
    *,
    claim_evidence_map_ref: str = "paper/claim_evidence_map.json",
    evidence_ledger_ref: str = "paper/evidence_ledger.json",
) -> dict[str, Any]:
    return {
        "surface_kind": "claim_evidence_alignment_gate_v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_claim_evidence_alignment_gate",
        "status": "ready",
        "input_refs": {
            "claim_evidence_map": claim_evidence_map_ref,
            "evidence_ledger": evidence_ledger_ref,
        },
        "claim_count": 1,
        "aligned_claim_count": 1,
        "claims": [
            {
                "claim_id": "claim-primary",
                "status": "aligned",
                "evidence_item_refs": ["evidence-primary"],
                "support_levels": ["direct"],
            }
        ],
        "fail_closed_when_missing": True,
        "missing_required_fields": [],
        "blockers": [],
        "body_included": False,
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
    }


def claim_evidence_alignment_digest(gate: dict[str, Any]) -> str:
    encoded = json.dumps(gate, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def claim_evidence_map_payload(*, evidence_ledger_ref: str) -> dict[str, Any]:
    return {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary manuscript claim is supported by the current analysis.",
                "status": "supported",
                "paper_role": "primary_result",
                "display_bindings": ["table-1"],
                "sections": ["Results"],
                "evidence_items": [
                    {
                        "item_id": "evidence-primary",
                        "support_level": "direct",
                        "source_paths": [evidence_ledger_ref],
                    }
                ],
            }
        ]
    }


def evidence_ledger_payload(*, evidence_ledger_ref: str, evidence_id: str = "evidence-primary") -> dict[str, Any]:
    return {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary manuscript claim is supported by the current analysis.",
                "status": "supported",
                "submission_scope": "manuscript",
                "evidence": [
                    {
                        "evidence_id": evidence_id,
                        "kind": "analysis_result",
                        "source_paths": [evidence_ledger_ref],
                        "support_level": "direct",
                        "summary": "Current analysis supports the primary claim.",
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "gap-none",
                        "description": "No blocking claim-evidence gap remains.",
                        "submission_impact": "none",
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "action-none",
                        "priority": "none",
                        "description": "No claim-evidence repair required.",
                    }
                ],
            }
        ]
    }


def review_ledger_payload(*, revision_log_path: str | Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "concerns": [
            {
                "concern_id": "concern-closed",
                "reviewer_id": "ai-reviewer",
                "summary": "Claim-evidence alignment reviewed.",
                "severity": "minor",
                "status": "resolved",
                "owner_action": "Keep claims tied to current evidence refs.",
                "revision_links": [
                    {
                        "revision_id": "revision-claim-alignment",
                        "revision_log_path": str(revision_log_path),
                    }
                ],
            }
        ],
    }
