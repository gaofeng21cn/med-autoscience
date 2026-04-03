from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from .study_runtime_test_helpers import (
    _clear_readiness_report,
    make_analysis_bundle_result,
    make_completion_sync_payload,
    make_partial_quest_recovery_payload,
    make_profile,
    make_runtime_overlay_result,
    make_startup_contract_validation_payload,
    make_startup_context_sync_payload,
    make_startup_hydration_report,
    make_startup_hydration_validation_report,
    write_study,
    write_text,
)


def test_study_runtime_status_round_trips_through_typed_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
        "decision": "resume",
        "reason": "quest_paused",
        "runtime_overlay": {"audit": {"all_roots_ready": True}},
    }

    status = module.StudyRuntimeStatus.from_payload(payload)
    expected_payload = dict(payload)
    expected_payload["study_completion_contract"] = {
        "ready": False,
        "status": "absent",
        "completion_status": None,
        "summary": "",
        "user_approval_text": "",
        "completed_at": None,
        "evidence_paths": [],
        "missing_evidence_paths": [],
        "errors": [],
    }

    assert status.decision is module.StudyRuntimeDecision.RESUME
    assert status.reason is module.StudyRuntimeReason.QUEST_PAUSED
    assert status.quest_status is module.StudyRuntimeQuestStatus.PAUSED
    assert status.quest_id == "quest-001"
    assert status.quest_root == "/tmp/runtime/quests/quest-001"
    assert status.quest_exists is True
    assert status.to_dict() == expected_payload

    status.set_decision("blocked", "startup_contract_resolution_failed")
    status.update_quest_runtime(
        quest_id="quest-002",
        quest_root="/tmp/runtime/quests/quest-002",
        quest_exists=False,
        quest_status="created",
    )

    assert status.decision is module.StudyRuntimeDecision.BLOCKED
    assert status.reason is module.StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED
    assert status.quest_status is module.StudyRuntimeQuestStatus.CREATED
    assert status.quest_id == "quest-002"
    assert status.quest_root == "/tmp/runtime/quests/quest-002"
    assert status.quest_exists is False
    assert status.to_dict()["decision"] == "blocked"
    assert status.to_dict()["reason"] == "startup_contract_resolution_failed"
    assert status.to_dict()["quest_status"] == "created"
    assert status.to_dict()["quest_id"] == "quest-002"
    assert status.to_dict()["quest_root"] == "/tmp/runtime/quests/quest-002"


def test_study_runtime_status_treats_stopped_quest_as_resumable(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stopped"
    assert result["quest_status"] == "stopped"


def test_study_runtime_status_mapping_semantics_follow_serialized_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)
    expected_payload = dict(payload)
    expected_payload["study_completion_contract"] = {
        "ready": False,
        "status": "absent",
        "completion_status": None,
        "summary": "",
        "user_approval_text": "",
        "completed_at": None,
        "evidence_paths": [],
        "missing_evidence_paths": [],
        "errors": [],
    }

    assert dict(status) == expected_payload
    assert "decision" not in status
    assert status.get("decision", "fallback") == "fallback"


