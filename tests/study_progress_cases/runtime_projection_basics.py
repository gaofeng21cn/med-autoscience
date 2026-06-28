from __future__ import annotations
from tests.study_progress_cases.runtime_projection_basics_cases.stale_supervision_and_restore import *  # noqa: F403,F401

from . import shared as _shared

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)

def test_latest_events_prefers_runtime_progress_over_newer_launch_report_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    launch_report_path = tmp_path / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
    publication_eval_path = tmp_path / "studies" / "001-risk" / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = tmp_path / "studies" / "001-risk" / "artifacts" / "controller_decisions" / "latest.json"
    bash_summary_path = (
        tmp_path
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "quest-001"
        / ".ds"
        / "bash_exec"
        / "summary.json"
    )

    events = module._latest_events(
        launch_report_payload={
            "recorded_at": "2026-04-10T09:14:00+00:00",
            "decision": "noop",
            "reason": "quest_already_running",
        },
        launch_report_path=launch_report_path,
        opl_runtime_owner_handoff_payload=None,
        opl_runtime_owner_handoff_path=None,
        runtime_escalation_payload=None,
        runtime_escalation_path=None,
        publication_eval_payload=None,
        publication_eval_path=publication_eval_path,
        controller_decision_payload=None,
        controller_decision_path=controller_decision_path,
        domain_health_diagnostic_payload=None,
        domain_health_diagnostic_path=None,
        details_projection_payload=None,
        details_projection_path=None,
        bash_summary_payload={
            "latest_session": {
                "updated_at": "2026-04-10T09:12:00+00:00",
                "last_progress": {
                    "ts": "2026-04-10T09:12:00+00:00",
                    "message": "完成外部验证数据清点，正在整理论文证据面。",
                },
            }
        },
        bash_summary_path=bash_summary_path,
    )

    assert [item["category"] for item in events[:2]] == ["runtime_progress", "launch_report"]
    assert "完成外部验证数据清点" in events[0]["summary"]


def _write_runtime_efficiency_fixture(quest_root: Path) -> tuple[Path, Path]:
    telemetry_path = quest_root / ".ds" / "runs" / "run-001" / "telemetry.json"
    evidence_index_path = quest_root / ".ds" / "evidence_packets" / "run-001" / "index.json"
    evidence_sidecar_path = quest_root / ".ds" / "evidence_packets" / "run-001" / "bash_exec-large-log.json"
    gate_cache_path = quest_root / ".ds" / "gate_cache" / "paper_contract_health.json"
    _write_json(
        telemetry_path,
        {
            "run_id": "run-001",
            "prompt_bytes": 123456,
            "stdout_bytes": 2345,
            "tool_result_bytes_total": 98765,
            "tool_result_bytes_after_compaction_total": 12345,
            "tool_result_bytes_saved_total": 86420,
            "compacted_tool_result_count": 4,
            "full_detail_tool_call_count": 1,
            "mcp_tool_call_count": 9,
            "tool_call_budget": 8,
            "tool_call_count": 6,
            "tool_call_budget_remaining": 2,
            "tool_call_budget_exceeded": False,
            "unique_command_count": 3,
            "read_tool_call_count": 4,
            "repeated_read_result_count": 2,
            "repeated_read_ratio": 0.5,
            "full_detail_count": 1,
            "model_inherited": True,
            "runner_profile": None,
            "token_usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 400,
                "output_tokens": 120,
            },
        },
    )
    _write_json(
        evidence_index_path,
        {
            "items": [
                {
                    "tool_name": "bash_exec",
                    "detail": "compact",
                    "summary": "bash_exec: log_line_count=1200; key_blockers=1",
                    "payload_bytes": 64000,
                    "sidecar_path": str(evidence_sidecar_path),
                    "payload_sha256": "abc123",
                    "key_blockers": ["submission_minimal missing"],
                }
            ],
        },
    )
    _write_json(
        gate_cache_path,
        {
            "input_fingerprint": "gate-fingerprint-001",
            "generated_at": "2026-04-10T09:30:00+00:00",
        },
    )
    return telemetry_path, evidence_index_path


