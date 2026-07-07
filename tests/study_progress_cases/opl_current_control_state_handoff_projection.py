from __future__ import annotations

from tests.provider_admission_current_control_helpers import opl_transition_readback

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _runtime_state_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json"


def _non_advancing_opl_transition_readback(
    *,
    study_id: str,
    work_unit_id: str,
    fingerprint: str,
    route_key: str,
) -> dict[str, object]:
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
    )
    readback["identity"]["transition_kind"] = "NonAdvancingApply"
    readback["identity"]["outcome_kind"] = "non_advancing_apply_typed_blocker_ref"
    readback["exactly_one_outcome"]["transition_kind"] = "NonAdvancingApply"
    readback["exactly_one_outcome"]["outcome_kind"] = "non_advancing_apply_typed_blocker_ref"
    readback["exactly_one_outcome"]["non_advancing_apply"] = True
    readback["read_model_readback"]["identity"] = readback["identity"]
    readback["read_model_readback"]["exactly_one_outcome"] = readback["exactly_one_outcome"]
    return readback


def test_non_advancing_apply_readback_demotes_current_control_to_typed_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapters/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    runtime_readback = _non_advancing_opl_transition_readback(
        study_id=study_id,
        work_unit_id=work_unit,
        fingerprint=fingerprint,
        route_key=route_key,
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    non_advancing_readback = {
        "surface_kind": "opl_current_control_transition_non_advancing_apply_readback",
        "status": "transition_non_advancing_apply_recorded",
        "reason": "opl_transition_request_missing_for_authorized_stage_packet",
        "study_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "idempotency_key": route_key,
        "route_identity_key": route_key,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "runtime_live_readback": runtime_readback,
        "exactly_one_outcome": runtime_readback["exactly_one_outcome"],
        "authority_boundary": {
            "domain_truth_owner": "med-autoscience",
            "substrate_owner": "one-person-lab",
            "opl_can_write_mas_truth": False,
            "provider_completion_is_domain_completion": False,
            "paper_progress_delta": False,
        },
    }
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-19T12:30:00+00:00",
            "authority": "observability_only",
            "provider_admission_pending_count": 0,
            "transition_request_pending_count": 0,
            "current_executable_owner_action": None,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "quest_status": "blocked",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "current_control_action": {
                        "status": "transition_non_advancing_apply_recorded",
                        "provider_admission_requires_opl_runtime_result": False,
                        "paper_progress_delta": False,
                        "non_advancing_apply": True,
                    },
                    "current_executable_owner_action": None,
                    "provider_admission_pending_count": 0,
                    "transition_request_pending_count": 0,
                    "provider_admission_candidates": [],
                    "domain_progress_transition_non_advancing_apply_readback": (
                        non_advancing_readback
                    ),
                    "domain_progress_transition_projection_metadata": {
                        "surface_kind": "opl_current_control_domain_progress_transition_projection_metadata",
                        "projection_role": "non_advancing_apply_current_transition_readback",
                        "authority": False,
                        "runtime_readback_status": "complete_transaction",
                        "transaction_complete": True,
                        "provider_admission_allowed": False,
                        "current_executable_owner_action_allowed": False,
                        "paper_progress_delta": False,
                        "non_advancing_apply": True,
                    },
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipts"
        / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "owner_callable_adapter_receipt",
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "execution_id": "sat-stale-no-selected-dispatch",
                    "stage_attempt_id": "sat-stale-no-selected-dispatch",
                    "generated_at": "2026-06-19T14:58:00+00:00",
                    "status": "blocked",
                    "execution_status": "typed_blocker",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
                    "typed_blocker": {
                        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit,
                        "work_unit_fingerprint": fingerprint,
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "continue",
            "reason": "quality_repair_followthrough",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": work_unit,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"status": "stale"}],
            "transition_request_pending_count": 1,
            "transition_request_candidates": [{"status": "stale"}],
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-current",
                "runtime_liveness_status": "none",
                "health_status": "none",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["typed_blocker"]["blocker_type"] == "non_advancing_apply"
    assert handoff["current_work_unit"]["status"] == "typed_blocker"
    assert handoff["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert handoff["provider_admission_pending_count"] == 0
    assert handoff["transition_request_pending_count"] == 0
    assert handoff["current_work_unit"]["state"]["typed_blocker"]["non_advancing_apply"] is True
    assert_default_next_action_legacy_surfaces_retired(result)


def test_provider_admission_readback_supersedes_stale_typed_blocker_stop_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    route_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapters/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    runtime_readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
    )
    candidate = {
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "opl_domain_progress_transition_runtime_live_readback": runtime_readback,
    }
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-19T14:59:00+00:00",
            "authority": "observability_only",
            "provider_admission_pending_count": 1,
            "transition_request_pending_count": 0,
            "provider_admission_candidates": [candidate],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "handoff_scan_status": "scanned_no_provider_admission",
                    "provider_admission_pending_count": 1,
                    "transition_request_pending_count": 0,
                    "current_control_action": {
                        "status": "provider_admission_pending",
                        "reason": "complete_opl_transition_runtime_readback",
                        "provider_admission_requires_opl_runtime_result": False,
                    },
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "schema_version": 1,
                        "status": "owner_receipt_recorded",
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                    },
                    "current_execution_envelope": {
                        "state_kind": "owner_receipt_recorded",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit,
                        "work_unit_fingerprint": fingerprint,
                    },
                    "provider_admission_candidates": [candidate],
                    "action_queue": [],
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "continue",
            "reason": "stale_terminal_typed_blocker",
            "current_executable_owner_action": None,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit,
                        "work_unit_fingerprint": fingerprint,
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit,
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-current",
                "runtime_liveness_status": "none",
                "health_status": "none",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["provider_admission_pending_count"] == 1
    assert handoff["transition_request_pending_count"] == 0
    assert handoff["provider_admission_candidates"][0]["work_unit_id"] == work_unit
    assert handoff["provider_admission_candidates"][0][
        "opl_domain_progress_transition_runtime_live_readback"
    ]["runtime_readback_status"] == "complete_transaction"
    assert_default_next_action_legacy_surfaces_retired(result)


def test_provider_admission_readback_supersedes_matching_stale_selector_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    route_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    stage_attempt_id = "sat-stale-no-selected-dispatch"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapters/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    runtime_readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
    )
    candidate = {
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "opl_domain_progress_transition_runtime_live_readback": runtime_readback,
    }
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-19T14:59:00+00:00",
            "authority": "observability_only",
            "provider_admission_pending_count": 1,
            "transition_request_pending_count": 0,
            "provider_admission_candidates": [candidate],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "provider_admission_pending_count": 1,
                    "transition_request_pending_count": 0,
                    "current_control_action": {
                        "status": "provider_admission_pending",
                        "reason": "opl_transition_runtime_readback_published",
                        "provider_admission_requires_opl_runtime_result": False,
                    },
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "schema_version": 1,
                        "status": "owner_receipt_recorded",
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                    },
                    "provider_admission_candidates": [candidate],
                    "action_queue": [],
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / f"{stage_attempt_id}.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "stage_outcome/opl-handoff",
            "generated_at": "2026-06-19T14:58:00Z",
            "status": "blocked",
            "execution_status": "typed_blocker",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "stage_packet_ref": stage_packet_ref,
            "typed_blocker_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                f"{stage_attempt_id}.closeout.json"
            ),
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "run_quality_repair_batch",
                "stage_work_done": ["Recorded a stale selector typed blocker."],
                "paper_work_done": [
                    "No paper, manuscript, current package, or publication gate surface was edited."
                ],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                    f"{stage_attempt_id}.closeout.json"
                ],
                "changed_paper_surfaces": [],
                "outcome": "typed_blocker",
                "remaining_blockers": ["no_selected_dispatch_for_authorized_stage_packet"],
                "progress_delta_classification": "typed_blocker",
                "next_forced_delta": {
                    "required_delta_kind": "typed_blocker_consumption_or_owner_route_selector_reconcile",
                    "work_unit_id": work_unit,
                    "owner_action": {
                        "next_owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit,
                    },
                },
            },
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id=study_id,
    )

    assert projection["provider_admission_pending_count"] == 1
    assert len(projection["provider_admission_candidates"]) == 1
    assert projection["provider_admission_candidates"][0]["attempt_idempotency_key"] == route_key
    assert projection["provider_admission_candidates"][0][
        "opl_domain_progress_transition_runtime_live_readback"
    ]["runtime_readback_status"] == "complete_transaction"
    assert "provider_admission_terminal_closeout_consumed" not in projection
    assert projection.get("blocked_reason") in (None, "")


def test_study_progress_projects_opl_current_control_state_handoff_and_mcp_markdown(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff_projection",
            "schema_version": 1,
            "generated_at": "2026-05-04T06:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {
                        "health_status": "escalated",
                        "runtime_liveness_status": "stale",
                    },
                    "artifact_delta": {
                        "status": "stale",
                        "summary": "No meaningful artifact delta since last tick.",
                    },
                    "gate_specificity": {
                        "status": "blocked",
                        "blocked_reason": "publication_gate_specificity_required",
                    },
                    "ai_reviewer_status": {
                        "status": "trace_missing",
                        "summary": "AI reviewer workflow must recheck the repaired package.",
                    },
                    "stage_progress_log": {
                        "surface_kind": "opl_stage_progress_log_summary",
                        "projection_scope": "stage_attempt_workbench",
                        "attempt_count": 2,
                        "completed_attempt_count": 1,
                        "blocked_attempt_count": 1,
                        "duration_observed_attempt_count": 1,
                        "missing_usage_telemetry_attempt_count": 1,
                        "attempt_refs": [
                            "/stage_attempt_workbench/attempts/sat-001/stage_progress_log",
                            "/stage_attempt_workbench/attempts/sat-002/stage_progress_log",
                        ],
                        "authority_boundary": {
                            "opl": "stage_attempt_progress_observability_projection_only",
                            "domain": "truth_quality_artifact_gate_owner",
                            "can_authorize_quality_verdict": False,
                        },
                    },
                    "action_queue": [
                        {
                            "action_type": "publication_gate_specificity_required",
                            "summary": "Ask controller to specify the publication gate blocker.",
                            "fingerprint": "publication_gate_specificity_required::publication_gate_specificity_required",
                            "queue_age_hours": 6.0,
                            "owner_pickup": {
                                "state": "overdue",
                                "owner": "publication_gate",
                                "duration_hours": 6.0,
                                "pickup_overdue": True,
                            },
                            "consumption": {
                                "state": "attention_required",
                                "unconsumed_duration_hours": 6.0,
                                "developer_supervisor_attention_required": True,
                            },
                        },
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "summary": "Return the package to AI reviewer after gate specificity.",
                        },
                    ],
                    "queue_slo": {
                        "max_queue_age_hours": 6.0,
                        "owner_pickup_overdue_count": 1,
                        "developer_supervisor_attention_required_count": 1,
                    },
                    "owner_pickup_overdue": True,
                    "developer_supervisor_attention_required": True,
                    "why_not_applied": [
                        "runtime_recovery_retry_budget_exhausted",
                        "ai_reviewer_trace_missing",
                    ],
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                    "blocked_reason": "runtime_recovery_not_authorized",
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {"attempt_state": "escalated", "retry_budget_remaining": 0},
            "authority_snapshot": {"control_state": "blocked_runtime_escalation"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    compact = mcp_projection.compact_study_progress_projection(result)
    markdown = mcp_projection.render_mcp_study_progress_markdown(result)

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["source_path"] == str(handoff_path)
    assert dashboard["authority"] == "observability_only"
    assert dashboard["quest_status"] == "running"
    assert dashboard["active_run_id"] == "run-001"
    assert dashboard["runtime_health"]["health_status"] == "escalated"
    assert dashboard["artifact_delta"]["status"] == "stale"
    assert dashboard["gate_specificity"]["blocked_reason"] == "publication_gate_specificity_required"
    assert dashboard["ai_reviewer_status"]["status"] == "trace_missing"
    assert dashboard["stage_progress_log"]["surface_kind"] == "opl_stage_progress_log_summary"
    assert dashboard["stage_progress_log"]["attempt_count"] == 2
    assert dashboard["stage_progress_log"]["missing_usage_telemetry_attempt_count"] == 1
    assert dashboard["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-001/stage_progress_log",
        "/stage_attempt_workbench/attempts/sat-002/stage_progress_log",
    ]
    assert (
        dashboard["stage_progress_log"]["authority_boundary"]["can_authorize_quality_verdict"]
        is False
    )
    assert [item["action_type"] for item in dashboard["action_queue"]] == [
        "publication_gate_specificity_required",
        "return_to_ai_reviewer_workflow",
    ]
    assert dashboard["queue_slo"]["max_queue_age_hours"] == 6.0
    assert dashboard["owner_pickup_overdue"] is True
    assert dashboard["developer_supervisor_attention_required"] is True
    assert dashboard["action_queue"][0]["fingerprint"] == (
        "publication_gate_specificity_required::publication_gate_specificity_required"
    )
    assert dashboard["action_queue"][0]["source"] == "opl_current_control_state_action_queue"
    assert dashboard["action_queue"][0]["owner_pickup"]["state"] == "overdue"
    assert dashboard["action_queue"][0]["consumption"]["developer_supervisor_attention_required"] is True
    assert dashboard["why_not_applied"] == [
        "runtime_recovery_retry_budget_exhausted",
        "ai_reviewer_trace_missing",
    ]
    assert dashboard["next_owner"] == "external_supervisor"
    assert dashboard["external_supervisor_required"] is True
    assert result["refs"]["opl_current_control_state_handoff_path"] == str(handoff_path)
    assert compact["opl_current_control_state_handoff"]["blocked_reason"] == "runtime_recovery_not_authorized"
    assert compact["opl_current_control_state_handoff"]["queue_slo"]["owner_pickup_overdue_count"] == 1
    assert compact["opl_current_control_state_handoff"]["stage_progress_log"]["attempt_count"] == 2
    assert compact["opl_current_control_state_handoff"]["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-001/stage_progress_log",
        "/stage_attempt_workbench/attempts/sat-002/stage_progress_log",
    ]
    assert compact["opl_current_control_state_handoff"]["action_queue"][0]["queue_age_hours"] == 6.0
    assert compact["opl_current_control_state_handoff"]["action_queue"][0]["action_type"] == (
        "publication_gate_specificity_required"
    )
    assert compact["opl_current_control_state_handoff"]["action_queue"][0]["source"] == (
        "opl_current_control_state_action_queue"
    )
    assert "OPL Current Control State Handoff" in markdown
    assert "publication_gate_specificity_required" in markdown
    assert "owner_pickup: `overdue`" in markdown
    assert "stage_progress_log: attempts `2`" in markdown
    assert "missing_usage_telemetry_attempt_count: `1`" in markdown
    assert "developer_supervisor_attention_required: `True`" in markdown
    assert "runtime_recovery_retry_budget_exhausted" in markdown
    assert result["paper_progress_delta"]["count"] == 0
    assert result["paper_progress_delta"]["token_usage_total"] is None
    assert result["platform_repair_delta"]["count"] == 1
def test_accepted_typed_closeout_consumes_matching_handoff_action_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = "domain-transition::route_back_same_line::dpcc"
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-10T07:27:46+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "active_stage_attempt_id": "sat-dm003-gate",
                    "active_run_id": "opl-stage-attempt://sat-dm003-gate",
                    "active_workflow_id": "wf-dm003-gate",
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "terminal",
                        "runtime_liveness_status": "terminal",
                    },
                    "action_queue": [
                        {
                            "action_type": "run_gate_clearing_batch",
                            "owner": "finalize",
                            "next_owner": "finalize",
                            "next_work_unit": work_unit,
                            "work_unit_id": work_unit,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "authority": "mas_provider_admission_identity",
                            "action_id": "provider-admission::dm003::run_gate_clearing_batch",
                        }
                    ],
                    "next_owner": "finalize",
                    "blocked_reason": "opl_stage_attempt_admission_required",
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "sat-dm003-gate.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat-dm003-gate",
            "stage_id": "stage_outcome/opl-handoff",
            "stage_packet_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/"
                "owner_callable_adapters/run_gate_clearing_batch.json"
            ),
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_gate_clearing_batch",
            "generated_at": "2026-06-10T07:20:00+00:00",
            "status": "blocked",
            "outcome": "typed_blocker",
            "blocked_reason": "publication_gate_replay_blocked",
            "domain_ready": False,
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "owner_route_basis": {
                "truth_epoch": "truth::dm003::2026-06-10T07:20:00Z",
                "source_eval_id": "publication-eval::dm003::ai-reviewer-record::current",
                "work_unit_id": work_unit,
                "work_unit_fingerprint": fingerprint,
                "owner_reason": "publication_gate_replay_blocked",
            },
            "domain_execution": {
                "action_type": "run_gate_clearing_batch",
                "execution_status": "blocked",
                "blocked_reason": "publication_gate_replay_blocked",
                "domain_owner": "publication_gate",
                "execution_id": "execution::dm003::run_gate_clearing_batch::2026-06-10T07:20:00Z",
            },
            "typed_blocker": {
                "surface_kind": "mas_typed_blocker",
                "reason": "publication_gate_replay_blocked",
                "status": "blocked",
                "blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "current_required_action": "return_to_publishability_gate",
                "recommended_route_back": "return_to_write",
                "phase_owner": "publication_gate",
                "evidence_refs": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/gate_clearing_batch/latest.json",
                    "runtime/quests/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/reports/publishability_gate/2026-06-10T072000Z.json",
                ],
            },
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/sat-dm003-gate.closeout.json",
                f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json",
            ],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "publication_gate_replay",
                "current_owner": "publication_gate",
                "problem_summary": "Gate replay remains blocked after default executor closeout.",
                "stage_goal": "Return a typed blocker instead of re-running the consumed gate replay work unit.",
                "stage_work_done": ["Recorded gate replay typed blocker."],
                "paper_work_done": [
                    "No manuscript-body quality verdict or publication readiness claim was made."
                ],
                "changed_stage_surfaces": [
                    f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json"
                ],
                "changed_paper_surfaces": [],
                "outcome": "typed_blocker",
                "remaining_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "duration": {"status": "missing", "seconds": None},
                "token_usage": {"status": "missing", "total_tokens": None},
                "cost": {"status": "missing", "usd": None},
                "usage_refs": [],
                "cost_refs": [],
                "evidence_refs": [
                    f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json"
                ],
                "progress_delta_classification": "typed_blocker",
                "deliverable_progress_delta": {"count": 0, "token_usage_total": None},
                "paper_progress_delta": {"count": 0, "token_usage_total": None},
                "platform_repair_delta": {"count": 1, "token_usage_total": None},
                "next_forced_delta": {
                    "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                    "work_unit_id": work_unit,
                    "owner_action": {
                        "next_owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit,
                    },
                },
            },
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "handoff_required",
            "reason": "opl_stage_attempt_admission_required",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-after-gate-closeout",
                "runtime_liveness_status": "none",
                "attempt_state": "blocked",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["blocked_reason"] == "publication_gate_replay_blocked"
    assert handoff["typed_blocker"]["blocker_type"] == "publication_gate_replay_blocked"
    assert handoff["typed_blocker"]["work_unit_id"] == work_unit
    assert handoff["typed_blocker"]["work_unit_fingerprint"] == fingerprint
    assert handoff["latest_typed_owner_callable_closeout"]["receipt_ref"].endswith(
        "sat-dm003-gate.closeout.json"
    )
    assert handoff["consumed_action_queue"][0]["work_unit_id"] == work_unit
    assert handoff["action_queue"] == []
    assert_default_next_action_legacy_surfaces_retired(result)


from .opl_current_control_state_handoff_projection_cases.supervisor_tick_audit import *  # noqa: F403,F401,E402
from .opl_current_control_state_handoff_projection_cases.owner_receipt_closeout import *  # noqa: F403,F401,E402
from .opl_current_control_state_handoff_projection_cases.current_control_current_work_unit import *  # noqa: F403,F401,E402
from .opl_current_control_state_handoff_projection_cases.running_attempt_identity import *  # noqa: F403,F401,E402
from .opl_current_control_state_handoff_projection_cases.stage_progress_log_delta import *  # noqa: F403,F401,E402
from .opl_current_control_state_handoff_projection_cases.terminal_closeout_cases import *  # noqa: F403,F401,E402
