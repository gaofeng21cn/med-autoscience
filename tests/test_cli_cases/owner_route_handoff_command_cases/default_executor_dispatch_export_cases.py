from __future__ import annotations

from .shared import *  # noqa: F403,F401
import builtins
from med_autoscience.controllers.quality_repair_batch_parts import writer_handoff
from med_autoscience.profiles import load_profile


def _write_default_executor_dispatch(
    *,
    dispatch_path: Path,
    study_root: Path,
    include_owner_route: bool,
    owner_reason: str = "manuscript_story_surface_delta_missing",
) -> None:
    prompt_contract: dict[str, object] = {
        "allowed_write_surfaces": ["paper/draft.md"],
        "forbidden_surfaces": ["artifacts/publication_eval/latest.json"],
    }
    refs = {
        "source_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    if include_owner_route:
        prompt_contract.update(
            {
                "owner_route": {
                    "surface": "domain_route_owner_route",
                    "study_id": study_root.name,
                    "quest_id": study_root.name,
                    "truth_epoch": "publication-eval::002::current",
                    "runtime_health_epoch": "runtime-health-event-002",
                    "work_unit_fingerprint": "medical-prose-routeback::write::fp",
                    "source_fingerprint": "truth-snapshot::002",
                    "route_epoch": "publication-eval::002::current",
                    "current_owner": "quality_repair_batch",
                    "next_owner": "write",
                    "source_refs": {
                        "source_eval_id": "publication-eval::002::current",
                        "work_unit_id": "medical_prose_write_repair",
                        "blocked_reason": owner_reason,
                    },
                    "owner_reason": owner_reason,
                    "allowed_actions": ["run_quality_repair_batch"],
                    "idempotency_key": "owner-route::002::medical-prose-write-repair",
                },
                "allowed_write_surfaces": [
                    "paper/draft.md",
                    "paper/build/review_manuscript.md",
                    "paper/claim_evidence_map.json",
                    "paper/evidence_ledger.json",
                    "paper/review/**",
                ],
                "forbidden_surfaces": [
                    "manuscript/**",
                    "current_package/**",
                    "paper/current_package/**",
                    "manuscript/current_package/**",
                    "artifacts/publication_eval/latest.json",
                    "artifacts/controller_decisions/latest.json",
                ],
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "medical_claim_authoring_allowed": False,
            }
        )
        refs.update(
            {
                "dispatch_path": str(dispatch_path),
                "repair_execution_evidence_path": str(
                    study_root
                    / "artifacts"
                    / "controller"
                    / "repair_execution_evidence"
                    / "latest.json"
                ),
            }
        )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_root.name,
            "quest_id": study_root.name,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "next_executable_owner": "write",
            "executor_kind": "codex_cli_default",
            "consumer_mutation_scope": "executor_dispatch_request_only",
            "prompt_contract": prompt_contract,
            "refs": refs,
        },
    )


