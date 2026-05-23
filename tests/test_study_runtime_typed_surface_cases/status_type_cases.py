from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_study_runtime_types_reexports_status_surfaces_from_progress_projection() -> None:
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    status_surface = importlib.import_module("med_autoscience.controllers.progress_projection")

    assert typed_surface.ProgressProjectionStatus is status_surface.ProgressProjectionStatus
    assert typed_surface.ProgressProjectionStatus.__module__ == status_surface.__name__
    assert not hasattr(typed_surface, "StudyRuntimeExecutionContext")
    assert not hasattr(typed_surface, "StudyRuntimeExecutionOutcome")
def test_study_runtime_types_reexports_publication_supervisor_surface() -> None:
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    status_surface = importlib.import_module("med_autoscience.controllers.progress_projection")

    assert typed_surface.StudyRuntimePublicationSupervisorState is status_surface.StudyRuntimePublicationSupervisorState
    assert typed_surface.StudyRuntimePublicationSupervisorState.__module__ == status_surface.__name__
def test_study_runtime_types_reexports_execution_owner_guard_surface() -> None:
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    status_surface = importlib.import_module("med_autoscience.controllers.progress_projection")

    assert typed_surface.StudyRuntimeExecutionOwnerGuard is status_surface.StudyRuntimeExecutionOwnerGuard
    assert typed_surface.StudyRuntimeExecutionOwnerGuard.__module__ == status_surface.__name__
def test_study_runtime_types_reexports_pending_user_interaction_surface() -> None:
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    status_surface = importlib.import_module("med_autoscience.controllers.progress_projection")

    assert typed_surface.StudyRuntimePendingUserInteraction is status_surface.StudyRuntimePendingUserInteraction
    assert typed_surface.StudyRuntimePendingUserInteraction.__module__ == status_surface.__name__
def test_study_runtime_types_reexports_continuation_state_surface() -> None:
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    status_surface = importlib.import_module("med_autoscience.controllers.progress_projection")

    assert typed_surface.StudyRuntimeContinuationState is status_surface.StudyRuntimeContinuationState
    assert typed_surface.StudyRuntimeContinuationState.__module__ == status_surface.__name__
def test_domain_status_projection_reexports_typed_surface_from_study_runtime_types() -> None:
    router = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    status_surface = importlib.import_module("med_autoscience.controllers.progress_projection")

    assert router.StudyRuntimeQuestStatus is typed_surface.StudyRuntimeQuestStatus
    assert router.StudyRuntimeAuditStatus is typed_surface.StudyRuntimeAuditStatus
    assert router.StudyRuntimeAuditRecord is typed_surface.StudyRuntimeAuditRecord
    assert router.StudyRuntimeAnalysisBundleResult is typed_surface.StudyRuntimeAnalysisBundleResult
    assert router.StudyRuntimeOverlayAudit is typed_surface.StudyRuntimeOverlayAudit
    assert router.StudyRuntimeOverlayResult is typed_surface.StudyRuntimeOverlayResult
    assert router.StudyRuntimePendingUserInteraction is typed_surface.StudyRuntimePendingUserInteraction
    assert router.StudyRuntimeStartupContextSyncResult is typed_surface.StudyRuntimeStartupContextSyncResult
    assert router.StudyRuntimePartialQuestRecoveryResult is typed_surface.StudyRuntimePartialQuestRecoveryResult
    assert router.StudyRuntimeWorkspaceContractsSummary is typed_surface.StudyRuntimeWorkspaceContractsSummary
    assert router.StudyRuntimeStartupDataReadinessReport is typed_surface.StudyRuntimeStartupDataReadinessReport
    assert router.StudyRuntimeStartupBoundaryGate is typed_surface.StudyRuntimeStartupBoundaryGate
    assert router.StudyRuntimeReentryGate is typed_surface.StudyRuntimeReentryGate
    assert router.StudyCompletionSyncResult is typed_surface.StudyCompletionSyncResult
    assert router.ProgressProjectionStatus is typed_surface.ProgressProjectionStatus
    assert router.ProgressProjectionStatus.__module__ == status_surface.__name__
    assert router.progress_projection.__module__ == router.__name__
    assert not hasattr(router, "StudyRuntimeDecision")
    assert not hasattr(router, "StudyRuntimeReason")
    assert not hasattr(router, "StudyRuntimeBindingAction")
    assert not hasattr(router, "StudyRuntimeDaemonStep")
    assert not hasattr(router, "StudyRuntimeExecutionContext")
    assert not hasattr(router, "StudyRuntimeExecutionOutcome")
    assert not hasattr(router, "ensure_study_runtime")
