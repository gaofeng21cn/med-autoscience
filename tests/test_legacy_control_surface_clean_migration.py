from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_profile(path: Path, workspace_root: Path) -> None:
    _write_text(
        path,
        "\n".join(
            [
                'name = "dm-cvd"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "runtime" / "quests"}"',
                f'managed_runtime_home = "{workspace_root / "runtime"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "",
            ]
        ),
    )


def _write_completed_study_yaml(path: Path, study_id: str) -> None:
    _write_text(
        path,
        "\n".join(
            [
                f"study_id: {study_id}",
                "status: completed",
                "study_completion:",
                "  status: completed",
                "  completed_at: '2026-04-02'",
                "  summary: Study delivery is complete.",
                "  evidence_paths:",
                "    - manuscript/paper.pdf",
                "execution:",
                "  auto_resume: false",
                "",
            ]
        ),
    )


def _dispatch(*, study_id: str, action_type: str, allowed_actions: list[str], blocked_actions: list[str]) -> dict[str, object]:
    dispatch_path = (
        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
        f"default_executor_dispatches/{action_type}.json"
    )
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "dispatch_status": "ready",
        "executor_kind": "default_executor",
        "next_executable_owner": "write",
        "refs": {"dispatch_path": dispatch_path},
        "owner_route": {
            "study_id": study_id,
            "next_owner": "write",
            "owner_reason": "fixture",
            "allowed_actions": allowed_actions,
            "blocked_actions": blocked_actions,
            "source_refs": {"work_unit_id": "current-work-unit"},
        },
        "prompt_contract": {
            "owner_route": {
                "study_id": study_id,
                "next_owner": "write",
                "allowed_actions": allowed_actions,
                "blocked_actions": blocked_actions,
                "source_refs": {"work_unit_id": "current-work-unit"},
            }
        },
    }


def _build_fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    quest_root = workspace_root / "runtime" / "quests" / study_id
    dispatch_root = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    manual_pause_root = quest_root / "artifacts" / "runtime" / "manual_pause"
    _write_profile(profile_path, workspace_root)
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\nstudy_id: {study_id}\n")
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "controller_work_unit_id": "manuscript_story_repair",
                    "handoff_packet": {
                        "owner_route": {
                            "study_id": study_id,
                            "next_owner": "write",
                            "owner_reason": "manuscript_story_surface_delta_missing",
                            "allowed_actions": ["run_quality_repair_batch"],
                            "blocked_actions": [
                                "publication_handoff_owner_gate",
                                "return_to_ai_reviewer_workflow",
                            ],
                            "source_refs": {"work_unit_id": "manuscript_story_repair"},
                        }
                    },
                }
            ],
        },
    )
    _write_json(
        dispatch_root / "run_quality_repair_batch.json",
        _dispatch(
            study_id=study_id,
            action_type="run_quality_repair_batch",
            allowed_actions=["run_quality_repair_batch"],
            blocked_actions=["publication_handoff_owner_gate"],
        ),
    )
    _write_json(
        dispatch_root / "publication_handoff_owner_gate.json",
        _dispatch(
            study_id=study_id,
            action_type="publication_handoff_owner_gate",
            allowed_actions=["publication_handoff_owner_gate"],
            blocked_actions=[],
        ),
    )
    _write_json(
        dispatch_root / "return_to_ai_reviewer_workflow.json",
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            allowed_actions=["return_to_ai_reviewer_workflow"],
            blocked_actions=[],
        ),
    )
    _write_json(
        dispatch_root / "immutable" / "run_quality_repair_batch" / "current.json",
        _dispatch(
            study_id=study_id,
            action_type="run_quality_repair_batch",
            allowed_actions=["run_quality_repair_batch"],
            blocked_actions=[],
        ),
    )
    _write_json(
        dispatch_root / "immutable" / "publication_handoff_owner_gate" / "old.json",
        _dispatch(
            study_id=study_id,
            action_type="publication_handoff_owner_gate",
            allowed_actions=["publication_handoff_owner_gate"],
            blocked_actions=[],
        ),
    )
    _write_json(
        manual_pause_root / "20260603T131732Z.json",
        {
            "surface_kind": "mas_quest_manual_pause_receipt",
            "study_id": study_id,
            "manual_pause": {"reason": "manual_pause_for_mas_rebuild"},
        },
    )
    _write_json(
        manual_pause_root / "latest.json",
        {
            "surface_kind": "mas_quest_manual_pause_receipt",
            "study_id": study_id,
            "manual_pause": {
                "reason": "manual_pause_for_mas_rebuild",
                "resume_requires_explicit_wakeup": True,
            },
            "previous_runtime_state": {
                "status": "active",
                "display_status": "running",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "active_run_id": None,
                "worker_running": False,
            },
        },
    )
    _write_json(
        quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json",
        {
            "quest_id": study_id,
            "status": "paused",
            "display_status": "paused",
            "pause_reason": "manual_pause_for_mas_rebuild",
            "turn_reason": "manual_pause_for_mas_rebuild",
            "continuation_reason": "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "last_manual_pause": {
                "reason": "manual_pause_for_mas_rebuild",
                "recorded_at": "2026-06-03T13:17:32Z",
            },
            "active_run_id": None,
            "worker_running": False,
        },
    )
    return profile_path, workspace_root


