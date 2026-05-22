from __future__ import annotations

from .shared import *  # noqa: F403,F401


def _write_default_executor_dispatch(
    *,
    dispatch_path: Path,
    study_root: Path,
    include_owner_route: bool,
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
                    "current_owner": "quality_repair_batch",
                    "next_owner": "write",
                    "source_refs": {
                        "source_eval_id": "publication-eval::002::current",
                        "work_unit_id": "medical_prose_write_repair",
                        "blocked_reason": "manuscript_story_surface_delta_missing",
                    },
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


def test_sidecar_export_projects_default_executor_dispatch_requests(tmp_path: Path, capsys) -> None:
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

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
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
    assert task["dedupe_key"] == (
        "mas:nfpitnet:002-dm-china-us-mortality-attribution:"
        "default-executor:run_quality_repair_batch:quality_repair_batch_writer_handoff"
    )
    assert task["payload"] == {
        "profile": str(profile_path),
        "study_id": "002-dm-china-us-mortality-attribution",
        "quest_id": "002-dm-china-us-mortality-attribution",
        "action_type": "run_quality_repair_batch",
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "dispatch_ref": dispatch_ref,
        "authority_boundary": "mas_default_executor_dispatch_request_only",
    }
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


def test_sidecar_export_skips_bare_default_executor_dispatch_without_owner_currentness(
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

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == []
