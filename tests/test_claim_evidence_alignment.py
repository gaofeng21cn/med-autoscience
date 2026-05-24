from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _claim_map() -> dict[str, Any]:
    return {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary claim is supported by the current cohort.",
                "status": "supported",
                "paper_role": "primary_result",
                "display_bindings": ["table-1"],
                "sections": ["Results"],
                "evidence_items": [
                    {
                        "item_id": "evidence-primary",
                        "support_level": "direct",
                        "source_paths": ["artifacts/results/main_result.json"],
                    }
                ],
            }
        ]
    }


def _evidence_ledger(*, evidence_id: str = "evidence-primary") -> dict[str, Any]:
    return {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary claim is supported by the current cohort.",
                "status": "supported",
                "submission_scope": "manuscript",
                "evidence": [
                    {
                        "evidence_id": evidence_id,
                        "kind": "analysis_result",
                        "source_paths": ["artifacts/results/main_result.json"],
                        "support_level": "direct",
                        "summary": "Current cohort result supports the primary claim.",
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "gap-none",
                        "description": "No blocker for the primary claim.",
                        "submission_impact": "none",
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "action-none",
                        "priority": "none",
                        "description": "No action required for this claim.",
                    }
                ],
            }
        ]
    }


def test_claim_evidence_alignment_gate_ready_when_claim_and_evidence_ids_match(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.claim_evidence_alignment")
    study_root = tmp_path / "study"
    claim_map_ref = study_root / "paper" / "claim_evidence_map.json"
    evidence_ledger_ref = study_root / "paper" / "evidence_ledger.json"
    _write_json(claim_map_ref, _claim_map())
    _write_json(evidence_ledger_ref, _evidence_ledger())

    gate = module.build_claim_evidence_alignment_gate(
        study_root=study_root,
        claim_evidence_map_ref="paper/claim_evidence_map.json",
        evidence_ledger_ref="paper/evidence_ledger.json",
    )

    assert gate["surface_kind"] == "claim_evidence_alignment_gate_v1"
    assert gate["source_project"] == "academic-research-skills"
    assert gate["absorbed_as"] == "mas_native_claim_evidence_alignment_gate"
    assert gate["status"] == "ready"
    assert gate["claim_count"] == 1
    assert gate["aligned_claim_count"] == 1
    assert gate["body_included"] is False
    assert gate["may_authorize_publication_readiness"] is False
    assert gate["may_authorize_quality_verdict"] is False
    assert gate["can_write_domain_truth"] is False
    assert gate["missing_required_fields"] == []
    assert gate["blockers"] == []
    assert gate["claims"] == [
        {
            "claim_id": "claim-primary",
            "status": "aligned",
            "evidence_item_refs": ["evidence-primary"],
            "support_levels": ["direct"],
        }
    ]


def test_claim_evidence_alignment_gate_blocks_when_source_paths_overlap_but_ids_do_not(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.claim_evidence_alignment")
    study_root = tmp_path / "study"
    claim_map_ref = study_root / "paper" / "claim_evidence_map.json"
    evidence_ledger_ref = study_root / "paper" / "evidence_ledger.json"
    _write_json(claim_map_ref, _claim_map())
    _write_json(evidence_ledger_ref, _evidence_ledger(evidence_id="evidence-renamed"))

    gate = module.build_claim_evidence_alignment_gate(
        study_root=study_root,
        claim_evidence_map_ref=claim_map_ref,
        evidence_ledger_ref=evidence_ledger_ref,
    )

    assert gate["status"] == "blocked"
    assert gate["aligned_claim_count"] == 0
    assert gate["blockers"] == ["claim-primary.evidence-primary_missing_from_evidence_ledger"]
    assert gate["claims"] == [
        {
            "claim_id": "claim-primary",
            "status": "blocked",
            "evidence_item_refs": ["evidence-primary"],
            "support_levels": ["direct"],
            "defect_stage": "evidence_id_alignment",
            "missing_evidence_item_refs": ["evidence-primary"],
        }
    ]