def test_study_progress_surfaces_evidence_packet_and_gate_cache_without_telemetry(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    evidence_index_path = quest_root / ".ds" / "evidence_packets" / "run-live" / "index.json"
    gate_cache_path = quest_root / ".ds" / "gate_cache" / "paper_contract_health.json"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        evidence_index_path,
        {
            "items": [
                {
                    "tool_name": "artifact.get_quest_state",
                    "detail": "full",
                    "summary": "artifact.get_quest_state: compact evidence packet available",
                    "payload_bytes": 120000,
                    "sidecar_path": str(evidence_index_path.parent / "artifact.get_quest_state.json"),
                    "payload_sha256": "packet-sha",
                    "key_blockers": ["stale_submission_minimal_authority"],
                }
            ],
        },
    )
    _write_json(
        gate_cache_path,
        {
            "surface_id": "paper_contract_health",
            "input_fingerprint": "gate-fingerprint-live",
            "generated_at": "2026-04-10T09:30:00+00:00",
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-current",
            "publication_supervisor_state": {
                "supervisor_phase": "write",
                "phase_owner": "publication_gate",
                "current_required_action": "continue_write_stage",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["refs"]["runtime_telemetry_path"] is None
    assert result["refs"]["evidence_packet_index_path"] == str(evidence_index_path)
    assert result["runtime_efficiency"]["run_id"] == "run-live"
    assert result["runtime_efficiency"]["evidence_packet_count"] == 1
    assert result["runtime_efficiency"]["latest_evidence_packets"][0]["payload_bytes"] == 120000
    assert result["runtime_efficiency"]["gate_cache"]["input_fingerprint"] == "gate-fingerprint-live"


def test_study_progress_records_stage_actions_when_runner_telemetry_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_publication_eval(
        study_root,
        quest_root,
        recommended_actions=[
            {
                "action_id": "action-stage-record",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Publication gate remains blocked.",
                "requires_controller_decision": True,
                "work_unit_fingerprint": "publication-blockers::stage-record",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence consistency.",
                },
            }
        ],
    )
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "status": "executed",
            "repair_execution_evidence_path": str(
                study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
            ),
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "repair_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
                "source_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                "changed_artifact_refs": [
                    {"path": str(study_root / "paper" / "claim_evidence_map.json")},
                    {"path": str(study_root / "paper" / "evidence_ledger.json")},
                ],
                "gate_replay_refs": [
                    str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
                ],
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "status": "executed",
            "work_unit_fingerprint": "publication-blockers::stage-record",
            "gate_replay": {
                "status": "blocked",
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "blockers": ["claim_evidence_consistency_failed"],
            },
            "gate_replay_step": {
                "step_id": "publication_gate_replay",
                "status": "blocked",
                "started_at": "2026-04-10T09:30:00+00:00",
                "finished_at": "2026-04-10T09:30:01+00:00",
            },
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    runtime_efficiency = result["runtime_efficiency"]
    assert runtime_efficiency["telemetry_status"] == "missing"
    assert runtime_efficiency["token_usage"] == {
        "status": "missing",
        "total_tokens": None,
        "missing_token_usage_reason": "no_completed_runner_telemetry_token_usage_observed",
    }
    assert runtime_efficiency["stage_execution_record_count"] == 2
    quality_record, gate_record = runtime_efficiency["stage_execution_records"]
    assert quality_record["action_type"] == "run_quality_repair_batch"
    assert quality_record["work_unit_id"] == "analysis_claim_evidence_repair"
    assert quality_record["changed_artifact_refs"] == [
        str(study_root / "paper" / "claim_evidence_map.json"),
        str(study_root / "paper" / "evidence_ledger.json"),
    ]
    assert quality_record["token_usage"]["status"] == "missing"
    assert gate_record["action_type"] == "run_gate_clearing_batch"
    assert gate_record["duration"] == {
        "status": "present",
        "seconds": 1.0,
        "source": "started_at_finished_at",
    }
    assert gate_record["remaining_blockers"] == ["claim_evidence_consistency_failed"]
    assert "stage records 2" in runtime_efficiency["summary"]
    assert result["deliverable_progress_delta"]["token_usage_total"] is None


def test_study_progress_marks_work_unit_lifecycle_span_as_elapsed_window(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    work_unit_ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    control_identity = importlib.import_module("med_autoscience.controllers.control_identity")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    identity = control_identity.ControlWorkUnitIdentity(
        domain="publication-work-unit",
        study_id="001-risk",
        quest_id="quest-001",
        lane="write",
        unit_id="medical_prose_write_repair",
        action_type="run_quality_repair_batch",
        effective_blockers=("publication-blockers::prose",),
        fingerprint_override="publication-blockers::prose",
        idempotency_scope="work_unit",
    )
    work_unit_ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="dispatched",
        payload={"source": "test"},
        recorded_at="2026-04-01T00:00:00+00:00",
    )
    work_unit_ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"source": "test"},
        recorded_at="2026-04-10T00:00:00+00:00",
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    [record] = result["runtime_efficiency"]["stage_execution_records"]
    assert record["record_kind"] == "work_unit_lifecycle"
    assert record["duration"] == {
        "status": "elapsed_window_only",
        "seconds": 777600.0,
        "source": "lifecycle_first_latest_recorded_at",
        "not_execution_duration": True,
        "event_count": 2,
    }


