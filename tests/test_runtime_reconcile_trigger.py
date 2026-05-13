from __future__ import annotations

import importlib


def _base_status(**overrides):
    payload = {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "recovery_intent": {"current_action": "safe_reconcile_ready"},
        "runtime_session": {
            "session_id": "session-001",
            "freshness_state": "stale",
        },
        "worker_state": "stale",
        "quest_status": "active",
        "decision": "noop",
        "reason": "runtime_session_stale",
        "runtime_health_snapshot": {
            "attempt_state": "degraded",
            "retry_budget_remaining": 2,
        },
        "execution_owner_guard": {"supervisor_only": False},
    }
    payload.update(overrides)
    return payload


def _build_projection(status, **kwargs):
    module = importlib.import_module("med_autoscience.controllers.runtime_reconcile_trigger")
    return module.build_runtime_reconcile_trigger_projection(
        status_payload=status,
        profile_ref="/workspace/profile.toml",
        study_id="001-risk",
        **kwargs,
    )


def test_stale_runtime_session_projects_safe_reconcile_recommendation() -> None:
    projection = _build_projection(_base_status())

    assert projection["safe_to_request"] is True
    assert projection["request_kind"] == "runtime_supervisor_reconcile"
    assert projection["recommended_command"] == (
        "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
        "--profile /workspace/profile.toml --studies 001-risk --mode developer_apply_safe --dry-run"
    )
    assert projection["dedupe_fingerprint"].startswith("runtime_supervisor_reconcile:")
    assert projection["blocked_reasons"] == []
    assert projection["authority"]["writes_runtime"] is False
    assert projection["authority"]["writes_publication_truth"] is False


def test_due_outer_supervision_slo_projects_safe_reconcile_recommendation() -> None:
    projection = _build_projection(
        _base_status(
            runtime_session={"freshness_state": "fresh"},
            worker_state="fresh",
            outer_supervision_slo={
                "surface_kind": "outer_supervision_slo",
                "state": "due",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
                    "--profile /workspace/profile.toml --studies 001-risk --mode developer_apply_safe --dry-run"
                ),
            },
        )
    )

    assert projection["safe_to_request"] is True
    assert projection["action_class"] == "reconcile_dry_run"
    assert projection["will_start_llm"] is False
    assert projection["action_fingerprint"] == projection["dedupe_fingerprint"]
    assert {"source": "outer_supervision_slo.state", "state": "due"} in projection["stale_signals"]
    assert projection["outer_supervision_slo"]["state"] == "due"


def test_stall_signals_project_paper_progress_stall_read_model() -> None:
    projection = _build_projection(
        _base_status(
            runtime_health_snapshot={
                "attempt_state": "recovering",
                "retry_budget_remaining": 2,
                "blocking_reasons": [
                    "same_fingerprint_loop",
                    "read_churn_without_artifact_delta",
                    "stale_truth_surface",
                ],
                "worker_liveness_state": {"state": "activity_timeout"},
            },
            autonomy_slo={
                "state": "breach",
                "breach_types": ["same_fingerprint_loop", "read_churn_without_artifact_delta"],
                "mds_progress_markers": {"turn_progress_kind": "read_churn_without_artifact_delta"},
            },
            study_truth_snapshot={"freshness_state": "stale", "truth_epoch": "truth-stale"},
        )
    )

    stall = projection["paper_progress_stall"]
    assert stall["surface_kind"] == "paper_progress_stall"
    assert stall["stalled"] is True
    assert stall["stall_reasons"] == [
        "same_fingerprint_loop",
        "read_churn_without_artifact_delta",
        "stale_truth_surface",
    ]
    assert stall["safe_reconcile_candidate"] is True
    assert stall["will_start_llm"] is False
    assert stall["codex_dispatch_count"] == 0
    assert {"source": "paper_progress_stall.stall_reasons", "state": "same_fingerprint_loop"} in projection[
        "stale_signals"
    ]
    assert projection["safe_to_request"] is True


