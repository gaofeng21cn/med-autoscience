from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import _clear_readiness_report, make_profile, write_study, write_text


def _write_controller_decision_authorization(
    study_root: Path,
    *,
    study_id: str,
) -> None:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    runtime_escalation_path = study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "decision-analysis-001",
                "study_id": study_id,
                "quest_id": study_id,
                "emitted_at": "2026-05-07T12:00:00+00:00",
                "decision_type": "bounded_analysis",
                "charter_ref": {
                    "charter_id": f"charter::{study_id}::v1",
                    "artifact_path": str(charter_path),
                },
                "runtime_escalation_ref": {
                    "record_id": f"runtime-escalation::{study_id}::v1",
                    "artifact_path": str(runtime_escalation_path),
                    "summary_ref": str(runtime_escalation_path),
                },
                "publication_eval_ref": {
                    "eval_id": f"publication-eval::{study_id}::{study_id}::latest",
                    "artifact_path": str(publication_eval_path),
                },
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": "run_quality_repair_batch", "payload_ref": str(decision_path)}],
                "reason": "Run one controller-owned quality repair batch before returning to gate.",
                "route_target": "analysis-campaign",
                "route_key_question": "What is the narrowest same-line manuscript repair required now?",
                "route_rationale": "The revision line needs a bounded quality pass.",
                "work_unit_fingerprint": "publication-blockers::claim-story-figure",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_publication_eval_work_unit_authority(study_root: Path) -> None:
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::001-risk::001-risk::latest",
                "emitted_at": "2026-05-07T12:01:00+00:00",
                "recommended_actions": [
                    {
                        "action_type": "bounded_analysis",
                        "route_target": "analysis-campaign",
                        "route_key_question": "broad reviewer revision checklist",
                        "route_rationale": "Gate requires controller-owned analysis repair.",
                        "work_unit_fingerprint": "publication-blockers::claim-story-figure",
                        "next_work_unit": {
                            "unit_id": "analysis_claim_evidence_repair",
                            "lane": "analysis-campaign",
                            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                        },
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "claim_evidence_map",
                                "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                                "blocking_reason": "claim_evidence_consistency_failed",
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_adopted_artifact_event(study_root: Path) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"source": "test"},
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="artifact_written",
        payload={
            "active_run_id": None,
            "created_at": "2026-05-07T12:06:55+00:00",
            "work_unit_id": "analysis_claim_evidence_repair",
            "route_target": "analysis-campaign",
            "recommended_next_route": "return_to_publication_gate_recheck",
            "source": "test",
            "result": {
                "local_traceability_repair_complete": True,
                "specificity_targets_repaired_or_classified": 1,
                "missing_target_files_after_repair": 0,
                "targets_with_repair_markers": 1,
                "publication_gate_cleared": False,
            },
        },
    )


def test_progress_projection_projects_adopted_work_unit_evidence_without_runtime_recovery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / study_id
    write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "active",
                "active_run_id": None,
                "pending_user_message_count": 0,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "same_fingerprint_no_artifact_delta",
            }
        )
        + "\n",
    )
    _write_controller_decision_authorization(study_root, study_id=study_id)
    _write_publication_eval_work_unit_authority(study_root)
    _write_adopted_artifact_event(study_root)
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, study_id),
    )
    result = module.progress_projection(profile=profile, study_id=study_id, include_progress_projection=False)

    assert not hasattr(module, "managed_runtime" + "_transport")
    assert result["decision"] == "noop"
    assert result["reason"] == "controller_work_unit_evidence_adopted"
    assert "runtime_recovery_lifecycle" not in result
    assert result["controller_work_unit_evidence_adoption"]["already_recorded"] is True
    assert result["controller_work_unit_next_route"] == {
        "recommended_next_route": "return_to_publication_gate_recheck",
        "owner": "publication_gate",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": True,
    }


def test_read_only_progress_projection_does_not_materialize_publication_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / study_id
    write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\nstudy_id: {study_id}\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": None,
                "pending_user_message_count": 0,
                "continuation_policy": "auto",
            }
        )
        + "\n",
    )
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    charter_path.parent.mkdir(parents=True, exist_ok=True)
    charter_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": f"charter::{study_id}::v1",
                "study_id": study_id,
                "title": "Read-only publication eval guard",
                "publication_objective": "Verify read projections do not write eval authority.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    gate_root = quest_root / "artifacts" / "reports" / "publishability_gate"
    gate_path = gate_root / "latest.json"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "gate_kind": "publishability_control",
                "generated_at": "2026-05-27T01:00:00+00:00",
                "quest_id": study_id,
                "study_id": study_id,
                "paper_root": str(study_root / "paper"),
                "latest_gate_path": str(gate_path),
                "main_result_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
                "submission_minimal_manifest_path": str(
                    study_root / "paper" / "submission_minimal" / "submission_manifest.json"
                ),
                "status": "blocked",
                "allow_write": False,
                "recommended_action": "return_to_controller",
                "blockers": ["medical_publication_surface_blocked"],
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "read-only projection should not materialize eval latest",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, study_id),
    )

    result = module.progress_projection(
        profile=profile,
        study_id=study_id,
        include_progress_projection=False,
        sync_runtime_summary=False,
    )

    assert result["study_id"] == study_id
    assert not eval_path.exists()


def test_read_only_study_progress_does_not_materialize_status_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    status_module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / study_id
    write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\nstudy_id: {study_id}\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": None,
                "pending_user_message_count": 0,
                "continuation_policy": "auto",
            }
        )
        + "\n",
    )
    write_text(
        quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.json",
        json.dumps(
            {
                "controllers": {
                    "publication_gate": {
                        "report_json": str(
                            quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
                        )
                    }
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "gate_kind": "publishability_control",
                "generated_at": "2026-05-27T01:00:00+00:00",
                "quest_id": study_id,
                "study_id": study_id,
                "paper_root": str(study_root / "paper"),
                "status": "blocked",
                "allow_write": False,
                "recommended_action": "return_to_controller",
                "blockers": ["medical_publication_surface_blocked"],
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "runtime" / "runtime_escalation_record.json",
        json.dumps(
            {
                "schema_version": 1,
                "record_id": f"runtime-escalation::{study_id}::v1",
                "study_id": study_id,
                "quest_id": study_id,
                "status": "blocked",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    forbidden_paths = [
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        study_root / "artifacts" / "controller" / "controller_summary.json",
        study_root / "artifacts" / "controller" / "study_charter.json",
        study_root / "artifacts" / "medical_paper" / "readiness.json",
        study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json",
    ]
    for path in forbidden_paths:
        if path.exists():
            path.unlink()
    monkeypatch.setattr(
        status_module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        status_module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, study_id),
    )

    result = progress_module.read_study_progress(
        profile=profile,
        study_id=study_id,
        sync_runtime_summary=False,
    )

    assert result["study_id"] == study_id
    assert [str(path.relative_to(study_root)) for path in forbidden_paths if path.exists()] == []