def test_study_runtime_types_excludes_retired_execution_aggregate() -> None:
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    status_module = importlib.import_module("med_autoscience.controllers.progress_projection")

    assert typed_surface.ProgressProjectionStatus is status_module.ProgressProjectionStatus
    assert typed_surface.StudyRuntimeDecision is status_module.StudyRuntimeDecision
    assert typed_surface.StudyRuntimeReason is status_module.StudyRuntimeReason
    assert typed_surface.ProgressProjectionStatus.__module__ == status_module.__name__
    assert not hasattr(typed_surface, "StudyRuntimeExecutionContext")
    assert not hasattr(typed_surface, "StudyRuntimeExecutionOutcome")
def test_study_runtime_reason_drops_legacy_med_deepscientist_only_owner_label() -> None:
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")

    assert (
        typed_surface.StudyRuntimeReason.STUDY_EXECUTION_NOT_MANAGED_RUNTIME_BACKEND.value
        == "study_execution_not_managed_runtime_backend"
    )
    assert not hasattr(typed_surface.StudyRuntimeReason, "STUDY_EXECUTION_NOT_MED_DEEPSCIENTIST")
def test_opl_runtime_owner_handoff_materialization_is_required_for_recovering_target(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    study_root = tmp_path / "studies" / "001-risk"
    latest_handoff_path = study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
    latest_handoff_path.parent.mkdir(parents=True, exist_ok=True)
    latest_handoff_path.write_text(
        json.dumps(
            {
                "status": "handoff_required",
                "runtime_owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "mas_materializes_runtime_supervision": False,
                "mas_runtime_read_model_retired": True,
                "provider_completion_is_domain_completion": False,
                "queue_succeeded_is_domain_completion": False,
                "reason": "stale_previous_reason",
                "opl_current_control_state_ref": {"required": True},
                "typed_blocker": {"blocker_type": "opl_runtime_owner_handoff_required"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    status = module.ProgressProjectionStatus.from_payload(
        make_status_payload(
            study_root=str(study_root),
            quest_status="running",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
            runtime_liveness_audit={
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        )
    )

    assert module._should_materialize_opl_runtime_owner_handoff_from_status(status=status, study_root=study_root) is True


def test_opl_runtime_owner_handoff_materialization_uses_runtime_health_recovery_target_for_strict_live_timeout(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    study_root = tmp_path / "studies" / "001-risk"
    latest_handoff_path = study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
    latest_handoff_path.parent.mkdir(parents=True, exist_ok=True)
    latest_handoff_path.write_text(
        json.dumps(
            {
                "status": "handoff_required",
                "runtime_owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "mas_materializes_runtime_supervision": False,
                "mas_runtime_read_model_retired": True,
                "provider_completion_is_domain_completion": False,
                "queue_succeeded_is_domain_completion": False,
                "reason": "quest_already_running",
                "opl_current_control_state_ref": {"required": True},
                "typed_blocker": {"blocker_type": "opl_runtime_owner_handoff_required"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    status = module.ProgressProjectionStatus.from_payload(
        make_status_payload(
            study_root=str(study_root),
            quest_status="running",
            decision="noop",
            reason="quest_already_running",
            runtime_liveness_audit={
                "status": "live",
                "active_run_id": "run-live-stale",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-stale",
                    "worker_running": True,
                },
            },
            runtime_health_snapshot={
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
                "retry_budget_remaining": 2,
            },
        )
    )

    assert module._should_materialize_opl_runtime_owner_handoff_from_status(status=status, study_root=study_root) is True
def test_progress_projection_round_trips_through_typed_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    payload = make_status_payload(
        quest_status="paused",
        workspace_contracts={"overall_ready": True},
        startup_data_readiness={"status": "clear"},
        startup_boundary_gate={"allow_compute_stage": True},
        runtime_reentry_gate={"allow_runtime_entry": True},
        decision="resume",
        reason="quest_paused",
        runtime_overlay={"audit": {"all_roots_ready": True}},
    )

    status = module.ProgressProjectionStatus.from_payload(payload)
    expected_payload = dict(payload)
    expected_payload["study_completion_contract"] = {
        "ready": False,
        "status": "absent",
        "completion_status": None,
        "summary": "",
        "user_approval_text": "",
        "requires_program_human_confirmation": False,
        "completed_at": None,
        "evidence_paths": [],
        "missing_evidence_paths": [],
        "errors": [],
    }

    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")

    assert status.decision is typed_surface.StudyRuntimeDecision.RESUME
    assert status.reason is typed_surface.StudyRuntimeReason.QUEST_PAUSED
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

    assert status.decision is typed_surface.StudyRuntimeDecision.BLOCKED
    assert status.reason is typed_surface.StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED
    assert status.quest_status is module.StudyRuntimeQuestStatus.CREATED
    assert status.quest_id == "quest-002"
    assert status.quest_root == "/tmp/runtime/quests/quest-002"
    assert status.quest_exists is False
    assert status.to_dict()["decision"] == "blocked"
    assert status.to_dict()["reason"] == "startup_contract_resolution_failed"
    assert status.to_dict()["quest_status"] == "created"
    assert status.to_dict()["quest_id"] == "quest-002"
    assert status.to_dict()["quest_root"] == "/tmp/runtime/quests/quest-002"
def test_progress_projection_mapping_semantics_follow_serialized_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    payload = make_status_payload()

    status = module.ProgressProjectionStatus.from_payload(payload)
    expected_payload = dict(payload)
    expected_payload["study_completion_contract"] = {
        "ready": False,
        "status": "absent",
        "completion_status": None,
        "summary": "",
        "user_approval_text": "",
        "requires_program_human_confirmation": False,
        "completed_at": None,
        "evidence_paths": [],
        "missing_evidence_paths": [],
        "errors": [],
    }

    assert dict(status) == expected_payload
    assert "decision" not in status
    assert status.get("decision", "missing") == "missing"
def test_progress_projection_accepts_retrying_live_quest_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    payload = make_status_payload(quest_status="retrying")

    status = module.ProgressProjectionStatus.from_payload(payload)

    assert status.quest_status is module.StudyRuntimeQuestStatus.RETRYING
    assert status.quest_status in typed_surface._LIVE_QUEST_STATUSES
    assert status.to_dict()["quest_status"] == "retrying"


def test_progress_projection_accepts_failed_non_live_quest_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    payload = make_status_payload(quest_status="failed")

    status = module.ProgressProjectionStatus.from_payload(payload)

    assert status.quest_status is module.StudyRuntimeQuestStatus.FAILED
    assert status.quest_status not in typed_surface._LIVE_QUEST_STATUSES
    assert status.to_dict()["quest_status"] == "failed"


def test_progress_projection_core_key_assignment_uses_typed_normalization() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload())

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

    assert status.decision is typed_surface.StudyRuntimeDecision.BLOCKED
    assert status.reason is typed_surface.StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY
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
def test_progress_projection_normalizes_study_completion_contract_to_typed_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    payload = make_status_payload(
        study_root=str(tmp_path / "studies" / "001-risk"),
        quest_root=str(tmp_path / "runtime" / "quests" / "quest-001"),
        runtime_binding_path=str(tmp_path / "studies" / "001-risk" / "runtime_binding.yaml"),
        study_completion_contract={"status": "absent", "ready": False, "errors": []},
    )

    status = module.ProgressProjectionStatus.from_payload(payload)
    status["study_completion_contract"] = {
        "ready": True,
        "status": "resolved",
        "completion_status": "completed",
        "summary": "Study is done.",
        "user_approval_text": "同意",
        "requires_program_human_confirmation": False,
        "completed_at": "2026-04-03T00:00:00+00:00",
        "evidence_paths": ["manuscript/submission_manifest.json"],
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
        "requires_program_human_confirmation": False,
        "completed_at": "2026-04-03T00:00:00+00:00",
        "evidence_paths": ["manuscript/submission_manifest.json"],
        "missing_evidence_paths": [],
        "errors": [],
    }

    with pytest.raises(TypeError, match="study_completion_contract must be dict"):
        status["study_completion_contract"] = []
def test_progress_projection_rejects_unknown_decision_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload())

    with pytest.raises(ValueError, match="unknown study runtime decision"):
        status.set_decision("unexpected_action", "test_only")
def test_progress_projection_rejects_unknown_reason_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload())

    with pytest.raises(ValueError, match="unknown study runtime reason"):
        status.set_decision("blocked", "unexpected_reason")
def test_progress_projection_rejects_unknown_quest_status_value() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload())

    with pytest.raises(ValueError, match="unknown study runtime quest status"):
        status.update_quest_runtime(quest_status="unexpected_status")
def test_progress_projection_records_structured_runtime_extras() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload())

    status.record_analysis_bundle({"ready": True})
    status.record_runtime_overlay({"audit": {"all_roots_ready": True}})
    with pytest.raises(ValueError, match="startup contract validation payload"):
        status.record_startup_contract_validation({"status": "clear"})
    status.record_startup_contract_validation(make_startup_contract_validation_payload())
    status.record_startup_context_sync(make_startup_context_sync_payload())
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
    assert payload["startup_context_sync"] == make_startup_context_sync_payload()
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
def test_progress_projection_records_typed_completion_sync_and_audits() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload(execution={"quest_id": "quest-001"}))
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
def test_progress_projection_records_typed_preflight_and_recovery_extras() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload(execution={"quest_id": "quest-001"}))
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
def test_progress_projection_records_typed_publication_supervisor_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    payload = make_status_payload(
        execution={"quest_id": "quest-001"},
        publication_supervisor_state=make_publication_supervisor_state_payload(),
    )

    status = module.ProgressProjectionStatus.from_payload(payload)
    status.record_publication_supervisor_state(
        module.StudyRuntimePublicationSupervisorState.from_payload(
            make_publication_supervisor_state_payload(
                supervisor_phase="publishability_gate_blocked",
                upstream_scientific_anchor_ready=True,
            )
        )
    )

    assert status.to_dict()["publication_supervisor_state"] == make_publication_supervisor_state_payload(
        supervisor_phase="publishability_gate_blocked",
        upstream_scientific_anchor_ready=True,
    )
    assert status.publication_supervisor_state.supervisor_phase == "publishability_gate_blocked"
    assert status.publication_supervisor_state.phase_owner == "publication_gate"
    assert status.publication_supervisor_state.upstream_scientific_anchor_ready is True
def test_progress_projection_records_typed_progress_projection() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload(execution={"quest_id": "quest-001"}))

    status.record_progress_projection(make_progress_projection_payload())

    payload = status.to_dict()

    assert payload["progress_projection"] == make_progress_projection_payload()
    assert status.progress_projection_result is not None
    assert status.progress_projection_result.current_stage == "publication_supervision"
    assert status.progress_projection_result.next_system_action == "先补齐论文证据与叙事，再回到发表门控复核。"
def test_startup_context_sync_result_requires_echoed_startup_contract() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")

    with pytest.raises(ValueError, match="startup_contract"):
        module.StudyRuntimeStartupContextSyncResult.from_payload(
            {
                "ok": True,
                "snapshot": {
                    "quest_id": "quest-001",
                },
            }
        )
def test_startup_context_sync_result_requires_echoed_quest_id() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")

    with pytest.raises(ValueError, match="quest_id"):
        module.StudyRuntimeStartupContextSyncResult.from_payload(
            {
                "ok": True,
                "snapshot": {
                    "startup_contract": {"schema_version": 4},
                },
            }
        )
def test_progress_projection_records_typed_startup_hydration_reports() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload(execution={"quest_id": "quest-001"}))
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
def test_progress_projection_records_typed_startup_contract_validation() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload(execution={"quest_id": "quest-001"}))
    validation = module.study_runtime_protocol.StartupContractValidation.from_payload(
        make_startup_contract_validation_payload()
    )

    status.record_startup_contract_validation(validation)

    assert status.to_dict()["startup_contract_validation"] == make_startup_contract_validation_payload()
