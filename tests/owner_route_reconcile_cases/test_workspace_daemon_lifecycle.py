from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.runtime_health_kernel_parts import event_log as runtime_health_event_log

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_runtime_health_fixture_event(
    runtime_health_kernel,
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    event_type: str,
    payload: dict[str, object],
    recorded_at: str,
) -> None:
    event_type_text = str(event_type or "").strip()
    path = runtime_health_kernel.runtime_health_events_path(study_root=study_root)
    existing = runtime_health_kernel.read_runtime_health_events(study_root=study_root)
    sequence = len(existing) + 1
    event = {
        "schema_version": runtime_health_kernel.SCHEMA_VERSION,
        "event_id": runtime_health_event_log.build_event_id(
            study_id=study_id,
            quest_id=quest_id,
            event_type=event_type_text,
            payload=payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ),
        "sequence": sequence,
        "study_id": study_id,
        "quest_id": quest_id,
        "event_type": event_type_text,
        "recorded_at": recorded_at,
        "payload": dict(payload),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def test_scan_domain_routes_apply_safe_actions_releases_idle_workspace_daemon(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_status": "stopped",
            "runtime_health_snapshot": {"attempt_state": "idle"},
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_ready",
            "supervision": {"active_run_id": None},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
    )

    assert result["workspace_daemon_lifecycle"]["released"] is False
    assert result["workspace_daemon_lifecycle"]["reason"] == "opl_provider_liveness_owner_required"
    assert result["workspace_daemon_lifecycle"]["typed_blocker"]["owner"] == "one-person-lab"


def test_scan_domain_routes_projects_opl_provider_readiness_from_owner_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_status": "active",
            "runtime_health_snapshot": {"attempt_state": "escalated"},
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "supervision": {"active_run_id": None},
        },
    )
    monkeypatch.setattr(
        module.opl_provider_attempts,
        "current_provider_readiness",
        lambda **_: {
            "surface_kind": "opl_provider_readiness_projection",
            "source": "opl_family_runtime_status",
            "provider_kind": "temporal",
            "provider_ready": True,
            "worker_ready": True,
            "managed_worker_source_current": True,
            "opl_current_control_state_ref": "opl://current-control/provider-readiness-test",
            "provider_completion_is_domain_ready": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_ready": False,
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    readiness = result["provider_readiness"]
    assert readiness["source"] == "opl_family_runtime_status"
    assert readiness["provider_ready"] is True
    assert readiness["worker_ready"] is True
    assert readiness["managed_worker_source_current"] is True
    assert readiness["provider_completion_is_domain_ready"] is False
    assert readiness["can_write_domain_truth"] is False
    assert readiness["can_authorize_publication_ready"] is False


def test_opl_bin_prefers_packaged_runtime_over_dev_checkout(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    packaged_bin = tmp_path / "runtime" / "current" / "bin" / "opl"
    dev_bin = tmp_path / "one-person-lab" / "bin" / "opl"
    packaged_bin.parent.mkdir(parents=True)
    dev_bin.parent.mkdir(parents=True)
    packaged_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    dev_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.delenv("OPL_BIN", raising=False)
    monkeypatch.delenv("OPL_FAMILY_RUNTIME_BIN", raising=False)
    monkeypatch.setattr(module.shutil, "which", lambda _name: None)
    monkeypatch.setattr(module, "PACKAGED_OPL_BIN", packaged_bin)
    monkeypatch.setattr(module, "DEV_OPL_BIN", dev_bin)

    assert module._opl_bin() == packaged_bin


def test_current_provider_readiness_uses_current_cli_over_stale_packaged_runtime(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    path_bin = tmp_path / "homebrew" / "opl"
    packaged_bin = tmp_path / "runtime" / "current" / "bin" / "opl"
    dev_bin = tmp_path / "one-person-lab" / "bin" / "opl"
    for path in (path_bin, packaged_bin, dev_bin):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n", encoding="utf-8")
    calls: list[Path] = []

    monkeypatch.delenv("OPL_BIN", raising=False)
    monkeypatch.delenv("OPL_FAMILY_RUNTIME_BIN", raising=False)
    monkeypatch.setattr(module.shutil, "which", lambda _name: str(path_bin))
    monkeypatch.setattr(module, "PACKAGED_OPL_BIN", packaged_bin)
    monkeypatch.setattr(module, "DEV_OPL_BIN", dev_bin)

    def fake_run_opl_json(opl_bin: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        assert args == ("family-runtime", "status", "--provider", "temporal", "--json")
        assert timeout_seconds > 0
        calls.append(opl_bin)
        if opl_bin == packaged_bin:
            return _opl_status_payload(provider_ready=False, worker_ready=False, source_current=False)
        if opl_bin == path_bin:
            return _opl_status_payload(provider_ready=True, worker_ready=True, source_current=True)
        raise AssertionError(opl_bin)

    monkeypatch.setattr(module, "_run_opl_json", fake_run_opl_json)

    readiness = module.current_provider_readiness(timeout_seconds=2.0)

    assert calls == [path_bin]
    assert readiness["provider_ready"] is True
    assert readiness["worker_ready"] is True
    assert readiness["managed_worker_source_current"] is True


def test_current_provider_readiness_can_skip_stale_packaged_for_current_dev_cli(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    packaged_bin = tmp_path / "runtime" / "current" / "bin" / "opl"
    dev_bin = tmp_path / "one-person-lab" / "bin" / "opl"
    for path in (packaged_bin, dev_bin):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n", encoding="utf-8")
    calls: list[Path] = []

    monkeypatch.delenv("OPL_BIN", raising=False)
    monkeypatch.delenv("OPL_FAMILY_RUNTIME_BIN", raising=False)
    monkeypatch.setattr(module.shutil, "which", lambda _name: None)
    monkeypatch.setattr(module, "PACKAGED_OPL_BIN", packaged_bin)
    monkeypatch.setattr(module, "DEV_OPL_BIN", dev_bin)

    def fake_run_opl_json(opl_bin: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        assert args == ("family-runtime", "status", "--provider", "temporal", "--json")
        assert timeout_seconds > 0
        calls.append(opl_bin)
        if opl_bin == packaged_bin:
            return _opl_status_payload(provider_ready=False, worker_ready=False, source_current=False)
        if opl_bin == dev_bin:
            return _opl_status_payload(provider_ready=True, worker_ready=True, source_current=True)
        raise AssertionError(opl_bin)

    monkeypatch.setattr(module, "_run_opl_json", fake_run_opl_json)

    readiness = module.current_provider_readiness(timeout_seconds=2.0)

    assert calls == [packaged_bin, dev_bin]
    assert readiness["provider_ready"] is True
    assert readiness["worker_ready"] is True
    assert readiness["managed_worker_source_current"] is True


def test_opl_bin_keeps_explicit_env_override(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    override_bin = tmp_path / "custom" / "opl"
    packaged_bin = tmp_path / "runtime" / "current" / "bin" / "opl"
    override_bin.parent.mkdir(parents=True)
    packaged_bin.parent.mkdir(parents=True)
    override_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    packaged_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setenv("OPL_BIN", str(override_bin))
    monkeypatch.delenv("OPL_FAMILY_RUNTIME_BIN", raising=False)
    monkeypatch.setattr(module, "PACKAGED_OPL_BIN", packaged_bin)

    assert module._opl_bin() == override_bin


def _opl_status_payload(*, provider_ready: bool, worker_ready: bool, source_current: bool) -> dict:
    return {
        "family_runtime": {
            "readiness": {
                "provider_ready": provider_ready,
                "full_online_ready": provider_ready,
                "durable_online_ready": provider_ready,
                "degraded": not provider_ready,
                "degraded_reason": None if provider_ready else "temporal_worker_source_stale",
                "selected_provider_can_replace_domain_daemons": provider_ready,
            },
            "provider_runtime": {
                "providers": {
                    "temporal": {
                        "details": {
                            "worker_ready": worker_ready,
                            "task_queue": "opl-stage-attempts",
                            "worker_readiness": {
                                "managed_worker_source_current": source_current,
                                "managed_worker_pid": 12345 if worker_ready else None,
                            },
                        }
                    }
                }
            },
            "periodic_execution": {
                "authority_boundary": {
                    "can_write_domain_truth": False,
                    "can_authorize_publication_ready": False,
                }
            },
        }
    }


def test_live_provider_attempt_default_budget_allows_temporal_queue_inspect(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    task_id = "frt-live-ai-reviewer"
    calls: list[tuple[str, ...]] = []

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))

    def fake_run_opl_json(
        _opl_bin: Path,
        args: tuple[str, ...],
        *,
        timeout_seconds: float,
    ) -> dict[str, object] | None:
        calls.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            assert timeout_seconds > 3.0
            assert timeout_seconds <= module.DEFAULT_LIVE_ATTEMPT_INSPECTION_TIMEOUT_SECONDS
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": task_id,
                            "status": "running",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "payload": {
                                "profile": str(profile_path),
                                "study_id": study_id,
                                "action_type": "return_to_ai_reviewer_workflow",
                                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                                "dispatch_ref": "studies/003/artifacts/supervision/consumer/default_executor_dispatches/immutable/return_to_ai_reviewer_workflow/live.json",
                            },
                        }
                    ]
                }
            }
        if args == ("family-runtime", "queue", "inspect", task_id, "--json"):
            assert timeout_seconds > 3.0
            return {
                "family_runtime_task": {
                    "task": {
                        "task_id": task_id,
                        "task_kind": "domain_owner/default-executor-dispatch",
                        "payload": {
                            "profile": str(profile_path),
                            "study_id": study_id,
                            "action_type": "return_to_ai_reviewer_workflow",
                            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            "dispatch_ref": "studies/003/artifacts/supervision/consumer/default_executor_dispatches/immutable/return_to_ai_reviewer_workflow/live.json",
                        },
                        "current_control_state": {
                            "running_provider_attempt": True,
                            "active_run_id": "opl-stage-attempt://sat-live",
                            "active_stage_attempt_id": "sat-live",
                            "active_workflow_id": "wf-live",
                            "current_attempt_state": "running",
                            "reconciliation_status": "running",
                            "provider_kind": "temporal",
                            "provider_run": {"provider_status": "running"},
                        },
                    },
                    "stage_attempts": [
                        {
                            "stage_attempt_id": "sat-live",
                            "status": "running",
                            "workspace_locator": {
                                "workspace_root": str(profile.workspace_root),
                                "action_type": "return_to_ai_reviewer_workflow",
                                "dispatch_ref": "studies/003/artifacts/supervision/consumer/default_executor_dispatches/immutable/return_to_ai_reviewer_workflow/live.json",
                            },
                        }
                    ],
                }
            }
        raise AssertionError(args)

    monkeypatch.setattr(module, "_run_opl_json", fake_run_opl_json)

    projection = module.live_provider_attempt_for_study(
        profile=profile,
        study_id=study_id,
        preferred_actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            }
        ],
    )

    assert calls == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "queue", "inspect", task_id, "--json"),
    ]
    assert projection is not None
    assert projection["running_provider_attempt"] is True
    assert projection["active_stage_attempt_id"] == "sat-live"
    assert projection["runtime_health"]["runtime_liveness_status"] == "live"


def test_scan_domain_routes_uses_current_provider_readiness_for_same_tick_runtime_health(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    runtime_health_kernel = importlib.import_module("med_autoscience.controllers.runtime_health_kernel")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    for sequence in range(1, 4):
        _write_runtime_health_fixture_event(
            runtime_health_kernel,
            study_root=study_root,
            study_id=study_id,
            quest_id=study_id,
            event_type="recover_attempt",
            payload={
                "attempt_state": "failed",
                "decision": "resume",
                "failure_reason": "quest_marked_running_but_no_live_session",
                "active_run_id": None,
                "opl_lifecycle_proof_ref": f"opl-stage-attempt://runtime-health-test-{sequence}",
            },
            recorded_at=f"2026-05-28T10:4{sequence}:00+00:00",
        )
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(
            {
                "surface": "opl_current_control_state_handoff",
                "generated_at": "2026-05-28T10:45:00+00:00",
                "studies": [
                    {
                        "study_id": study_id,
                        "runtime_health": {
                            "attempt_state": "escalated",
                            "retry_budget_remaining": 0,
                            "canonical_runtime_action": "external_supervisor_required",
                            "blocking_reasons": [
                                "quest_marked_running_but_no_live_session",
                                "runtime_recovery_retry_budget_exhausted",
                            ],
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "status": "parked",
                "runtime_audit": {"worker_running": False},
            },
            "supervisor_tick_audit": {
                "status": "stale",
                "required": True,
                "latest_recorded_at": "2026-05-28T10:49:00+00:00",
                "seconds_since_latest_recorded_at": 1880,
                "reason": "opl_current_control_state_handoff_stale",
            },
            "runtime_health_snapshot": {
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "canonical_runtime_action": "external_supervisor_required",
                "blocking_reasons": [
                    "quest_marked_running_but_no_live_session",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            },
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "paper_stage": "publication_supervision",
            "supervision": {"active_run_id": None},
            "authority_snapshot": {
                "control_state": "blocked_runtime_escalation",
                "canonical_runtime_action": "external_supervisor_required",
                "blocking_reasons": [
                    "quest_marked_running_but_no_live_session",
                    "runtime_recovery_retry_budget_exhausted",
                ],
                "dispatch_gate": {
                    "state": "blocked",
                    "dispatch_allowed": False,
                    "blocking_reasons": [
                        "quest_marked_running_but_no_live_session",
                        "runtime_recovery_retry_budget_exhausted",
                    ],
                },
                "route_authorization": {"runtime_recovery_allowed": False},
            },
            "ai_repair_lifecycle": {
                "surface": "ai_repair_lifecycle",
                "schema_version": 1,
                "study_id": study_id,
                "quest_id": study_id,
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "top_action": {
                    "action_type": "controller_repair",
                    "owner": "mas_controller",
                    "repair_kind": "analysis_claim_evidence_redrive",
                    "auto_apply_allowed": True,
                },
            },
        },
    )
    monkeypatch.setattr(module.opl_provider_attempts, "live_provider_attempt_for_study", lambda **_: None)
    monkeypatch.setattr(
        module.opl_provider_attempts,
        "current_provider_readiness",
        lambda **_: {
            "surface_kind": "opl_provider_readiness_projection",
            "source": "opl_family_runtime_status",
            "provider_kind": "temporal",
            "provider_ready": True,
            "worker_ready": True,
            "managed_worker_source_current": True,
            "opl_current_control_state_ref": "opl://current-control/provider-readiness-same-tick",
            "provider_completion_is_domain_ready": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_ready": False,
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    health = result["studies"][0]["runtime_health"]
    assert health["attempt_state"] == "recovering"
    assert health["retry_budget_remaining"] == 2
    assert health["canonical_runtime_action"] == "recover_runtime"
    assert health["blocking_reasons"] == ["quest_marked_running_but_no_live_session"]
    assert health["supervisor_state"]["status"] == "fresh"
    assert health["supervisor_state"]["latest_recorded_at"] == result["generated_at"]
    assert result["studies"][0]["blocked_reason"] != "runtime_recovery_retry_budget_exhausted"
    assert result["studies"][0]["blocked_reason"] == "opl_stage_attempt_admission_required"
    assert result["studies"][0]["owner_route"]["owner_reason"] == "opl_stage_attempt_admission_required"


def test_scan_domain_routes_observe_mode_does_not_release_workspace_daemon(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_status": "stopped",
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "paper_stage": "bundle_stage_ready",
            "supervision": {"active_run_id": None},
        },
    )
    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=False,
    )

    assert result["workspace_daemon_lifecycle"]["released"] is False
    assert result["workspace_daemon_lifecycle"]["reason"] == "safe_actions_not_enabled"
