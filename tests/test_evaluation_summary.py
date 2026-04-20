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
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Primary claim still lacks external validation support.",
            "stop_loss_pressure": "watch",
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


def test_resolve_evaluation_summary_ref_defaults_to_eval_hygiene_latest_surface(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_evaluation_summary_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json").resolve()


def test_resolve_promotion_gate_ref_defaults_to_eval_hygiene_latest_surface(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_promotion_gate_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json").resolve()


def test_resolve_promotion_gate_ref_rejects_controller_publishability_gate_projection(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    projected_ref = study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"

    with pytest.raises(ValueError, match="eval hygiene-owned promotion gate artifact"):
        module.resolve_promotion_gate_ref(study_root=study_root, ref=projected_ref)


def test_materialize_evaluation_summary_artifacts_writes_typed_stable_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    runtime_escalation_payload = inputs["runtime_escalation_payload"]
    gate_report_path = inputs["gate_report_path"]

    written_refs = module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref={
            "record_id": runtime_escalation_payload["record_id"],
            "artifact_path": runtime_escalation_payload["artifact_path"],
            "summary_ref": runtime_escalation_payload["summary_ref"],
        },
        publishability_gate_report_ref=gate_report_path,
    )

    promotion_gate_path = study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json"
    evaluation_summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    promotion_gate_payload = json.loads(promotion_gate_path.read_text(encoding="utf-8"))
    evaluation_summary_payload = json.loads(evaluation_summary_path.read_text(encoding="utf-8"))

    assert written_refs == {
        "evaluation_summary_ref": {
            "summary_id": "evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "artifact_path": str(evaluation_summary_path.resolve()),
        },
        "promotion_gate_ref": {
            "gate_id": "promotion-gate::001-risk::quest-001::2026-04-05T06:05:00+00:00",
            "artifact_path": str(promotion_gate_path.resolve()),
        },
    }
    assert promotion_gate_payload == {
        "schema_version": 1,
        "gate_id": "promotion-gate::001-risk::quest-001::2026-04-05T06:05:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:05:00+00:00",
        "source_gate_report_ref": str(gate_report_path.resolve()),
        "publication_eval_ref": {
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "artifact_path": str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
        },
        "runtime_escalation_ref": {
            "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-05T05:58:00+00:00",
            "artifact_path": str(
                (
                    inputs["quest_root"]
                    / "artifacts"
                    / "reports"
                    / "escalation"
                    / "runtime_escalation_record.json"
                ).resolve()
            ),
            "summary_ref": str((study_root / "artifacts" / "runtime" / "last_launch_report.json").resolve()),
        },
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "stop_loss_pressure": "watch",
        "status": "blocked",
        "allow_write": False,
        "recommended_action": "return_to_publishability_gate",
        "current_required_action": "return_to_publishability_gate",
        "supervisor_phase": "publishability_gate_blocked",
        "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        "blockers": ["missing_post_main_publishability_gate"],
    }
    assert evaluation_summary_payload == {
        "schema_version": 1,
        "summary_id": "evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "charter_ref": {
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str((study_root / "artifacts" / "controller" / "study_charter.json").resolve()),
            "publication_objective": "risk stratification external validation",
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "artifact_path": str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
        },
        "runtime_escalation_ref": {
            "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-05T05:58:00+00:00",
            "artifact_path": str(
                (
                    inputs["quest_root"]
                    / "artifacts"
                    / "reports"
                    / "escalation"
                    / "runtime_escalation_record.json"
                ).resolve()
            ),
            "summary_ref": str((study_root / "artifacts" / "runtime" / "last_launch_report.json").resolve()),
        },
        "promotion_gate_ref": {
            "gate_id": "promotion-gate::001-risk::quest-001::2026-04-05T06:05:00+00:00",
            "artifact_path": str(promotion_gate_path.resolve()),
        },
        "evaluation_scope": "publication",
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "verdict_summary": "Primary claim still lacks external validation support.",
        "stop_loss_pressure": "watch",
        "publication_objective": "risk stratification external validation",
        "gap_counts": {
            "must_fix": 1,
            "important": 1,
            "optional": 0,
            "total": 2,
        },
        "recommended_action_types": ["return_to_controller", "bounded_analysis"],
        "route_repair_plan": {
            "action_id": "action-002",
            "action_type": "bounded_analysis",
            "priority": "next",
            "route_target": "analysis-campaign",
            "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
            "route_rationale": "The study direction remains valid; only a bounded analysis-campaign repair is needed.",
        },
        "requires_controller_decision": True,
        "promotion_gate_status": {
            "status": "blocked",
            "allow_write": False,
            "current_required_action": "return_to_publishability_gate",
            "blockers": ["missing_post_main_publishability_gate"],
        },
    }
    assert module.read_promotion_gate(study_root=study_root) == promotion_gate_payload
    assert module.read_evaluation_summary(study_root=study_root) == evaluation_summary_payload


def test_materialize_evaluation_summary_artifacts_rejects_runtime_escalation_ref_mismatch(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    gate_report_path = inputs["gate_report_path"]

    with pytest.raises(ValueError, match="runtime escalation ref mismatch"):
        module.materialize_evaluation_summary_artifacts(
            study_root=study_root,
            runtime_escalation_ref={
                "record_id": "runtime-escalation::wrong",
                "artifact_path": str(inputs["runtime_escalation_path"]),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "wrong_launch_report.json"),
            },
            publishability_gate_report_ref=gate_report_path,
        )


def test_materialize_evaluation_summary_artifacts_rejects_charter_context_drift(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    gate_report_path = inputs["gate_report_path"]
    publication_eval_path = inputs["publication_eval_path"]
    publication_eval_payload = dict(inputs["publication_eval_payload"])
    publication_eval_payload["charter_context_ref"] = {
        "ref": str(inputs["charter_path"]),
        "charter_id": "charter::001-risk::v1",
        "publication_objective": "mismatched objective",
    }
    _write_json(publication_eval_path, publication_eval_payload)

    with pytest.raises(ValueError, match="publication objective mismatch"):
        module.materialize_evaluation_summary_artifacts(
            study_root=study_root,
            runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
            publishability_gate_report_ref=gate_report_path,
        )


def test_read_evaluation_summary_rejects_non_object_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    evaluation_summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    _write_json(evaluation_summary_path, ["not", "an", "object"])

    with pytest.raises(ValueError, match="JSON object"):
        module.read_evaluation_summary(study_root=study_root)


def test_materialize_evaluation_summary_artifacts_prefers_now_priority_route_repair_plan(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    publication_eval_path = inputs["publication_eval_path"]
    gate_report_path = inputs["gate_report_path"]
    publication_eval_payload = dict(inputs["publication_eval_payload"])
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "action-010",
            "action_type": "bounded_analysis",
            "priority": "next",
            "reason": "Prepare sensitivity analysis after the main repair.",
            "route_target": "analysis-campaign",
            "route_key_question": "What bounded robustness check should run after the main repair?",
            "route_rationale": "This remains a next-step bounded analysis.",
            "evidence_refs": [str(gate_report_path)],
            "requires_controller_decision": True,
        },
        {
            "action_id": "action-011",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Repair the manuscript claim-evidence surface first.",
            "route_target": "write",
            "route_key_question": "What is the narrowest paper-writing repair needed before any follow-up analysis?",
            "route_rationale": "The current blocker sits on the write surface, so same-line repair should start there.",
            "evidence_refs": [str(inputs["runtime_escalation_path"])],
            "requires_controller_decision": True,
        },
    ]
    _write_json(publication_eval_path, publication_eval_payload)

    module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
        publishability_gate_report_ref=gate_report_path,
    )

    evaluation_summary_payload = module.read_evaluation_summary(study_root=study_root)

    assert evaluation_summary_payload["route_repair_plan"] == {
        "action_id": "action-011",
        "action_type": "route_back_same_line",
        "priority": "now",
        "route_target": "write",
        "route_key_question": "What is the narrowest paper-writing repair needed before any follow-up analysis?",
        "route_rationale": "The current blocker sits on the write surface, so same-line repair should start there.",
    }
