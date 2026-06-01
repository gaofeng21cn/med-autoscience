from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_platform_only_repair_projects_next_forced_paper_delta_without_counting_paper_progress(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff_projection",
            "schema_version": 1,
            "generated_at": "2026-05-29T00:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "escalated"},
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "next_owner": "runtime_mechanism_repair",
                    "owner_route": {
                        "next_owner": "runtime_mechanism_repair",
                        "route_target": "write",
                        "allowed_actions": ["paper_autonomy/repair-recheck"],
                        "target_surface": {
                            "ref_kind": "route_obligation",
                            "route_target": "write",
                            "surface_ref": "canonical_manuscript",
                        },
                        "acceptance_refs": [
                            "canonical_manuscript_delta",
                            "ai_reviewer_gate_replay_request",
                        ],
                        "source_refs": {
                            "work_unit_id": "publishability_repair_sprint",
                            "source_eval_id": "eval-current",
                        },
                        "source_fingerprint": "source-current",
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
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "execution_owner_guard": {"supervisor_only": True},
            "runtime_health_snapshot": {"attempt_state": "escalated"},
            "authority_snapshot": {"control_state": "blocked_runtime_escalation"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["deliverable_progress_delta"] == result["paper_progress_delta"]
    assert result["paper_progress_delta"]["count"] == 0
    assert result["platform_repair_delta"]["count"] == 1
    assert result["progress_delta_classification"] == "platform_repair"
    assert result["progress_first_sprint_state"]["deliverable_progress_delta"] == result["paper_progress_delta"]
    assert result["progress_first_sprint_state"]["classification"] == "platform_repair"
    assert result["progress_first_sprint_state"]["paper_progress_delta_counted"] is False
    assert result["next_forced_delta"]["required_delta_kind"] == "paper_progress_delta_or_typed_blocker"
    assert result["next_forced_delta"]["work_unit_id"] == "publishability_repair_sprint"
    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": "canonical_manuscript",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "owner_route.target_surface",
        "missing_explicit_target_surface": False,
    }
    assert result["next_forced_delta"]["acceptance_refs"] == [
        "canonical_manuscript_delta",
        "ai_reviewer_gate_replay_request",
    ]
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": "runtime_mechanism_repair",
        "work_unit_id": "publishability_repair_sprint",
        "allowed_actions": ["paper_autonomy/repair-recheck"],
        "owner_receipt_required": True,
    }
    monitoring = result["progress_first_monitoring_summary"]
    assert monitoring["authority"] == "refs_only_observability"
    assert monitoring["active_run_id"] == "run-001"
    assert monitoring["worker_liveness"]["health_status"] == "escalated"
    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["next_owner"] == "runtime_mechanism_repair"
    assert monitoring["next_work_unit"] == "publishability_repair_sprint"
    assert monitoring["typed_blocker"]["blocker_type"] == "runtime_recovery_retry_budget_exhausted"
    assert monitoring["progress_delta_classification"] == "platform_repair"
    assert monitoring["paper_progress_delta_counted"] is False
    assert monitoring["platform_repair_delta_counted"] is True
    assert monitoring["next_forced_delta"]["target_surface"]["surface_ref"] == "canonical_manuscript"
    assert monitoring["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert monitoring["next_forced_delta"]["target_surface_diagnostic"]["source"] == "owner_route.target_surface"
    assert monitoring["next_forced_delta"]["acceptance_refs"] == [
        "canonical_manuscript_delta",
        "ai_reviewer_gate_replay_request",
    ]
    assert monitoring["next_forced_delta"]["owner_action"]["next_owner"] == "runtime_mechanism_repair"
    assert monitoring["foreground_write_policy"] == {
        "supervisor_only": True,
        "foreground_can_write_runtime_owned_surfaces": False,
        "rule": "supervisor_only_no_runtime_owned_writes",
    }
    assert monitoring["authority_boundary"]["can_write_paper_or_package"] is False
    assert monitoring["authority_boundary"]["can_authorize_quality_verdict"] is False
    compact = mcp_projection.compact_study_progress_projection(result)
    markdown = mcp_projection.render_mcp_study_progress_markdown(result)
    assert compact["next_forced_delta"]["target_surface"]["surface_ref"] == "canonical_manuscript"
    assert compact["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert compact["next_forced_delta"]["owner_action"]["work_unit_id"] == "publishability_repair_sprint"
    assert compact["progress_first_monitoring_summary"]["active_run_id"] == "run-001"
    assert compact["progress_first_monitoring_summary"]["next_work_unit"] == "publishability_repair_sprint"
    assert compact["progress_first_monitoring_summary"]["next_forced_delta"]["acceptance_refs"] == [
        "canonical_manuscript_delta",
        "ai_reviewer_gate_replay_request",
    ]
    assert "## Progress-First Monitoring" in markdown
    assert "platform_delta_counted: `True`" in markdown


def test_next_forced_delta_marks_next_forced_target_surface_as_precise() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 1},
            "current_execution_envelope": {
                "owner_route": {
                    "next_owner": "paper_author",
                    "route_target": "write",
                    "next_forced_target_surface": {
                        "ref_kind": "route_obligation",
                        "route_target": "write",
                        "surface_ref": "canonical_manuscript#discussion",
                    },
                    "source_refs": {"work_unit_id": "publishability_repair_sprint"},
                }
            },
        }
    )

    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": "canonical_manuscript#discussion",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "owner_route.next_forced_target_surface",
        "missing_explicit_target_surface": False,
    }


def test_next_forced_delta_reports_generic_target_surface_fallback_when_owner_route_lacks_precise_surface() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 1},
            "current_execution_envelope": {
                "owner_route": {
                    "next_owner": "paper_author",
                    "route_target": "write",
                    "source_refs": {"work_unit_id": "publishability_repair_sprint"},
                }
            },
        }
    )

    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": "study_progress.next_forced_delta",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "generic_route_obligation_fallback"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is True
    assert result["next_forced_delta"]["target_surface_fallback_reason"] == (
        "owner_route_missing_explicit_target_surface"
    )
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "generic_fallback",
        "source": "study_progress.next_forced_delta",
        "missing_explicit_target_surface": True,
        "fallback_reason": "owner_route_missing_explicit_target_surface",
    }
