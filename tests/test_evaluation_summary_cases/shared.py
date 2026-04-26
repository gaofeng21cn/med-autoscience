from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


MODULE_NAME = "med_autoscience.evaluation_summary"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _stable_inputs(tmp_path: Path) -> dict[str, object]:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    runtime_escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"

    charter_payload = {
        "schema_version": 1,
        "charter_id": "charter::001-risk::v1",
        "study_id": "001-risk",
        "publication_objective": "risk stratification external validation",
    }
    runtime_escalation_payload = {
        "schema_version": 1,
        "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-05T05:58:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T05:58:00+00:00",
        "trigger": {
            "trigger_id": "publishability_gate_blocked",
            "source": "publication_gate",
        },
        "scope": "quest",
        "severity": "study",
        "reason": "publishability_gate_blocked",
        "recommended_actions": ["return_to_controller", "review_publishability_gate"],
        "evidence_refs": [
            str(gate_report_path),
            str(quest_root / "artifacts" / "results" / "main_result.json"),
        ],
        "runtime_context_refs": {
            "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        },
        "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        "artifact_path": str(runtime_escalation_path),
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(charter_path),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(runtime_escalation_path),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [
                str(study_root / "paper"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
                str(study_root / "paper" / "review" / "review_ledger.json"),
                str(charter_path),
            ],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Primary claim still lacks external validation support.",
            "stop_loss_pressure": "watch",
        },
        "quality_assessment": {
            "clinical_significance": {
                "status": "partial",
                "summary": "Clinical framing is frozen, but the current result surface is still incomplete.",
                "evidence_refs": [str(gate_report_path)],
            },
            "evidence_strength": {
                "status": "blocked",
                "summary": "The current claim-evidence surface is still missing external validation support.",
                "evidence_refs": [str(gate_report_path)],
            },
            "novelty_positioning": {
                "status": "partial",
                "summary": "Novelty framing exists, but reviewer-facing contribution boundaries still need tightening.",
                "evidence_refs": [str(charter_path)],
            },
            "human_review_readiness": {
                "status": "blocked",
                "summary": "The draft is not yet honest enough to release as a human review package.",
                "evidence_refs": [str(gate_report_path)],
            },
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "External validation cohort is still missing.",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "results" / "main_result.json"),
                ],
            },
            {
                "gap_id": "gap-002",
                "gap_type": "reporting",
                "severity": "important",
                "summary": "Methods section still lacks endpoint provenance note.",
                "evidence_refs": [
                    str(gate_report_path),
                ],
            },
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Controller must decide whether to invest in external validation.",
                "evidence_refs": [
                    str(runtime_escalation_path),
                ],
                "requires_controller_decision": True,
            },
            {
                "action_id": "action-002",
                "action_type": "bounded_analysis",
                "priority": "next",
                "reason": "Prepare the missing endpoint provenance note before the next gate pass.",
                "route_target": "analysis-campaign",
                "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
                "route_rationale": "The study direction remains valid; only a bounded analysis-campaign repair is needed.",
                "evidence_refs": [
                    str(gate_report_path),
                ],
                "requires_controller_decision": True,
            },
        ],
    }
    gate_report_payload = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-04-05T06:05:00+00:00",
        "quest_id": "quest-001",
        "status": "blocked",
        "allow_write": False,
        "recommended_action": "return_to_publishability_gate",
        "latest_gate_path": str(gate_report_path),
        "supervisor_phase": "publishability_gate_blocked",
        "current_required_action": "return_to_publishability_gate",
        "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        "blockers": ["missing_post_main_publishability_gate"],
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
    }

    _write_json(charter_path, charter_payload)
    _write_json(publication_eval_path, publication_eval_payload)
    _write_json(runtime_escalation_path, runtime_escalation_payload)
    _write_json(gate_report_path, gate_report_payload)

    return {
        "study_root": study_root,
        "quest_root": quest_root,
        "charter_path": charter_path,
        "publication_eval_path": publication_eval_path,
        "runtime_escalation_path": runtime_escalation_path,
        "gate_report_path": gate_report_path,
        "charter_payload": charter_payload,
        "publication_eval_payload": publication_eval_payload,
        "runtime_escalation_payload": runtime_escalation_payload,
        "gate_report_payload": gate_report_payload,
    }


def _write_reporting_contract_task_intake(study_root: Path) -> dict[str, object]:
    payload = {
        "schema_version": 1,
        "task_id": f"study-task::{study_root.name}::20260418T210434Z",
        "emitted_at": "2026-04-18T21:04:34+00:00",
        "study_id": study_root.name,
        "study_root": str(study_root.resolve()),
        "entry_mode": "full_research",
        "task_intent": (
            "Continue non-final write/review maintenance under supervisor-only runtime ownership. "
            "Repair the medical reporting/display contract mismatch that still blocks medical_reporting_audit: "
            "registry_contract_mismatch, missing_local_architecture_overview_shell, and "
            "missing_local_architecture_overview_inputs. Do not reopen manuscript evidence adequacy, "
            "do not expand public data, and do not change scientific claims; align the reporting contract, "
            "display registry, and required shell/input surfaces to the already accepted active display package. "
            "After the repair, rerun medical_reporting_audit/runtime_watch/publication-gate status so the "
            "study-level progress card no longer reports stale quality-floor blockers."
        ),
        "journal_target": None,
        "constraints": [
            "Keep route non-final write/review; do not treat gate clear, bundle presence, or checklist handoff as finalize or quest completion.",
            "Foreground Codex remains supervisor-only and must not directly edit runtime-owned paper surfaces unless runtime is explicitly paused and takeover is approved.",
        ],
        "evidence_boundary": [
            "Retained public evidence stays unchanged; do not reopen manuscript evidence adequacy or expand public data."
        ],
        "trusted_inputs": [
            "Latest manuscript/story contract is valid; current blocker is delivery/reporting contract mismatch, not manuscript evidence failure."
        ],
        "reference_papers": [],
        "first_cycle_outputs": [],
    }
    _write_json(study_root / "artifacts" / "controller" / "task_intake" / "latest.json", payload)
    return payload





































