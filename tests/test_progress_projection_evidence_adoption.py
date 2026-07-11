from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import (
    _clear_readiness_report,
    make_profile,
    write_study,
    write_text,
)


STUDY_ID = "001-risk"
FINGERPRINT = "publication-blockers::claim-story-figure"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _setup_study(tmp_path: Path):
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        STUDY_ID,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / STUDY_ID
    write_text(quest_root / "quest.yaml", f"quest_id: {STUDY_ID}\nstudy_id: {STUDY_ID}\n")
    state = {
        "status": "active",
        "active_run_id": None,
        "pending_user_message_count": 0,
        "continuation_policy": "auto",
        "continuation_anchor": "decision",
        "continuation_reason": "same_fingerprint_no_artifact_delta",
    }
    _write_json(quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json", state)
    _write_json(quest_root / ".ds" / "runtime_state.json", state)
    return profile, study_root, quest_root


def _patch_readiness(module, monkeypatch, profile) -> None:
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, STUDY_ID),
    )


def _write_work_unit_authority(study_root: Path) -> None:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_id": "decision-analysis-001",
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "emitted_at": "2026-05-07T12:00:00+00:00",
            "decision_type": "bounded_analysis",
            "charter_ref": {
                "charter_id": f"charter::{STUDY_ID}::v1",
                "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            },
            "runtime_escalation_ref": {
                "record_id": f"runtime-escalation::{STUDY_ID}::v1",
                "artifact_path": str(
                    study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"
                ),
                "summary_ref": str(
                    study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"
                ),
            },
            "publication_eval_ref": {
                "eval_id": f"publication-eval::{STUDY_ID}::{STUDY_ID}::latest",
                "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "requires_human_confirmation": False,
            "controller_actions": [{
                "action_type": "run_quality_repair_batch",
                "payload_ref": str(decision_path),
            }],
            "reason": "Run one controller-owned quality repair batch.",
            "route_target": "analysis-campaign",
            "route_key_question": "What is the narrowest same-line repair?",
            "route_rationale": "The revision line needs a bounded quality pass.",
            "work_unit_fingerprint": FINGERPRINT,
            "next_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence and traceability blockers.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": f"publication-eval::{STUDY_ID}::{STUDY_ID}::latest",
            "emitted_at": "2026-05-07T12:01:00+00:00",
            "recommended_actions": [{
                "action_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "route_key_question": "broad reviewer revision checklist",
                "route_rationale": "Gate requires controller-owned analysis repair.",
                "work_unit_fingerprint": FINGERPRINT,
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence and traceability blockers.",
                },
                "specificity_targets": [{
                    "target_kind": "claim",
                    "target_id": "claim_evidence_map",
                    "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    "blocking_reason": "claim_evidence_consistency_failed",
                }],
            }],
        },
    )


def _write_adopted_event(study_root: Path) -> None:
    authorization = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    context = authorization._load_controller_decision_authorization_context(study_root=study_root)
    assert context is not None
    identity = authorization._controller_decision_authorization_identity(context)
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
            "work_unit_id": "analysis_claim_evidence_repair",
            "route_target": "analysis-campaign",
            "recommended_next_route": "return_to_publication_gate_recheck",
            "source": "test",
            "result": {
                "local_traceability_repair_complete": True,
                "specificity_targets_repaired_or_classified": 1,
                "missing_target_files_after_repair": 0,
                "publication_gate_cleared": False,
            },
        },
    )


def test_progress_projection_projects_adopted_work_unit_evidence_without_runtime_recovery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    profile, study_root, _ = _setup_study(tmp_path)
    _write_work_unit_authority(study_root)
    _write_adopted_event(study_root)
    _patch_readiness(module, monkeypatch, profile)

    result = module.progress_projection(
        profile=profile,
        study_id=STUDY_ID,
        include_progress_projection=False,
    )

    assert result["reason"] == "controller_work_unit_evidence_adopted"
    assert "runtime_recovery_lifecycle" not in result
    assert result["controller_work_unit_evidence_adoption"]["already_recorded"] is True
    assert result["controller_work_unit_next_route"] == {
        "recommended_next_route": "return_to_publication_gate_recheck",
        "owner": "publication_gate",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": True,
    }


def test_read_only_study_progress_does_not_materialize_authority_or_status_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    status_module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile, study_root, quest_root = _setup_study(tmp_path)
    _write_json(
        quest_root / "artifacts" / "reports" / "domain_diagnostic_report" / "latest.json",
        {"controllers": {"publication_gate": {"report_json": str(
            quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        )}}},
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "quest_id": STUDY_ID,
            "study_id": STUDY_ID,
            "paper_root": str(study_root / "paper"),
            "status": "blocked",
            "allow_write": False,
            "recommended_action": "return_to_controller",
            "blockers": ["medical_publication_surface_blocked"],
            "supervisor_phase": "publishability_gate_blocked",
            "current_required_action": "return_to_publishability_gate",
        },
    )
    forbidden = [
        study_root / "artifacts" / "publication_eval" / "latest.json",
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        study_root / "artifacts" / "controller" / "controller_summary.json",
        study_root / "artifacts" / "controller" / "study_charter.json",
        study_root / "artifacts" / "medical_paper" / "readiness.json",
        study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json",
        study_root / "artifacts" / "eval_hygiene" / "runtime_escalation_context" / "latest.json",
    ]
    for path in forbidden:
        path.unlink(missing_ok=True)
    _patch_readiness(status_module, monkeypatch, profile)

    with pytest.raises(
        FileNotFoundError,
        match="requires an OPL runtime owner handoff ref",
    ):
        progress_module.read_study_progress(
            profile=profile,
            study_id=STUDY_ID,
            sync_runtime_summary=False,
        )

    assert not any(path.exists() for path in forbidden)
