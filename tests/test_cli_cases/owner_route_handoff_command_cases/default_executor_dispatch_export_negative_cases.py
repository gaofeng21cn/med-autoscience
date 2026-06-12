from __future__ import annotations

from .shared import *  # noqa: F403,F401
from .default_executor_dispatch_export_cases import _write_default_executor_dispatch


def test_export_current_owner_action_suppresses_stale_projection_under_execution_state_kind_blocker() -> None:
    export = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.domain_handler_export"
    )

    stale_projection_action = {
        "source": "stale_projection_action",
        "status": "ready",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "medical-prose-routeback::write::fp",
        "allowed_actions": ["run_quality_repair_batch"],
    }

    assert (
        export._export_current_owner_action(
            study={"current_owner_action": stale_projection_action},
            current_progress={
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": None,
                },
                "current_execution_envelope": {
                    "execution_state_kind": "typed_blocker",
                    "owner": "MedAutoScience",
                    "typed_blocker": {
                        "blocker_type": "medical_paper_readiness_missing",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                    },
                },
                "current_executable_owner_action": None,
            },
        )
        == {}
    )


def test_domain_handler_export_skips_bare_default_executor_dispatch_without_owner_currentness(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=False,
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == []


def test_domain_handler_export_keeps_current_dispatch_with_unregistered_diagnostic_owner_reason(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
        owner_reason="unregistered_local_reason",
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert len(tasks) == 1
    envelope = tasks[0]["owner_route_attempt_envelope"]
    assert envelope["dispatchable"] is True
    assert envelope["owner_reason_contract"]["registered"] is False
    assert envelope["action_type"] == "run_quality_repair_batch"
    assert envelope["owner_route_currentness_basis"]["work_unit_id"] == "medical_prose_write_repair"


def test_domain_handler_export_suppresses_persisted_dispatch_under_canonical_typed_blocker(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
    )

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "medical_paper_readiness_missing",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "source_ref": (
                            "studies/002-dm-china-us-mortality-attribution/"
                            "artifacts/stage_outputs/08-publication_package_handoff/"
                            "receipts/typed_blocker.json"
                        ),
                    },
                    "stale_queue_or_handoff_can_override": False,
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
                "next_work_unit": None,
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == []


def test_domain_handler_export_suppresses_stale_projection_action_under_execution_state_kind_blocker(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
    )
    _write_json(
        workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-12T00:00:00Z",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_owner_action": {
                        "source": "stale_projection_action",
                        "status": "ready",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "medical-prose-routeback::write::fp",
                        "allowed_actions": ["run_quality_repair_batch"],
                    },
                }
            ],
            "action_queue": [],
        },
    )

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": None,
                "study_id": study_id,
                "quest_id": study_id,
            },
            "current_execution_envelope": {
                "execution_state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
                "next_work_unit": None,
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["studies"][0].get("current_owner_action") in ({}, None)
    assert [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == []


def test_domain_handler_export_keeps_dispatch_matching_canonical_current_work_unit(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
    )

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "medical-prose-routeback::write::fp",
                "action_fingerprint": "medical-prose-routeback::write::fp",
                "currentness_basis": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "medical-prose-routeback::write::fp",
                    "truth_epoch": "publication-eval::002::current",
                    "runtime_health_epoch": "runtime-health-event-002",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "canonical_current_work_unit",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "medical-prose-routeback::write::fp",
                "allowed_actions": ["run_quality_repair_batch"],
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert len(tasks) == 1
    assert tasks[0]["payload"]["action_type"] == "run_quality_repair_batch"
    assert tasks[0]["payload"]["work_unit_id"] == "medical_prose_write_repair"