def test_study_progress_reads_stage_token_usage_from_closeout_refs_when_runner_telemetry_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    work_unit_ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    control_identity = importlib.import_module("med_autoscience.controllers.control_identity")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    closeout_ref = (
        "studies/001-risk/artifacts/supervision/consumer/default_executor_execution/"
        "sat-001.closeout.json"
    )
    _write_publication_eval(study_root, quest_root)
    _write_json(
        profile.workspace_root / closeout_ref,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "paper_stage_log": {
                "token_usage": {
                    "input_tokens": 1000,
                    "output_tokens": 200,
                    "total_tokens": 1200,
                }
            },
        },
    )
    identity = control_identity.ControlWorkUnitIdentity(
        domain="publication-work-unit",
        study_id="001-risk",
        quest_id="quest-001",
        lane="write",
        unit_id="medical_prose_write_repair",
        action_type="run_quality_repair_batch",
        effective_blockers=("publication-blockers::prose",),
        fingerprint_override="publication-blockers::prose",
        idempotency_scope="work_unit",
    )
    work_unit_ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"closeout_refs": [closeout_ref]},
        recorded_at="2026-04-10T00:00:00+00:00",
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    [record] = result["runtime_efficiency"]["stage_execution_records"]
    assert record["token_usage"]["status"] == "present"
    assert record["token_usage"]["total_tokens"] == 1200
    assert record["token_usage"]["source"] == "stage_closeout_user_stage_log"
    assert result["runtime_efficiency"]["token_usage"]["status"] == "present"
    assert result["runtime_efficiency"]["token_usage"]["total_tokens"] == 1200
    assert result["runtime_efficiency"]["token_usage"]["source"] == "stage_closeout_user_stage_log"


def test_study_progress_reads_provider_token_usage_from_closeout_top_level(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    work_unit_ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    control_identity = importlib.import_module("med_autoscience.controllers.control_identity")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    closeout_ref = (
        "studies/001-risk/artifacts/supervision/consumer/default_executor_execution/"
        "sat-002.closeout.json"
    )
    _write_publication_eval(study_root, quest_root)
    _write_json(
        profile.workspace_root / closeout_ref,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "tokenUsage": {
                "inputTokens": 700,
                "outputTokens": 300,
                "totalTokens": 1000,
            },
        },
    )
    identity = control_identity.ControlWorkUnitIdentity(
        domain="publication-work-unit",
        study_id="001-risk",
        quest_id="quest-001",
        lane="write",
        unit_id="medical_prose_write_repair",
        action_type="run_quality_repair_batch",
        effective_blockers=("publication-blockers::prose",),
        fingerprint_override="publication-blockers::prose",
        idempotency_scope="work_unit",
    )
    work_unit_ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"closeout_refs": [closeout_ref]},
        recorded_at="2026-04-10T00:00:00+00:00",
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    [record] = result["runtime_efficiency"]["stage_execution_records"]
    assert record["token_usage"]["status"] == "present"
    assert record["token_usage"]["total_tokens"] == 1000
    assert record["token_usage"]["input_tokens"] == 700
    assert record["token_usage"]["output_tokens"] == 300
    assert record["token_usage"]["source"] == "stage_closeout_user_stage_log"
    assert result["runtime_efficiency"]["token_usage"]["total_tokens"] == 1000


