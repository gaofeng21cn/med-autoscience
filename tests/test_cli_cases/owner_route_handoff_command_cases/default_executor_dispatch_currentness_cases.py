from __future__ import annotations

import os

from .shared import *  # noqa: F403,F401


def _owner_route(
    *,
    study_id: str,
    next_owner: str,
    owner_reason: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    runtime_health_epoch: str,
    blocked_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "allowed_actions": [action_type],
        "blocked_actions": blocked_actions,
        "source_refs": {
            "runtime_health_epoch": runtime_health_epoch,
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "work_unit_id": work_unit_id,
            "blocked_reason": owner_reason,
        },
        "idempotency_key": f"owner-route::{study_id}::{work_unit_fingerprint}",
    }


def _write_dispatch(
    *,
    workspace_root: Path,
    study_id: str,
    filename: str,
    action_type: str,
    next_owner: str,
    dispatch_authority: str,
    owner_route: dict[str, object],
    generated_at: str | None = None,
    allowed_write_surfaces: list[str] | None = None,
) -> None:
    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / filename
    )
    payload = {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "dispatch_status": "ready",
            "dispatch_authority": dispatch_authority,
            "next_executable_owner": next_owner,
            "executor_kind": "codex_cli_default",
            "consumer_mutation_scope": "executor_dispatch_request_only",
            "owner_route": owner_route,
            "prompt_contract": {
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": action_type,
                "next_executable_owner": next_owner,
                "owner_route": owner_route,
                "allowed_write_surfaces": allowed_write_surfaces or ["paper/draft.md"],
                "forbidden_surfaces": [
                    "paper/current_package/**",
                    "manuscript/current_package/**",
                    "artifacts/publication_eval/latest.json",
                    "artifacts/controller_decisions/latest.json",
                ],
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "medical_claim_authoring_allowed": False,
            },
            "refs": {
                "dispatch_path": str(dispatch_path),
                "source_eval_path": str(
                    workspace_root
                    / "studies"
                    / study_id
                    / "artifacts"
                    / "publication_eval"
                    / "latest.json"
                ),
            },
        }
    if generated_at is not None:
        payload["generated_at"] = generated_at
    _write_json(dispatch_path, payload)


def test_domain_handler_export_suppresses_stale_dispatch_blocked_by_current_owner_route(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_record_stale_after_current_manuscript",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id="repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
            work_unit_fingerprint="truth-snapshot::old-ai-reviewer",
            runtime_health_epoch="runtime-health-event-006306-2365a556e7176a6b",
            blocked_actions=["run_quality_repair_batch"],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
            work_unit_fingerprint="domain-transition::current-write",
            runtime_health_epoch="runtime-health-event-006315-6046777ae24dd127",
            blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
        ),
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["owner_route_currentness_basis"]["runtime_health_epoch"] == (
        "runtime-health-event-006315-6046777ae24dd127"
    )


def test_domain_handler_export_suppresses_stale_dispatch_blocked_by_current_route_when_work_unit_changed(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="consumer_default_executor_dispatch",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_record_stale_after_current_manuscript",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            work_unit_fingerprint="truth-snapshot::old-ai-reviewer-record",
            runtime_health_epoch="runtime-health-event-006325-ff1404193e350d0c",
            blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T06:07:53+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
            work_unit_fingerprint=(
                "domain-transition::route_back_same_line::"
                "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
            ),
            runtime_health_epoch="runtime-health-event-006327-307bbee727d9e286",
            blocked_actions=[
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
            ],
        ),
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == (
        "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
    )


def test_domain_handler_export_uses_mtime_for_legacy_dispatch_without_generated_at(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    dispatch_dir = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    ai_reviewer_dispatch = dispatch_dir / "return_to_ai_reviewer_workflow.json"
    write_dispatch = dispatch_dir / "run_quality_repair_batch.json"

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=ai_reviewer_dispatch.name,
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-05-31T15:54:37+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_record_stale_after_current_manuscript",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            work_unit_fingerprint="dm003::ai-reviewer::older",
            runtime_health_epoch="runtime-health-event-006227-ai",
            blocked_actions=["run_quality_repair_batch"],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=write_dispatch.name,
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="consumer_default_executor_dispatch",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="quest_waiting_opl_runtime_owner_route",
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_currentness_recheck",
            work_unit_fingerprint="dm003::write::current",
            runtime_health_epoch="runtime-health-event-006237-write",
            blocked_actions=[
                "publication_gate_specificity_required",
                "current_package_freshness_required",
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
            ],
        ),
    )
    write_payload = json.loads(write_dispatch.read_text(encoding="utf-8"))
    write_payload.pop("generated_at", None)
    _write_json(write_dispatch, write_payload)
    os.utime(ai_reviewer_dispatch, (1_780_000_000, 1_780_000_000))
    os.utime(write_dispatch, (1_780_000_600, 1_780_000_600))

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == "medical_prose_currentness_recheck"
    assert tasks[0]["payload"]["next_executable_owner"] == "write"


def test_domain_handler_export_keeps_new_ai_reviewer_handoff_when_older_write_route_has_later_runtime_epoch(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T00:24:22+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id=work_unit_id,
            work_unit_fingerprint="domain-transition::current-write",
            runtime_health_epoch="runtime-health-event-006315-6046777ae24dd127",
            blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-05-28T01:01:03+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_assessment_required",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id=work_unit_id,
            work_unit_fingerprint="truth-snapshot::current-ai-reviewer",
            runtime_health_epoch="runtime-health-event-006306-2365a556e7176a6b",
            blocked_actions=[
                "publication_gate_specificity_required",
                "current_package_freshness_required",
                "artifact_display_surface_materialization_required",
                "canonical_paper_inputs_rehydrate_required",
                "run_quality_repair_batch",
                "run_gate_clearing_batch",
            ],
        ),
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert tasks[0]["payload"]["next_executable_owner"] == "ai_reviewer"
    assert tasks[0]["payload"]["allowed_write_surfaces"] == [
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    ]


def test_domain_handler_export_hydrates_only_one_current_default_executor_action_per_study(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T01:00:00+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_write_repair",
            work_unit_fingerprint="dm003::write::old",
            runtime_health_epoch="runtime-health-event-001",
            blocked_actions=[],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-05-28T01:05:00+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_assessment_required",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            work_unit_fingerprint="dm003::ai-reviewer::current",
            runtime_health_epoch="runtime-health-event-002",
            blocked_actions=[],
        ),
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )


def test_domain_handler_export_prefers_current_control_action_queue_over_later_dispatch(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_blocking_eval(study_root),
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})

    current_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="dm003::ai-reviewer::current-control",
        runtime_health_epoch="runtime-health-event-007001-ai",
        blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
    )
    write_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
        work_unit_fingerprint="dm003::writer::later-dispatch",
        runtime_health_epoch="runtime-health-event-007002-write",
        blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-02T09:15:18+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=ai_route,
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-02T09:52:05+00:00",
        owner_route=write_route,
    )
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-02T10:00:00Z",
            "studies": [],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner_route": {
                        **ai_route,
                        "currentness_contract": {
                            "basis": {
                                "owner_reason": "ai_reviewer_assessment_required",
                                "runtime_health_epoch": "runtime-health-event-007001-ai",
                                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                                "work_unit_fingerprint": "dm003::ai-reviewer::current-control",
                            },
                            "missing_required_fields": [],
                        },
                    },
                    "controller_next_work_unit": {
                        "unit_id": current_work_unit_id,
                        "owner": "ai_reviewer",
                    },
                    "consumption": {
                        "state": "unconsumed",
                        "first_seen_at": "2026-06-02T09:15:18Z",
                    },
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["current_owner_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert study["current_owner_action"]["work_unit_id"] == current_work_unit_id
    assert study["paper_autonomy_loop"]["status"] == "superseded_by_opl_current_owner_route"
    assert study["publication_aftercare"]["currentness_status"] == "superseded_by_opl_current_owner_route"
    task_kinds = [task["task_kind"] for task in payload["pending_family_tasks"]]
    assert "paper_autonomy/repair-recheck" not in task_kinds
    assert "publication_aftercare/analysis-queue-progress" not in task_kinds
    assert "publication_aftercare/reviewer-refresh" not in task_kinds
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["work_unit_id"] == current_work_unit_id
    assert tasks[0]["payload"]["next_executable_owner"] == "ai_reviewer"


def test_domain_handler_export_does_not_fall_back_when_current_control_action_has_no_dispatch(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)

    current_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="dm003::ai-reviewer::current-control",
        runtime_health_epoch="runtime-health-event-007001-ai",
        blocked_actions=["run_quality_repair_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-02T09:52:05+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_write_repair",
            work_unit_fingerprint="dm003::writer::later-dispatch",
            runtime_health_epoch="runtime-health-event-007002-write",
            blocked_actions=["return_to_ai_reviewer_workflow"],
        ),
    )
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-02T10:00:00Z",
            "studies": [],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner_route": {
                        **ai_route,
                        "currentness_contract": {
                            "basis": {
                                "owner_reason": "ai_reviewer_assessment_required",
                                "runtime_health_epoch": "runtime-health-event-007001-ai",
                                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                                "work_unit_fingerprint": "dm003::ai-reviewer::current-control",
                            },
                            "missing_required_fields": [],
                        },
                    },
                    "controller_next_work_unit": {
                        "unit_id": current_work_unit_id,
                        "owner": "ai_reviewer",
                    },
                    "consumption": {"state": "unconsumed"},
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert tasks == []


