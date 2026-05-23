from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from tests.test_cli_cases.shared import write_profile


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _touch(path: Path, timestamp: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    os.utime(path, (timestamp, timestamp))


def _write_opl_handoff(path: Path, *, recorded_at: str, status: str = "owner_receipt_written") -> None:
    _write_json(
        path,
        {
            "surface_kind": "mas_opl_runtime_owner_handoff",
            "schema_version": 1,
            "recorded_at": recorded_at,
            "status": status,
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "provider_completion_is_domain_completion": False,
            "queue_succeeded_is_domain_completion": False,
            "mas_materializes_runtime_supervision": False,
            "mas_runtime_read_model_retired": True,
            "reason": "opl_current_control_state_required",
            "typed_blocker": {
                "blocker_type": "opl_runtime_owner_handoff_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
            },
        },
    )


def test_study_cycle_profiler_builds_timing_profile_and_ignores_latest_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    study_root.mkdir(parents=True)
    quest_root.mkdir(parents=True)
    (study_root / "runtime_binding.yaml").write_text(
        "\n".join(
            [
                "study_id: 001-risk",
                "quest_id: quest-001",
                f"runtime_root: {workspace_root / 'ops' / 'med-deepscientist' / 'runtime' / 'quests'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "20260424T235500Z.json",
        {
            "emitted_at": "2026-04-24T23:55:00+00:00",
            "task_id": "task-001",
            "study_id": "001-risk",
            "task_intent": "revision intake",
        },
    )
    _write_opl_handoff(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "20260425T000000Z.json",
        recorded_at="2026-04-25T00:00:00+00:00",
    )
    _write_opl_handoff(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "20260425T001000Z.json",
        recorded_at="2026-04-25T00:10:00+00:00",
    )
    _write_opl_handoff(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        recorded_at="2026-04-25T00:10:00+00:00",
        status="handoff_required",
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "recorded_at": "2026-04-25T00:10:00+00:00",
            "health_status": "escalated",
            "runtime_reason": "retired_surface_must_be_ignored",
        },
    )
    for index in range(2):
        _write_json(
            study_root / "artifacts" / "controller_decisions" / f"20260425T002{index}00Z.json",
            {
                "emitted_at": f"2026-04-25T00:2{index}:00+00:00",
                "decision_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "reason": "route back to analysis-campaign until claim evidence is clear",
            },
        )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:30:00+00:00",
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "claim_id": "claim-001",
                    "source_path": str(study_root / "paper" / "manuscript.md"),
                }
            ],
            "recommended_actions": [
                {
                    "action_type": "bounded_analysis",
                    "route_target": "analysis-campaign",
                    "reason": "claim evidence repair",
                }
            ],
        },
    )
    _touch(study_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_776_999_000)

    profile_payload = module.profile_study_cycle(
        profile=profile,
        study_id="001-risk",
        study_root=None,
        since="2026-04-24T23:50:00+00:00",
    )

    assert profile_payload["study_id"] == "001-risk"
    assert profile_payload["quest_id"] == "quest-001"
    assert "runtime_supervision" not in profile_payload["category_windows"]
    assert profile_payload["category_windows"]["opl_runtime_owner_handoff"]["event_count"] == 2
    assert profile_payload["opl_runtime_owner_handoff_summary"]["status_counts"] == {
        "owner_receipt_written": 2,
    }
    assert profile_payload["controller_decision_fingerprints"]["top_repeats"][0]["count"] == 2
    assert profile_payload["gate_blocker_summary"]["current_blockers"] == ["claim_evidence_consistency_failed"]
    assert profile_payload["package_currentness"]["status"] == "stale"
    assert profile_payload["step_latest_times"]["task_intake"] == "2026-04-24T23:55:00+00:00"
    assert profile_payload["step_timings"][0] == {
        "from_step": "task_intake",
        "to_step": "opl_runtime_owner_handoff",
        "from_at": "2026-04-24T23:55:00+00:00",
        "to_at": "2026-04-25T00:00:00+00:00",
        "duration_seconds": 300,
    }
    assert profile_payload["eta_confidence_band"]["classification"] == "claim_evidence"
    assert profile_payload["sli_summary"]["opl_runtime_owner_handoff_clear_ratio"] == 1.0
    assert profile_payload["sli_summary"]["next_work_unit_id"] == "analysis_claim_evidence_repair"
    assert profile_payload["cycle_observability"]["flow_metrics"]["task_intake_to_opl_handoff_seconds"] == 300
    assert profile_payload["cycle_observability"]["stability_metrics"]["repeated_controller_dispatch_count"] == 1
    assert profile_payload["cycle_observability"]["quality_preservation"]["gate_relaxation_allowed"] is False
    assert profile_payload["cycle_observability"]["acceleration_readiness"] == {
        "state": "restore_before_accelerating",
        "no_progress_signal": True,
        "requires_quality_gate_preservation": True,
        "next_work_unit_id": "analysis_claim_evidence_repair",
    }
    assert [item["bottleneck_id"] for item in profile_payload["bottlenecks"]] == [
        "repeated_controller_decision",
        "publication_gate_blocked",
    ]


