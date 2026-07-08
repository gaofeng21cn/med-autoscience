from __future__ import annotations

from tests.test_cli_cases.owner_route_handoff_command.shared import (
    annotations,
    _shared,
    claim_evidence_alignment_digest,
    ready_claim_evidence_alignment_gate,
    argparse,
    builtins,
    importlib,
    json,
    Path,
    sys,
    pytest,
    render_codex_entry_skill,
    render_openclaw_entry_prompt,
    render_public_yaml,
    render_stage_route_contract_guide,
    render_stage_route_contract_payload,
    FIGURE_ROUTE_ILLUSTRATION_PROGRAM,
    FIGURE_ROUTE_SCRIPT_FIX,
    build_figure_route,
    write_profile,
    _write_json,
    _patch_canonical_current_work_unit,
    _owner_route,
    _write_dispatch,
    _opl_execution_authorization,
    _write_opl_production_proof,
    assert_stable_blocker_reason,
    _ai_reviewer_blocking_eval,
)


def test_domain_handler_dispatch_materializes_embedded_ai_reviewer_handoff_inside_mas_owner(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-ai-reviewer-callable",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "opl_execution_authorization": _opl_execution_authorization("quest-001"),
                "repair_work_unit": {
                    "unit_id": "unit-ai-reviewer",
                    "work_unit_type": "ai_reviewer_recheck",
                    "owner": "ai_reviewer",
                    "callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                    "source_fingerprint": "sha256:unit-ai-reviewer",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "controller_decisions/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["execution_status"] == "handoff_ready"
    assert paper_receipt["owner_callable_surface"] == (
        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    )
    handoff = paper_receipt["ai_reviewer_record_worker_handoff"]
    assert handoff["surface"] == "mas_domain_progress_transition_request_projection"
    assert handoff["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert handoff["next_executable_owner"] == "ai_reviewer"
    assert payload["dispatch"]["downstream_worker_handoff"] == handoff
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").is_file()
    assert (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "return_to_ai_reviewer_workflow.json"
    ).is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_domain_handler_dispatch_blocks_embedded_ai_reviewer_callable_without_opl_authorization(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-ai-reviewer-callable-blocked",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-ai-reviewer-blocked",
                    "work_unit_type": "ai_reviewer_recheck",
                    "owner": "ai_reviewer",
                    "callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                    "source_fingerprint": "sha256:unit-ai-reviewer-blocked",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "controller_decisions/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["stable_typed_blocker"] == "opl_execution_authorization_required"
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["accepted"] is False
    assert paper_receipt["execution_status"] == "blocked"
    assert paper_receipt["typed_blocker"] == "opl_execution_authorization_required"


def test_domain_handler_dispatch_preserves_ai_reviewer_record_production_handoff(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-ai-reviewer-current-manuscript-stale",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "opl_execution_authorization": _opl_execution_authorization(
                    "002-dm-china-us-mortality-attribution"
                ),
                "repair_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                    "work_unit_type": "ai_reviewer_recheck",
                    "owner": "ai_reviewer",
                    "callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                    "source_fingerprint": "sha256:current-manuscript-stale-record",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "controller_decisions/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    assert "stable_typed_blocker" not in payload
    assert "reason" not in payload
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["accepted"] is True
    assert paper_receipt["execution_status"] == "handoff_ready"
    assert paper_receipt["typed_blocker"] is None
    handoff = paper_receipt["ai_reviewer_record_worker_handoff"]
    assert handoff["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert handoff["next_executable_owner"] == "ai_reviewer"
    assert payload["dispatch"]["downstream_worker_handoff"] == handoff
    assert payload["receipt_ref"].startswith("runtime/artifacts/opl_family_domain_handler/dispatch_receipts/")
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()
