from __future__ import annotations

from pathlib import Path

from tests.test_domain_health_diagnostic_cases.shared import (
    _write_charter,
    _write_publication_eval,
)


def _domain_health_diagnostic_tick_request(study_root: Path, quest_root: Path) -> dict[str, object]:
    return {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(
            study_root,
            quest_root,
            action_type="bounded_analysis",
        ),
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": "Run bounded claim-evidence repair.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run bounded claim-evidence repair.",
        "work_unit_fingerprint": "publication-blockers::control-plane",
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
        },
    }


def _authority_snapshot(*, state: str, blocking_reasons: list[str] | None = None) -> dict[str, object]:
    blocked = state == "blocked"
    return {
        "schema_version": 1,
        "surface": "authority_snapshot",
        "control_state": "ready" if not blocked else "supervisor_gated",
        "canonical_next_action": "resume_same_study_line",
        "canonical_runtime_action": "continue_supervising_runtime",
        "dispatch_gate": {
            "state": state,
            "dispatch_allowed": not blocked,
            "blocking_reasons": blocking_reasons or [],
        },
        "route_authorization": {
            "authorized": not blocked,
            "paper_write_allowed": not blocked,
            "bundle_build_allowed": not blocked,
            "runtime_recovery_allowed": True,
        },
        "blocking_reasons": blocking_reasons or [],
        "allowed_controller_actions": ["read_runtime_status", "reconcile_control_plane"],
        "quality_gate_relaxation_allowed": False,
    }