def test_study_runtime_status_core_key_assignment_uses_typed_normalization() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    status["decision"] = "blocked"
    status["reason"] = "runtime_overlay_not_ready"
    status["quest_root"] = Path("/tmp/runtime/quests/quest-002")
    status["quest_exists"] = False
    status["quest_status"] = None
    status["workspace_contracts"] = {"overall_ready": False}
    status["startup_data_readiness"] = {"study_summary": {"unresolved_contract_study_ids": ["001-risk"]}}
    status["startup_boundary_gate"] = {
        "allow_compute_stage": False,
        "required_first_anchor": "scout",
        "effective_custom_profile": "freeform",
        "legacy_code_execution_allowed": False,
    }
    status["runtime_reentry_gate"] = {
        "allow_runtime_entry": False,
        "require_startup_hydration": True,
        "require_managed_skill_audit": True,
    }

    assert status.decision is module.StudyRuntimeDecision.BLOCKED
    assert status.reason is module.StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY
    assert status.quest_root == "/tmp/runtime/quests/quest-002"
    assert status.quest_exists is False
    assert status.quest_status is None
    assert status.workspace_contracts_summary.overall_ready is False
    assert status.startup_data_readiness_report.has_unresolved_contract_for("001-risk") is True
    assert status.startup_boundary_gate_result.allow_compute_stage is False
    assert status.runtime_reentry_gate_result.require_startup_hydration is True
    assert status.to_dict()["quest_root"] == "/tmp/runtime/quests/quest-002"

    with pytest.raises(TypeError, match="quest_exists"):
        status["quest_exists"] = "false"
    with pytest.raises(TypeError, match="study runtime workspace contracts payload"):
        status["workspace_contracts"] = []
    with pytest.raises(ValueError, match="study runtime startup data readiness study_summary"):
        status["startup_data_readiness"] = {"study_summary": []}
    with pytest.raises(TypeError, match="study runtime startup boundary allow_compute_stage"):
        status["startup_boundary_gate"] = {"allow_compute_stage": "false"}
    with pytest.raises(TypeError, match="study runtime reentry require_managed_skill_audit"):
        status["runtime_reentry_gate"] = {"allow_runtime_entry": True, "require_managed_skill_audit": "true"}


def test_study_runtime_status_normalizes_study_completion_contract_to_typed_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(tmp_path / "studies" / "001-risk"),
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": str(tmp_path / "runtime" / "quests" / "quest-001"),
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": str(tmp_path / "studies" / "001-risk" / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False, "errors": []},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)
    status["study_completion_contract"] = {
        "ready": True,
        "status": "resolved",
        "completion_status": "completed",
        "summary": "Study is done.",
        "user_approval_text": "同意",
        "completed_at": "2026-04-03T00:00:00+00:00",
        "evidence_paths": ["manuscript/final/submission_manifest.json"],
        "missing_evidence_paths": [],
        "errors": [],
    }

    assert status.study_completion_state.status is module.StudyCompletionStateStatus.RESOLVED
    assert status.study_completion_state.ready is True
    assert status.to_dict()["study_completion_contract"] == {
        "ready": True,
        "status": "resolved",
        "completion_status": "completed",
        "summary": "Study is done.",
        "user_approval_text": "同意",
        "completed_at": "2026-04-03T00:00:00+00:00",
        "evidence_paths": ["manuscript/final/submission_manifest.json"],
        "missing_evidence_paths": [],
        "errors": [],
    }

    with pytest.raises(TypeError, match="study_completion_contract must be dict"):
        status["study_completion_contract"] = []


def test_study_runtime_status_rejects_unknown_decision_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    with pytest.raises(ValueError, match="unknown study runtime decision"):
        status.set_decision("unexpected_action", "test_only")


def test_study_runtime_status_rejects_unknown_reason_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    with pytest.raises(ValueError, match="unknown study runtime reason"):
        status.set_decision("blocked", "unexpected_reason")


def test_study_runtime_status_rejects_unknown_quest_status_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    with pytest.raises(ValueError, match="unknown study runtime quest status"):
        status.update_quest_runtime(quest_status="unexpected_status")


