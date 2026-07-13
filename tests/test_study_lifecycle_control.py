from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.profile_test_helpers import write_profile
from tests.study_runtime_test_helpers import write_study


def _profile(tmp_path: Path):
    profiles = importlib.import_module("med_autoscience.profiles")
    profile_ref = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_ref, workspace_root=workspace_root)
    return profiles.load_profile(profile_ref), profile_ref


def test_set_study_lifecycle_materializes_domain_truth_and_workspace_projection(
    tmp_path: Path,
) -> None:
    lifecycle = importlib.import_module(
        "med_autoscience.controllers.study_lifecycle_control"
    )
    profile, profile_ref = _profile(tmp_path)
    study_id = "002-early-residual-risk"
    study_root = write_study(profile.workspace_root, study_id)

    result = lifecycle.set_study_lifecycle(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        lifecycle_state="delivered_paused",
        reason_code="milestone_package_delivered_pending_submission_metadata",
        reason_summary="Milestone package delivered; submission metadata remains external.",
        source_kind="explicit_user_truth",
        source_ref="user_instruction:2026-07-13:mas-nine-paper-lifecycle-truth",
        evidence_refs=("submission/current_package.zip",),
        recorded_at="2026-07-13T12:00:00Z",
    )

    current = json.loads(
        (study_root / "control" / "lifecycle.json").read_text(encoding="utf-8")
    )
    workspace_ledger = json.loads(
        (
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "study_lifecycle_control"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    workspace_index = json.loads(
        (profile.workspace_root / "workspace_index.json").read_text(encoding="utf-8")
    )
    item = workspace_index["studies"][0]

    assert result["status"] == "recorded"
    assert current["schema_version"] == "mas.study_lifecycle_control.v1"
    assert current["lifecycle_state"] == "delivered_paused"
    assert current["generation"] == 1
    assert current["current_stage_id"] is None
    assert current["milestone_package_delivered"] is True
    assert current["submission_ready"] is False
    assert current["package_status"] == "milestone_delivered"
    assert current["resume_policy"]["auto_resume_allowed"] is False
    assert len(list((study_root / "artifacts/controller/lifecycle_control/history").glob("*.json"))) == 1
    assert workspace_ledger["study_count"] == 1
    assert workspace_ledger["recorded_study_count"] == 1
    assert workspace_ledger["unrecorded_study_ids"] == []
    assert item["status"] == "delivered_paused"
    assert item["business_status"] == "delivered_paused"
    assert item["current_stage_id"] is None
    assert item["current_stage_status"] is None
    assert item["package_status"] == "milestone_delivered"
    assert item["lifecycle_ref"] == "control/lifecycle.json"
    assert item["blockers"] == []
    assert item["diagnostic_blockers"]


def test_lifecycle_progress_readback_suppresses_stale_runtime_route(tmp_path: Path) -> None:
    lifecycle = importlib.import_module(
        "med_autoscience.controllers.study_lifecycle_control"
    )
    profile, profile_ref = _profile(tmp_path)
    study_id = "004-invasive-architecture"
    study_root = write_study(profile.workspace_root, study_id)
    lifecycle.set_study_lifecycle(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        lifecycle_state="stopped",
        reason_code="publishability_stop_loss",
        reason_summary="The study was stopped because it is not viable as an SCI paper.",
        source_kind="explicit_user_truth",
        source_ref="user_instruction:2026-07-13:mas-nine-paper-lifecycle-truth",
        recorded_at="2026-07-13T12:01:00Z",
    )

    projected = lifecycle.apply_lifecycle_to_progress_readback(
        payload={
            "study_id": study_id,
            "current_stage": "runtime_preflight",
            "active_run_id": "run-stale",
            "current_blockers": ["provider_missing"],
            "next_action": {"action_id": "request_opl_stage_attempt"},
            "current_package": {"status": "ready", "can_submit": True},
        },
        study_root=study_root,
    )

    assert projected["business_status"] == "stopped"
    assert projected["current_stage"] is None
    assert projected["active_run_id"] is None
    assert projected["current_blockers"] == []
    assert projected["runtime_liveness_status"] == "not_running_by_lifecycle"
    assert projected["next_action"]["action_id"] == (
        "remain_stopped_until_explicit_relaunch"
    )
    assert projected["current_package"]["can_submit"] is False
    assert projected["ai_route_context"]["can_submit_to_opl_runtime"] is False


def test_stopped_launch_requires_wakeup_and_relaunch_authorization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    lifecycle = importlib.import_module(
        "med_autoscience.controllers.study_lifecycle_control"
    )
    launch = importlib.import_module(
        "med_autoscience.controllers.study_launch_projection"
    )
    profile, profile_ref = _profile(tmp_path)
    study_id = "001-lineage-pfs"
    write_study(profile.workspace_root, study_id)
    lifecycle.set_study_lifecycle(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        lifecycle_state="stopped",
        reason_code="publishability_stop_loss",
        reason_summary="The study was stopped because it is not viable as an SCI paper.",
        source_kind="explicit_user_truth",
        source_ref="user_instruction:2026-07-13:mas-nine-paper-lifecycle-truth",
        recorded_at="2026-07-13T12:02:00Z",
    )
    monkeypatch.setattr(
        launch.domain_status_projection,
        "progress_projection",
        lambda **kwargs: pytest.fail("runtime projection must not run before lifecycle admission"),
    )

    result = launch.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        explicit_user_wakeup=True,
        allow_stopped_relaunch=False,
    )

    assert result["runtime_handoff"]["status"] == "lifecycle_reactivation_required"
    assert result["runtime_handoff"]["can_submit_to_opl_runtime"] is False
    assert result["runtime_handoff"]["required_reactivation"] == (
        "explicit_user_wakeup_and_allow_stopped_relaunch"
    )
    assert result["progress"]["current_stage"] is None


def test_explicit_wakeup_reactivates_paused_lifecycle_before_runtime_admission(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    lifecycle = importlib.import_module(
        "med_autoscience.controllers.study_lifecycle_control"
    )
    launch = importlib.import_module(
        "med_autoscience.controllers.study_launch_projection"
    )
    profile, profile_ref = _profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id)
    lifecycle.set_study_lifecycle(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        lifecycle_state="paused",
        reason_code="user_paused_pending_direction",
        reason_summary="The user paused this study pending a later decision.",
        source_kind="explicit_user_truth",
        source_ref="user_instruction:2026-07-13:mas-nine-paper-lifecycle-truth",
        recorded_at="2026-07-13T12:02:30Z",
    )
    projection_calls: list[str] = []

    def progress_projection(**kwargs):
        observed = lifecycle.read_study_lifecycle(
            study_root=study_root,
            study_id=study_id,
        )
        projection_calls.append(str(observed["lifecycle_state"]))
        return {
            "study_id": study_id,
            "decision": "ready",
            "reason": "pytest_runtime_projection",
        }

    monkeypatch.setattr(
        launch.domain_status_projection,
        "progress_projection",
        progress_projection,
    )
    monkeypatch.setattr(
        launch,
        "build_study_progress_projection",
        lambda **kwargs: {"study_id": study_id, "status": "projected"},
    )

    result = launch.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        explicit_user_wakeup=True,
    )
    current = lifecycle.read_study_lifecycle(
        study_root=study_root,
        study_id=study_id,
    )

    assert projection_calls == ["paused", "active"]
    assert current["lifecycle_state"] == "active"
    assert current["generation"] == 2
    assert current["reason_code"] == "explicit_user_wakeup"
    assert current["resume_policy"]["auto_resume_allowed"] is True
    assert result["runtime_handoff"]["status"] == "opl_attempt_admission_required"
    assert result["runtime_handoff"]["lifecycle_transition"]["status"] == "recorded"
    assert result["runtime_handoff"]["lifecycle_transition"]["lifecycle_state"] == "active"