def test_progress_projection_exposes_typed_gate_and_completion_accessors() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(
        make_status_payload(
            startup_data_readiness={
                "study_summary": {
                    "unresolved_contract_study_ids": ["001-risk"],
                }
            },
            startup_boundary_gate={
                "allow_compute_stage": True,
                "required_first_anchor": "00_entry_validation",
                "effective_custom_profile": "continue_existing_state",
                "legacy_code_execution_allowed": False,
            },
            runtime_reentry_gate={
                "allow_runtime_entry": False,
                "require_startup_hydration": False,
                "require_managed_skill_audit": True,
            },
            study_completion_contract={
                "ready": True,
                "status": "resolved",
                "completion_status": "completed",
                "summary": "Study is done.",
                "user_approval_text": "同意",
                "completed_at": "2026-04-03T00:00:00+00:00",
                "evidence_paths": [
                    "manuscript/submission_manifest.json",
                ],
                "missing_evidence_paths": [],
                "errors": [],
            },
        )
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
def test_progress_projection_records_runtime_artifacts_with_binding_existence(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    binding_path = tmp_path / "studies" / "001-risk" / "runtime_binding.yaml"
    launch_report_path = tmp_path / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
    startup_payload_path = tmp_path / "runtime" / "startup_payloads" / "001-risk.json"
    status = module.ProgressProjectionStatus.from_payload(
        make_status_payload(
            study_root=str(tmp_path / "studies" / "001-risk"),
            quest_root=str(tmp_path / "runtime" / "quests" / "quest-001"),
            runtime_binding_path=str(binding_path),
            runtime_binding_exists=False,
        )
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
def test_progress_projection_records_autonomous_runtime_notice_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload())

    status.record_autonomous_runtime_notice(
        {
            "required": True,
            "notice_key": "quest:001-risk:run-live",
            "notification_reason": "detected_existing_live_managed_runtime",
            "quest_id": "001-risk",
            "quest_status": "running",
            "active_run_id": "run-live",
            "browser_url": "http://127.0.0.1:20999",
            "quest_api_url": "http://127.0.0.1:20999/api/quests/001-risk",
            "quest_session_api_url": "http://127.0.0.1:20999/api/quests/001-risk/session",
            "monitoring_available": True,
            "monitoring_error": None,
            "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
        }
    )

    assert status.to_dict()["autonomous_runtime_notice"] == {
        "required": True,
        "notice_key": "quest:001-risk:run-live",
        "notification_reason": "detected_existing_live_managed_runtime",
        "quest_id": "001-risk",
        "quest_status": "running",
        "active_run_id": "run-live",
        "browser_url": "http://127.0.0.1:20999",
        "quest_api_url": "http://127.0.0.1:20999/api/quests/001-risk",
        "quest_session_api_url": "http://127.0.0.1:20999/api/quests/001-risk/session",
        "monitoring_available": True,
        "monitoring_error": None,
        "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
    }
def test_progress_projection_records_execution_owner_guard_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload())

    status.record_execution_owner_guard(make_execution_owner_guard_payload())

    assert status.to_dict()["execution_owner_guard"] == make_execution_owner_guard_payload()
    assert status.execution_owner_guard.owner == "managed_runtime"
    assert status.execution_owner_guard.supervisor_only is True
    assert status.execution_owner_guard.takeover_required is True
def test_progress_projection_records_pending_user_interaction_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload())

    status.record_pending_user_interaction(make_pending_user_interaction_payload())

    assert status.to_dict()["pending_user_interaction"] == make_pending_user_interaction_payload()
    assert status.pending_user_interaction.interaction_id == "progress-standby-001"
    assert status.pending_user_interaction.blocking is True
    assert status.pending_user_interaction.relay_required is True