def test_study_progress_builds_physician_friendly_projection(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="研究主线是糖尿病死亡风险外部验证。",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"

    _write_study_charter_and_controller_summary(study_root)
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    controller_decision_path = _write_controller_decision(study_root, quest_root)
    runtime_escalation_path = _write_runtime_escalation(quest_root, study_root)
    publishability_gate_report_path = _write_publishability_gate_report(quest_root)
    domain_health_diagnostic_path = _write_domain_health_diagnostic(quest_root)
    bash_summary_path = _write_bash_summary(quest_root)
    details_projection_path = _write_details_projection(quest_root)
    telemetry_path, evidence_index_path = _write_runtime_efficiency_fixture(quest_root)
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="把当前研究收口到 SCI-ready 投稿标准，并持续自检卡住、无进度和质量回退。",
        journal_target="BMC Medicine",
        first_cycle_outputs=("study-progress", "domain_health_diagnostic", "publication_eval/latest.json"),
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "notice_key": "notice-001",
                "notification_reason": "managed_runtime_live",
                "quest_id": "quest-001",
                "quest_status": "running",
                "active_run_id": "run-001",
                "browser_url": "http://127.0.0.1:21999/quests/quest-001",
                "quest_api_url": "http://127.0.0.1:21999/api/quests/quest-001",
                "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
                "monitoring_available": True,
                "monitoring_error": None,
                "launch_report_path": str(launch_report_path),
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "runtime_live",
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "allowed_actions": ["read_status", "monitor_runtime"],
                "forbidden_actions": ["write_runtime_owned_roots"],
                "runtime_owned_roots": [str(quest_root / ".ds")],
                "takeover_required": False,
                "takeover_action": "pause_before_takeover",
                "publication_gate_allows_direct_write": False,
                "controller_stage_note": "当前只能做监管，不能直接越过托管运行时写入其拥有的表面。",
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(runtime_escalation_path),
                "summary_ref": str(launch_report_path),
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["study_id"] == "001-risk"
    assert result["quest_id"] == "quest-001"
    assert result["current_stage"] == "publication_supervision"
    assert result.get("parked_state") is None
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["parked_state"] is None
    assert result["auto_runtime_parked"]["superseded_by_current_owner_action"] is True
    assert result["paper_stage"] == "write"
    assert result["needs_physician_decision"] is False
    assert result["needs_user_decision"] is False
    assert "用户" in result["current_stage_summary"]
    assert result["status_narration_contract"]["contract_kind"] == "ai_status_narration"
    assert (
        result["status_narration_contract"]["narration_policy"]["answer_checklist"]
        == ["current_stage", "current_blockers", "next_step"]
    )
    assert "写作" in result["paper_stage_summary"]
    assert any("外部验证" in item for item in result["current_blockers"])
    assert any("发表" in item for item in result["current_blockers"])
    assert "owner receipt" in result["next_system_action"]
    assert result["supervision"]["browser_url"] == "http://127.0.0.1:21999/quests/quest-001"
    assert result["supervision"]["quest_session_api_url"] == "http://127.0.0.1:21999/api/sessions/run-001"
    assert result["supervision"]["active_run_id"] == "run-001"
    assert result["task_intake"]["journal_target"] == "BMC Medicine"
    assert "SCI-ready 投稿标准" in result["task_intake"]["task_intent"]
    assert result["progress_freshness"]["status"] == "not_required"
    assert result["latest_events"][0]["category"] == "runtime_progress"
    assert result["latest_events"][0]["timestamp"] == "2026-04-10T09:12:00+00:00"
    assert "外部验证数据清点" in result["latest_events"][0]["summary"]
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert result["refs"]["controller_decision_path"] == str(controller_decision_path)
    assert result["refs"]["controller_confirmation_summary_path"] == str(
        study_root / "artifacts" / "controller" / "controller_confirmation_summary.json"
    )
    assert result["refs"]["domain_health_diagnostic_report_path"] == str(domain_health_diagnostic_path)
    assert result["refs"]["controller_summary_path"] == str(
        study_root / "artifacts" / "controller" / "controller_summary.json"
    )
    assert result["refs"]["evaluation_summary_path"] == str(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    )
    assert result["refs"]["promotion_gate_path"] == str(
        study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json"
    )
    assert result["module_surfaces"]["controller_charter"]["summary_ref"] == result["refs"]["controller_summary_path"]
    assert result["module_surfaces"]["controller_charter"]["human_confirmation"] == {
        "gate_id": "controller-human-confirmation-001-risk",
        "status": "pending",
        "requested_at": "2026-04-10T09:10:00+00:00",
        "question_for_user": "请确认是否允许 MAS 停止当前研究运行。",
        "allowed_responses": ["approve", "request_changes", "reject"],
        "next_action_if_approved": "停止当前研究运行",
        "summary_ref": str(study_root / "artifacts" / "controller" / "controller_confirmation_summary.json"),
    }
    assert result["module_surfaces"]["runtime"]["summary_ref"] == result["refs"]["runtime_status_summary_path"]
    assert result["module_surfaces"]["eval_hygiene"]["summary_ref"] == result["refs"]["evaluation_summary_path"]
    assert result["refs"]["bash_summary_path"] == str(bash_summary_path)
    assert result["refs"]["details_projection_path"] == str(details_projection_path)
    assert result["refs"]["runtime_telemetry_path"] == str(telemetry_path)
    assert result["refs"]["evidence_packet_index_path"] == str(evidence_index_path)
    assert result["runtime_efficiency"]["run_id"] == "run-001"
    assert result["runtime_efficiency"]["prompt_bytes"] == 123456
    assert result["runtime_efficiency"]["tool_result_bytes_total"] == 98765
    assert result["runtime_efficiency"]["compacted_tool_result_count"] == 4
    assert result["runtime_efficiency"]["full_detail_tool_call_count"] == 1
    assert result["runtime_efficiency"]["token_usage"]["cached_input_tokens"] == 400
    assert result["runtime_efficiency"]["latest_evidence_packets"][0]["summary"].startswith("bash_exec:")
    assert result["runtime_efficiency"]["gate_cache"]["input_fingerprint"] == "gate-fingerprint-001"
    dashboard = result["ai_first_operations_dashboard"]
    assert dashboard["surface"] == "ai_first_operations_dashboard_summary"
    assert dashboard["read_model"] == "ai_first_operations_dashboard_read_model"
    assert dashboard["contract"]["shared_read_model_consumers"] == [
        "product_entry_status",
        "workspace_cockpit",
        "study_progress",
    ]
    assert dashboard["user_view"]["current_stage"] == result["current_stage"]
    assert dashboard["user_view"]["blockers"] == result["current_blockers"]
    assert dashboard["user_view"]["next_step"] == result["next_system_action"]
    assert dashboard["user_view"]["human_review_required"] is False
    assert dashboard["maintainer_view"]["ai_reviewer_trace"]["complete"] is False
    assert dashboard["maintainer_view"]["route_back"]["count"] == 0
    assert dashboard["maintainer_view"]["artifact_stale"]["stale_artifact_count"] >= 1
    assert dashboard["authority"]["observability_can_authorize_quality"] is False
    assert result["refs"]["ai_first_observability_publication_eval_path"] == str(publication_eval_path)
    assert publishability_gate_report_path.exists()


def test_study_progress_skips_eval_hygiene_materialization_when_runtime_escalation_record_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="研究主线是糖尿病死亡风险外部验证。",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    runtime_escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"

    _write_study_charter_and_controller_summary(study_root)
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    publishability_gate_report_path = _write_publishability_gate_report(quest_root)
    domain_health_diagnostic_path = _write_domain_health_diagnostic(quest_root)

    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::missing",
                "artifact_path": str(runtime_escalation_path),
                "summary_ref": str(launch_report_path),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["study_id"] == "001-risk"
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert result["refs"]["domain_health_diagnostic_report_path"] == str(domain_health_diagnostic_path)
    assert result["refs"]["runtime_escalation_path"] == str(runtime_escalation_path)
    assert result["refs"]["evaluation_summary_path"] is None
    assert result["refs"]["promotion_gate_path"] is None
    assert "eval_hygiene" not in result["module_surfaces"]
    assert not runtime_escalation_path.exists()
    assert publishability_gate_report_path.exists()


def test_render_study_progress_markdown_uses_physician_friendly_sections(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_study_charter_and_controller_summary(study_root)
    _write_publication_eval(study_root, quest_root)
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        action_type="request_opl_stage_attempt",
        reason="MAS should keep repairing the current publication blockers autonomously.",
    )
    runtime_escalation_path = _write_runtime_escalation(quest_root, study_root)
    _write_publishability_gate_report(quest_root)
    _write_domain_health_diagnostic(quest_root)
    _write_bash_summary(quest_root)
    _write_details_projection(quest_root)
    _write_runtime_efficiency_fixture(quest_root)
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="优先保证系统能发现卡住、没进度和质量回退。",
        journal_target="JAMA Network Open",
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "notice_key": "notice-001",
                "notification_reason": "managed_runtime_live",
                "quest_id": "quest-001",
                "quest_status": "running",
                "active_run_id": "run-001",
                "browser_url": "http://127.0.0.1:21999/quests/quest-001",
                "quest_api_url": "http://127.0.0.1:21999/api/quests/quest-001",
                "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
                "monitoring_available": True,
                "monitoring_error": None,
                "launch_report_path": str(launch_report_path),
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "runtime_live",
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "allowed_actions": ["read_status", "monitor_runtime"],
                "forbidden_actions": ["write_runtime_owned_roots"],
                "runtime_owned_roots": [str(quest_root / ".ds")],
                "takeover_required": False,
                "takeover_action": "pause_before_takeover",
                "publication_gate_allows_direct_write": False,
                "controller_stage_note": "当前只能做监管，不能直接越过托管运行时写入其拥有的表面。",
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(runtime_escalation_path),
                "summary_ref": str(launch_report_path),
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc),
    )

    payload = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(payload)

    assert markdown.strip()