def test_study_runtime_status_records_structured_runtime_extras() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {"quest_id": "quest-001", "auto_resume": True},
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "paused",
        "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "workspace_contracts": {"overall_ready": True},
        "startup_data_readiness": {"status": "clear"},
        "startup_boundary_gate": {"allow_compute_stage": True},
        "runtime_reentry_gate": {"allow_runtime_entry": True},
        "study_completion_contract": {"status": "absent", "ready": False},
        "controller_first_policy_summary": "summary",
        "automation_ready_summary": "ready",
    }

    status = module.StudyRuntimeStatus.from_payload(payload)

    status.record_analysis_bundle({"ready": True})
    status.record_runtime_overlay({"audit": {"all_roots_ready": True}})
    with pytest.raises(ValueError, match="startup contract validation payload"):
        status.record_startup_contract_validation({"status": "clear"})
    status.record_startup_contract_validation(make_startup_contract_validation_payload())
    status.record_startup_context_sync({"ok": True})
    with pytest.raises(ValueError, match="startup hydration payload"):
        status.record_startup_hydration({"status": "hydrated"}, {"status": "clear"})
    status.record_startup_hydration(
        make_startup_hydration_report(Path("/tmp/runtime/quests/quest-001")),
        make_startup_hydration_validation_report(Path("/tmp/runtime/quests/quest-001")),
    )
    status.record_completion_sync(make_completion_sync_payload())
    status.record_bash_session_audit({"status": "live"})
    status.record_runtime_artifacts(
        runtime_binding_path=Path("/tmp/studies/001-risk/runtime_binding.updated.yaml"),
        launch_report_path=Path("/tmp/studies/001-risk/launch_report.json"),
        startup_payload_path=Path("/tmp/runtime/startup_payloads/001-risk.json"),
    )

    payload = status.to_dict()

    assert payload["analysis_bundle"] == {"ready": True}
    assert payload["runtime_overlay"] == {"audit": {"all_roots_ready": True}}
    assert payload["startup_contract_validation"] == make_startup_contract_validation_payload()
    assert payload["startup_context_sync"] == {"ok": True}
    assert payload["startup_hydration"]["status"] == "hydrated"
    assert payload["startup_hydration"]["report_path"] == (
        "/tmp/runtime/quests/quest-001/artifacts/reports/startup/hydration_report.json"
    )
    assert payload["startup_hydration_validation"]["status"] == "clear"
    assert payload["startup_hydration_validation"]["report_path"] == (
        "/tmp/runtime/quests/quest-001/artifacts/reports/startup/hydration_validation_report.json"
    )
    assert payload["completion_sync"] == make_completion_sync_payload()
    assert payload["bash_session_audit"] == {"status": "live"}
    assert payload["runtime_binding_path"] == "/tmp/studies/001-risk/runtime_binding.updated.yaml"
    assert payload["launch_report_path"] == "/tmp/studies/001-risk/launch_report.json"
    assert payload["startup_payload_path"] == "/tmp/runtime/startup_payloads/001-risk.json"


def test_study_runtime_status_records_typed_completion_sync_and_audits() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": "/tmp/studies/001-risk",
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001"},
            "quest_id": "quest-001",
            "quest_root": "/tmp/runtime/quests/quest-001",
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
            "runtime_binding_exists": True,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
        }
    )
    completion_sync = module.StudyCompletionSyncResult.from_payload(make_completion_sync_payload())
    runtime_liveness_audit = module.StudyRuntimeAuditRecord.from_payload(
        {
            "ok": True,
            "status": "live",
            "active_run_id": "run-001",
        }
    )
    bash_session_audit = module.StudyRuntimeAuditRecord.from_payload(
        {
            "ok": True,
            "status": "none",
            "session_count": 1,
            "live_session_count": 0,
            "live_session_ids": [],
        }
    )

    status.record_completion_sync(completion_sync)
    status.record_runtime_liveness_audit(runtime_liveness_audit)
    status.record_bash_session_audit(bash_session_audit)

    payload = status.to_dict()

    assert payload["completion_sync"] == make_completion_sync_payload()
    assert status.completion_sync_result.completion_snapshot_status == "completed"
    assert status.runtime_liveness_audit_record.status is module.StudyRuntimeAuditStatus.LIVE
    assert status.bash_session_audit_record.status is module.StudyRuntimeAuditStatus.NONE