def test_study_cycle_profiler_uses_current_manual_finishing_state_over_window_churn(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "004-ready"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-004"
    study_root.mkdir(parents=True)
    quest_root.mkdir(parents=True)
    (study_root / "runtime_binding.yaml").write_text(
        "\n".join(
            [
                "study_id: 004-ready",
                "quest_id: quest-004",
                f"runtime_root: {workspace_root / 'ops' / 'med-deepscientist' / 'runtime' / 'quests'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "recorded_at": "2026-04-25T00:20:00+00:00",
            "health_status": "inactive",
            "runtime_decision": "blocked",
            "runtime_reason": "retired_surface_must_be_ignored",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:15:00+00:00",
            "gaps": [
                {
                    "severity": "optional",
                    "summary": "bundle-stage work is unlocked and can proceed on the critical path",
                }
            ],
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "generated_at": "2026-04-25T00:20:00+00:00",
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "supervisor_phase": "bundle_stage_ready",
            "current_required_action": "continue_bundle_stage",
            "external_submission_metadata_pending": True,
        },
    )
    _touch(study_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_776_999_000)

    profile_payload = module.profile_study_cycle(
        profile=profile,
        study_id="004-ready",
        study_root=None,
        since="2026-04-24T23:50:00+00:00",
    )

    assert profile_payload["current_state_summary"]["state"] == "auto_runtime_parked"
    assert "legacy_current_stage" not in profile_payload["current_state_summary"]
    assert profile_payload["current_state_summary"]["parked_state"] == "external_metadata_pending"
    assert profile_payload["gate_blocker_summary"]["current_blockers"] == []
    assert profile_payload["eta_confidence_band"]["classification"] == "external_metadata_pending"
    assert profile_payload["bottlenecks"] == []


def test_study_cycle_profiler_does_not_treat_control_refresh_as_package_drift(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    control_report = workspace_root / "ops" / "runtime" / "quests" / "003-dpcc" / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    _write_json(control_report, {"generated_at": "2026-04-25T00:20:00+00:00"})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:30:00+00:00",
            "gaps": [{"summary": "claim_evidence_consistency_failed", "evidence_refs": [str(control_report)]}],
        },
    )
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_777_000_000)
    _touch(control_report, 1_777_000_100)
    _touch(study_root / "artifacts" / "publication_eval" / "latest.json", 1_777_000_100)

    profile_payload = module.profile_study_cycle(profile=profile, study_id="003-dpcc", study_root=None)

    assert profile_payload["package_currentness"]["status"] == "fresh"
    assert profile_payload["package_currentness"]["status_reason"] == "content_authority_not_newer_than_current_package"
    assert profile_payload["package_currentness"]["control_surface_latest_mtime"] == "2026-04-24T03:08:20+00:00"
    assert "stale_current_package" not in {
        item["bottleneck_id"] for item in profile_payload["bottlenecks"]
    }