def test_progress_projection_records_continuation_state_payload() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(make_status_payload(quest_status="active"))

    payload = {
        "quest_status": "active",
        "active_run_id": None,
        "continuation_policy": "wait_for_user_or_resume",
        "continuation_anchor": "decision",
        "continuation_reason": "unchanged_finalize_state",
        "pending_user_message_count": 0,
        "runtime_state_path": "/tmp/runtime/quests/quest-001/.ds/runtime_state.json",
    }
    status.record_continuation_state(payload)

    assert status.to_dict()["continuation_state"] == payload
    assert status.continuation_state.continuation_reason == "unchanged_finalize_state"
    assert status.continuation_state.continuation_policy == "wait_for_user_or_resume"
def test_progress_projection_detects_blocked_hydration_refresh_candidate() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(
        make_status_payload(
            execution={"quest_id": "quest-001", "auto_resume": False},
            quest_status="created",
            startup_boundary_gate={"allow_compute_stage": False},
            decision="blocked",
            reason="startup_boundary_not_ready_for_resume",
        )
    )

    assert status.should_refresh_startup_hydration_while_blocked() is True

    status.set_decision("blocked", "workspace_contract_not_ready")

    assert status.should_refresh_startup_hydration_while_blocked() is False


def test_progress_projection_detects_owner_route_ai_reviewer_reference_context_hydration_gap() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    status = module.ProgressProjectionStatus.from_payload(
        make_status_payload(
            execution={"quest_id": "quest-001", "auto_resume": False},
            quest_status="active",
            decision="blocked",
            reason="quest_waiting_opl_runtime_owner_route",
            ai_reviewer_request={
                "input_contract": {
                    "all_required_refs_present": False,
                    "missing_or_invalid_refs": ["stage_knowledge_packet"],
                    "required_refs": {
                        "stage_knowledge_packet": {
                            "surface": "stage_knowledge_packet",
                            "relative_path": "artifacts/stage_knowledge/review/latest.json",
                            "status": "missing",
                            "missing_reasons": ["missing_ref:study_reference_context"],
                        }
                    },
                },
                "stage_knowledge_status": "missing",
                "stage_knowledge_missing_reasons": ["missing_ref:study_reference_context"],
            },
        )
    )

    assert status.should_refresh_startup_hydration_while_blocked() is True


def test_runtime_binding_and_daemon_step_enums_remain_progress_projection_owned() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_projection")

    assert module.StudyRuntimeBindingAction.RESUME.value == "resume"
    assert module.StudyRuntimeBindingAction.PAUSE.value == "pause"
    assert module.StudyRuntimeDaemonStep.COMPLETION_SYNC.value == "completion_sync"