def test_study_runtime_status_records_typed_preflight_and_recovery_extras() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": "/tmp/studies/001-risk",
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001"},
            "quest_id": "quest-001",
            "quest_root": "/tmp/runtime/quests/quest-001",
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
            "runtime_binding_exists": True,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
        }
    )
    analysis_bundle = module.StudyRuntimeAnalysisBundleResult.from_payload(make_analysis_bundle_result())
    runtime_overlay = module.StudyRuntimeOverlayResult.from_payload(make_runtime_overlay_result())
    startup_context_sync = module.StudyRuntimeStartupContextSyncResult.from_payload(
        make_startup_context_sync_payload()
    )
    partial_quest_recovery = module.StudyRuntimePartialQuestRecoveryResult.from_payload(
        make_partial_quest_recovery_payload()
    )

    status.record_analysis_bundle(analysis_bundle)
    status.record_runtime_overlay(runtime_overlay)
    status.record_startup_context_sync(startup_context_sync)
    status.record_partial_quest_recovery(partial_quest_recovery)

    payload = status.to_dict()

    assert payload["analysis_bundle"] == make_analysis_bundle_result()
    assert payload["runtime_overlay"] == make_runtime_overlay_result()
    assert payload["startup_context_sync"] == make_startup_context_sync_payload()
    assert payload["partial_quest_recovery"] == make_partial_quest_recovery_payload()
    assert status.analysis_bundle_result.ready is True
    assert status.runtime_overlay_result.audit.all_roots_ready is True
    assert status.startup_context_sync_result.ok is True
    assert status.partial_quest_recovery_result.archived_root.endswith("20260403T000000Z")


def test_study_runtime_status_records_typed_startup_hydration_reports() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": "/tmp/studies/001-risk",
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001"},
            "quest_id": "quest-001",
            "quest_root": "/tmp/runtime/quests/quest-001",
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
            "runtime_binding_exists": True,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
        }
    )
    hydration_report = module.study_runtime_protocol.StartupHydrationReport.from_payload(
        make_startup_hydration_report(Path("/tmp/runtime/quests/quest-001"))
    )
    validation_report = module.study_runtime_protocol.StartupHydrationValidationReport.from_payload(
        make_startup_hydration_validation_report(Path("/tmp/runtime/quests/quest-001"))
    )

    status.record_startup_hydration(hydration_report, validation_report)

    payload = status.to_dict()
    assert payload["startup_hydration"]["status"] == "hydrated"
    assert payload["startup_hydration_validation"]["status"] == "clear"


def test_study_runtime_status_records_typed_startup_contract_validation() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": "/tmp/studies/001-risk",
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001"},
            "quest_id": "quest-001",
            "quest_root": "/tmp/runtime/quests/quest-001",
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
            "runtime_binding_exists": True,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
        }
    )
    validation = module.study_runtime_protocol.StartupContractValidation.from_payload(
        make_startup_contract_validation_payload()
    )

    status.record_startup_contract_validation(validation)

    assert status.to_dict()["startup_contract_validation"] == make_startup_contract_validation_payload()