def test_domain_handler_export_default_executor_dispatch_does_not_require_pdf_dependency(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "pypdf"
            or module_name.startswith("pypdf.")
            or module_name == "med_autoscience.cli"
            or module_name == "med_autoscience.controllers.owner_route_handoff"
            or module_name.startswith("med_autoscience.controllers.owner_route_handoff_parts.")
            or module_name == "med_autoscience.controllers.submission_minimal"
        ):
            sys.modules.pop(module_name, None)

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pypdf" or name.startswith("pypdf."):
            raise ModuleNotFoundError("No module named 'pypdf'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
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
    )

    cli = importlib.import_module("med_autoscience.cli")
    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [
        task["task_kind"]
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == ["domain_owner/default-executor-dispatch"]


def test_domain_handler_export_projects_default_executor_dispatch_requests(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/default_executor_dispatches/run_quality_repair_batch.json"
    )
    dispatch_path = workspace_root / dispatch_ref
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
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
    task = tasks[0]
    assert task["domain_id"] == "medautoscience"
    assert task["dispatch_owner"] == "one-person-lab"
    assert task["domain_truth_owner"] == "med-autoscience"
    assert task["queue_owner"] == "one-person-lab"
    assert task["profile_name"] == "nfpitnet"
    assert task["requires_approval"] is False
    assert task["dedupe_key"].startswith(
        "mas:nfpitnet:002-dm-china-us-mortality-attribution:"
        "default-executor:run_quality_repair_batch:quality_repair_batch_writer_handoff:"
    )
    assert task["dedupe_key"].endswith(task["source_fingerprint"])
    assert task["payload"] == {
        "profile": str(profile_path),
        "study_id": "002-dm-china-us-mortality-attribution",
        "quest_id": "002-dm-china-us-mortality-attribution",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "source_eval_id": "publication-eval::002::current",
        "source_fingerprint": "truth-snapshot::002",
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "domain_owner": "write",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "dispatch_ref": dispatch_ref,
        "authority_boundary": "mas_default_executor_dispatch_request_only",
        "owner_route_currentness_basis": {
            "source_eval_id": "publication-eval::002::current",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "medical-prose-routeback::write::fp",
            "truth_epoch": "publication-eval::002::current",
            "runtime_health_epoch": "runtime-health-event-002",
            "owner_reason": "manuscript_story_surface_delta_missing",
        },
        "allowed_write_surfaces": [
            "paper/draft.md",
            "paper/build/review_manuscript.md",
            "paper/claim_evidence_map.json",
            "paper/evidence_ledger.json",
            "paper/review/**",
        ],
        "forbidden_surfaces": [
            "manuscript/**",
            "current_package/**",
            "paper/current_package/**",
            "manuscript/current_package/**",
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
        ],
        "required_closeout_packet": {
            "typed_closeout_required_for_completion": True,
            "free_text_closeout_accepted": False,
            "accepted_surface_kinds": [
                "stage_attempt_closeout_packet",
                "stage_memory_closeout_packet",
                "domain_stage_closeout_packet",
            ],
            "required_ref_field": "closeout_refs",
            "minimum_closeout_refs": 1,
            "required_user_stage_log_field": "paper_stage_log",
            "accepted_user_stage_log_fields": [
                "paper_stage_log",
                "user_stage_log",
                "stage_log_summary",
            ],
            "required_user_stage_log_fields": [
                "stage_name",
                "problem_summary",
                "stage_goal",
                "paper_work_done",
                "changed_paper_surfaces",
                "outcome",
                "remaining_blockers",
                "evidence_refs",
            ],
            "user_stage_log_policy": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "summary_scope": "stage_log_read_model_only",
                "paper_body_included": False,
                "paper_body_target": False,
                "internal_review_language_allowed_in_paper_body": False,
                "quality_verdict_authorized": False,
                "submission_readiness_authorized": False,
            },
        },
        "completion_boundary": {
            "provider_completion": "typed_closeout_packet_observed",
            "domain_ready_verdict": "read_from_mas_publication_or_gate_surface",
            "provider_completion_is_domain_ready": False,
        },
    }
    envelope = task["owner_route_attempt_envelope"]
    assert envelope["version"] == "mas-owner-route-attempt-protocol.v1"
    assert envelope["domain_owner"] == "write"
    assert envelope["action_type"] == "run_quality_repair_batch"
    assert envelope["work_unit_id"] == "medical_prose_write_repair"
    assert envelope["source_eval_id"] == "publication-eval::002::current"
    assert envelope["owner_reason_contract"]["reason"] == "manuscript_story_surface_delta_missing"
    assert envelope["owner_reason_contract"]["registered"] is True
    assert envelope["dispatchable"] is True
    source_refs_by_role = {ref["role"]: ref for ref in task["source_refs"]}
    assert source_refs_by_role["default_executor_dispatch_request"]["ref"] == dispatch_ref
    assert source_refs_by_role["default_executor_dispatch_request"]["body_included"] is False
    assert source_refs_by_role["default_executor_prompt_contract"]["ref"] == f"{dispatch_ref}#prompt_contract"
    assert source_refs_by_role["mas_default_executor_owner_receipt_contract"]["ref"] == (
        "mas-default-executor-owner-receipt.v1"
    )
    assert source_refs_by_role["owner_route_currentness_basis"]["ref"] == f"{dispatch_ref}#owner_route"
    assert {
        "default_executor_dispatch_path",
        "source_publication_eval_currentness",
        "repair_execution_evidence_currentness",
        "owner_route_truth_epoch",
        "owner_route_work_unit_fingerprint",
        "owner_route_source_eval_id",
        "owner_route_runtime_health_epoch",
        "owner_route_work_unit_id",
        "owner_route_blocked_reason",
    } <= set(source_refs_by_role)
    evidence_payload = task["domain_dispatch_evidence_record_payload"]
    assert (evidence_payload["surface_kind"], evidence_payload["domain_id"], evidence_payload["task_kind"]) == (
        "mas_domain_dispatch_evidence_record_payload",
        "medautoscience",
        "domain_owner/default-executor-dispatch",
    )
    assert evidence_payload["study_id"] == "002-dm-china-us-mortality-attribution"
    assert evidence_payload["source_fingerprint"] == task["source_fingerprint"]
    assert evidence_payload["domain_source_fingerprint"] == task["source_fingerprint"]
    assert evidence_payload["profile_name"] == "nfpitnet"
    assert {
        key: evidence_payload["record_payload"][key]
        for key in (
            "domain_id",
            "task_kind",
            "study_id",
            "source_fingerprint",
            "domain_source_fingerprint",
            "profile_name",
        )
    } == {
        "domain_id": "medautoscience",
        "task_kind": "domain_owner/default-executor-dispatch",
        "study_id": "002-dm-china-us-mortality-attribution",
        "source_fingerprint": task["source_fingerprint"],
        "domain_source_fingerprint": task["source_fingerprint"],
        "profile_name": "nfpitnet",
    }
    assert all(
        evidence_payload[field] is False
        for field in (
            "body_included",
            "domain_ready_claimed",
            "publication_ready_claimed",
            "artifact_mutation_authorized",
            "current_package_mutation_authorized",
        )
    )
    assert evidence_payload["record_payload"]["typed_blocker_refs"]
    assert evidence_payload["record_payload"]["no_regression_refs"]
    assert "receipt_ref" not in evidence_payload["record_payload"]
    assert {
        dispatch_ref,
        "studies/002-dm-china-us-mortality-attribution/artifacts/publication_eval/latest.json",
    } <= set(evidence_payload["record_payload"]["evidence_refs"])
    assert {packet["role"] for packet in evidence_payload["body_free_evidence_packets"]} == {
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    }
    assert evidence_payload["authority_boundary"] == {
        "owner": "med-autoscience",
        "opl_records_refs_only": True,
        "opl_writes_mas_truth": False,
        "opl_reads_memory_body": False,
        "opl_reads_artifact_body": False,
        "opl_authorizes_quality_or_publication": False,
        "provider_completion_is_domain_ready": False,
        "typed_blocker_is_domain_ready": False,
    }