def test_domain_handler_export_falls_through_consumed_newer_dispatch_to_pending_owner_action(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        work_unit_fingerprint="truth-snapshot::current-ai-reviewer-record",
        runtime_health_epoch="runtime-health-event-006265-ai",
        blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
    )
    write_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        action_type="run_quality_repair_batch",
        work_unit_id="dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        work_unit_fingerprint=(
            "domain-transition::route_back_same_line::"
            "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
        ),
        runtime_health_epoch="runtime-health-event-006251-write",
        blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-31T23:02:05+00:00",
        owner_route=write_route,
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-01T01:53:26+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=ai_route,
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "executed",
                    "execution_id": f"execution::{study_id}::return_to_ai_reviewer_workflow::current",
                    "idempotency_key": ai_route["idempotency_key"],
                    "current_owner_route": ai_route,
                    "prompt_contract": {"owner_route": ai_route},
                    "owner_result": {
                        "status": "materialized",
                        "eval_id": f"publication-eval::{study_id}::current-ai-reviewer",
                        "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        "publication_eval_surface": "artifacts/publication_eval/latest.json",
                        "reviewer_operating_system": {
                            "contract_id": "medical_publication_ai_reviewer_os_v1",
                        },
                        "controller_decision_refresh": {
                            "refresh_status": "materialized",
                        },
                    },
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert tasks[0]["payload"]["next_executable_owner"] == "write"


def test_domain_handler_export_uses_immutable_packet_ref_when_latest_slot_is_overwritten(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    dispatch_dir = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    latest_path = dispatch_dir / "run_quality_repair_batch.json"
    immutable_path = (
        dispatch_dir
        / "immutable"
        / "run_quality_repair_batch"
        / "medical-prose-write-repair.json"
    )

    current_dispatch = _dispatch_payload(
        workspace_root=workspace_root,
        study_id=study_id,
        dispatch_path=latest_path,
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T18:00:05+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_write_repair",
            work_unit_fingerprint="dm003::medical-prose-write-repair",
            runtime_health_epoch="runtime-health-event-medical-prose",
            blocked_actions=[],
        ),
    )
    current_dispatch["refs"]["immutable_dispatch_path"] = str(immutable_path)
    current_dispatch["refs"]["stage_packet_path"] = str(immutable_path)
    _write_json(immutable_path, current_dispatch)

    overwritten_latest = _dispatch_payload(
        workspace_root=workspace_root,
        study_id=study_id,
        dispatch_path=latest_path,
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T18:00:29+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="manuscript_story_repair",
            work_unit_fingerprint="dm003::manuscript-story-repair",
            runtime_health_epoch="runtime-health-event-story-repair",
            blocked_actions=[],
        ),
    )
    _write_json(latest_path, overwritten_latest)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["work_unit_id"] for task in tasks] == ["manuscript_story_repair"]

    _write_json(latest_path, current_dispatch)
    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    task = next(
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )

    expected_ref = str(immutable_path.relative_to(workspace_root))
    latest_ref = str(latest_path.relative_to(workspace_root))
    assert task["payload"]["work_unit_id"] == "medical_prose_write_repair"
    assert task["payload"]["dispatch_ref"] == expected_ref
    assert task["payload"]["dispatch_ref"] != latest_ref
    assert task["source_fingerprint"] in task["dedupe_key"]
    source_refs_by_role = {ref["role"]: ref for ref in task["source_refs"]}
    assert source_refs_by_role["default_executor_stage_packet"]["ref"] == expected_ref
    assert source_refs_by_role["default_executor_dispatch_request"]["ref"] == expected_ref
    assert source_refs_by_role["default_executor_latest_dispatch_request"]["ref"] == latest_ref
    assert source_refs_by_role["default_executor_immutable_dispatch_path"]["ref"] == expected_ref


def _dispatch_payload(
    *,
    workspace_root: Path,
    study_id: str,
    dispatch_path: Path,
    action_type: str,
    next_owner: str,
    dispatch_authority: str,
    owner_route: dict[str, object],
    generated_at: str,
) -> dict[str, object]:
    payload = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "dispatch_status": "ready",
        "dispatch_authority": dispatch_authority,
        "next_executable_owner": next_owner,
        "executor_kind": "codex_cli_default",
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "owner_route": owner_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "next_executable_owner": next_owner,
            "owner_route": owner_route,
            "allowed_write_surfaces": ["paper/draft.md"],
            "forbidden_surfaces": [
                "paper/current_package/**",
                "manuscript/current_package/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "source_eval_path": str(
                workspace_root / "studies" / study_id / "artifacts" / "publication_eval" / "latest.json"
            ),
        },
        "generated_at": generated_at,
    }
    return payload