def test_study_runtime_status_exposes_typed_gate_and_completion_accessors() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": "/tmp/studies/001-risk",
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": "/tmp/runtime/quests/quest-001",
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
            "runtime_binding_exists": True,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {
                "study_summary": {
                    "unresolved_contract_study_ids": ["001-risk"],
                }
            },
            "startup_boundary_gate": {
                "allow_compute_stage": True,
                "required_first_anchor": "00_entry_validation",
                "effective_custom_profile": "continue_existing_state",
                "legacy_code_execution_allowed": False,
            },
            "runtime_reentry_gate": {
                "allow_runtime_entry": False,
                "require_startup_hydration": False,
                "require_managed_skill_audit": True,
            },
            "study_completion_contract": {
                "ready": True,
                "status": "resolved",
                "completion_status": "completed",
                "summary": "Study is done.",
                "user_approval_text": "同意",
                "completed_at": "2026-04-03T00:00:00+00:00",
                "evidence_paths": [
                    "manuscript/final/submission_manifest.json",
                ],
                "missing_evidence_paths": [],
                "errors": [],
            },
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
        }
    )

    assert status.workspace_overall_ready is True
    assert status.startup_boundary_allows_compute_stage is True
    assert status.runtime_reentry_allows_runtime_entry is False
    assert status.runtime_reentry_requires_managed_skill_audit is True
    assert status.has_unresolved_contract_for("001-risk") is True
    assert status.has_unresolved_contract_for("002-risk") is False
    assert status.workspace_contracts_summary.overall_ready is True
    assert status.startup_boundary_gate_result.allow_compute_stage is True
    assert status.startup_boundary_gate_result.required_first_anchor == "00_entry_validation"
    assert status.startup_boundary_gate_result.effective_custom_profile == "continue_existing_state"
    assert status.startup_boundary_gate_result.legacy_code_execution_allowed is False
    assert status.runtime_reentry_gate_result.allow_runtime_entry is False
    assert status.runtime_reentry_gate_result.require_startup_hydration is False
    assert status.runtime_reentry_gate_result.require_managed_skill_audit is True
    assert status.startup_data_readiness_report.has_unresolved_contract_for("001-risk") is True
    assert status.study_completion_state.status is module.StudyCompletionStateStatus.RESOLVED
    assert status.study_completion_state.ready is True
    assert status.study_completion_state.contract is not None
    assert status.study_completion_state.contract.status.value == "completed"


def test_study_runtime_status_records_runtime_artifacts_with_binding_existence(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    binding_path = tmp_path / "studies" / "001-risk" / "runtime_binding.yaml"
    launch_report_path = tmp_path / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
    startup_payload_path = tmp_path / "runtime" / "startup_payloads" / "001-risk.json"
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(tmp_path / "studies" / "001-risk"),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001"},
            "quest_id": "quest-001",
            "quest_root": str(tmp_path / "runtime" / "quests" / "quest-001"),
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": str(binding_path),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
        }
    )

    status.record_runtime_artifacts(
        runtime_binding_path=binding_path,
        launch_report_path=launch_report_path,
        startup_payload_path=startup_payload_path,
    )

    payload = status.to_dict()

    assert payload["runtime_binding_exists"] is False
    assert payload["launch_report_path"] == str(launch_report_path)
    assert payload["startup_payload_path"] == str(startup_payload_path)


def test_study_runtime_execution_outcome_rejects_unknown_binding_action() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")

    with pytest.raises(ValueError, match="unknown study runtime binding action"):
        module.StudyRuntimeExecutionOutcome(binding_last_action="unexpected_action")


def test_study_runtime_execution_outcome_records_named_daemon_steps_and_resolves_status() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    outcome = module.StudyRuntimeExecutionOutcome()

    outcome.record_daemon_step(
        "create",
        {
            "snapshot": {
                "status": "created",
            }
        },
    )
    outcome.record_daemon_step(
        "resume",
        {
            "ok": True,
            "status": "running",
        },
    )
    outcome.record_daemon_step(
        "completion_sync",
        {
            "completion": {
                "snapshot": {
                    "status": "completed",
                }
            }
        },
    )

    assert outcome.daemon_step("create") == {"snapshot": {"status": "created"}}
    assert outcome.daemon_step("resume") == {"ok": True, "status": "running"}
    assert outcome.quest_status_for_step("create", fallback="unknown") == "created"
    assert outcome.quest_status_for_step("resume", fallback="unknown") == "running"
    assert outcome.completion_snapshot_status(fallback="unknown") == "completed"


def test_study_runtime_execution_outcome_resolves_completion_status_from_typed_sync_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    outcome = module.StudyRuntimeExecutionOutcome()
    completion_sync = module.StudyCompletionSyncResult.from_payload(make_completion_sync_payload(status="completed"))

    outcome.record_daemon_step("completion_sync", completion_sync.to_dict())

    assert outcome.completion_snapshot_status(fallback="unknown") == "completed"