def test_study_cycle_profiler_marks_package_stale_from_new_content_evidence_ref(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    paper_root = workspace_root / "ops" / "runtime" / "quests" / "003-dpcc" / ".ds" / "worktrees" / "paper-main" / "paper"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:30:00+00:00",
            "gaps": [{"summary": "stale_submission_minimal_authority", "evidence_refs": [str(paper_root)]}],
        },
    )
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_777_000_000)
    _touch(paper_root / "paper_line_state.json", 1_777_000_180)
    _touch(study_root / "artifacts" / "publication_eval" / "latest.json", 1_777_000_020)

    profile_payload = module.profile_study_cycle(profile=profile, study_id="003-dpcc", study_root=None)

    assert profile_payload["package_currentness"]["status"] == "stale"
    assert profile_payload["package_currentness"]["status_reason"] == "content_authority_newer_than_current_package"
    assert profile_payload["package_currentness"]["stale_seconds"] == 180
    assert profile_payload["package_currentness"]["authority_source"]["path"] == str(paper_root.resolve())
    assert "stale_current_package" in {
        item["bottleneck_id"] for item in profile_payload["bottlenecks"]
    }


def test_study_cycle_profiler_suppresses_repeated_decision_after_work_unit_dedupe(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    for minute in (10, 11):
        _write_json(
            study_root / "artifacts" / "controller_decisions" / f"20260425T00{minute}00Z.json",
            {
                "emitted_at": f"2026-04-25T00:{minute}:00+00:00",
                "decision_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "reason": "same blocker fingerprint",
            },
        )
    _write_json(
        study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json",
        {
            "recorded_at": "2026-04-25T00:12:00+00:00",
            "outcome": "skipped_matching_work_unit",
            "reason": "outer-loop work unit already dispatched for the same blocker fingerprint",
            "work_unit_dispatch_key": "publication-blockers::abc::analysis_claim_evidence_repair::run_gate_clearing_batch",
        },
    )

    profile_payload = module.profile_study_cycle(
        profile=profile,
        study_id="003-dpcc",
        study_root=None,
        since="2026-04-25T00:00:00+00:00",
    )

    assert profile_payload["controller_decision_fingerprints"]["top_repeats"][0]["count"] == 2
    assert profile_payload["domain_health_diagnostic_wakeup_dedupe_summary"]["status"] == "dedupe_confirmed"
    assert "repeated_controller_decision" not in {
        item["bottleneck_id"] for item in profile_payload["bottlenecks"]
    }
    assert "dedupe-controller-dispatch" not in {
        item["recommendation_id"] for item in profile_payload["optimization_recommendations"]
    }


def test_study_cycle_profiler_treats_concrete_work_unit_dispatch_as_not_controller_churn(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    for minute in (10, 11):
        _write_json(
            study_root / "artifacts" / "controller_decisions" / f"20260425T00{minute}00Z.json",
            {
                "emitted_at": f"2026-04-25T00:{minute}:00+00:00",
                "decision_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "reason": "same route but new blocker fingerprint",
            },
        )
    _write_json(
        study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json",
        {
            "recorded_at": "2026-04-25T00:10:54+00:00",
            "outcome": "dispatched",
            "reason": "outer-loop wakeup dispatched an autonomous controller decision",
            "work_unit_dispatch_key": "publication-blockers::new::analysis_claim_evidence_repair::run_gate_clearing_batch",
            "work_unit_fingerprint": "publication-blockers::new",
        },
    )

    profile_payload = module.profile_study_cycle(
        profile=profile,
        study_id="003-dpcc",
        study_root=None,
        since="2026-04-25T00:00:00+00:00",
    )

    assert profile_payload["domain_health_diagnostic_wakeup_dedupe_summary"]["status"] == "work_unit_dispatched"
    assert "repeated_controller_decision" not in {
        item["bottleneck_id"] for item in profile_payload["bottlenecks"]
    }
    assert "dedupe-controller-dispatch" not in {
        item["recommendation_id"] for item in profile_payload["optimization_recommendations"]
    }


def test_study_cycle_profiler_exposes_work_unit_lifecycle_replay_and_eval_lag(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    identity_module = importlib.import_module("med_autoscience.controllers.control_identity")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-003"
    study_root.mkdir(parents=True)
    quest_root.mkdir(parents=True)
    (study_root / "runtime_binding.yaml").write_text(
        "\n".join(
            [
                "study_id: 003-dpcc",
                "quest_id: quest-003",
                f"runtime_root: {workspace_root / 'ops' / 'med-deepscientist' / 'runtime' / 'quests'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:10:00+00:00",
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "generated_at": "2026-04-25T00:20:00+00:00",
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        },
    )
    identity = identity_module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=["claim_evidence_consistency_failed"],
        next_work_unit={"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        action_type="run_gate_clearing_batch",
    )
    for event_type, recorded_at in (
        ("planned", "2026-04-25T00:11:00+00:00"),
        ("dispatched", "2026-04-25T00:12:00+00:00"),
        ("accepted", "2026-04-25T00:13:00+00:00"),
        ("artifact_written", "2026-04-25T00:14:00+00:00"),
        ("gate_replayed", "2026-04-25T00:15:00+00:00"),
    ):
        ledger.append_event(
            study_root=study_root,
            identity=identity,
            event_type=event_type,
            payload={"writer_id": "run-1"},
            recorded_at=recorded_at,
        )

    profile_payload = module.profile_study_cycle(profile=profile, study_id="003-dpcc", study_root=None)

    lifecycle = profile_payload["work_unit_lifecycle_summary"]
    assert lifecycle["totals"]["unit_count"] == 1
    assert lifecycle["totals"]["replay_count"] == 1
    assert lifecycle["units"][0]["lifecycle_state"] == "gate_replayed"
    assert lifecycle["units"][0]["accepted_writer_id"] == "run-1"
    assert profile_payload["publication_eval_replay_lag"] == {
        "status": "stale_after_gate_replay",
        "lag_seconds": 300,
        "publication_eval_latest_at": "2026-04-25T00:10:00+00:00",
        "latest_gate_replayed_at": "2026-04-25T00:15:00+00:00",
        "publishability_gate_latest_at": "2026-04-25T00:20:00+00:00",
    }


def test_study_cycle_profiler_renders_markdown(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")

    rendered = module.render_study_cycle_profile_markdown(
        {
            "study_id": "001-risk",
            "study_root": str(tmp_path / "study"),
            "quest_id": "quest-001",
            "quest_root": str(tmp_path / "quest"),
            "profiling_window": {"since": None, "until": "2026-04-25T00:00:00+00:00", "event_count": 0},
            "category_windows": {},
            "opl_runtime_owner_handoff_summary": {"status_counts": {}},
            "controller_decision_fingerprints": {"top_repeats": []},
            "gate_blocker_summary": {"current_blockers": []},
            "package_currentness": {"status": "fresh"},
            "step_latest_times": {},
            "step_timings": [],
            "eta_confidence_band": {"classification": "delivery_only", "label": "delivery-only"},
            "bottlenecks": [],
            "optimization_recommendations": [],
        }
    )

    assert "# Study Cycle Profile: 001-risk" in rendered
    assert "Package currentness: fresh" in rendered


def test_workspace_cycle_profiler_profiles_active_studies_and_sorts_bottlenecks(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)

    active_root = workspace_root / "studies" / "001-risk"
    quieter_root = workspace_root / "studies" / "002-followup"
    inactive_root = workspace_root / "studies" / "draft-no-study-yaml"
    for study_root in (active_root, quieter_root, inactive_root):
        study_root.mkdir(parents=True)
    (active_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    (quieter_root / "study.yaml").write_text("study_id: 002-followup\n", encoding="utf-8")

    for index in range(2):
        _write_opl_handoff(
            active_root
            / "artifacts"
            / "supervision"
            / "opl_runtime_owner_handoff"
            / f"20260425T000{index}00Z.json",
            recorded_at=f"2026-04-25T00:0{index}:00+00:00",
            status="handoff_required",
        )
    for index in range(3):
        _write_json(
            active_root / "artifacts" / "controller_decisions" / f"20260425T001{index}00Z.json",
            {
                "emitted_at": f"2026-04-25T00:1{index}:00+00:00",
                "decision_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "reason": "same dispatch",
            },
        )
    _write_json(
        active_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:20:00+00:00",
            "blockers": ["claim_evidence_consistency_failed"],
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "claim_id": "claim-001",
                    "source_path": str(active_root / "paper" / "manuscript.md"),
                }
            ],
        },
    )
    _touch(active_root / "artifacts" / "publication_eval" / "latest.json", 1_777_000_000)
    _touch(active_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(active_root / "manuscript" / "current_package" / "manuscript.docx", 1_776_999_900)

    _write_opl_handoff(
        quieter_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "20260425T000000Z.json",
        recorded_at="2026-04-25T00:00:00+00:00",
    )
    _touch(quieter_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(quieter_root / "manuscript" / "current_package" / "manuscript.docx", 1_777_000_000)

    payload = module.profile_workspace_cycles(
        profile=profile,
        since="2026-04-25T00:00:00+00:00",
    )

    assert payload["workspace_root"] == str(workspace_root.resolve())
    assert payload["study_count"] == 2
    assert [item["study_id"] for item in payload["studies"]] == ["001-risk", "002-followup"]
    active_summary = payload["studies"][0]["cycle_summary"]
    assert active_summary["repeated_controller_dispatch_count"] == 2
    assert active_summary["opl_runtime_owner_handoff_required_count"] == 2
    assert active_summary["package_stale_seconds"] == 100
    assert payload["workspace_totals"] == {
        "repeated_controller_dispatch_count": 2,
        "opl_runtime_owner_handoff_required_count": 2,
        "package_stale_seconds": 100,
        "non_actionable_gate_count": 0,
    }


def test_workspace_cycle_profiler_renders_markdown() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")

    rendered = module.render_workspace_cycle_profile_markdown(
        {
            "profile_name": "nfpitnet",
            "workspace_root": "/tmp/workspace",
            "study_count": 1,
            "workspace_totals": {
                "repeated_controller_dispatch_count": 2,
                "opl_runtime_owner_handoff_required_count": 1,
                "package_stale_seconds": 100,
                "non_actionable_gate_count": 0,
            },
            "studies": [
                {
                    "study_id": "001-risk",
                    "bottleneck_score": 10,
                    "cycle_summary": {
                        "repeated_controller_dispatch_count": 2,
                        "opl_runtime_owner_handoff_required_count": 1,
                        "package_stale_seconds": 100,
                        "non_actionable_gate_count": 0,
                    },
                    "eta_confidence_band": {"classification": "opl_handoff_required", "label": "OPL handoff required"},
                    "bottlenecks": [{"bottleneck_id": "opl_runtime_owner_handoff_required"}],
                }
            ],
            "optimization_action_units": [
                {
                    "action_unit_id": "optimization-action::001-risk::opl_runtime_owner_handoff_required",
                    "study_id": "001-risk",
                    "action_type": "request_opl_handoff_hydration",
                    "controller_surface": "domain_health_diagnostic",
                    "priority": "now",
                }
            ],
            "workspace_scheduler": {
                "ready_count": 1,
                "ready_action_unit_ids": ["optimization-action::001-risk::opl_runtime_owner_handoff_required"],
            },
        }
    )

    assert "# Workspace Cycle Profile: nfpitnet" in rendered
    assert "001-risk" in rendered
    assert "repeated dispatch: 2" in rendered
    assert "Optimization Action Queue" in rendered
    assert "request_opl_handoff_hydration" in rendered


def test_workspace_cycle_profiler_emits_action_units_and_scheduler_queue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    _write_opl_handoff(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "20260425T000000Z.json",
        recorded_at="2026-04-25T00:00:00+00:00",
        status="handoff_required",
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "20260425T001000Z.json",
        {
            "emitted_at": "2026-04-25T00:10:00+00:00",
            "decision_type": "bounded_analysis",
            "route_target": "analysis-campaign",
            "reason": "same dispatch",
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "20260425T001100Z.json",
        {
            "emitted_at": "2026-04-25T00:11:00+00:00",
            "decision_type": "bounded_analysis",
            "route_target": "analysis-campaign",
            "reason": "same dispatch",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"emitted_at": "2026-04-25T00:20:00+00:00", "blockers": ["stale_submission_minimal_authority"]},
    )
    _touch(study_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_776_999_900)

    payload = module.profile_workspace_cycles(profile=profile, since="2026-04-25T00:00:00+00:00")

    action_units = payload["optimization_action_units"]
    assert [item["action_type"] for item in action_units] == [
        "request_opl_handoff_hydration",
        "dedupe_controller_dispatch",
        "run_publication_work_unit",
        "refresh_current_package_after_settle",
    ]
    assert all(item["study_id"] == "001-risk" for item in action_units)
    assert action_units[0]["controller_surface"] == "domain_health_diagnostic"
    assert action_units[2]["controller_surface"] == "gate_clearing_batch"
    assert payload["workspace_scheduler"]["ready_action_unit_ids"] == [
        item["action_unit_id"] for item in action_units
    ]
    assert payload["workspace_scheduler"]["ready_count"] == 4


def test_study_cycle_profiler_marks_non_actionable_gate_and_eta_band(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 003-dpcc\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:20:00+00:00",
            "status": "blocked",
            "blockers": ["publication_gate_blocked", "submission_hardening_needed"],
        },
    )

    payload = module.profile_study_cycle(profile=profile, study_id="003-dpcc", study_root=None)

    assert payload["gate_blocker_summary"]["actionability_status"] == "blocked_by_non_actionable_gate"
    assert [item["bottleneck_id"] for item in payload["bottlenecks"]] == [
        "non_actionable_gate",
        "publication_gate_blocked",
    ]
    assert payload["eta_confidence_band"] == {
        "classification": "non_actionable_gate",
        "label": "non-actionable gate",
        "confidence": "blocked",
        "min_seconds": None,
        "max_seconds": None,
        "reason": "Gate blockers are label-only and must be narrowed to concrete claim, display, evidence, citation, metric, or package-artifact targets before automated execution.",
    }


def test_eta_classifies_submission_minimal_authority_as_delivery_not_human_admin() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler_eta")

    band = module.eta_confidence_band(
        opl_runtime_owner_handoff_summary={"status_counts": {}},
        gate_blocker_summary={
            "current_blockers": [
                "stale_submission_minimal_authority",
                "submission_surface_qc_failure_present",
            ],
            "actionability_status": "actionable",
        },
        package_currentness={"status": "stale"},
    )

    assert band["classification"] == "delivery_only"


def test_eta_blocks_on_opl_handoff_required() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler_eta")

    band = module.eta_confidence_band(
        opl_runtime_owner_handoff_summary={"status_counts": {"handoff_required": 1}},
        gate_blocker_summary={
            "current_blockers": ["claim_evidence_consistency_failed"],
            "actionability_status": "actionable",
        },
        package_currentness={"status": "fresh"},
    )

    assert band["classification"] == "opl_handoff_required"


def test_eta_uses_claim_evidence_when_latest_runtime_is_live_despite_window_churn() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler_eta")

    band = module.eta_confidence_band(
        opl_runtime_owner_handoff_summary={"status_counts": {"owner_receipt_written": 3}},
        gate_blocker_summary={
            "current_blockers": ["claim_evidence_consistency_failed"],
            "actionability_status": "actionable",
        },
        package_currentness={"status": "fresh"},
    )

    assert band["classification"] == "claim_evidence"