def test_new_run_grace_suppresses_historical_same_fingerprint_stall_signal() -> None:
    projection = _build_projection(
        _base_status(
            runtime_session={"freshness_state": "fresh"},
            worker_state="fresh",
            reason="quest_already_running",
            active_run_id="run-new",
            runtime_liveness_audit={
                "status": "live",
                "active_run_id": "run-new",
                "runtime_audit": {
                    "status": "live",
                    "worker_running": True,
                    "active_run_id": "run-new",
                },
            },
            autonomy_slo={
                "state": "breach",
                "active_run_id": "run-old",
                "breach_types": ["same_fingerprint_loop", "read_churn_without_artifact_delta"],
                "mds_progress_markers": {"turn_progress_kind": "read_churn_without_artifact_delta"},
            },
            progress_freshness={
                "activity_timeout": {
                    "state": "watching_new_run",
                    "active_run_id": "run-new",
                    "breach_types": ["same_fingerprint_loop"],
                    "new_run_grace": {
                        "state": "new_run_grace",
                        "active_run_id": "run-new",
                        "observed_at": "2026-05-13T06:47:25+00:00",
                        "seconds_since_observed": 24,
                        "grace_after_seconds": 1800,
                    },
                },
                "meaningful_artifact_delta_freshness": {
                    "status": "missing",
                    "turn_progress_kind": "read_churn_without_artifact_delta",
                },
            },
        )
    )

    stall = projection["paper_progress_stall"]
    assert stall["stalled"] is False
    assert stall["stall_reasons"] == []
    assert stall["safe_reconcile_candidate"] is False
    assert {"source": "paper_progress_stall.stall_reasons", "state": "same_fingerprint_loop"} not in projection[
        "stale_signals"
    ]
    assert projection["safe_to_request"] is False
    assert "runtime_session_not_stale" in projection["blocked_reasons"]


def test_fresh_paper_artifact_delta_suppresses_historical_same_fingerprint_stall_signal() -> None:
    projection = _build_projection(
        _base_status(
            runtime_session={"freshness_state": "fresh"},
            worker_state="fresh",
            reason="quest_already_running",
            active_run_id="run-live",
            runtime_liveness_audit={
                "status": "live",
                "active_run_id": "run-live",
                "runtime_audit": {
                    "status": "live",
                    "worker_running": True,
                    "active_run_id": "run-live",
                },
            },
            autonomy_slo={
                "state": "breach",
                "active_run_id": "run-live",
                "breach_types": ["same_fingerprint_loop", "read_churn_without_artifact_delta"],
                "mds_progress_markers": {"turn_progress_kind": "read_churn_without_artifact_delta"},
            },
            progress_freshness={
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_source": "gate_clearing_batch",
                    "latest_progress_summary": (
                        "controller-owned gate-clearing batch updated 12 paper-facing artifact(s)."
                    ),
                },
                "activity_timeout": {
                    "state": "ok",
                    "active_run_id": "run-live",
                    "breach_types": ["same_fingerprint_loop"],
                },
            },
        )
    )

    stall = projection["paper_progress_stall"]
    assert stall["stalled"] is False
    assert stall["stall_reasons"] == []
    assert stall["safe_reconcile_candidate"] is False
    assert {"source": "paper_progress_stall.stall_reasons", "state": "same_fingerprint_loop"} not in projection[
        "stale_signals"
    ]
    assert projection["safe_to_request"] is False
    assert "runtime_session_not_stale" in projection["blocked_reasons"]


def test_retry_budget_exhausted_projects_terminal_paper_progress_stall() -> None:
    projection = _build_projection(
        _base_status(
            runtime_health_snapshot={
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        )
    )

    stall = projection["paper_progress_stall"]
    assert stall["stalled"] is True
    assert stall["terminal"] is True
    assert stall["safe_reconcile_candidate"] is False
    assert stall["stall_reasons"] == ["runtime_recovery_retry_budget_exhausted"]
    assert "runtime_recovery_retry_budget_exhausted" in projection["blocked_reasons"]
    assert projection["safe_to_request"] is False


def test_duplicate_reconcile_fingerprint_is_not_requestable() -> None:
    first = _build_projection(_base_status())
    duplicate = _build_projection(
        _base_status(),
        existing_fingerprints={first["dedupe_fingerprint"]},
    )

    assert duplicate["safe_to_request"] is False
    assert duplicate["dedupe_state"] == "duplicate"
    assert duplicate["recommended_command"] is None
    assert "duplicate_reconcile_request" in duplicate["blocked_reasons"]


def test_human_gate_parked_completed_and_retry_exhausted_fail_closed() -> None:
    cases = [
        _base_status(needs_user_decision=True),
        _base_status(quest_status="parked"),
        _base_status(quest_status="completed", study_completion_contract={"ready": True, "status": "resolved"}),
        _base_status(
            runtime_health_snapshot={
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        ),
    ]

    for status in cases:
        projection = _build_projection(status)
        assert projection["safe_to_request"] is False
        assert projection["recommended_command"] is None
        assert projection["blocked_reasons"]


def test_blocked_outer_supervision_slo_fail_closes_reconcile_trigger() -> None:
    projection = _build_projection(
        _base_status(
            outer_supervision_slo={
                "surface_kind": "outer_supervision_slo",
                "state": "blocked",
                "blocked_reasons": ["retired_legacy_service_present"],
            }
        )
    )

    assert projection["safe_to_request"] is False
    assert projection["recommended_command"] is None
    assert "outer_supervision_slo_blocked" in projection["blocked_reasons"]


def test_reconcile_projection_never_authorizes_quality_publication_or_submission_ready() -> None:
    projection = _build_projection(_base_status())

    assert projection["authority_flags"] == {
        "quality_ready_authorized": False,
        "publication_ready_authorized": False,
        "submission_ready_authorized": False,
    }
    assert "quality_ready" not in projection
    assert "publication_ready" not in projection
    assert "submission_ready" not in projection


def test_progress_portal_surfaces_runtime_reconcile_recommendation() -> None:
    trigger = _build_projection(_base_status())
    portal = importlib.import_module("med_autoscience.controllers.progress_portal")

    payload = portal.build_progress_portal_payload(
        profile_name="test-profile",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload={
            "study_id": "001-risk",
            "progress_freshness": {"status": "stale"},
            "outer_supervision_slo": {"surface_kind": "outer_supervision_slo", "state": "stale"},
            "runtime_reconcile_trigger": trigger,
            "user_visible_projection": {
                "schema_version": 2,
                "writer_state": "recovering",
                "user_next": "monitor",
                "reason": "runtime_session_stale",
            },
        },
    )

    assert payload["study"]["runtime_reconcile_trigger"]["safe_to_request"] is True
    assert payload["study"]["outer_supervision_slo"]["state"] == "stale"
    assert payload["study"]["runtime_reconcile_trigger"]["recommended_command"] == trigger["recommended_command"]
    assert "runtime_reconcile_requestable" in payload["conditions"]["stale"]
    assert "outer_supervision_slo_stale" in payload["conditions"]["stale"]


def test_workspace_attention_prefers_safe_reconcile_command_for_requestable_trigger() -> None:
    trigger = _build_projection(_base_status())
    attention = importlib.import_module("med_autoscience.controllers.product_entry_parts.workspace_attention")

    queue = attention._attention_queue(
        workspace_status="attention_required",
        workspace_supervision={"service": {"loaded": True}, "study_counts": {}},
        studies=[
            {
                "study_id": "001-risk",
                "runtime_reconcile_trigger": trigger,
                "outer_supervision_slo": {"surface_kind": "outer_supervision_slo", "state": "stale"},
                "commands": {"progress": "progress-command"},
                "progress_freshness": {"status": "stale"},
            }
        ],
        commands={},
    )

    assert queue[0]["code"] == "study_runtime_reconcile_requestable"
    assert queue[0]["recommended_command"] == trigger["recommended_command"]
    assert queue[0]["runtime_reconcile_trigger"]["dedupe_fingerprint"] == trigger["dedupe_fingerprint"]
    assert queue[0]["outer_supervision_slo"]["state"] == "stale"


def test_study_progress_includes_safe_reconcile_trigger(monkeypatch, tmp_path) -> None:
    from tests.study_runtime_test_helpers import make_profile, write_study

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

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            **_base_status(study_root=str(study_root), quest_root=str(quest_root)),
            "schema_version": 1,
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_exists": True,
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "publication_supervisor_state": {
                "supervisor_phase": "write_stage",
                "phase_owner": "runtime",
                "current_required_action": "continue_supervising_runtime",
            },
            "runtime_liveness_audit": {
                "status": "stale",
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "stale",
                "reason": "supervisor_tick_report_stale",
                "summary": "supervisor tick is stale.",
            },
        },
    )

    result = module.read_study_progress(
        profile=profile,
        profile_ref="/workspace/profile.toml",
        study_id="001-risk",
    )

    trigger = result["runtime_reconcile_trigger"]
    slo = result["outer_supervision_slo"]
    assert slo["surface_kind"] == "outer_supervision_slo"
    assert slo["state"] in {"missing", "due", "stale"}
    assert trigger["safe_to_request"] is True
    assert trigger["recommended_command"] == (
        "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
        "--profile /workspace/profile.toml --studies 001-risk --mode developer_apply_safe --dry-run"
    )