def test_study_runtime_execution_outcome_rejects_invalid_daemon_step_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    outcome = module.StudyRuntimeExecutionOutcome()

    with pytest.raises(ValueError, match="unknown study runtime daemon step"):
        outcome.record_daemon_step("unexpected_step", {"ok": True})
    with pytest.raises(TypeError, match="daemon step payload must be dict"):
        outcome.record_daemon_step("resume", [])


def test_study_runtime_execution_outcome_serializes_single_resume_and_pause_steps_as_legacy_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    resume_outcome = module.StudyRuntimeExecutionOutcome(binding_last_action="resume")
    resume_outcome.record_daemon_step("resume", {"ok": True, "status": "running"})

    pause_outcome = module.StudyRuntimeExecutionOutcome(binding_last_action="pause")
    pause_outcome.record_daemon_step("pause", {"ok": True, "status": "paused"})

    create_outcome = module.StudyRuntimeExecutionOutcome(binding_last_action="create_and_start")
    create_outcome.record_daemon_step("create", {"ok": True, "snapshot": {"status": "created"}})
    create_outcome.record_daemon_step("resume", {"ok": True, "status": "running"})

    assert resume_outcome.serialized_daemon_result() == {"ok": True, "status": "running"}
    assert pause_outcome.serialized_daemon_result() == {"ok": True, "status": "paused"}
    assert create_outcome.serialized_daemon_result() == {
        "create": {"ok": True, "snapshot": {"status": "created"}},
        "resume": {"ok": True, "status": "running"},
    }


def test_study_runtime_router_reexports_typed_surface_from_study_runtime_types() -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")

    assert router.StudyRuntimeDecision is typed_surface.StudyRuntimeDecision
    assert router.StudyRuntimeReason is typed_surface.StudyRuntimeReason
    assert router.StudyRuntimeQuestStatus is typed_surface.StudyRuntimeQuestStatus
    assert router.StudyRuntimeBindingAction is typed_surface.StudyRuntimeBindingAction
    assert router.StudyRuntimeDaemonStep is typed_surface.StudyRuntimeDaemonStep
    assert router.StudyRuntimeAuditStatus is typed_surface.StudyRuntimeAuditStatus
    assert router.StudyRuntimeAuditRecord is typed_surface.StudyRuntimeAuditRecord
    assert router.StudyRuntimeAnalysisBundleResult is typed_surface.StudyRuntimeAnalysisBundleResult
    assert router.StudyRuntimeOverlayAudit is typed_surface.StudyRuntimeOverlayAudit
    assert router.StudyRuntimeOverlayResult is typed_surface.StudyRuntimeOverlayResult
    assert (
        router.StudyRuntimeStartupContextSyncResult
        is typed_surface.StudyRuntimeStartupContextSyncResult
    )
    assert router.StudyRuntimePartialQuestRecoveryResult is typed_surface.StudyRuntimePartialQuestRecoveryResult
    assert router.StudyRuntimeWorkspaceContractsSummary is typed_surface.StudyRuntimeWorkspaceContractsSummary
    assert (
        router.StudyRuntimeStartupDataReadinessReport
        is typed_surface.StudyRuntimeStartupDataReadinessReport
    )
    assert router.StudyRuntimeStartupBoundaryGate is typed_surface.StudyRuntimeStartupBoundaryGate
    assert router.StudyRuntimeReentryGate is typed_surface.StudyRuntimeReentryGate
    assert router.StudyCompletionSyncResult is typed_surface.StudyCompletionSyncResult
    assert router.StudyRuntimeStatus is typed_surface.StudyRuntimeStatus
    assert router.StudyRuntimeExecutionContext is typed_surface.StudyRuntimeExecutionContext
    assert router.StudyRuntimeExecutionOutcome is typed_surface.StudyRuntimeExecutionOutcome
    assert router.StudyRuntimeStatus.__module__ == typed_surface.__name__
    assert router.StudyRuntimeExecutionOutcome.__module__ == typed_surface.__name__
    assert router.study_runtime_status.__module__ == router.__name__
    assert router.ensure_study_runtime.__module__ == router.__name__