def test_paper_mission_inspect_uses_lifecycle_truth_before_old_runtime(
    tmp_path: Path,
) -> None:
    lifecycle = importlib.import_module(
        "med_autoscience.controllers.study_lifecycle_control"
    )
    paper_mission = importlib.import_module("med_autoscience.paper_mission_domain")
    profile, profile_ref = _profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    write_study(profile.workspace_root, study_id)
    lifecycle.set_study_lifecycle(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        lifecycle_state="delivered_paused",
        reason_code="milestone_package_delivered_pending_submission_metadata",
        reason_summary="Milestone package delivered; submission metadata remains external.",
        source_kind="explicit_user_truth",
        source_ref="user_instruction:2026-07-13:mas-nine-paper-lifecycle-truth",
        recorded_at="2026-07-13T12:03:00Z",
    )

    result = paper_mission.build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        source="pytest",
    )

    assert result["surface_kind"] == "paper_mission_lifecycle_readback"
    assert result["mission_state"] == "delivered_paused"
    assert result["current_stage"] is None
    assert result["current_package"]["status"] == "milestone_delivered"
    assert result["can_submit_to_opl_runtime"] is False
    assert result["durable_mission_stop_guard"]["stop"] is True


def test_study_state_matrix_projects_lifecycle_as_business_truth(tmp_path: Path) -> None:
    lifecycle = importlib.import_module(
        "med_autoscience.controllers.study_lifecycle_control"
    )
    matrix = importlib.import_module("med_autoscience.controllers.study_state_matrix")
    profile, profile_ref = _profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    write_study(profile.workspace_root, study_id)
    lifecycle.set_study_lifecycle(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        lifecycle_state="paused",
        reason_code="quest_user_paused_requires_explicit_wakeup",
        reason_summary="The owner readback records an explicit user pause.",
        source_kind="owner_readback",
        source_ref="artifacts/supervision/opl_runtime_owner_handoff/latest.json",
        recorded_at="2026-06-06T06:59:24Z",
    )

    class StatusProjection:
        @staticmethod
        def progress_projection(**kwargs):
            return {
                "current_stage": "runtime_preflight",
                "quest_status": "running",
                "active_run_id": "run-stale",
            }

    result = matrix.build_study_state_matrix(
        profile=profile,
        domain_status_projection=StatusProjection,
    )
    item = result["studies"][0]

    assert item["business_status"] == "paused"
    assert item["lifecycle_state"] == "paused"
    assert item["current_stage"] is None
    assert item["quest_status"] is None
    assert item["active_run_id"] is None
    assert item["lifecycle_ref"].endswith("control/lifecycle.json")


def test_set_study_lifecycle_rejects_unknown_state(tmp_path: Path) -> None:
    lifecycle = importlib.import_module(
        "med_autoscience.controllers.study_lifecycle_control"
    )
    profile, profile_ref = _profile(tmp_path)
    study_id = "study-001"
    write_study(profile.workspace_root, study_id)

    with pytest.raises(ValueError, match="unsupported lifecycle_state"):
        lifecycle.set_study_lifecycle(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            lifecycle_state="blocked",
            reason_code="invalid",
            reason_summary="Invalid state.",
            source_kind="pytest",
            source_ref="pytest",
        )