def test_default_executor_dispatch_dedupe_key_tracks_owner_route_currentness(
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
    )

    first_exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    first_payload = json.loads(capsys.readouterr().out)
    assert first_exit_code == 0
    first_task = next(
        task
        for task in first_payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )

    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    dispatch["prompt_contract"]["owner_route"]["work_unit_fingerprint"] = (
        "medical-prose-routeback::write::fp::rerun"
    )
    dispatch["prompt_contract"]["owner_route"]["runtime_health_epoch"] = "runtime-health-event-003"
    dispatch["prompt_contract"]["owner_route"]["source_refs"]["runtime_health_epoch"] = (
        "runtime-health-event-003"
    )
    _write_json(dispatch_path, dispatch)

    second_exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    second_payload = json.loads(capsys.readouterr().out)
    assert second_exit_code == 0
    second_task = next(
        task
        for task in second_payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )

    assert second_task["source_fingerprint"] != first_task["source_fingerprint"]
    assert second_task["dedupe_key"] != first_task["dedupe_key"]
    assert second_task["source_fingerprint"] in second_task["dedupe_key"]


def test_domain_handler_export_skips_consumed_default_executor_dispatch(
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
    )
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    owner_route = dispatch["prompt_contract"]["owner_route"]
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_root.name,
                    "quest_id": study_root.name,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::consumed",
                    "idempotency_key": "owner-route::previous-runtime-health",
                    "current_owner_route": {
                        **owner_route,
                        "idempotency_key": "owner-route::previous-runtime-health",
                        "runtime_health_epoch": "runtime-health-event-previous",
                        "source_refs": {
                            **owner_route["source_refs"],
                            "runtime_health_epoch": "runtime-health-event-previous",
                        },
                    },
                    "prompt_contract": {"owner_route": owner_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == []


def test_domain_handler_export_keeps_default_executor_dispatch_when_receipt_work_unit_differs(
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
    )
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    owner_route = dispatch["prompt_contract"]["owner_route"]
    previous_route = {
        **owner_route,
        "idempotency_key": "owner-route::previous-work-unit",
        "work_unit_fingerprint": "medical-prose-routeback::write::previous",
        "source_refs": {
            **owner_route["source_refs"],
            "work_unit_id": "previous_work_unit",
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_root.name,
                    "quest_id": study_root.name,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::previous",
                    "idempotency_key": previous_route["idempotency_key"],
                    "current_owner_route": previous_route,
                    "prompt_contract": {"owner_route": previous_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
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
    assert len(tasks) == 1
    assert tasks[0]["payload"]["work_unit_id"] == "medical_prose_write_repair"


def test_domain_handler_export_redrives_nonconsumable_same_work_unit_closeout(
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
    )

    first_exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    first_payload = json.loads(capsys.readouterr().out)
    assert first_exit_code == 0
    first_task = next(
        task
        for task in first_payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    owner_route = dispatch["prompt_contract"]["owner_route"]
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_root.name,
                    "quest_id": study_root.name,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::ledger-only",
                    "idempotency_key": owner_route["idempotency_key"],
                    "current_owner_route": owner_route,
                    "prompt_contract": {"owner_route": owner_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "manuscript_surface_hygiene": {
                                "story_surface_delta_required": True,
                                "story_surface_delta_present": False,
                            },
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "claim_evidence_map.json")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    second_exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    second_payload = json.loads(capsys.readouterr().out)

    assert second_exit_code == 0
    second_task = next(
        task
        for task in second_payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )
    assert second_task["source_fingerprint"] != first_task["source_fingerprint"]
    assert second_task["dedupe_key"] != first_task["dedupe_key"]
    assert second_task["payload"]["redrive_context"] == {
        "status": "non_consumable_closeout",
        "receipt_kind": "default_executor_execution",
        "receipt_ref": "artifacts/supervision/consumer/default_executor_execution/latest.json",
        "execution_id": "execution::dm002::run_quality_repair_batch::ledger-only",
        "action_type": "run_quality_repair_batch",
        "execution_status": "executed",
        "owner_result_status": "executed",
        "repair_execution_evidence_status": "progress_delta_candidate",
        "reason": "manuscript_story_surface_delta_missing",
        "changed_artifact_ref_count": 1,
        "quality_authorized": False,
        "submission_authorized": False,
        "current_package_write_authorized": False,
        "next_action": "redrive_owner_route_with_closeout_context",
    }
    roles = {ref["role"] for ref in second_task["source_refs"]}
    assert "nonconsumable_default_executor_closeout" in roles
    assert "nonconsumable_default_executor_execution_id" in roles


def test_domain_handler_export_projects_bridged_dm003_writer_handoff(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    source_eval_id = "publication-eval::dm003::medical-prose-routeback"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = load_profile(profile_path)
    current_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-dm003-medical-prose",
        "runtime_health_epoch": "runtime-health-event-dm003-medical-prose",
        "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
        "source_fingerprint": "truth-source::dm003::medical-prose",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "failure_signature": "quest_waiting_opl_runtime_owner_route",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": [],
        "idempotency_key": "owner-route::dm003::medical-prose",
        "source_refs": {
            "source_eval_id": source_eval_id,
            "work_unit_id": "medical_prose_write_repair",
            "runtime_health_epoch": "runtime-health-event-dm003-medical-prose",
            "study_truth_epoch": "truth-event-dm003-medical-prose",
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
        },
    }
    handoff = writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=study_id,
        schema_version=1,
        source_eval_id=source_eval_id,
        source_eval_artifact_path=str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        source_summary_artifact_path=str(
            study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
        ),
        repair_execution_evidence_path=(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "current_owner_route": current_route,
            "controller_route_context": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
                "source_eval_id": source_eval_id,
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, handoff)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["payload"]["study_id"] == study_id
    assert task["payload"]["work_unit_id"] == "medical_prose_write_repair"
    assert task["payload"]["owner_route_currentness_basis"] == {
        "source_eval_id": source_eval_id,
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
        "truth_epoch": "truth-event-dm003-medical-prose",
        "runtime_health_epoch": "runtime-health-event-dm003-medical-prose",
        "owner_reason": "manuscript_story_surface_delta_missing",
    }
    assert task["owner_route_attempt_envelope"]["dispatchable"] is True
    source_refs_by_role = {ref["role"]: ref for ref in task["source_refs"]}
    assert source_refs_by_role["owner_route_runtime_health_epoch"]["ref"] == (
        "runtime-health-event-dm003-medical-prose"
    )
    assert source_refs_by_role["owner_route_blocked_reason"]["ref"] == (
        "manuscript_story_surface_delta_missing"
    )


def test_domain_handler_export_projects_ai_reviewer_default_executor_dispatch_request(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "return_to_ai_reviewer_workflow.json"
    )
    dispatch_path = workspace_root / dispatch_ref
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-000017-bac190eb1c889a78",
        "runtime_health_epoch": "runtime-health-event-006195-9cdb58e3383bd0a9",
        "work_unit_fingerprint": "truth-snapshot::085b4164f248a2f4c92bf66b",
        "source_fingerprint": "truth-snapshot::085b4164f248a2f4c92bf66b",
        "route_epoch": "truth-event-000017-bac190eb1c889a78",
        "current_owner": "mas_controller",
        "next_owner": "ai_reviewer",
        "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "blocked_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "runtime_health_epoch": "runtime-health-event-006195-9cdb58e3383bd0a9",
            "study_truth_epoch": "truth-event-000017-bac190eb1c889a78",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
        },
        "idempotency_key": (
            "owner-route::002-dm-china-us-mortality-attribution::"
            "ai-reviewer-current-manuscript"
        ),
    }
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "executor_kind": "codex_cli_default",
            "consumer_mutation_scope": "executor_dispatch_request_only",
            "owner_route": owner_route,
            "prompt_contract": {
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "return_to_ai_reviewer_workflow",
                "next_executable_owner": "ai_reviewer",
                "owner_route": owner_route,
                "allowed_write_surfaces": [
                    "artifacts/supervision/consumer/latest.json",
                    "artifacts/supervision/consumer/history.jsonl",
                    "studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/*.json",
                    "studies/<study_id>/artifacts/supervision/requests/ai_reviewer/latest.json",
                    (
                        "artifacts/publication_eval/ai_reviewer_responses/"
                        "*_publication_eval_record.json"
                    ),
                ],
                "forbidden_surfaces": [
                    "paper/**",
                    "manuscript/**",
                    "current_package/**",
                    "paper/current_package/**",
                    "manuscript/current_package/**",
                    "artifacts/publication_eval/latest.json",
                    "artifacts/controller_decisions/latest.json",
                ],
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "medical_claim_authoring_allowed": False,
                "prompt_budget": {"max_prompt_tokens": 6000},
                "compact_evidence_packet_ref": (
                    "artifacts/supervision/compact_evidence_packets/"
                    "return_to_ai_reviewer_workflow.json"
                ),
                "do_not_repeat": True,
                "repeat_suppression_key": "truth-snapshot::085b4164f248a2f4c92bf66b",
            },
            "refs": {
                "dispatch_path": str(dispatch_path),
                "scan_latest": str(workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"),
            },
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
    assert len(tasks) == 1
    task = tasks[0]
    assert task["payload"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert task["payload"]["domain_owner"] == "ai_reviewer"
    assert task["payload"]["next_executable_owner"] == "ai_reviewer"
    assert task["payload"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )
    assert task["payload"]["dispatch_ref"] == dispatch_ref
    assert task["payload"]["authority_boundary"] == "mas_default_executor_dispatch_request_only"
    assert task["payload"]["owner_route_currentness_basis"] == {
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "work_unit_fingerprint": "truth-snapshot::085b4164f248a2f4c92bf66b",
        "truth_epoch": "truth-event-000017-bac190eb1c889a78",
        "runtime_health_epoch": "runtime-health-event-006195-9cdb58e3383bd0a9",
        "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
    }
    assert task["owner_route_attempt_envelope"]["domain_owner"] == "ai_reviewer"
    assert task["owner_route_attempt_envelope"]["dispatchable"] is True
    assert {
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
        "paper/current_package/**",
        "manuscript/current_package/**",
    } <= set(task["payload"]["forbidden_surfaces"])
    source_refs_by_role = {ref["role"]: ref for ref in task["source_refs"]}
    assert source_refs_by_role["default_executor_dispatch_request"]["ref"] == dispatch_ref
    assert source_refs_by_role["default_executor_prompt_contract"]["ref"] == f"{dispatch_ref}#prompt_contract"
    assert source_refs_by_role["owner_route_work_unit_id"]["ref"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )
    assert source_refs_by_role["owner_route_blocked_reason"]["ref"] == (
        "ai_reviewer_record_stale_after_current_manuscript"
    )
    evidence_payload = task["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["authority_boundary"]["opl_writes_mas_truth"] is False
    assert evidence_payload["authority_boundary"]["opl_authorizes_quality_or_publication"] is False
    assert evidence_payload["current_package_mutation_authorized"] is False
    assert evidence_payload["publication_ready_claimed"] is False


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


def test_domain_handler_export_skips_default_executor_dispatch_with_unregistered_owner_reason(
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
    assert [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == []
