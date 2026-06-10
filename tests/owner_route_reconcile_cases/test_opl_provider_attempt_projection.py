from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
import time

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_stage_attempt_closeout(
    *,
    profile,
    study_id: str,
    stage_attempt_id: str,
    status: str = "blocked",
) -> Path:
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json"
    )
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_attempt_id": stage_attempt_id,
                "study_id": study_id,
                "status": status,
                "typed_blocker_ref": f"{closeout_path}#typed_blocker",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return closeout_path


def test_live_provider_attempt_projection_reads_opl_queue_inspect(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    profile_ref = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": "frt-live",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": "2026-05-26T13:35:24Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": "001-risk",
                            },
                        }
                    ]
                }
            }
        if args == ("family-runtime", "queue", "inspect", "frt-live", "--json"):
            return {
                "family_runtime_task": {
                    "task": {
                        "task_id": "frt-live",
                        "task_kind": "domain_owner/default-executor-dispatch",
                        "payload": {
                            "study_id": "001-risk",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "dm002_methods_write_pass",
                            "dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
                        },
                        "current_control_state": {
                            "active_run_id": "opl-stage-attempt://sat-live",
                            "active_stage_attempt_id": "sat-live",
                            "active_workflow_id": "wf-live",
                            "running_provider_attempt": True,
                            "provider_kind": "temporal",
                            "current_attempt_state": "running",
                            "reconciliation_status": "running",
                            "provider_run": {
                                "provider_status": "running",
                                "last_heartbeat_at": "2026-05-26T13:35:24Z",
                            },
                            "stage_progress_log": {
                                "surface_kind": "opl_stage_progress_log_summary",
                                "projection_scope": "stage_attempt_workbench",
                                "attempt_count": 2,
                                "completed_attempt_count": 1,
                                "blocked_attempt_count": 0,
                                "missing_usage_telemetry_attempt_count": 1,
                                "attempt_refs": [
                                    "/stage_attempt_workbench/attempts/sat-live/stage_progress_log"
                                ],
                                "authority_boundary": {
                                    "opl": "stage_attempt_progress_observability_projection_only",
                                    "domain": "truth_quality_artifact_gate_owner",
                                    "can_authorize_quality_verdict": False,
                                },
                            },
                        },
                    },
                    "stage_attempts": [
                        {
                            "workspace_locator": {
                                "workspace_root": str(profile.workspace_root),
                                "action_type": "run_quality_repair_batch",
                                "dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
                            }
                        }
                    ],
                }
            }
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(profile=profile, study_id="001-risk")

    assert result is not None
    assert result["active_run_id"] == "opl-stage-attempt://sat-live"
    assert result["active_stage_attempt_id"] == "sat-live"
    assert result["active_workflow_id"] == "wf-live"
    assert result["running_provider_attempt"] is True
    assert result["runtime_health"]["runtime_liveness_status"] == "live"
    assert result["action_type"] == "run_quality_repair_batch"
    assert result["work_unit_id"] == "dm002_methods_write_pass"
    assert result["stage_progress_log"]["attempt_count"] == 2
    assert result["stage_progress_log"]["missing_usage_telemetry_attempt_count"] == 1
    assert result["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-live/stage_progress_log"
    ]
    assert result["stage_progress_log"]["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert result["authority_boundary"]["provider_completion_is_domain_ready"] is False
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "queue", "inspect", "frt-live", "--json"),
    ]


def test_live_provider_attempt_projection_reads_queue_list_linked_liveness(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    profile_ref = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": "frt-live-linked",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": "2026-06-10T21:42:00.690Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "workspace_root": str(profile.workspace_root),
                                "study_id": "001-risk",
                                "quest_id": "001-risk",
                                "action_type": "return_to_ai_reviewer_workflow",
                                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                                "work_unit_fingerprint": "sha256:current-ai-reviewer",
                                "dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/return_to_ai_reviewer_workflow.json",
                            },
                            "linked_stage_attempt_liveness": {
                                "status": "live",
                                "stage_attempt_id": "sat-linked",
                                "workflow_id": "wf-linked",
                                "provider_kind": "temporal",
                                "provider_status": "running",
                                "stage_attempt_status": "running",
                                "last_heartbeat_at": "2026-06-10T21:42:00.690Z",
                                "ledger_last_heartbeat_at": "2026-06-10T21:42:00.690Z",
                            },
                        }
                    ]
                }
            }
        raise AssertionError(f"queue list linked liveness should avoid inspect fallback: {args}")

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(profile=profile, study_id="001-risk")

    assert result is not None
    assert result["source"] == "opl_family_runtime_queue_list_linked_liveness"
    assert result["active_run_id"] == "opl-stage-attempt://sat-linked"
    assert result["active_stage_attempt_id"] == "sat-linked"
    assert result["active_workflow_id"] == "wf-linked"
    assert result["running_provider_attempt"] is True
    assert result["task_id"] == "frt-live-linked"
    assert result["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert result["work_unit_fingerprint"] == "sha256:current-ai-reviewer"
    assert result["runtime_health"]["runtime_liveness_status"] == "live"
    assert result["runtime_health"]["provider_status"] == "running"
    assert commands == [("family-runtime", "queue", "list", "--json")]


def test_live_provider_attempt_projection_skips_linked_liveness_with_terminal_mas_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    profile_ref = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    study_id = "001-risk"
    _write_stage_attempt_closeout(
        profile=profile,
        study_id=study_id,
        stage_attempt_id="sat-linked",
        status="blocked",
    )
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": "frt-live-linked",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": "2026-06-10T21:42:00.690Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "workspace_root": str(profile.workspace_root),
                                "study_id": study_id,
                                "quest_id": study_id,
                                "action_type": "return_to_ai_reviewer_workflow",
                                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            },
                            "linked_stage_attempt_liveness": {
                                "status": "live",
                                "stage_attempt_id": "sat-linked",
                                "workflow_id": "wf-linked",
                                "provider_kind": "temporal",
                                "provider_status": "running",
                                "stage_attempt_status": "running",
                            },
                        }
                    ]
                }
            }
        if args == ("family-runtime", "attempt", "list", "--json"):
            return {"family_runtime_stage_attempts": {"attempts": []}}
        raise AssertionError(f"terminal MAS closeout must suppress stale live projection: {args}")

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(profile=profile, study_id=study_id)

    assert result is None
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "attempt", "list", "--json"),
    ]


def test_live_provider_attempt_projection_skips_queue_inspect_with_terminal_mas_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    profile_ref = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    study_id = "001-risk"
    _write_stage_attempt_closeout(
        profile=profile,
        study_id=study_id,
        stage_attempt_id="sat-live",
        status="blocked",
    )
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": "frt-live",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": "2026-05-26T13:35:24Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": study_id,
                            },
                        }
                    ]
                }
            }
        if args == ("family-runtime", "queue", "inspect", "frt-live", "--json"):
            return {
                "family_runtime_task": {
                    "task": {
                        "task_id": "frt-live",
                        "task_kind": "domain_owner/default-executor-dispatch",
                        "payload": {
                            "study_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "dm002_methods_write_pass",
                        },
                        "current_control_state": {
                            "active_run_id": "opl-stage-attempt://sat-live",
                            "active_stage_attempt_id": "sat-live",
                            "active_workflow_id": "wf-live",
                            "running_provider_attempt": True,
                            "provider_kind": "temporal",
                            "current_attempt_state": "running",
                            "reconciliation_status": "running",
                            "provider_run": {"provider_status": "running"},
                        },
                    },
                    "stage_attempts": [
                        {
                            "workspace_locator": {
                                "workspace_root": str(profile.workspace_root),
                                "action_type": "run_quality_repair_batch",
                            }
                        }
                    ],
                }
            }
        if args == ("family-runtime", "attempt", "list", "--json"):
            return {"family_runtime_stage_attempts": {"attempts": []}}
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(profile=profile, study_id=study_id)

    assert result is None
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "queue", "inspect", "frt-live", "--json"),
        ("family-runtime", "attempt", "list", "--json"),
    ]


def test_live_provider_attempt_projection_prefers_current_owner_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    profile_ref = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": "frt-ai-reviewer",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": "2026-05-28T15:17:25Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": "001-risk",
                                "action_type": "return_to_ai_reviewer_workflow",
                                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                                "dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/return_to_ai_reviewer_workflow.json",
                            },
                        },
                        {
                            "task_id": "frt-write-repair",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": "2026-05-28T15:15:39Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": "001-risk",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": "manuscript_story_repair",
                                "dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
                            },
                        },
                    ]
                }
            }
        task_id = args[3]
        action_type = "run_quality_repair_batch" if task_id == "frt-write-repair" else "return_to_ai_reviewer_workflow"
        work_unit_id = (
            "manuscript_story_repair"
            if task_id == "frt-write-repair"
            else "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
        )
        dispatch_ref = (
            "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json"
            if task_id == "frt-write-repair"
            else "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/return_to_ai_reviewer_workflow.json"
        )
        return {
            "family_runtime_task": {
                "task": {
                    "task_id": task_id,
                    "task_kind": "domain_owner/default-executor-dispatch",
                    "payload": {
                        "study_id": "001-risk",
                        "action_type": action_type,
                        "work_unit_id": work_unit_id,
                        "dispatch_ref": dispatch_ref,
                    },
                    "current_control_state": {
                        "active_run_id": f"opl-stage-attempt://sat-{task_id}",
                        "active_stage_attempt_id": f"sat-{task_id}",
                        "active_workflow_id": f"wf-{task_id}",
                        "running_provider_attempt": True,
                        "provider_kind": "temporal",
                        "current_attempt_state": "running",
                        "reconciliation_status": "running",
                        "provider_run": {"provider_status": "running"},
                    },
                },
                "stage_attempts": [
                    {
                        "workspace_locator": {
                            "workspace_root": str(profile.workspace_root),
                            "action_type": action_type,
                            "dispatch_ref": dispatch_ref,
                        }
                    }
                ],
            }
        }

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(
        profile=profile,
        study_id="001-risk",
        preferred_actions=[
            {
                "action_type": "run_quality_repair_batch",
                "controller_work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization",
                "executable_work_unit": "manuscript_story_repair",
            }
        ],
    )

    assert result is not None
    assert result["task_id"] == "frt-write-repair"
    assert result["action_type"] == "run_quality_repair_batch"
    assert result["work_unit_id"] == "manuscript_story_repair"
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "queue", "inspect", "frt-write-repair", "--json"),
    ]


def test_live_provider_attempt_projection_uses_action_type_when_work_unit_ids_differ(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    profile_ref = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": "frt-ai-reviewer",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": "2026-05-28T15:17:25Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": "001-risk",
                                "action_type": "return_to_ai_reviewer_workflow",
                                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                                "dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/return_to_ai_reviewer_workflow.json",
                            },
                        },
                        {
                            "task_id": "frt-write-repair",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": "2026-05-28T15:15:39Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": "001-risk",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": "manuscript_story_repair",
                                "dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
                            },
                        },
                    ]
                }
            }
        task_id = args[3]
        action_type = "run_quality_repair_batch" if task_id == "frt-write-repair" else "return_to_ai_reviewer_workflow"
        work_unit_id = (
            "manuscript_story_repair"
            if task_id == "frt-write-repair"
            else "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
        )
        return {
            "family_runtime_task": {
                "task": {
                    "task_id": task_id,
                    "task_kind": "domain_owner/default-executor-dispatch",
                    "payload": {
                        "study_id": "001-risk",
                        "action_type": action_type,
                        "work_unit_id": work_unit_id,
                    },
                    "current_control_state": {
                        "active_run_id": f"opl-stage-attempt://sat-{task_id}",
                        "active_stage_attempt_id": f"sat-{task_id}",
                        "active_workflow_id": f"wf-{task_id}",
                        "running_provider_attempt": True,
                        "provider_kind": "temporal",
                        "current_attempt_state": "running",
                        "reconciliation_status": "running",
                        "provider_run": {"provider_status": "running"},
                    },
                },
                "stage_attempts": [
                    {
                        "workspace_locator": {
                            "workspace_root": str(profile.workspace_root),
                            "action_type": action_type,
                        }
                    }
                ],
            }
        }

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(
        profile=profile,
        study_id="001-risk",
        preferred_actions=[
            {
                "action_type": "run_quality_repair_batch",
                "controller_work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization",
            }
        ],
    )

    assert result is not None
    assert result["task_id"] == "frt-write-repair"
    assert result["action_type"] == "run_quality_repair_batch"
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "queue", "inspect", "frt-write-repair", "--json"),
    ]


def test_live_provider_attempt_projection_skips_non_live_tasks(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    profile_ref = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": "frt-old-succeeded",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "succeeded",
                            "updated_at": "2026-05-27T13:35:24Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": "001-risk",
                            },
                        },
                        {
                            "task_id": "frt-old-dead-letter",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "dead_letter",
                            "updated_at": "2026-05-27T13:36:24Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": "001-risk",
                            },
                        },
                    ]
                }
            }
        if args == ("family-runtime", "attempt", "list", "--json"):
            return {"family_runtime_stage_attempts": {"attempts": []}}
        raise AssertionError(f"non-live queue tasks must not be inspected: {args}")

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(profile=profile, study_id="001-risk")

    assert result is None
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "attempt", "list", "--json"),
    ]


def test_live_provider_attempt_projection_falls_back_to_stage_attempt_ledger(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {"family_runtime_queue": {"tasks": []}}
        if args == ("family-runtime", "attempt", "list", "--json"):
            return {
                "family_runtime_stage_attempts": {
                    "attempts": [
                        {
                            "stage_attempt_id": "sat-live",
                            "domain_id": "medautoscience",
                            "stage_id": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "task_id": "frt-live",
                            "provider_run": {
                                "provider_status": "running",
                                "workflow_id": "wf-live",
                                "last_heartbeat_at": "2026-05-29T09:13:53Z",
                            },
                            "workspace_locator": {
                                "workspace_root": str(profile.workspace_root),
                                "study_id": study_id,
                                "quest_id": study_id,
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": "medical_prose_write_repair",
                                "dispatch_ref": "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
                            },
                        }
                    ]
                }
            }
        if args == ("family-runtime", "attempt", "inspect", "sat-live", "--json"):
            return {
                "family_runtime_stage_attempt": {
                    "attempt": {
                        "stage_attempt_id": "sat-live",
                        "domain_id": "medautoscience",
                        "stage_id": "domain_owner/default-executor-dispatch",
                        "status": "running",
                        "task_id": "frt-live",
                        "provider_kind": "temporal",
                        "workflow_id": "wf-live",
                        "provider_run": {
                            "provider_status": "running",
                            "workflow_id": "wf-live",
                            "last_heartbeat_at": "2026-05-29T09:13:53Z",
                        },
                        "workspace_locator": {
                            "workspace_root": str(profile.workspace_root),
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "dispatch_ref": "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
                        },
                        "stage_progress_log": {
                            "surface_kind": "opl_stage_progress_log_summary",
                            "projection_scope": "stage_attempt_workbench",
                            "attempt_count": 1,
                            "runner_progress_event_count": 4,
                            "attempt_refs": [
                                "/stage_attempt_workbench/attempts/sat-live/stage_progress_log"
                            ],
                        },
                    }
                }
            }
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(profile=profile, study_id=study_id)

    assert result is not None
    assert result["source"] == "opl_family_runtime_attempt_inspect"
    assert result["active_run_id"] == "opl-stage-attempt://sat-live"
    assert result["active_stage_attempt_id"] == "sat-live"
    assert result["active_workflow_id"] == "wf-live"
    assert result["running_provider_attempt"] is True
    assert result["task_id"] == "frt-live"
    assert result["action_type"] == "run_quality_repair_batch"
    assert result["work_unit_id"] == "medical_prose_write_repair"
    assert result["runtime_health"]["runtime_liveness_status"] == "live"
    assert result["stage_progress_log"]["attempt_count"] == 1
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "attempt", "list", "--json"),
        ("family-runtime", "attempt", "inspect", "sat-live", "--json"),
    ]


def test_live_provider_attempt_projection_skips_attempt_ledger_entry_with_terminal_mas_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    _write_stage_attempt_closeout(
        profile=profile,
        study_id=study_id,
        stage_attempt_id="sat-closed",
        status="blocked",
    )
    commands: list[tuple[str, ...]] = []

    def _attempt(stage_attempt_id: str, *, updated_at: str) -> dict:
        return {
            "stage_attempt_id": stage_attempt_id,
            "domain_id": "medautoscience",
            "stage_id": "domain_owner/default-executor-dispatch",
            "status": "running",
            "task_id": f"frt-{stage_attempt_id}",
            "updated_at": updated_at,
            "provider_run": {
                "provider_status": "running",
                "workflow_id": f"wf-{stage_attempt_id}",
                "last_heartbeat_at": updated_at,
            },
            "workspace_locator": {
                "workspace_root": str(profile.workspace_root),
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
            },
        }

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {"family_runtime_queue": {"tasks": []}}
        if args == ("family-runtime", "attempt", "list", "--json"):
            return {
                "family_runtime_stage_attempts": {
                    "attempts": [
                        _attempt("sat-closed", updated_at="2026-06-10T22:00:00Z"),
                        _attempt("sat-live", updated_at="2026-06-10T21:59:00Z"),
                    ]
                }
            }
        if args == ("family-runtime", "attempt", "inspect", "sat-live", "--json"):
            return {
                "family_runtime_stage_attempt": {
                    "attempt": _attempt("sat-live", updated_at="2026-06-10T21:59:00Z")
                }
            }
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(
        profile=profile,
        study_id=study_id,
        max_inspect_count=1,
    )

    assert result is not None
    assert result["active_stage_attempt_id"] == "sat-live"
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "attempt", "list", "--json"),
        ("family-runtime", "attempt", "inspect", "sat-live", "--json"),
    ]


def test_live_provider_attempt_projection_limits_queue_inspect_candidates(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    profile_ref = profile.workspace_root / "ops" / "medautoscience" / "profiles" / "local.toml"
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "queue", "list", "--json"):
            return {
                "family_runtime_queue": {
                    "tasks": [
                        {
                            "task_id": f"frt-{index}",
                            "task_kind": "domain_owner/default-executor-dispatch",
                            "status": "running",
                            "updated_at": f"2026-05-26T13:35:2{index}Z",
                            "payload": {
                                "profile": str(profile_ref),
                                "study_id": "001-risk",
                            },
                        }
                        for index in range(5)
                    ]
                }
            }
        return {
            "family_runtime_task": {
                "task": {
                    "task_id": args[3],
                    "payload": {"study_id": "001-risk"},
                    "current_control_state": {"running_provider_attempt": False},
                }
            }
        }

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(
        profile=profile,
        study_id="001-risk",
        max_inspect_count=2,
    )

    assert result is None
    assert commands == [
        ("family-runtime", "queue", "list", "--json"),
        ("family-runtime", "queue", "inspect", "frt-4", "--json"),
        ("family-runtime", "queue", "inspect", "frt-3", "--json"),
        ("family-runtime", "attempt", "list", "--json"),
    ]


def test_run_opl_json_timeout_kills_process_group(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    marker = tmp_path / "child.pid"
    script = tmp_path / "opl"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "sleep 30 &",
                f"echo $! > {str(marker)!r}",
                "sleep 30",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    script.chmod(0o755)

    started = time.monotonic()
    result = module._run_opl_json(script, ("family-runtime", "queue", "inspect", "frt-hangs", "--json"), timeout_seconds=2)

    assert result is None
    assert time.monotonic() - started < 5
    deadline = time.monotonic() + 3
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert marker.exists()
    child_pid = int(marker.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        completed = subprocess.run(["/bin/ps", "-p", str(child_pid)], capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("timed-out OPL subprocess child was still running")


def test_scan_projects_live_opl_provider_attempt_for_current_owner_route(monkeypatch, tmp_path: Path) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    opl_attempts = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm002",
            "canonical_runtime_action": "continue_supervising_runtime",
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {
                "unit_id": "dm002_methods_write_pass",
                "lane": "write",
                "summary": "Repair manuscript methods and package currentness.",
            },
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002",
            "source_signature": "truth-source-dm002",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "active_run_id": None,
        "supervision": {"active_run_id": None, "health_status": "stale"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::write-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )
    monkeypatch.setattr(
        opl_attempts,
        "live_provider_attempt_for_study",
        lambda **_: {
            "surface_kind": "opl_current_control_state_provider_attempt",
            "active_run_id": "opl-stage-attempt://sat-live",
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "running_provider_attempt": True,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "dm002_methods_write_pass",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["active_run_id"] == "opl-stage-attempt://sat-live"
    assert study["active_stage_attempt_id"] == "sat-live"
    assert study["active_workflow_id"] == "wf-live"
    assert study["running_provider_attempt"] is True
    assert study["runtime_health"]["runtime_liveness_status"] == "live"
    assert study["action_queue"] == []
    assert result["action_queue"] == []
    assert study["blocked_reason"] is None
    assert study["why_not_applied"] is None
    assert study["next_owner"] == "supervisor_only/live_provider_attempt"
    envelope = study["current_execution_envelope"]
    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "supervisor_only/live_provider_attempt"
    assert envelope["next_work_unit"] == "dm002_methods_write_pass"
    assert envelope["typed_blocker"] is None


def test_scan_passes_bounded_opl_probe_budget_to_provider_projection(monkeypatch, tmp_path: Path) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    opl_attempts = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm002",
            "canonical_runtime_action": "continue_supervising_runtime",
            "worker_liveness_state": {"state": "not_live", "worker_running": False},
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {
                "unit_id": "dm002_methods_write_pass",
                "lane": "write",
            },
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002",
            "source_signature": "truth-source-dm002",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "active_run_id": None,
        "supervision": {"active_run_id": None, "health_status": "stale"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::write-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
    }
    readiness_calls: list[float] = []
    live_attempt_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )
    monkeypatch.setattr(
        opl_attempts,
        "current_provider_readiness",
        lambda *, timeout_seconds: readiness_calls.append(timeout_seconds) or None,
    )
    monkeypatch.setattr(
        opl_attempts,
        "live_provider_attempt_for_study",
        lambda **kwargs: live_attempt_calls.append(kwargs) or None,
    )

    scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
        live_attempt_timeout_seconds=1.25,
        live_attempt_max_inspect_count=1,
        provider_readiness_timeout_seconds=0.75,
    )

    assert readiness_calls == [0.75]
    assert len(live_attempt_calls) == 1
    assert live_attempt_calls[0]["timeout_seconds"] == 1.25
    assert live_attempt_calls[0]["max_inspect_count"] == 1
    assert live_attempt_calls[0]["profile"] == profile
    assert live_attempt_calls[0]["study_id"] == study_id


def test_scan_does_not_project_terminal_stage_attempt_as_active_run(monkeypatch, tmp_path: Path) -> None:
    scan = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    opl_attempts = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": "opl-stage-attempt://sat-terminal",
        "runtime_liveness_audit": {
            "status": "unknown",
            "source": "opl_current_control_state_required",
            "active_run_id": None,
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-terminal",
            "canonical_runtime_action": "external_supervisor_required",
            "active_run_id": None,
            "last_known_run_id": "opl-stage-attempt://sat-terminal",
            "worker_liveness_state": {
                "state": "unknown",
                "runtime_liveness_status": "live",
                "worker_running": None,
                "active_run_id": None,
            },
            "blocking_reasons": [
                "live_worker_requires_worker_running",
                "runtime_recovery_retry_budget_exhausted",
            ],
            "retry_budget_remaining": 0,
        },
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {
                "unit_id": "dm002_methods_write_pass",
                "lane": "write",
                "summary": "Repair manuscript methods and package currentness.",
            },
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002",
            "source_signature": "truth-source-dm002",
        },
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_runtime_escalated",
        "paper_stage": "publishability_gate_blocked",
        "active_run_id": None,
        "supervision": {"active_run_id": None, "health_status": "stale"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::write-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer"},
    }
    monkeypatch.setattr(
        scan,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval_payload),
    )
    monkeypatch.setattr(opl_attempts, "live_provider_attempt_for_study", lambda **_: None)

    result = scan.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["running_provider_attempt"] is False
    assert study["active_run_id"] is None
    assert study["owner_route"]["active_run_id"] is None
    assert study["runtime_health"]["last_known_run_id"] == "opl-stage-attempt://sat-terminal"
    assert [item["action_type"] for item in study["action_queue"]] == ["run_quality_repair_batch"]