def test_legacy_control_surface_clean_migration_dry_run_reports_residue_without_writing(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.legacy_control_surface_clean_migration")
    profile_path, workspace_root = _build_fixture(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"

    report = migration.run_legacy_control_surface_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    study = report["studies"][0]
    assert report["surface_kind"] == "legacy_control_surface_clean_migration"
    assert report["mode"] == "dry_run"
    assert study["apply_allowed"] is True
    assert [item["action_type"] for item in study["retained_dispatch_files"]] == ["run_quality_repair_batch"]
    assert {item["action_type"] for item in study["dispatch_files"]} == {
        "publication_handoff_owner_gate",
        "return_to_ai_reviewer_workflow",
    }
    assert study["manual_pause"]["migration_required"] is True
    assert study["manual_pause"]["runtime_state_migration_required"] is True
    assert not (workspace_root / "artifacts" / "runtime" / "legacy_control_surface_clean_migration").exists()


def test_legacy_control_surface_clean_migration_apply_tombstones_old_active_material(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.legacy_control_surface_clean_migration")
    profile_path, workspace_root = _build_fixture(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    quest_root = workspace_root / "runtime" / "quests" / study_id
    dispatch_root = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"

    report = migration.run_legacy_control_surface_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    current_dispatch = json.loads((dispatch_root / "run_quality_repair_batch.json").read_text(encoding="utf-8"))
    migrated_dispatch = json.loads(
        (dispatch_root / "publication_handoff_owner_gate.json").read_text(encoding="utf-8")
    )
    manual_pause = json.loads(
        (quest_root / "artifacts" / "runtime" / "manual_pause" / "latest.json").read_text(encoding="utf-8")
    )
    runtime_state = json.loads(
        (quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json").read_text(encoding="utf-8")
    )
    latest_receipt = json.loads(
        (workspace_root / "artifacts" / "runtime" / "legacy_control_surface_clean_migration" / "latest.json").read_text(
            encoding="utf-8"
        )
    )

    assert current_dispatch["surface"] == "default_executor_dispatch_request"
    assert migrated_dispatch["surface_kind"] == "legacy_control_surface_tombstone"
    assert manual_pause["surface_kind"] == "legacy_control_surface_tombstone"
    assert not (dispatch_root / "immutable" / "publication_handoff_owner_gate").exists()
    assert (dispatch_root / "immutable" / "run_quality_repair_batch" / "current.json").exists()
    assert runtime_state["status"] == "active"
    assert runtime_state["display_status"] == "running"
    assert runtime_state["continuation_reason"] == "blocked_turn_closeout_waiting_for_owner"
    assert "pause_reason" not in runtime_state
    assert "last_manual_pause" not in runtime_state
    assert report["post_apply"]["dispatch_file_tombstone_count"] == 2
    assert report["post_apply"]["immutable_action_directory_migration_count"] == 1
    assert report["post_apply"]["manual_pause_tombstone_count"] == 1
    assert report["post_apply"]["runtime_state_pause_migration_count"] == 1
    assert latest_receipt["authority_boundary"]["publication_eval_written"] is False
    assert latest_receipt["authority_boundary"]["runtime_queue_mutation"] is False


def test_legacy_control_surface_clean_migration_tombstones_completed_study_stale_dispatch_without_current_route(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.legacy_control_surface_clean_migration")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-early-residual-risk"
    study_root = workspace_root / "studies" / study_id
    dispatch_root = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    _write_profile(profile_path, workspace_root)
    _write_completed_study_yaml(study_root / "study.yaml", study_id)
    _write_text(study_root / "manuscript" / "paper.pdf", "fixture\n")
    _write_text(study_root / "manuscript" / "submission_package.zip", "zip\n")
    _write_text(workspace_root / "runtime" / "quests" / study_id / "quest.yaml", f"quest_id: {study_id}\n")
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {"surface_kind": "opl_current_control_state", "action_queue": []},
    )
    _write_json(
        dispatch_root / "return_to_ai_reviewer_workflow.json",
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            allowed_actions=["return_to_ai_reviewer_workflow"],
            blocked_actions=[],
        ),
    )

    dry_run = migration.run_legacy_control_surface_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    study = dry_run["studies"][0]
    assert study["apply_allowed"] is True
    assert study["blockers"] == []
    assert study["current_route"]["owner_reason"] == "study_completion_contract_completed"
    assert study["study_completion_contract"]["status"] == "completed"
    assert study["study_completion_contract"]["auto_resume"] is False
    assert [item["action_type"] for item in study["dispatch_files"]] == ["return_to_ai_reviewer_workflow"]

    applied = migration.run_legacy_control_surface_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    migrated_dispatch = json.loads(
        (dispatch_root / "return_to_ai_reviewer_workflow.json").read_text(encoding="utf-8")
    )
    assert migrated_dispatch["surface_kind"] == "legacy_control_surface_tombstone"
    assert migrated_dispatch["current_route"]["owner_reason"] == "study_completion_contract_completed"
    assert applied["post_apply"]["dispatch_file_tombstone_count"] == 1
