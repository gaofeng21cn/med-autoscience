from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from .shared import write_profile


FORBIDDEN_AUTHORITY_RELATIVE_PATHS = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "paper/current_package",
)
DM_CANARY_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "paper_mission_dm_canary"
)


@pytest.fixture(autouse=True)
def _disable_default_opl_live_probe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_BIN", str(tmp_path / "missing-opl"))


def _paper_mission_forbidden_write_guard() -> dict:
    return {
        "candidate_writes_authority": False,
        "blocked_paths": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "current_package",
            "runtime queue/provider attempts",
            "/Users/gaofeng/workspace/Yang/**",
        ],
        "forbidden_claims": [
            "publication_ready",
            "current_package",
            "owner_receipt_written",
        ],
    }


def _write_profile_with_study(tmp_path: Path, *, study_id: str = "001-paper") -> Path:
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=workspace_root)
    (workspace_root / "studies" / study_id).mkdir(parents=True)
    return profile_path


def _assert_forbidden_authority_untouched(tmp_path: Path, *, study_id: str = "001-paper") -> None:
    study_root = tmp_path / "workspace" / "studies" / study_id
    for relative_path in FORBIDDEN_AUTHORITY_RELATIVE_PATHS:
        assert not (study_root / relative_path).exists()


def _write_paper_source_fixture(tmp_path: Path, *, study_id: str) -> None:
    paper_root = tmp_path / "workspace" / "studies" / study_id / "paper"
    (paper_root / "build").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)
    (paper_root / "figures").mkdir(parents=True, exist_ok=True)
    (paper_root / "review").mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text(
        "\n".join(
            [
                "# DM paper draft",
                "",
                "## Methods",
                "Current methods text.",
                "",
                "## Results",
                "Current results text.",
                "",
                "## Limitations",
                "Current limitations text.",
            ]
        ),
        encoding="utf-8",
    )
    (paper_root / "build" / "review_manuscript.md").write_text(
        "\n".join(
            [
                "# Review manuscript",
                "",
                "## Discussion",
                "Reviewer-facing discussion text.",
            ]
        ),
        encoding="utf-8",
    )
    (paper_root / "claim_evidence_map.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "claim-primary",
                        "title": "Primary mortality gap claim",
                        "status": "needs_binding",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (paper_root / "evidence_ledger.json").write_text(
        json.dumps(
            {
                "evidence": [
                    {
                        "evidence_id": "ev-primary",
                        "title": "Model comparison evidence",
                        "source_ref": "analysis://primary-model",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (paper_root / "tables" / "table_catalog.json").write_text(
        json.dumps(
            {
                "tables": [
                    {
                        "table_id": "T1",
                        "title": "Cohort characteristics",
                        "status": "candidate",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (paper_root / "figures" / "figure_catalog.json").write_text(
        json.dumps(
            {
                "figures": [
                    {
                        "figure_id": "F1",
                        "title": "Attribution curve",
                        "status": "candidate",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (paper_root / "review" / "review_ledger.json").write_text(
        json.dumps(
            {
                "reviews": [
                    {
                        "id": "gate-1",
                        "verdict": "revise",
                        "section": "Results",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_candidate_manifest(
    tmp_path: Path,
    *,
    study_id: str = "001-paper",
    requested_outcome: str = "accepted_candidate",
    paper_mission_transaction: dict | None = None,
) -> Path:
    candidate_path = tmp_path / "candidate.json"
    candidate = {
        "candidate_id": "pmc-001",
        "mission_id": f"paper-mission::{study_id}::gate-clearing::manual",
        "study_id": study_id,
        "requested_outcome": requested_outcome,
        "candidate_manifest_ref": "paper-mission/pmc-001.json",
        "candidate_artifact_refs": ["paper-mission/patch-plan.md"],
        "source_readiness_refs": ["source-readiness:001"],
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": "mas_authority_kernel",
        "resume_condition": "MAS consumes or routes back the mission candidate",
    }
    if paper_mission_transaction is not None:
        candidate["paper_mission_transaction"] = paper_mission_transaction
    if requested_outcome == "typed_blocker_required":
        candidate["typed_blocker_request"] = {
            "blocker_id": "source_readiness_missing",
            "blocker_ref": "typed-blocker-request:pmc-001",
        }
    if requested_outcome == "human_gate_required":
        candidate["human_gate_request"] = {
            "decision_packet_ref": "human-gate-request:pmc-001",
        }
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return candidate_path


def _paper_mission_transaction_payload(
    *,
    mission_id: str,
    study_id: str,
    decision_kind: str = "route_back",
) -> dict:
    transaction_id = "paper-mission-transaction::pmc-001"
    stage_id = "paper-stage::gate-clearing"
    stage_run_ref = "opl-stage-run://pmc-001"
    if decision_kind == "advance":
        terminal_decision = {
            "decision_kind": "advance",
            "status": "accepted",
            "reason": "candidate accepted for the next MAS paper stage",
            "next_owner": "analysis-campaign",
            "next_stage_id": "publication_gate_replay",
        }
        route_command = {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
            "reason": "candidate accepted for the next MAS paper stage",
            "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "stage_run_ref": stage_run_ref,
            "runtime_owner": "one-person-lab",
        }
        transaction_state = "accepted"
    elif decision_kind == "continue_same_stage":
        terminal_decision = {
            "decision_kind": "continue_same_stage",
            "status": "accepted_submission_milestone_candidate",
            "reason": "candidate accepted for continued paper-facing work",
            "next_owner": "mission_executor",
            "next_work_unit": "continue paper-facing submission milestone work",
        }
        route_command = {
            "command_kind": "resume_stage",
            "target": "continue paper-facing submission milestone work",
            "reason": "candidate accepted for continued paper-facing work",
            "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "stage_run_ref": stage_run_ref,
            "runtime_owner": "one-person-lab",
        }
        transaction_state = "accepted_submission_milestone_candidate"
    elif decision_kind == "typed_blocker":
        terminal_decision = {
            "decision_kind": "typed_blocker",
            "status": "typed_blocker",
            "reason": "source readiness is missing",
            "next_owner": "mas_authority_kernel",
            "blocker_id": "source_readiness_missing",
            "unblock_condition": "MAS authority kernel records or rejects the typed blocker request",
        }
        route_command = {
            "command_kind": "stop_with_typed_blocker",
            "target": "source_readiness_missing",
            "reason": "source readiness is missing",
            "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "stage_run_ref": stage_run_ref,
            "runtime_owner": "one-person-lab",
        }
        transaction_state = "typed_blocker"
    else:
        terminal_decision = {
            "decision_kind": "route_back",
            "status": "terminal_decision_recorded",
            "reason": "candidate needs a claim/evidence repair pass",
            "next_owner": "mission_executor",
            "target_stage_id": "paper-stage::gate-clearing",
            "repair_scope": "claim-evidence-repair",
        }
        route_command = {
            "command_kind": "route_back",
            "target": "paper-stage::gate-clearing",
            "reason": "MAS terminal decision requested route back",
            "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "stage_run_ref": stage_run_ref,
            "runtime_owner": "one-person-lab",
        }
        transaction_state = "terminal_decision_recorded"
    fingerprint = (
        f"{mission_id}::{stage_id}::{terminal_decision['decision_kind']}::"
        f"{terminal_decision['status']}"
    )
    return {
        "transaction_id": transaction_id,
        "mission_id": mission_id,
        "study_id": study_id,
        "stage_id": stage_id,
        "stage_run_ref": stage_run_ref,
        "stage_terminal_decision": terminal_decision,
        "opl_route_command": route_command,
        "artifact_delta_refs": [
            {
                "ref_id": "artifact-delta::pmc-001",
                "ref_kind": "candidate_artifact_delta",
                "uri": "mission://pmc-001/artifact-delta",
            }
        ],
        "paper_audit_pack_refs": {
            family: [
                {
                    "ref_id": f"{family}::pmc-001",
                    "ref_kind": family,
                    "uri": f"mission://pmc-001/{family}",
                }
            ]
            for family in (
                "analysis_rationale_log",
                "decision_trace",
                "evidence_ledger_delta",
                "review_ledger_delta",
                "revision_log_delta",
                "failed_path_ledger",
                "artifact_lineage",
                "reproducibility_refs",
            )
        },
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_provider_attempt": False,
            "writes_yang_authority": False,
        },
        "idempotency": {
            "idempotency_key": f"{study_id}::{stage_id}::{decision_kind}",
            "transaction_fingerprint": fingerprint,
        },
        "transaction_state": transaction_state,
    }


def _write_matching_domain_gate_closeout(
    *,
    study_root: Path,
    study_id: str,
    transaction: dict,
) -> Path:
    closeout_root = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
    )
    closeout_root.mkdir(parents=True, exist_ok=True)
    closeout_ref = closeout_root / "sat-terminal.closeout.json"
    closeout_ref.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "blocked",
                "study_id": study_id,
                "stage_id": transaction["opl_route_command"]["target"],
                "stage_attempt_id": "sat-terminal",
                "action_type": transaction["opl_route_command"]["command_kind"],
                "work_unit_id": transaction["stage_id"],
                "work_unit_fingerprint": transaction["idempotency"][
                    "transaction_fingerprint"
                ],
                "stage_packet_ref": (
                    f"{transaction['transaction_id']}#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    f"{transaction['transaction_id']}#opl_route_command"
                ),
                "provider_attempt_ref": "temporal://attempt/sat-terminal",
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "typed_blocker_ref": (
                    "artifacts/supervision/consumer/default_executor_execution/"
                    "sat-terminal.closeout.json#domain_blocker"
                ),
                "blocked_reason": "domain_gate_pending",
                "closeout_refs": [
                    f"{transaction['transaction_id']}#opl_route_command",
                    "artifacts/supervision/consumer/default_executor_execution/"
                    "sat-terminal.closeout.json",
                    "typed-blocker:domain_gate_pending",
                ],
                "authority_boundary": {
                    "record_only_surface": True,
                    "provider_completion_is_domain_completion": False,
                    "artifact_mutation_authorized": False,
                    "publication_eval_latest_write_authorized": False,
                    "controller_decision_write_authorized": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return closeout_ref


def test_paper_mission_help_exposes_default_commands(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["paper-mission", "--help"])
    captured = capsys.readouterr()

    assert excinfo.value.code == 0
    for command in (
        "inspect",
        "start",
        "resume",
        "consume-candidate",
        "package-candidate",
        "drive",
    ):
        assert command in captured.out


@pytest.mark.parametrize(
    ("argv_tail", "expected_command", "expected_intent", "expected_dry_run"),
    (
        (["inspect"], "inspect", "paper_mission/inspect", False),
        (
            ["start", "--objective", "gate clearing", "--dry-run"],
            "start",
            "paper_mission/start_or_resume",
            True,
        ),
        (
            ["resume", "--mission-id", "mission-001", "--dry-run"],
            "resume",
            "paper_mission/start_or_resume",
            True,
        ),
        (
            ["consume-candidate", "--candidate", "candidates/mission.json", "--dry-run"],
            "consume-candidate",
            "paper_mission/consume_candidate",
            True,
        ),
    ),
)
def test_paper_mission_cli_returns_no_write_json_plan(
    tmp_path: Path,
    capsys,
    argv_tail: list[str],
    expected_command: str,
    expected_intent: str,
    expected_dry_run: bool,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)

    exit_code = cli.main(
        [
            "paper-mission",
            *argv_tail,
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_no_write_readback"
    assert payload["paper_mission_command"] == expected_command
    assert payload["action_intent"] == expected_intent
    assert payload["dry_run"] is expected_dry_run
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    assert payload["transaction_state"] == "not_materialized"
    assert payload["stage_terminal_decision"]["authority_materialized"] is False
    assert payload["opl_route_command"]["authority_materialized"] is False
    assert payload["opl_runtime_carrier"]["surface_kind"] == (
        "mas_domain_progress_transition_request"
    )
    assert payload["opl_runtime_carrier"]["provider_admission_pending"] is False
    assert payload["opl_runtime_carrier"][
        "provider_admission_requires_opl_runtime_result"
    ] is True
    assert payload["paper_mission_run_candidate"]["transaction_state"] == (
        "not_materialized"
    )
    assert "publication_eval/latest.json" in payload["forbidden_authority_writes"]
    _assert_forbidden_authority_untouched(tmp_path)


def test_domain_entry_dispatch_handles_paper_mission_dry_run_without_authority_writes(
    tmp_path: Path,
) -> None:
    domain_entry = importlib.import_module("med_autoscience.domain_entry")
    profile_path = _write_profile_with_study(tmp_path)

    result = domain_entry.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "paper-mission",
            "paper_mission_command": "resume",
            "profile_ref": str(profile_path),
            "study_id": "001-paper",
            "mission_id": "mission-001",
            "dry_run": True,
        }
    )

    assert result["command"] == "paper-mission"
    assert result["paper_mission_command"] == "resume"
    assert result["action_intent"] == "paper_mission/start_or_resume"
    assert result["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path)


def test_domain_handler_export_defaults_to_paper_mission_start_or_resume(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["dispatch"]["default_action_intent"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["default_queue_source"] == "/paper_mission_default_tasks"
    assert payload["dispatch"]["legacy_queue_source"] == "/pending_family_tasks"
    assert "paper_mission/start_or_resume" in payload["dispatch"]["allowed_task_kinds"]
    assert payload["pending_family_tasks_policy"] == {
        "default_paper_mission_queue_source": "/paper_mission_default_tasks",
        "legacy_mixed_queue_source": "/pending_family_tasks",
        "pending_family_tasks_role": "mixed_explicit_owner_handoff_and_migration_compatibility_queue",
        "ordinary_consumer_rule": (
            "OPL consumers that want the MAS paper loop must hydrate only "
            "/paper_mission_default_tasks unless an explicit owner handoff task "
            "was selected by a MAS StageTerminalDecision or authority receipt."
        ),
        "non_default_task_policy": {
            "default_paper_mission_entry": False,
            "paper_mission_default_role": "diagnostic_or_explicit_owner_handoff",
            "can_select_next_paper_stage": False,
            "can_authorize_provider_admission": False,
            "counts_as_paper_progress": False,
        },
    }
    paper_mission_tasks = payload["paper_mission_default_tasks"]
    assert paper_mission_tasks
    assert paper_mission_tasks[0]["default_paper_mission_entry"] is True
    assert paper_mission_tasks[0]["payload"]["paper_mission_command"] == "drive"
    assert paper_mission_tasks[0]["payload"]["dry_run"] is False
    assert paper_mission_tasks[0]["payload"]["submit_opl_runtime"] is False
    assert paper_mission_tasks[0]["payload"]["run_id"].startswith(
        "domain-handler-default-drive-"
    )
    assert paper_mission_tasks[0]["payload"]["dispatch_execution_boundary"] == {
        "mode": "non_authority_candidate_package_and_consumption_ledger",
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "runtime_queue_submission_requires_explicit_submit_opl_runtime": True,
    }
    assert paper_mission_tasks[0]["payload"]["diagnostic_readback_command"] == "start"
    assert paper_mission_tasks[0]["payload"]["diagnostic_readback_dry_run"] is True
    assert paper_mission_tasks[0]["payload"]["paper_mission"]["dry_run"] is True
    assert not [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
    ]
    for task in payload["pending_family_tasks"]:
        assert task["default_paper_mission_entry"] is False
        assert task["paper_mission_default_role"] == "diagnostic_or_explicit_owner_handoff"
        assert task["can_select_next_paper_stage"] is False
        assert task["can_authorize_provider_admission"] is False
        assert task["counts_as_paper_progress"] is False


def test_domain_handler_export_paper_mission_task_carries_opl_runtime_carrier_for_materialized_mission(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260623T2032Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": f"paper-mission::{study_id}::gate-clearing::one-shot-migration",
        "study_id": study_id,
        "objective": "Consume DM002 publication blockers and repair claim/evidence gaps.",
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::claim-evidence-repair",
                "artifact_ref": "mission://dm002/claim-evidence-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    mission_payload["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission_id=mission_payload["mission_id"],
        study_id=study_id,
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps({"candidate_id": "pmc-dm002"}),
        encoding="utf-8",
    )

    exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    paper_mission_task = next(
        task
        for task in payload["paper_mission_default_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
        and task["study_id"] == study_id
    )
    task_payload = paper_mission_task["payload"]
    carrier = task_payload["opl_runtime_carrier"]
    assert carrier["surface_kind"] == "mas_domain_progress_transition_request"
    assert task_payload["opl_domain_progress_transition_request"] == carrier
    assert task_payload["dispatch_authority"] == "paper_mission_transaction"
    assert task_payload["action_type"] == carrier["action_type"]
    assert task_payload["work_unit_id"] == carrier["work_unit_id"]
    assert task_payload["work_unit_fingerprint"] == carrier["work_unit_fingerprint"]
    assert task_payload["route_identity_key"] == carrier["route_identity_key"]
    assert task_payload["attempt_idempotency_key"] == carrier["attempt_idempotency_key"]
    assert task_payload["provider_completion_is_domain_completion"] is False
    assert task_payload["stage_transition_authority_boundary"] == carrier[
        "authority_boundary"
    ]
    assert task_payload["stage_packet_ref"] == carrier["stage_run_ref"]
    assert carrier["stage_run_ref"] in task_payload["stage_packet_refs"]
    assert task_payload["paper_mission"]["materialized_mission_ref"].endswith(
        "/paper_mission_run.json"
    )
    assert task_payload["paper_mission"]["candidate_manifest_ref"].endswith(
        "/candidate_manifest.json"
    )
    assert task_payload["paper_mission"]["opl_runtime_carrier"] == carrier


def test_domain_handler_export_default_task_dispatches_to_drive(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624Texportdispatch"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::exportdispatch"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Exported default task must dispatch to paper mission drive.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
        },
        "paper_mission_transaction": transaction,
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-exportdispatch",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )

    export_exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    export_payload = json.loads(capsys.readouterr().out)
    assert export_exit_code == 0
    exported_task = next(
        task
        for task in export_payload["paper_mission_default_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
        and task["study_id"] == study_id
    )
    task_path = tmp_path / "exported-paper-mission-task.json"
    task_path.write_text(json.dumps(exported_task), encoding="utf-8")

    dispatch_exit_code = cli.main(
        ["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]
    )
    dispatch_payload = json.loads(capsys.readouterr().out)

    assert dispatch_exit_code == 0
    assert dispatch_payload["dispatch"]["execution_policy"] == (
        "paper_mission_drive_non_authority_candidate_and_ledger"
    )
    result = dispatch_payload["dispatch"]["result"]
    assert result["surface_kind"] == "paper_mission_drive_readback"
    assert result["paper_mission_command"] == "drive"
    assert result["output_manifest"]["writes_authority"] is False
    assert result["output_manifest"]["writes_runtime"] is False
    assert result["output_manifest"]["writes_yang_authority"] is False
    assert result["candidate_package_readback"]["output_manifest"][
        "package_manifest_ref"
    ].endswith(f"/{study_id}/package_manifest.json")
    assert result["consume_readback"]["consume_output_manifest"][
        "opl_route_handoff_ref"
    ].endswith(f"/{study_id}/opl_route_handoff.json")
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)



def test_paper_mission_package_candidate_writes_non_authority_owner_decision_package(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260623T2032Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": f"paper-mission::{study_id}::gate-clearing::one-shot-migration",
        "study_id": study_id,
        "objective": "Consume DM002 publication blockers and repair claim/evidence gaps.",
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::claim-evidence-repair",
                "artifact_ref": "mission://dm002/claim-evidence-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    mission_payload["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission_id=mission_payload["mission_id"],
        study_id=study_id,
        decision_kind="advance",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002",
                "mission_id": mission_payload["mission_id"],
                "study_id": study_id,
                "next_owner": "analysis-campaign",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260623T2100Z"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "package-candidate",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--output-root",
            str(output_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_candidate_package_write_readback"
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    assert payload["mutation_policy"]["writes_yang_authority"] is False
    assert (
        "Yang output outside ops/medautoscience/paper_mission_candidate_package"
        in payload["mutation_policy"]["forbidden_authority_writes"]
    )
    assert (
        "Yang output outside ops/medautoscience/paper_mission_one_shot_migration"
        not in payload["mutation_policy"]["forbidden_authority_writes"]
    )
    assert payload["output_manifest"]["writes_authority"] is False
    assert payload["output_manifest"]["writes_runtime"] is False
    assert payload["output_manifest"]["writes_yang_authority"] is False
    assert payload["output_manifest"]["package_manifest_ref"].endswith(
        "/package_manifest.json"
    )
    assert payload["output_manifest"]["mission_executor_handoff_ref"].endswith(
        "/mission_executor_handoff.json"
    )
    assert payload["output_manifest"]["paper_facing_candidate_delta_ref"].endswith(
        "/paper_facing_candidate_delta.json"
    )
    assert payload["output_manifest"]["owner_consumption_request_ref"].endswith(
        "/owner_consumption_request.json"
    )
    assert payload["output_manifest"]["owner_blocker_packet_ref"].endswith(
        "/owner_blocker_packet.json"
    )
    written_files = [Path(path) for path in payload["output_manifest"]["written_files"]]
    assert len(written_files) == 16
    assert all(path.is_file() for path in written_files)
    assert all(output_root in path.parents for path in written_files)
    package_manifest = json.loads(
        Path(payload["output_manifest"]["package_manifest_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_summary = json.loads(
        Path(payload["output_manifest"]["foreground_owner_decision_summary_ref"]).read_text(
            encoding="utf-8"
        )
    )
    mission_executor_handoff = json.loads(
        Path(payload["output_manifest"]["mission_executor_handoff_ref"]).read_text(
            encoding="utf-8"
        )
    )
    paper_facing_delta = json.loads(
        Path(payload["output_manifest"]["paper_facing_candidate_delta_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_consumption_request = json.loads(
        Path(payload["output_manifest"]["owner_consumption_request_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_blocker_packet = json.loads(
        Path(payload["output_manifest"]["owner_blocker_packet_ref"]).read_text(
            encoding="utf-8"
        )
    )
    candidate_manifest = json.loads(
        Path(payload["output_manifest"]["candidate_manifest_ref"]).read_text(
            encoding="utf-8"
        )
    )
    assert package_manifest["mode"] == "non_authority_candidate_package"
    assert package_manifest["milestone_kind"] == "submission_milestone_candidate"
    assert package_manifest["counts_as_paper_progress"] is True
    assert package_manifest["can_claim_submission_ready"] is False
    assert package_manifest["can_claim_publication_ready"] is False
    assert package_manifest["candidate_is_authority"] is False
    assert package_manifest["authority_materialized_by_this_package"] is False
    assert (
        package_manifest["artifact_refs"]["mission_executor_handoff"]
        == payload["output_manifest"]["mission_executor_handoff_ref"]
    )
    assert (
        package_manifest["artifact_refs"]["paper_facing_candidate_delta"]
        == payload["output_manifest"]["paper_facing_candidate_delta_ref"]
    )
    assert (
        package_manifest["artifact_refs"]["owner_consumption_request"]
        == payload["output_manifest"]["owner_consumption_request_ref"]
    )
    assert (
        package_manifest["artifact_refs"]["owner_blocker_packet"]
        == payload["output_manifest"]["owner_blocker_packet_ref"]
    )
    assert (
        package_manifest["artifact_refs"]["submission_milestone_checklist"]
        == payload["output_manifest"]["submission_milestone_checklist_ref"]
    )
    assert (
        "Yang output outside ops/medautoscience/paper_mission_candidate_package"
        in package_manifest["forbidden_authority_writes"]
    )
    assert (
        "Yang output outside ops/medautoscience/paper_mission_one_shot_migration"
        not in package_manifest["forbidden_authority_writes"]
    )
    assert owner_summary["candidate_is_authority"] is False
    assert owner_summary["governed_runtime_truth"] is False
    assert owner_summary["authority_materialized_by_this_packet"] is False
    assert (
        "Yang output outside ops/medautoscience/paper_mission_candidate_package"
        in owner_summary["forbidden_authority_writes"]
    )
    assert "remaining_owner_gap" in owner_summary
    assert mission_executor_handoff["surface_kind"] == "paper_mission_executor_handoff"
    assert mission_executor_handoff["status"] == "not_routed_to_mission_executor"
    assert mission_executor_handoff["next_owner"] == "analysis-campaign"
    assert mission_executor_handoff["authority_boundary"]["writes_authority"] is False
    assert mission_executor_handoff["authority_boundary"]["writes_runtime"] is False
    assert mission_executor_handoff["authority_boundary"]["writes_yang_authority"] is False
    assert (
        mission_executor_handoff["authority_boundary"]["can_claim_paper_progress"]
        is False
    )
    assert paper_facing_delta["surface_kind"] == (
        "paper_mission_paper_facing_candidate_delta"
    )
    assert paper_facing_delta["milestone_kind"] == "submission_milestone_candidate"
    assert paper_facing_delta["status"] == "submission_milestone_candidate_ready"
    assert paper_facing_delta["counts_as_paper_progress"] is True
    assert paper_facing_delta["candidate_is_authority"] is False
    assert paper_facing_delta["can_claim_submission_ready"] is False
    assert paper_facing_delta["can_claim_publication_ready"] is False
    assert paper_facing_delta["authority_boundary"]["writes_authority"] is False
    assert owner_consumption_request["surface_kind"] == (
        "paper_mission_owner_consumption_request"
    )
    assert owner_consumption_request["status"] == "owner_review_required"
    assert owner_consumption_request["request_kind"] == "owner_decision_consumption"
    assert owner_consumption_request["candidate_refs"][
        "paper_facing_candidate_delta"
    ] == payload["output_manifest"]["paper_facing_candidate_delta_ref"]
    assert owner_consumption_request["candidate_refs"]["owner_blocker_packet"] == (
        payload["output_manifest"]["owner_blocker_packet_ref"]
    )
    assert owner_consumption_request["accepted_owner_answer_shapes"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert owner_consumption_request["authority_boundary"]["writes_authority"] is False
    assert owner_consumption_request["authority_boundary"]["writes_runtime"] is False
    assert owner_consumption_request["authority_boundary"][
        "can_claim_paper_progress"
    ] is False
    assert owner_consumption_request["counts_as_paper_progress"] is False
    assert owner_blocker_packet["surface_kind"] == "paper_mission_owner_blocker_packet"
    assert owner_blocker_packet["status"] == "context_only"
    assert owner_blocker_packet["candidate_is_authority"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_typed_blocker"] is False
    assert set(payload["output_manifest"]["paper_facing_artifact_refs"]) == {
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    }
    assert set(paper_facing_delta["paper_facing_artifact_refs"]) == set(
        payload["output_manifest"]["paper_facing_artifact_refs"]
    )
    assert all(
        Path(path).exists()
        for path in payload["output_manifest"]["paper_facing_artifact_refs"].values()
    )
    assert (
        payload["output_manifest"]["paper_facing_candidate_delta_ref"]
        in candidate_manifest["candidate_artifact_refs"]
    )
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_package_candidate_materializes_route_back_executor_handoff(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    _write_paper_source_fixture(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624T0115Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::route-back"
    route_back_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
    )
    route_back_transaction["stage_terminal_decision"][
        "route_back_evidence_ref"
    ] = "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Repair DM002 claim/evidence gaps after terminal owner gate.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::route-back-repair",
                "artifact_ref": "mission://dm002/route-back-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": route_back_transaction[
                "stage_terminal_decision"
            ],
            "opl_route_command": route_back_transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
        },
        "paper_mission_transaction": route_back_transaction,
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-route-back",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260624T0116Z"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "package-candidate",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--output-root",
            str(output_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    output_manifest = payload["output_manifest"]
    assert len(output_manifest["written_files"]) == 16
    assert output_manifest["writes_authority"] is False
    assert output_manifest["writes_runtime"] is False
    assert output_manifest["writes_yang_authority"] is False
    assert output_manifest["written_files"]
    handoff = json.loads(
        Path(output_manifest["mission_executor_handoff_ref"]).read_text(
            encoding="utf-8"
        )
    )
    paper_facing_delta = json.loads(
        Path(output_manifest["paper_facing_candidate_delta_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_consumption_request = json.loads(
        Path(output_manifest["owner_consumption_request_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_blocker_packet = json.loads(
        Path(output_manifest["owner_blocker_packet_ref"]).read_text(encoding="utf-8")
    )
    submission_milestone_checklist = json.loads(
        Path(output_manifest["submission_milestone_checklist_ref"]).read_text(
            encoding="utf-8"
        )
    )
    candidate_manifest = json.loads(
        Path(output_manifest["candidate_manifest_ref"]).read_text(encoding="utf-8")
    )
    package_manifest = json.loads(
        Path(output_manifest["package_manifest_ref"]).read_text(encoding="utf-8")
    )
    assert payload["mission_executor_handoff"] == handoff
    assert payload["owner_consumption_request"] == owner_consumption_request
    assert payload["owner_blocker_packet"] == owner_blocker_packet
    assert package_manifest["mission_executor_materialized"] is True
    assert package_manifest["candidate_content_kind"] == (
        "concrete_non_authority_paper_delta"
    )
    assert any(
        ref.endswith("/paper/draft.md")
        for ref in package_manifest["source_document_refs"]
    )
    assert handoff["surface_kind"] == "paper_mission_executor_handoff"
    assert handoff["status"] == "ready_for_mission_executor"
    assert handoff["next_owner"] == "mission_executor"
    assert handoff["route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert handoff["repair_scope"] == "claim-evidence-repair"
    assert handoff["target_stage_id"] == "paper-stage::gate-clearing"
    assert handoff["current_terminal_decision"]["decision_kind"] == "route_back"
    assert handoff["current_terminal_decision"]["route_command"] == "route_back"
    assert [
        item["kind"] for item in handoff["expected_paper_facing_outputs"]
    ] == [
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    ]
    assert handoff["authority_boundary"]["writes_authority"] is False
    assert handoff["authority_boundary"]["writes_runtime"] is False
    assert handoff["authority_boundary"]["writes_yang_authority"] is False
    assert handoff["authority_boundary"]["writes_paper_body"] is False
    assert handoff["authority_boundary"]["can_claim_paper_progress"] is False
    assert "owner receipt" in handoff["forbidden_authority_writes"]
    assert payload["paper_facing_candidate_delta"] == paper_facing_delta
    assert paper_facing_delta["surface_kind"] == (
        "paper_mission_paper_facing_candidate_delta"
    )
    assert paper_facing_delta["milestone_kind"] == "submission_milestone_candidate"
    assert paper_facing_delta["status"] == "submission_milestone_candidate_ready"
    assert paper_facing_delta["counts_as_paper_progress"] is True
    assert paper_facing_delta["candidate_is_authority"] is False
    assert paper_facing_delta["mission_executor_materialized"] is True
    assert paper_facing_delta["candidate_content_kind"] == (
        "concrete_non_authority_paper_delta"
    )
    assert any(
        ref.endswith("/paper/claim_evidence_map.json")
        for ref in paper_facing_delta["source_document_refs"]
    )
    assert paper_facing_delta["paper_source_snapshot"]["source_snapshot_complete"] is False
    assert paper_facing_delta["can_claim_submission_ready"] is False
    assert paper_facing_delta["can_claim_publication_ready"] is False
    assert paper_facing_delta["route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert [item["kind"] for item in paper_facing_delta["paper_facing_outputs"]] == [
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    ]
    assert all(
        item["status"] == "candidate_required"
        for item in paper_facing_delta["paper_facing_outputs"]
    )
    assert paper_facing_delta["authority_boundary"]["writes_paper_body"] is False
    assert paper_facing_delta["authority_boundary"]["can_claim_paper_progress"] is False
    assert owner_consumption_request["status"] == "ready_for_mas_authority_consume"
    assert owner_consumption_request["request_kind"] == (
        "route_back_candidate_delta_consumption"
    )
    assert owner_consumption_request["next_owner"] == "mission_executor"
    assert "mission_executor:" in owner_consumption_request["owner_question"]
    assert "route_back_without_blocker" in owner_consumption_request["owner_question"]
    assert owner_consumption_request["next_legal_action"] == (
        "consume_candidate_or_return_owner_answer_shape"
    )
    assert (
        output_manifest["package_manifest_ref"]
        in owner_consumption_request["next_legal_command"]["argv_template"]
    )
    assert owner_consumption_request["requested_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert owner_consumption_request["evidence_refs"]["route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert owner_consumption_request["candidate_refs"]["mission_executor_handoff"] == (
        output_manifest["mission_executor_handoff_ref"]
    )
    assert owner_consumption_request["candidate_refs"][
        "paper_facing_candidate_delta"
    ] == output_manifest["paper_facing_candidate_delta_ref"]
    assert owner_consumption_request["candidate_refs"]["owner_blocker_packet"] == (
        output_manifest["owner_blocker_packet_ref"]
    )
    assert owner_consumption_request["authority_boundary"]["writes_authority"] is False
    assert owner_consumption_request["authority_boundary"]["writes_runtime"] is False
    assert owner_consumption_request["authority_boundary"]["writes_paper_body"] is False
    assert owner_consumption_request["authority_boundary"][
        "can_claim_paper_progress"
    ] is False
    assert owner_blocker_packet["status"] == "context_only"
    assert owner_blocker_packet["blocker_kind"] == "route_back_without_blocker"
    assert "mission_executor:" in owner_blocker_packet["owner_question"]
    assert owner_blocker_packet["next_legal_action"] == (
        "consume_candidate_or_return_owner_answer_shape"
    )
    assert (
        output_manifest["package_manifest_ref"]
        in owner_blocker_packet["next_legal_command"]["argv_template"]
    )
    assert owner_blocker_packet["requested_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert owner_blocker_packet["evidence_refs"]["route_back_evidence_ref"] == (
        "route-back:paper-mission-terminal-owner-gate:dm002:abc123"
    )
    assert owner_blocker_packet["terminal_owner_gate_materialized"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_owner_receipt"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_typed_blocker"] is False
    assert (
        submission_milestone_checklist["milestone_kind"]
        == "submission_milestone_candidate"
    )
    assert submission_milestone_checklist["counts_as_paper_progress"] is True
    assert submission_milestone_checklist["candidate_is_authority"] is False
    assert {
        item["item_id"]: item["status"]
        for item in submission_milestone_checklist["mas_automatable_items"]
    }["manuscript_patch_plan"] == "candidate_included"
    assert set(output_manifest["paper_facing_artifact_refs"]) == {
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    }
    assert paper_facing_delta["paper_facing_artifact_refs"] == output_manifest[
        "paper_facing_artifact_refs"
    ]
    manuscript_patch_plan = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["manuscript_patch_plan"]).read_text(
            encoding="utf-8"
        )
    )
    claim_evidence_delta = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["claim_evidence_ledger_delta"]).read_text(
            encoding="utf-8"
        )
    )
    figure_table_delta = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["figure_table_caption_delta"]).read_text(
            encoding="utf-8"
        )
    )
    reviewer_response = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["reviewer_gate_response_draft"]).read_text(
            encoding="utf-8"
        )
    )
    owner_decision_artifact = json.loads(
        Path(output_manifest["paper_facing_artifact_refs"]["owner_decision_packet"]).read_text(
            encoding="utf-8"
        )
    )
    assert manuscript_patch_plan["surface_kind"] == (
        "paper_mission_manuscript_patch_plan"
    )
    assert manuscript_patch_plan["candidate_content"]["patch_targets"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
    ]
    assert manuscript_patch_plan["mission_executor_materialized"] is True
    assert manuscript_patch_plan["candidate_content_kind"] == (
        "concrete_non_authority_paper_delta"
    )
    assert manuscript_patch_plan["candidate_content"]["source_headings"][0][
        "headings"
    ][0]["text"] == "DM paper draft"
    assert manuscript_patch_plan["candidate_content"]["candidate_patch_operations"][0][
        "target_heading"
    ]["text"] == "Results"
    assert manuscript_patch_plan["authority_boundary"]["writes_paper_body"] is False
    assert manuscript_patch_plan["milestone_kind"] == "submission_milestone_candidate"
    assert manuscript_patch_plan["counts_as_paper_progress"] is True
    assert manuscript_patch_plan["candidate_is_authority"] is False
    assert manuscript_patch_plan["authority_materialized"] is False
    assert manuscript_patch_plan["can_claim_submission_ready"] is False
    assert claim_evidence_delta["surface_kind"] == (
        "paper_mission_claim_evidence_ledger_delta"
    )
    assert claim_evidence_delta["candidate_content"]["delta_targets"] == [
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
    ]
    assert claim_evidence_delta["candidate_content"]["claim_evidence_rows"][0][
        "candidate_row"
    ]["claim_id"] == "claim-primary"
    assert claim_evidence_delta["candidate_content"]["source_claim_count"] == 1
    assert claim_evidence_delta["candidate_content"]["source_evidence_count"] == 1
    assert claim_evidence_delta["authority_boundary"]["writes_authority"] is False
    assert claim_evidence_delta["counts_as_paper_progress"] is True
    assert figure_table_delta["candidate_content"]["table_candidates"][0][
        "candidate_ref"
    ]["table_id"] == "T1"
    assert figure_table_delta["candidate_content"]["figure_candidates"][0][
        "candidate_ref"
    ]["figure_id"] == "F1"
    assert reviewer_response["candidate_content"]["response_draft_items"][0][
        "review_item"
    ]["id"] == "gate-1"
    assert owner_decision_artifact["candidate_content"]["owner_ballot"][
        "recommended_owner"
    ] == "MAS authority consume path"
    assert (
        output_manifest["paper_facing_candidate_delta_ref"]
        in candidate_manifest["candidate_artifact_refs"]
    )
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_package_candidate_materializes_typed_blocker_owner_packet(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    migration_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624T0200Z"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--one-shot-migration",
            "--study-progress-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dm003_progress.json"),
            "--domain-health-diagnostic-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dhd_dry_run.json"),
            "--output-root",
            str(migration_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    package_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260624T0201Z"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "package-candidate",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--output-root",
            str(package_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["consume_candidate_status"] == "typed_blocker"
    output_manifest = payload["output_manifest"]
    assert len(output_manifest["written_files"]) == 16
    assert output_manifest["writes_authority"] is False
    assert output_manifest["writes_runtime"] is False
    assert output_manifest["writes_yang_authority"] is False
    owner_consumption_request = json.loads(
        Path(output_manifest["owner_consumption_request_ref"]).read_text(
            encoding="utf-8"
        )
    )
    owner_blocker_packet = json.loads(
        Path(output_manifest["owner_blocker_packet_ref"]).read_text(encoding="utf-8")
    )
    submission_milestone_checklist = json.loads(
        Path(output_manifest["submission_milestone_checklist_ref"]).read_text(
            encoding="utf-8"
        )
    )
    paper_facing_delta = json.loads(
        Path(output_manifest["paper_facing_candidate_delta_ref"]).read_text(
            encoding="utf-8"
        )
    )
    assert payload["owner_consumption_request"] == owner_consumption_request
    assert payload["owner_blocker_packet"] == owner_blocker_packet
    assert payload["paper_facing_candidate_delta"] == paper_facing_delta
    assert paper_facing_delta["milestone_kind"] == "submission_milestone_candidate"
    assert (
        paper_facing_delta["status"]
        == "submission_milestone_candidate_ready_with_owner_blocker_context"
    )
    assert paper_facing_delta["counts_as_paper_progress"] is True
    assert paper_facing_delta["candidate_is_authority"] is False
    assert paper_facing_delta["can_claim_submission_ready"] is False
    assert paper_facing_delta["can_claim_publication_ready"] is False
    assert (
        submission_milestone_checklist["milestone_kind"]
        == "submission_milestone_candidate"
    )
    assert (
        submission_milestone_checklist["status"]
        == "candidate_ready_with_owner_blocker_context"
    )
    assert submission_milestone_checklist["counts_as_paper_progress"] is True
    assert submission_milestone_checklist["authority_materialized"] is False
    assert set(output_manifest["paper_facing_artifact_refs"]) == {
        "manuscript_patch_plan",
        "claim_evidence_ledger_delta",
        "figure_table_caption_delta",
        "reviewer_gate_response_draft",
        "owner_decision_packet",
    }
    assert owner_consumption_request["status"] == "owner_blocker_packet_required"
    assert owner_consumption_request["request_kind"] == "owner_blocker_resolution"
    assert owner_consumption_request["next_owner"] == "one-person-lab"
    assert "one-person-lab:" in owner_consumption_request["owner_question"]
    assert owner_consumption_request["next_legal_action"] == (
        "provide_opl_terminal_readback_or_governed_owner_answer"
    )
    assert (
        output_manifest["package_manifest_ref"]
        in owner_consumption_request["next_legal_command"]["argv_template"]
    )
    assert owner_consumption_request["requested_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert owner_consumption_request["candidate_refs"]["owner_blocker_packet"] == (
        output_manifest["owner_blocker_packet_ref"]
    )
    assert owner_consumption_request["authority_boundary"]["writes_authority"] is False
    assert owner_consumption_request["authority_boundary"]["writes_runtime"] is False
    assert owner_consumption_request["authority_boundary"]["writes_paper_body"] is False
    assert owner_consumption_request["authority_boundary"][
        "can_claim_paper_progress"
    ] is False
    assert owner_blocker_packet["surface_kind"] == "paper_mission_owner_blocker_packet"
    assert owner_blocker_packet["status"] == "owner_blocker_candidate_ready"
    assert owner_blocker_packet["blocker_kind"] == "missing_opl_runtime_readback"
    assert "one-person-lab:" in owner_blocker_packet["owner_question"]
    assert owner_blocker_packet["next_legal_action"] == (
        "provide_opl_terminal_readback_or_governed_owner_answer"
    )
    assert (
        output_manifest["package_manifest_ref"]
        in owner_blocker_packet["next_legal_command"]["argv_template"]
    )
    assert owner_blocker_packet["requested_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert owner_blocker_packet["current_terminal_decision"]["decision_kind"] == (
        "typed_blocker"
    )
    assert owner_blocker_packet["current_terminal_decision"]["route_command"] == (
        "stop_with_typed_blocker"
    )
    assert owner_blocker_packet["terminal_owner_gate_materialized"] is False
    assert owner_blocker_packet["typed_blocker_authority_materialized"] is False
    assert owner_blocker_packet["human_gate_materialized"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_owner_receipt"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_typed_blocker"] is False
    assert owner_blocker_packet["authority_boundary"]["can_write_human_gate"] is False
    assert owner_blocker_packet["authority_boundary"]["can_claim_paper_progress"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_domain_handler_dispatch_accepts_paper_mission_dry_run_without_authority_writes(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    task_path = tmp_path / "paper-mission-task.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "paper-mission-001",
                "domain_id": "medautoscience",
                "task_kind": "paper_mission/start_or_resume",
                "action_intent": "paper_mission/start_or_resume",
                "payload": {
                    "profile": str(profile_path),
                    "study_id": "001-paper",
                    "paper_mission_command": "start",
                    "objective": "gate clearing",
                    "dry_run": True,
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["task_kind"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["action_intent"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["execution_policy"] == "paper_mission_no_write_dry_run"
    assert payload["dispatch"]["result"]["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path)


def test_domain_handler_dispatch_drives_default_paper_mission_without_authority_writes(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624Tdispatch"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::dispatch"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Dispatch default paper mission into submission milestone packaging.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
        },
        "paper_mission_transaction": transaction,
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-dispatch",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )
    task_path = tmp_path / "paper-mission-default-task.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "paper-mission-start-or-resume::dm002",
                "domain_id": "medautoscience",
                "task_kind": "paper_mission/start_or_resume",
                "action_intent": "paper_mission/start_or_resume",
                "payload": {
                    "profile": str(profile_path),
                    "study_id": study_id,
                    "paper_mission_command": "start",
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        ["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_intent"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["execution_policy"] == (
        "paper_mission_drive_non_authority_candidate_and_ledger"
    )
    result = payload["dispatch"]["result"]
    assert result["surface_kind"] == "paper_mission_drive_readback"
    assert result["paper_mission_command"] == "drive"
    assert result["consume_candidate_status"] == "accepted_candidate"
    assert result["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert result["opl_route_command"]["command_kind"] == "resume_stage"
    assert result["drive_result"]["status"] == "opl_runtime_submission_failed"
    assert result["drive_result"]["opl_runtime_submission_status"] == "not_configured"
    assert result["mutation_policy"]["writes_authority"] is False
    assert result["mutation_policy"]["writes_runtime"] is False
    assert result["mutation_policy"]["writes_yang_authority"] is False
    package_manifest = result["candidate_package_readback"]["output_manifest"]
    consume_manifest = result["consume_readback"]["consume_output_manifest"]
    assert package_manifest["mode"] == "non_authority_candidate_package"
    assert consume_manifest["mode"] == "governed_consume_record"
    assert Path(package_manifest["package_manifest_ref"]).exists()
    assert Path(consume_manifest["opl_route_handoff_ref"]).exists()
    assert str(workspace_root / "ops" / "medautoscience") in result["output_root"]
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_start_reads_materialized_one_shot_mission_when_present(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260623T2032Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": f"paper-mission::{study_id}::gate-clearing::one-shot-migration",
        "study_id": study_id,
        "objective": "Consume DM002 publication blockers and repair claim/evidence gaps.",
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::claim-evidence-repair",
                "artifact_ref": "mission://dm002/claim-evidence-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "route_back"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "route_back",
        },
    }
    mission_payload["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission_id=mission_payload["mission_id"],
        study_id=study_id,
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps({"candidate_id": "pmc-dm002"}),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "start",
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["paper_mission_run"]["mission_id"] == mission_payload["mission_id"]
    assert payload["paper_mission_run"]["mission_state"] == (
        "candidate_ready_for_consumption"
    )
    assert payload["default_readback"]["current_mission"]["objective_kind"] == (
        "gate_clearing_claim_evidence_repair"
    )
    assert payload["consume_candidate_status"] == "route_back"
    assert payload["transaction_state"] == "terminal_decision_recorded"
    assert payload["stage_terminal_decision"] == (
        mission_payload["paper_mission_transaction"]["stage_terminal_decision"]
    )
    assert payload["opl_route_command"] == (
        mission_payload["paper_mission_transaction"]["opl_route_command"]
    )
    assert payload["opl_runtime_carrier"]["paper_mission_transaction_ref"] == (
        mission_payload["paper_mission_transaction"]["transaction_id"]
    )
    assert payload["opl_runtime_carrier"]["opl_route_command"] == payload[
        "opl_route_command"
    ]
    assert payload["opl_runtime_carrier"]["can_write_opl_stage_run"] is False
    assert payload["dispatch_plan"]["domain_handler_dispatch_mode"] == (
        "materialized_mission_readback_no_write"
    )
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_start_reads_materialized_mission_for_dm_alias(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    canonical_study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=canonical_study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260623T2032Z"
        / canonical_study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": (
            f"paper-mission::{canonical_study_id}::gate-clearing::one-shot-migration"
        ),
        "study_id": canonical_study_id,
        "objective": "Consume DM002 publication blockers and repair claim/evidence gaps.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::claim-evidence-repair",
                "artifact_ref": "mission://dm002/claim-evidence-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate_consumed",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "start",
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "DM002",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["requested_study_id"] == "DM002"
    assert payload["study_id"] == canonical_study_id
    assert payload["study_root"].endswith(f"/studies/{canonical_study_id}")
    assert payload["study_root_exists"] is True
    assert payload["paper_mission_run"]["mission_id"] == mission_payload["mission_id"]
    assert payload["consume_candidate_status"] == "accepted"
    assert payload["dispatch_plan"]["domain_handler_dispatch_mode"] == (
        "materialized_mission_readback_no_write"
    )
    _assert_forbidden_authority_untouched(tmp_path, study_id=canonical_study_id)


def test_paper_mission_materialized_legacy_run_without_transaction_terminalizes_consume_result(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "legacy"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": f"paper-mission::{study_id}::legacy::one-shot-migration",
        "study_id": study_id,
        "objective": "Legacy materialized mission without a transaction field.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::legacy",
                "artifact_ref": "mission://legacy/artifact-delta",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate_consumed",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["paper_mission_transaction"]["transaction_id"].startswith(
        f"paper-mission-transaction::{study_id}::gate_clearing_claim_evidence_repair"
    )
    assert payload["transaction_state"] == "accepted"
    assert payload["stage_terminal_decision"]["decision_kind"] == "advance"
    assert payload["stage_terminal_decision"]["next_stage_id"] == (
        "publication_gate_replay"
    )
    assert payload["opl_route_command"]["command_kind"] == "start_next_stage"
    assert payload["opl_route_command"]["target"] == "publication_gate_replay"
    assert payload["opl_runtime_carrier"]["surface_kind"] == (
        "mas_domain_progress_transition_request"
    )
    assert payload["opl_runtime_carrier"]["carrier_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )
    assert payload["opl_runtime_carrier"]["can_claim_provider_running"] is False
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "materialized_paper_mission_run"
    )
    assert payload["paper_mission_transaction_readback"]["validation"]["status"] == (
        "validated"
    )
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["paper_mission_run"]["paper_audit_pack"]
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_materialized_readback_consumes_matching_opl_terminal_closeout(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    mission_root.mkdir(parents=True)
    transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::gate-clearing::one-shot-migration",
        study_id=study_id,
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": transaction["mission_id"],
        "study_id": study_id,
        "objective": "Accepted paper mission waiting for OPL closeout readback.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::one-shot",
                "artifact_ref": "mission://dm002/owner-decision",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate_consumed",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": "mission://dm002/import-pack",
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "paper_mission_transaction": transaction,
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    _write_matching_domain_gate_closeout(
        study_root=study_root,
        study_id=study_id,
        transaction=transaction,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["opl_runtime_carrier"]["carrier_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )
    assert payload["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )
    carrier_readback = payload["opl_runtime_carrier_readback"]
    assert carrier_readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert carrier_readback["domain_ready_verdict"] == "domain_gate_pending"
    assert carrier_readback["can_claim_paper_progress"] is False
    assert carrier_readback["provider_completion_is_domain_completion"] is False
    assert carrier_readback["provider_completion_is_domain_ready"] is False
    assert carrier_readback["authority_materialized"] is False
    assert carrier_readback["terminal_closeout"]["stage_attempt_id"] == "sat-terminal"
    assert carrier_readback["terminal_closeout"]["closeout_ref"] == (
        "artifacts/supervision/consumer/default_executor_execution/"
        "sat-terminal.closeout.json"
    )
    assert payload["terminal_owner_gate"] == {
        "surface_kind": "paper_mission_terminal_owner_gate",
        "owner": "mas_authority_kernel",
        "gate_kind": "domain_gate",
        "blocked_reason": "domain_gate_pending",
        "typed_blocker_ref": (
            "artifacts/supervision/consumer/default_executor_execution/"
            "sat-terminal.closeout.json#domain_blocker"
        ),
        "closeout_ref": (
            "artifacts/supervision/consumer/default_executor_execution/"
            "sat-terminal.closeout.json"
        ),
        "stage_attempt_id": "sat-terminal",
        "work_unit_id": "paper-stage::gate-clearing",
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "legal_next_action": "route_to_owner_or_human_gate",
    }
    assert payload["next_owner_or_human_decision"] == {
        "kind": "owner_or_route",
        "next_owner": "mission_executor",
        "human_decision_required": False,
        "summary": "route_back",
        "route_back_evidence_ref": payload[
            "terminal_owner_gate_owner_answer_readback"
        ]["route_back_evidence_ref"],
        "opl_route_command_ref": payload[
            "terminal_owner_gate_owner_answer_readback"
        ]["opl_route_command"]["source_terminal_decision_ref"],
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }
    authority_readback = payload["terminal_owner_gate_authority_readback"]
    assert authority_readback["surface_kind"] == (
        "mas_terminal_owner_gate_authority_readback"
    )
    assert authority_readback["status"] == "route_back"
    assert authority_readback["next_owner"] == "mas_authority_kernel"
    assert authority_readback["owner_answer_materialized"] is True
    assert authority_readback["consume_result"]["status"] == "route_back"
    assert authority_readback["consume_result"]["outcome"] == "route_back_evidence_ref"
    assert authority_readback["consume_result"]["authority_materialized"] is False
    assert authority_readback["consume_result"][
        "authority_answer_readback_materialized"
    ] is True
    assert authority_readback["consume_result"]["authority_file_materialized"] is False
    assert authority_readback["route_back_evidence_ref"].startswith(
        f"route-back:paper-mission-terminal-owner-gate:{study_id}:"
    )
    owner_answer = payload["terminal_owner_gate_owner_answer_readback"]
    assert owner_answer["surface_kind"] == (
        "mas_terminal_owner_gate_owner_answer_readback"
    )
    assert owner_answer["status"] == "route_back"
    assert owner_answer["owner_answer_shape"] == "route_back_evidence_ref"
    assert owner_answer["authority_materialized"] is False
    assert owner_answer["authority_answer_readback_materialized"] is True
    assert owner_answer["authority_file_materialized"] is False
    assert owner_answer["can_claim_paper_progress"] is False
    assert owner_answer["can_claim_runtime_ready"] is False
    assert owner_answer["write_plan"]["written_files"] == []
    assert owner_answer["write_plan"]["can_write_owner_receipts"] is False
    assert owner_answer["write_plan"]["can_write_typed_blockers"] is False
    assert owner_answer["write_plan"]["can_write_human_gate_authority_records"] is False
    assert owner_answer["stage_terminal_decision"]["decision_kind"] == "route_back"
    assert owner_answer["opl_route_command"]["command_kind"] == "route_back"
    assert payload["stage_terminal_decision"] == owner_answer["stage_terminal_decision"]
    assert payload["opl_route_command"] == owner_answer["opl_route_command"]
    assert payload["paper_mission_transaction"] == owner_answer["paper_mission_transaction"]
    assert payload["transaction_state"] == "route_back"
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "terminal_owner_gate_owner_answer"
    )
    assert authority_readback["owner_answer_contract"]["accepted_shapes"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert authority_readback["owner_answer_contract"]["typed_blocker_ref"] == (
        "artifacts/supervision/consumer/default_executor_execution/"
        "sat-terminal.closeout.json#domain_blocker"
    )
    assert authority_readback["authority_boundary"]["can_claim_paper_progress"] is False
    assert authority_readback["authority_boundary"][
        "can_authorize_provider_admission"
    ] is False
    assert authority_readback["write_plan"]["written_files"] == []
    assert payload["paper_mission_transaction_readback"][
        "terminal_owner_gate_authority_readback"
    ] == authority_readback
    assert payload["paper_mission_transaction_readback"][
        "terminal_owner_gate_owner_answer_readback"
    ] == owner_answer
    assert payload["paper_mission_transaction_readback"]["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_materialized_readback_keeps_governed_consumption_current_when_terminal_residue_exists(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = (
        f"paper-mission::{study_id}::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    old_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="typed_blocker",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Older typed blocker mission with terminal residue.",
        "mission_state": "stable_blocker",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm003::one-shot",
                "artifact_ref": "mission://dm003/prose-repair-owner-decision",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": "mission://dm003/import-pack",
            }
        ],
        "authority_touchpoints": [],
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "consume_result": {"status": "typed_blocker"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "paper_mission_transaction": old_transaction,
        "one_shot_migration_readback": {
            "required_output": {
                "next_owner": "one-person-lab",
                "work_unit_id": "analysis_claim_evidence_repair",
            },
            "consume_candidate_status": "typed_blocker",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=old_transaction,
    )

    consume_exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_consumption_ledger"
                / "sat-current"
            ),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert consume_exit_code == 0
    consume_payload = json.loads(capsys.readouterr().out)
    current_transaction = consume_payload["paper_mission_transaction_readback"][
        "paper_mission_transaction"
    ]
    _write_matching_domain_gate_closeout(
        study_root=study_root,
        study_id=study_id,
        transaction=current_transaction,
    )

    inspect_exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    inspect_payload = json.loads(capsys.readouterr().out)

    assert inspect_exit_code == 0
    assert inspect_payload["mission_state"] == "consumed"
    assert inspect_payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert inspect_payload["paper_mission_current_transaction_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert inspect_payload["paper_mission_run"]["consume_result"]["status"] == (
        "accepted"
    )
    assert inspect_payload["paper_mission_run"]["consume_result"]["outcome"] == (
        "accepted_submission_milestone_candidate"
    )
    assert inspect_payload["stage_terminal_decision"]["decision_kind"] == (
        "continue_same_stage"
    )
    assert inspect_payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert inspect_payload["paper_mission_transaction"]["stage_id"] == (
        "submission_milestone_candidate"
    )
    assert inspect_payload["paper_mission_transaction_readback"]["source"] == (
        "paper_mission_consumption_ledger"
    )
    assert inspect_payload["next_owner_or_human_decision"]["next_owner"] == (
        "mission_executor"
    )
    assert inspect_payload["next_owner_or_human_decision"]["route_command"] == (
        "resume_stage"
    )
    terminal_gate = inspect_payload["terminal_owner_gate"]
    assert terminal_gate["owner"] == "mas_authority_kernel"
    assert terminal_gate["gate_kind"] == "domain_gate"
    assert terminal_gate["can_claim_paper_progress"] is False
    assert terminal_gate["can_claim_runtime_ready"] is False
    authority_readback = inspect_payload["terminal_owner_gate_authority_readback"]
    assert authority_readback["status"] == "route_back"
    assert authority_readback["selected_outcome"] == "route_back_evidence_ref"
    assert authority_readback["owner_answer_materialized"] is True
    assert authority_readback["authority_boundary"]["can_claim_paper_progress"] is False
    owner_answer = inspect_payload["terminal_owner_gate_owner_answer_readback"]
    assert owner_answer["owner_answer_shape"] == "route_back_evidence_ref"
    assert owner_answer["can_claim_paper_progress"] is False
    assert owner_answer["can_claim_runtime_ready"] is False
    assert owner_answer["write_plan"]["written_files"] == []
    assert owner_answer["stage_terminal_decision"]["decision_kind"] == "route_back"
    assert inspect_payload["paper_mission_transaction_readback"][
        "terminal_owner_gate_owner_answer_readback"
    ] == owner_answer
    assert inspect_payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_uses_authority_consume_readback(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    candidate_path = _write_candidate_manifest(tmp_path)

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["paper_mission_command"] == "consume-candidate"
    assert payload["action_intent"] == "paper_mission/consume_candidate"
    assert payload["authority_consume_readback"]["status"] == "accepted_candidate"
    assert payload["authority_consume_readback"]["consume_result"]["status"] == "accepted"
    assert (
        payload["paper_mission_run_candidate"]["consume_result"]
        == payload["authority_consume_readback"]["consume_result"]
    )
    assert payload["paper_mission_run_candidate"]["mission_state"] == "consumed"
    assert payload["paper_mission_run_candidate"]["artifact_delta_ledger"][0]["status"] == (
        "candidate_consumed"
    )
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["authority_consume_readback"]["write_plan"]["written_files"] == []
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_consume_candidate_accepts_submission_package_manifest(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    mission_id = f"paper-mission::{study_id}::gate-clearing::route-back"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    package_root = tmp_path / "candidate-package" / study_id
    package_root.mkdir(parents=True)
    candidate_manifest = {
        "candidate_id": "paper-mission-candidate::dm002::submission",
        "mission_id": mission_id,
        "study_id": study_id,
        "requested_outcome": "accepted_candidate",
        "candidate_manifest_ref": str(package_root / "candidate_manifest.json"),
        "candidate_artifact_refs": [
            str(package_root / "paper_facing_candidate_delta.json"),
        ],
        "source_readiness_refs": ["source-readiness:dm002"],
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": "mission_executor",
        "resume_condition": "MAS consumes or routes back the milestone package",
        "paper_mission_transaction": transaction,
    }
    (package_root / "candidate_manifest.json").write_text(
        json.dumps(candidate_manifest),
        encoding="utf-8",
    )
    package_manifest = {
        "surface_kind": "paper_mission_foreground_candidate_package_manifest",
        "schema_version": 1,
        "mode": "non_authority_candidate_package",
        "milestone_kind": "submission_milestone_candidate",
        "study_id": study_id,
        "mission_id": mission_id,
        "counts_as_paper_progress": True,
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "artifact_refs": {
            "candidate_manifest": str(package_root / "candidate_manifest.json"),
            "paper_facing_candidate_delta": str(
                package_root / "paper_facing_candidate_delta.json"
            ),
            "owner_decision_packet": str(package_root / "owner_decision_packet.json"),
        },
        "paper_facing_candidate_delta_ref": str(
            package_root / "paper_facing_candidate_delta.json"
        ),
        "owner_consumption_request_ref": str(
            package_root / "owner_consumption_request.json"
        ),
        "owner_blocker_packet_ref": str(package_root / "owner_blocker_packet.json"),
        "forbidden_authority_writes": ["owner receipt", "typed blocker"],
        "forbidden_authority_claims": ["submission_ready"],
    }
    package_manifest_path = package_root / "package_manifest.json"
    package_manifest_path.write_text(json.dumps(package_manifest), encoding="utf-8")
    output_root = tmp_path / "consumption-ledger"

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_manifest_path),
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["authority_consume_readback"]["status"] == "accepted_candidate"
    assert payload["authority_consume_readback"]["candidate_id"] == (
        "paper-mission-candidate::dm002::submission"
    )
    assert payload["authority_consume_readback"]["candidate_manifest_input"][
        "resolved_manifest_ref"
    ] == str(package_root / "candidate_manifest.json")
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "candidate_manifest"
    )
    assert payload["transaction_state"] == "terminal_decision_recorded"
    assert payload["opl_route_command"]["command_kind"] == "route_back"
    assert payload["consume_output_manifest"]["mode"] == "governed_consume_record"
    assert payload["consume_output_manifest"]["route_command_kind"] == "route_back"
    assert payload["consume_output_manifest"]["writes_authority"] is False
    assert payload["consume_output_manifest"]["writes_runtime"] is False
    assert payload["consume_output_manifest"]["writes_yang_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_reports_repeated_route_back_as_non_advancing(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::gate-clearing::route-back"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=transaction,
        requested_outcome="route_back",
    )

    for ledger_id in ("repeat-first", "repeat-second"):
        exit_code = cli.main(
            [
                "paper-mission",
                "consume-candidate",
                "--candidate",
                str(package_path),
                "--output-root",
                str(
                    workspace_root
                    / "ops"
                    / "medautoscience"
                    / "paper_mission_consumption_ledger"
                    / ledger_id
                ),
                "--profile",
                str(profile_path),
                "--study-id",
                study_id,
                "--format",
                "json",
            ]
        )
        assert exit_code == 0
        payload = json.loads(capsys.readouterr().out)

    guard = payload["semantic_progress_guard"]
    assert guard["status"] == "non_advancing_route_back"
    assert guard["required_executor_delta_present"] is False
    assert guard["semantic_progress_observed"] is False
    assert payload["non_advancing_route_back"] == guard
    assert payload["requires_mas_owned_executor_delta"] is True
    assert guard["next_legal_actions"] == [
        "owner_decision_packet",
        "human_gate_question",
        "paper_facing_delta",
        "typed_blocker_materialization",
    ]
    assert guard["can_claim_paper_progress"] is False
    assert guard["can_claim_submission_ready"] is False
    assert payload["authority_consume_readback"]["status"] == "route_back"
    assert payload["consume_candidate_status"] == "route_back"
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_auto_discovers_latest_package_manifest(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    package_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260624T0200Z"
        / study_id
    )
    package_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::prose-repair::manual"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="typed_blocker",
    )
    candidate_manifest = {
        "candidate_id": "paper-mission-candidate::dm003::submission",
        "mission_id": mission_id,
        "study_id": study_id,
        "requested_outcome": "accepted_candidate",
        "candidate_manifest_ref": str(package_root / "candidate_manifest.json"),
        "candidate_artifact_refs": [
            str(package_root / "paper_facing_candidate_delta.json"),
        ],
        "source_readiness_refs": ["source-readiness:dm003"],
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": "one-person-lab",
        "resume_condition": "MAS consumes or routes the milestone package",
        "paper_mission_transaction": transaction,
    }
    (package_root / "candidate_manifest.json").write_text(
        json.dumps(candidate_manifest),
        encoding="utf-8",
    )
    package_manifest = {
        "surface_kind": "paper_mission_foreground_candidate_package_manifest",
        "schema_version": 1,
        "mode": "non_authority_candidate_package",
        "milestone_kind": "submission_milestone_candidate",
        "study_id": study_id,
        "mission_id": mission_id,
        "counts_as_paper_progress": True,
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "artifact_refs": {
            "candidate_manifest": str(package_root / "candidate_manifest.json"),
            "paper_facing_candidate_delta": str(
                package_root / "paper_facing_candidate_delta.json"
            ),
        },
        "paper_facing_candidate_delta_ref": str(
            package_root / "paper_facing_candidate_delta.json"
        ),
        "owner_consumption_request_ref": str(
            package_root / "owner_consumption_request.json"
        ),
        "owner_blocker_packet_ref": str(package_root / "owner_blocker_packet.json"),
    }
    (package_root / "owner_blocker_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_owner_blocker_packet",
                "status": "owner_blocker_candidate_ready",
                "blocker_kind": "missing_opl_runtime_readback",
                "study_id": study_id,
                "mission_id": mission_id,
                "next_owner": "one-person-lab",
            }
        ),
        encoding="utf-8",
    )
    package_manifest_path = package_root / "package_manifest.json"
    package_manifest_path.write_text(json.dumps(package_manifest), encoding="utf-8")
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "20260624T0201Z"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["candidate_ref"] == str(package_manifest_path)
    assert payload["authority_consume_readback"]["status"] == "accepted_candidate"
    assert payload["transaction_state"] == "accepted_submission_milestone_candidate"
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["consume_output_manifest"]["mode"] == "governed_consume_record"
    assert payload["consume_output_manifest"]["route_handoff_status"] == (
        "ready_for_opl_route_command"
    )
    assert payload["consume_output_manifest"]["writes_yang_ops_consumption_ledger"] is False
    assert payload["consume_output_manifest"]["writes_authority"] is False
    assert payload["consume_output_manifest"]["writes_runtime"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_inspect_prefers_latest_governed_consumption_ledger_transaction(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = (
        f"paper-mission::{study_id}::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    one_shot_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="typed_blocker",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Older one-shot typed blocker mission.",
                "mission_state": "stable_blocker",
                "artifact_delta_ledger": [
                    {
                        "delta_id": "delta::dm003::one-shot",
                        "artifact_ref": "mission://dm003/prose-repair-owner-decision",
                        "delta_kind": "formal_paper_mission_owner_decision_packet",
                        "status": "candidate",
                    }
                ],
                "source_refs": [
                    {
                        "ref_id": "legacy_truth_import_pack",
                        "ref_kind": "legacy_truth_import_pack",
                        "uri": "mission://dm003/import-pack",
                    }
                ],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "typed_blocker"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": one_shot_transaction,
                "one_shot_migration_readback": {
                    "required_output": {
                        "next_owner": "one-person-lab",
                        "work_unit_id": "analysis_claim_evidence_repair",
                    },
                    "consume_candidate_status": "typed_blocker",
                },
            }
        ),
        encoding="utf-8",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=one_shot_transaction,
    )
    consume_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "sat-current"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(consume_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["paper_mission_current_transaction_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["consume_result"]["status"] == "accepted"
    assert payload["paper_mission_run"]["consume_result"]["outcome"] == (
        "accepted_submission_milestone_candidate"
    )
    assert payload["transaction_state"] == "accepted_submission_milestone_candidate"
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["next_owner_or_human_decision"]["next_owner"] == (
        "mission_executor"
    )
    assert payload["next_owner_or_human_decision"]["route_command"] == (
        "resume_stage"
    )
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "paper_mission_consumption_ledger"
    )
    assert payload["paper_mission_transaction"]["stage_id"] == (
        "submission_milestone_candidate"
    )
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["paper_mission_run"]["paper_mission_transaction"] == (
        payload["paper_mission_transaction"]
    )
    assert payload["paper_mission_consumption_ledger_readback"]["source_ref"].endswith(
        f"/paper_mission_consumption_ledger/sat-current/{study_id}/consume_record.json"
    )
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_can_write_governed_consume_record(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    mission_id = "paper-mission::001-paper::gate-clearing::manual"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id="001-paper",
        decision_kind="advance",
    )
    candidate_path = _write_candidate_manifest(
        tmp_path,
        paper_mission_transaction=transaction,
    )
    output_root = tmp_path / "consumption-ledger"

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["paper_mission_command"] == "consume-candidate"
    assert payload["authority_consume_readback"]["status"] == "accepted_candidate"
    output_manifest = payload["consume_output_manifest"]
    assert output_manifest["mode"] == "governed_consume_record"
    assert output_manifest["writes_authority"] is False
    assert output_manifest["writes_runtime"] is False
    assert output_manifest["writes_yang_authority"] is False
    assert len(output_manifest["written_files"]) == 5
    assert output_manifest["route_handoff_status"] == "ready_for_opl_route_command"
    assert output_manifest["route_command_kind"] == "start_next_stage"
    consume_record = json.loads(
        Path(output_manifest["consume_record_ref"]).read_text(encoding="utf-8")
    )
    assert consume_record["surface_kind"] == (
        "mas_paper_mission_candidate_consumption_record"
    )
    assert consume_record["status"] == "accepted_candidate"
    assert consume_record["consume_result"]["status"] == "accepted"
    assert consume_record["authority_materialized"] is False
    assert consume_record["candidate_is_authority"] is False
    assert consume_record["counts_as_owner_consumption_evidence"] is True
    assert consume_record["counts_as_stage_terminalizer_evidence"] is True
    assert consume_record["counts_as_opl_route_handoff_evidence"] is True
    assert consume_record["counts_as_paper_progress"] is False
    assert consume_record["authority_boundary"]["can_write_owner_receipt"] is False
    assert consume_record["authority_boundary"]["can_write_typed_blocker"] is False
    assert consume_record["authority_boundary"]["can_write_human_gate"] is False
    assert "owner receipt" in consume_record["forbidden_authority_writes"]
    assert Path(output_manifest["consume_readback_ref"]).exists()
    consume_readback = json.loads(
        Path(output_manifest["consume_readback_ref"]).read_text(encoding="utf-8")
    )
    assert consume_readback["paper_mission_transaction"] == transaction
    assert consume_readback["stage_terminal_decision"] == (
        transaction["stage_terminal_decision"]
    )
    assert consume_readback["opl_route_command"] == transaction["opl_route_command"]
    assert consume_readback["consume_candidate_status"] == "accepted_candidate"
    assert consume_readback["route_handoff_status"] == "ready_for_opl_route_command"
    assert consume_readback["next_owner"] == "analysis-campaign"
    assert consume_readback["can_submit_to_opl_runtime"] is True
    assert consume_readback["can_claim_paper_progress"] is False
    terminal_packet = json.loads(
        Path(output_manifest["stage_terminal_decision_ref"]).read_text(
            encoding="utf-8"
        )
    )
    assert terminal_packet["surface_kind"] == (
        "mas_paper_mission_stage_terminal_decision_packet"
    )
    assert terminal_packet["terminal_decision_materialized"] is True
    assert terminal_packet["stage_terminal_decision"]["decision_kind"] == "advance"
    route_packet = json.loads(
        Path(output_manifest["opl_route_command_ref"]).read_text(encoding="utf-8")
    )
    assert route_packet["surface_kind"] == "mas_paper_mission_opl_route_command_packet"
    assert route_packet["command_kind"] == "start_next_stage"
    assert route_packet["writes_opl_outbox"] is False
    assert route_packet["writes_opl_stage_run"] is False
    handoff = json.loads(
        Path(output_manifest["opl_route_handoff_ref"]).read_text(encoding="utf-8")
    )
    assert handoff["surface_kind"] == "mas_paper_mission_opl_route_handoff_record"
    assert handoff["handoff_status"] == "ready_for_opl_route_command"
    assert handoff["can_submit_to_opl_runtime"] is True
    carrier = handoff["opl_runtime_carrier"]
    assert handoff["route_identity_key"] == carrier["route_identity_key"]
    assert handoff["attempt_idempotency_key"] == carrier["attempt_idempotency_key"]
    assert handoff["request_idempotency_key"] == carrier["request_idempotency_key"]
    assert handoff["can_claim_opl_stage_run_created"] is False
    assert handoff["can_claim_paper_progress"] is False
    assert payload["dispatch_plan"]["domain_handler_dispatch_mode"] == (
        "governed_consume_record"
    )
    _assert_forbidden_authority_untouched(tmp_path)


def test_domain_handler_export_default_route_handoff_carries_top_level_identity(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "001-paper"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    mission_id = f"paper-mission::{study_id}::gate-clearing::manual"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="advance",
    )
    candidate_path = _write_candidate_manifest(
        tmp_path,
        study_id=study_id,
        paper_mission_transaction=transaction,
    )
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "domain-handler-export-identity"
        / study_id
    )
    mission_root.mkdir(parents=True)
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Consume paper mission candidate and hand it to OPL.",
                "mission_state": "candidate_ready_for_consumption",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "accepted"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": transaction,
            }
        ),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps({"candidate_id": "pmc-001", "study_id": study_id}),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "domain-handler-export-identity"
    )

    consume_exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert consume_exit_code == 0
    capsys.readouterr()

    export_exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    export_payload = json.loads(capsys.readouterr().out)

    assert export_exit_code == 0
    task = next(
        item
        for item in export_payload["paper_mission_default_tasks"]
        if item["study_id"] == study_id
    )
    handoff = task["opl_route_handoff"]
    record = task["opl_route_handoff_record"]
    payload_handoff = task["payload"]["opl_route_handoff"]
    carrier = handoff["opl_runtime_carrier"]

    for exported_handoff in (handoff, record, payload_handoff):
        assert exported_handoff["route_identity_key"] == carrier["route_identity_key"]
        assert exported_handoff["attempt_idempotency_key"] == (
            carrier["attempt_idempotency_key"]
        )
        assert exported_handoff["request_idempotency_key"] == (
            carrier["request_idempotency_key"]
        )
    assert task["route_identity_key"] == carrier["route_identity_key"]
    assert task["attempt_idempotency_key"] == carrier["attempt_idempotency_key"]
    assert task["request_idempotency_key"] == carrier["request_idempotency_key"]
    assert task["payload"]["route_identity_key"] == carrier["route_identity_key"]
    assert task["payload"]["attempt_idempotency_key"] == carrier[
        "attempt_idempotency_key"
    ]
    assert task["payload"]["request_idempotency_key"] == carrier[
        "request_idempotency_key"
    ]
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_route_back_owner_comes_from_terminal_decision(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    mission_id = "paper-mission::001-paper::gate-clearing::manual"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id="001-paper",
        decision_kind="route_back",
    )
    candidate_path = _write_candidate_manifest(
        tmp_path,
        paper_mission_transaction=transaction,
    )
    output_root = tmp_path / "consumption-ledger"

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    output_manifest = payload["consume_output_manifest"]
    assert output_manifest["route_handoff_status"] == "ready_for_opl_route_command"
    assert output_manifest["route_command_kind"] == "route_back"
    assert output_manifest["next_owner"] == "mission_executor"
    consume_record = json.loads(
        Path(output_manifest["consume_record_ref"]).read_text(encoding="utf-8")
    )
    handoff = json.loads(
        Path(output_manifest["opl_route_handoff_ref"]).read_text(encoding="utf-8")
    )
    assert consume_record["next_owner"] == "mission_executor"
    assert handoff["next_owner"] == "mission_executor"
    assert handoff["stage_terminal_decision"]["next_owner"] == "mission_executor"
    assert handoff["can_submit_to_opl_runtime"] is True
    assert handoff["can_claim_paper_progress"] is False
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_drive_packages_consumes_and_returns_opl_route_handoff(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624Tdrive"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::drive"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive DM002 route-back candidate to OPL handoff.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::route-back",
                "artifact_ref": "mission://dm002/route-back",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
        },
        "paper_mission_transaction": transaction,
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-drive",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Tdrive",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_drive_readback"
    assert payload["action_intent"] == "paper_mission/drive"
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["consume_candidate_status"] == "accepted_candidate"
    assert payload["drive_result"]["status"] == "opl_runtime_submission_failed"
    assert payload["drive_result"]["stage_terminal_decision"] == "continue_same_stage"
    assert payload["drive_result"]["route_command"] == "resume_stage"
    assert payload["drive_result"]["next_owner"] == "mission_executor"
    assert payload["drive_result"]["can_submit_to_opl_runtime"] is True
    assert payload["drive_result"]["opl_runtime_submission_status"] == "not_configured"
    assert payload["drive_result"]["opl_runtime_readback_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )
    assert payload["drive_result"]["provider_attempt_running_observed"] is False
    assert payload["drive_result"]["terminal_closeout_observed"] is False
    assert payload["drive_result"]["can_claim_paper_progress"] is False
    assert payload["drive_result"]["can_claim_runtime_ready"] is False
    assert payload["drive_result"]["authority_materialized"] is False
    package_manifest = payload["candidate_package_readback"]["output_manifest"]
    consume_manifest = payload["consume_readback"]["consume_output_manifest"]
    assert package_manifest["mode"] == "non_authority_candidate_package"
    assert consume_manifest["mode"] == "governed_consume_record"
    assert consume_manifest["route_handoff_status"] == "ready_for_opl_route_command"
    assert consume_manifest["next_owner"] == "mission_executor"
    assert payload["opl_route_handoff"]["next_owner"] == "mission_executor"
    assert payload["opl_route_handoff"]["can_submit_to_opl_runtime"] is True
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    assert payload["mutation_policy"]["writes_yang_authority"] is False
    assert payload["output_manifest"]["writes_authority"] is False
    assert payload["output_manifest"]["writes_runtime"] is False
    assert payload["output_manifest"]["writes_yang_authority"] is False
    assert Path(package_manifest["package_manifest_ref"]).exists()
    assert Path(consume_manifest["opl_route_handoff_ref"]).exists()
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_can_submit_opl_stage_route_via_public_enqueue(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624Tdrive"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::submission-milestone::drive"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive DM003 consumed candidate into OPL stage-route.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [],
        "source_refs": [],
        "consume_result": {"status": "accepted"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "submission_milestone_candidate",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "submission_milestone_candidate",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "accepted_candidate",
        },
        "paper_mission_transaction": transaction,
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm003-drive",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
            }
        ),
        encoding="utf-8",
    )
    capture_path = tmp_path / "opl-capture.json"
    fake_opl = tmp_path / "fake-opl.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                f"capture_path = {str(capture_path)!r}",
                "args = sys.argv[1:]",
                "records = []",
                "try:",
                "    records = json.loads(open(capture_path, encoding='utf-8').read())",
                "except Exception:",
                "    records = []",
                "def persist(record):",
                "    records.append(record)",
                "    open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))",
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_test_drive',",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_owner_answer_terminal',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_owner_answer_terminal',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_test_drive','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = records[0]['payload'] if records else {}",
                "    task = {'task_id':'frt_test_drive','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = records[0]['payload'] if records else {}",
                "    task = {'task_id':'frt_test_drive','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':[running_attempt(payload)]}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Tdrive",
            "--opl-bin",
            str(fake_opl),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    captured = json.loads(capture_path.read_text(encoding="utf-8"))
    enqueue_record = captured[0]
    tick_record = captured[1]

    assert exit_code == 0
    assert enqueue_record["argv"][:3] == ["family-runtime", "enqueue", "--domain"]
    assert "--task-kind" in enqueue_record["argv"]
    assert enqueue_record["argv"][enqueue_record["argv"].index("--task-kind") + 1] == (
        "paper_mission/stage-route"
    )
    assert tick_record["argv"][:2] == ["family-runtime", "tick"]
    assert "--hydrate" in tick_record["argv"]
    assert "--payload-match" in tick_record["argv"]
    submitted_payload = enqueue_record["payload"]
    assert submitted_payload["surface_kind"] == (
        "opl_mas_paper_mission_route_runtime_request"
    )
    assert submitted_payload["study_id"] == study_id
    assert submitted_payload["command_kind"] == "resume_stage"
    assert submitted_payload["workspace_root"] == str(workspace_root.resolve())
    assert submitted_payload["domain_workspace_root"] == str(workspace_root.resolve())
    assert submitted_payload["authority_boundary"]["writes_opl_queue"] is True
    assert submitted_payload["authority_boundary"]["writes_opl_stage_run"] is False
    assert submitted_payload["authority_boundary"]["writes_provider_attempt"] is False
    assert submitted_payload["authority_boundary"]["can_claim_paper_progress"] is False
    submission = payload["opl_runtime_submission"]
    assert submission["status"] == "submitted"
    assert submission["stage_route_followthrough_attempted"] is True
    assert submission["tick_readback"]["status"] == "completed"
    assert submission["tick_readback"]["can_claim_provider_running"] is True
    assert submission["writes_runtime"] is True
    assert submission["writes_runtime_owner"] == "one-person-lab"
    assert submission["writes_mas_authority"] is False
    assert submission["can_claim_provider_running"] is False
    assert submission["can_claim_paper_progress"] is False
    assert payload["mutation_policy"]["writes_runtime"] is True
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["drive_result"]["opl_runtime_submission_status"] == "submitted"
    assert payload["drive_result"]["status"] == "opl_stage_route_running"
    assert payload["drive_result"]["opl_runtime_readback_status"] == (
        "opl_runtime_attempt_running_observed"
    )
    assert payload["drive_result"]["provider_attempt_running_observed"] is True
    assert payload["opl_runtime_readback_status"] == "opl_runtime_attempt_running_observed"
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_followthroughs_terminal_route_back_into_fresh_stage_route(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260624Tdrivefollowthrough"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::drive-followthrough"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive DM002 route-back through MAS followthrough.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::route-back",
                "artifact_ref": "mission://dm002/route-back",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
        },
        "paper_mission_transaction": transaction,
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-followthrough",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )
    capture_path = tmp_path / "opl-capture.json"
    fake_opl = tmp_path / "fake-opl-followthrough.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                f"capture_path = {str(capture_path)!r}",
                "args = sys.argv[1:]",
                "try:",
                "    records = json.loads(open(capture_path, encoding='utf-8').read())",
                "except Exception:",
                "    records = []",
                "def persist(record):",
                "    records.append(record)",
                "    open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))",
                "def payloads():",
                "    return [r['payload'] for r in records if 'payload' in r]",
                "def current_payload():",
                "    ps = payloads()",
                "    return ps[-1] if ps else {}",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_terminal_followthrough',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_running_followthrough',",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_followthrough','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = current_payload()",
                "    ps = payloads()",
                "    attempt = terminal_attempt(payload) if len(ps) == 1 else running_attempt(payload)",
                "    task = {'task_id':'frt_followthrough','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task], 'queue': {'total': 1}, 'stage_attempts':[attempt]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = current_payload()",
                "    ps = payloads()",
                "    attempt = terminal_attempt(payload) if len(ps) == 1 else running_attempt(payload)",
                "    task = {'task_id':'frt_followthrough','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':'running','payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':[attempt]}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Tdrivefollowthrough",
            "--opl-bin",
            str(fake_opl),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    captured = json.loads(capture_path.read_text(encoding="utf-8"))
    enqueues = [record for record in captured if "payload" in record]

    assert exit_code == 0
    assert len(enqueues) == 2
    assert payload["followthrough"]["attempted"] is True
    assert payload["followthrough"]["round_count"] == 1
    assert payload["followthrough"]["rounds"][0]["trigger"] == (
        "terminal_owner_answer_route_back_followthrough"
    )
    assert payload["drive_result"]["status"] == "opl_stage_route_running"
    assert payload["drive_result"]["terminal_closeout_observed"] is False
    assert payload["drive_result"]["provider_attempt_running_observed"] is True
    assert payload["consume_candidate_status"] == "accepted_candidate"
    assert payload["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert enqueues[0]["payload"]["paper_mission_transaction_ref"] != (
        enqueues[1]["payload"]["paper_mission_transaction_ref"]
    )
    assert payload["output_manifest"]["followthrough_round_count"] == 1
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_drive_followthroughs_terminal_owner_answer_route_back(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::owner-answer-followthrough"
    route_back_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Drive owner-answer route-back through MAS followthrough.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::owner-answer",
                "artifact_ref": "mission://dm002/owner-answer-route-back",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": "mission://dm002/import-pack",
            }
        ],
        "authority_touchpoints": [],
        "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
        "consume_result": {"status": "route_back"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "paper_mission_transaction": route_back_transaction,
        "one_shot_migration_readback": {
            "required_output": {
                "next_owner": "mission_executor",
                "work_unit_id": "gate_clearing_claim_evidence_repair",
            },
            "consume_candidate_status": "route_back",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    capture_path = tmp_path / "opl-owner-answer-capture.json"
    fake_opl = tmp_path / "fake-opl-owner-answer.py"
    fake_opl.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                f"capture_path = {str(capture_path)!r}",
                "args = sys.argv[1:]",
                "try:",
                "    records = json.loads(open(capture_path, encoding='utf-8').read())",
                "except Exception:",
                "    records = []",
                "def persist(record):",
                "    records.append(record)",
                "    open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))",
                "def payloads():",
                "    return [r['payload'] for r in records if 'payload' in r]",
                "def current_payload():",
                "    ps = payloads()",
                "    return ps[-1] if ps else {}",
                "def running_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_running_readback',",
                "        'status': 'running',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_owner_answer_followthrough',",
                "        'provider_status': 'running',",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "def terminal_attempt(payload):",
                "    return {",
                "        'surface_kind': 'opl_stage_attempt_terminal_readback',",
                "        'status': 'completed',",
                "        'stage_id': payload.get('route_target'),",
                "        'stage_attempt_id': 'sat_owner_answer_terminal',",
                "        'closeout_receipt_status': 'accepted_typed_closeout',",
                "        'typed_blocker_ref': 'typed-blocker:domain-gate-pending',",
                "        'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',",
                "        'domain_ready_verdict': 'domain_gate_pending',",
                "        'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],",
                "        'workspace_locator': {",
                "            'study_id': payload.get('study_id'),",
                "            'paper_mission_transaction_ref': payload.get('paper_mission_transaction_ref'),",
                "            'opl_route_command_ref': payload.get('opl_route_command_ref'),",
                "            'command_kind': payload.get('command_kind'),",
                "            'route_target': payload.get('route_target'),",
                "        },",
                "    }",
                "if args[:2] == ['family-runtime', 'enqueue']:",
                "    payload = json.loads(args[args.index('--payload') + 1])",
                "    persist({'argv': args, 'payload': payload})",
                "    print(json.dumps({'version':'g2','family_runtime_enqueue':{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{'task_id':'frt_owner_answer','status':'queued','payload':payload}}}))",
                "elif args[:2] == ['family-runtime', 'tick']:",
                "    persist({'argv': args})",
                "    print(json.dumps({'family_runtime_tick':{'selected_count':1,'dispatches':[{'status':'running','stage_run_request':{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}]}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'list']:",
                "    payload = current_payload()",
                "    ps = payloads()",
                "    task_status = 'blocked' if len(ps) == 1 else 'running'",
                "    attempts = [terminal_attempt(payload)] if len(ps) == 1 else [running_attempt(payload)]",
                "    task = {'task_id':'frt_owner_answer','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':task_status,'payload':payload}",
                "    print(json.dumps({'family_runtime_queue':{'tasks':[task], 'queue': {'total': 1}, 'stage_attempts':attempts}}))",
                "elif args[:3] == ['family-runtime', 'queue', 'inspect']:",
                "    payload = current_payload()",
                "    ps = payloads()",
                "    task_status = 'blocked' if len(ps) == 1 else 'running'",
                "    attempts = [terminal_attempt(payload)] if len(ps) == 1 else [running_attempt(payload)]",
                "    task = {'task_id':'frt_owner_answer','domain_id':'medautoscience','task_kind':'paper_mission/stage-route','status':task_status,'payload':payload}",
                "    print(json.dumps({'family_runtime_task':{'task':task,'stage_attempts':attempts}}))",
                "else:",
                "    persist({'argv': args})",
                "    print(json.dumps({'error':'unexpected_args','args':args}))",
            ]
        ),
        encoding="utf-8",
    )
    fake_opl.chmod(0o755)

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--run-id",
            "20260624Towneranswerfollowthrough",
            "--opl-bin",
            str(fake_opl),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    captured = json.loads(capture_path.read_text(encoding="utf-8"))
    enqueues = [record for record in captured if "payload" in record]

    assert exit_code == 0
    assert len(enqueues) >= 1
    assert all(item["payload"]["command_kind"] == "resume_stage" for item in enqueues)
    assert all(
        "paper_mission_transaction_ref" in item["payload"] for item in enqueues
    )
    assert payload["followthrough"]["rounds"] == [] or payload["followthrough"][
        "rounds"
    ][0]["trigger"] == "terminal_owner_answer_route_back_followthrough"
    assert payload["drive_result"]["status"] == "opl_stage_route_running"
    assert payload["stage_terminal_decision"]["decision_kind"] == (
        "continue_same_stage"
    )
    assert payload["opl_route_command"]["command_kind"] == "resume_stage"
    assert payload["opl_runtime_readback_status"] == (
        "opl_runtime_attempt_running_observed"
    )
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_typed_blocker_handoff_waits_for_authority(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    candidate_path = _write_candidate_manifest(
        tmp_path,
        requested_outcome="typed_blocker_required",
    )
    output_root = tmp_path / "consumption-ledger"

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    output_manifest = payload["consume_output_manifest"]
    assert output_manifest["route_handoff_status"] == (
        "waiting_for_typed_blocker_authority"
    )
    assert output_manifest["route_command_kind"] == "resume_stage"
    handoff = json.loads(
        Path(output_manifest["opl_route_handoff_ref"]).read_text(encoding="utf-8")
    )
    assert handoff["handoff_status"] == "waiting_for_typed_blocker_authority"
    assert handoff["can_submit_to_opl_runtime"] is False
    assert handoff["can_claim_paper_progress"] is False
    assert handoff["authority_boundary"]["can_write_typed_blocker"] is False
    assert "typed blocker" in handoff["forbidden_authority_writes"]
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_consume_candidate_picks_up_transaction_fields(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    mission_id = "paper-mission::001-paper::gate-clearing::manual"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id="001-paper",
    )
    candidate_path = _write_candidate_manifest(
        tmp_path,
        paper_mission_transaction=transaction,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["transaction_state"] == "terminal_decision_recorded"
    assert payload["stage_terminal_decision"] == transaction["stage_terminal_decision"]
    assert payload["opl_route_command"] == transaction["opl_route_command"]
    assert payload["paper_mission_run_candidate"]["transaction_state"] == (
        "terminal_decision_recorded"
    )
    assert payload["paper_mission_transaction_readback"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["authority_consume_readback"]["write_plan"]["written_files"] == []
    _assert_forbidden_authority_untouched(tmp_path)


@pytest.mark.parametrize(
    ("requested_outcome", "expected_consume_status", "expected_mission_state"),
    (
        ("route_back", "route_back", "route_back"),
        ("typed_blocker_required", "typed_blocker", "stable_blocker"),
        ("human_gate_required", "human_gate", "waiting_human_decision"),
    ),
)
def test_paper_mission_consume_candidate_maps_non_accept_outcomes(
    tmp_path: Path,
    capsys,
    requested_outcome: str,
    expected_consume_status: str,
    expected_mission_state: str,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    candidate_path = _write_candidate_manifest(
        tmp_path,
        requested_outcome=requested_outcome,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["authority_consume_readback"]["consume_result"]["status"] == (
        expected_consume_status
    )
    assert payload["paper_mission_run_candidate"]["consume_result"]["status"] == (
        expected_consume_status
    )
    assert payload["paper_mission_run_candidate"]["mission_state"] == expected_mission_state
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["authority_consume_readback"]["write_plan"]["written_files"] == []
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_inspect_one_shot_migration_returns_default_readback(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(
        tmp_path,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--one-shot-migration",
            "--study-progress-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dm003_progress.json"),
            "--domain-health-diagnostic-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dhd_dry_run.json"),
            "--profile",
            str(profile_path),
            "--study-id",
            "003-dpcc-primary-care-phenotype-treatment-gap",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_one_shot_migration_cli_readback"
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["default_readback"]["current_mission"]["objective_kind"] == (
        "medical_prose_write_repair_publication_gate_replay"
    )
    assert (
        payload["default_readback"]["current_mission"][
            "legacy_blocker_is_default_execution_state"
        ]
        is False
    )
    assert payload["default_readback"]["next_owner"] == "one-person-lab"
    assert payload["consume_candidate_status"] == "typed_blocker"
    assert payload["mission_candidate_artifact_delta"]["surface_kind"] == (
        "paper_mission_candidate_artifact_delta"
    )
    assert payload["mission_candidate_artifact_delta"]["candidate_is_authority"] is False
    assert payload["owner_decision_packet"]["surface_kind"] == (
        "paper_mission_owner_decision_packet"
    )
    assert payload["owner_decision_packet"]["packet_status"] == (
        "candidate_ready_for_mas_consume"
    )
    assert payload["owner_decision_packet"]["candidate_is_authority"] is False
    assert payload["legacy_truth_import_pack"]["legacy_constraints"][
        "old_blocker_is_default_execution_state"
    ] is False
    assert payload["output_manifest"]["written_files"] == []
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_yang_authority"] is False
    assert payload["mutation_policy"]["writes_yang_ops_candidate_package"] is False
    _assert_forbidden_authority_untouched(
        tmp_path,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
    )


def test_one_shot_migration_can_write_non_authority_candidate_package_and_consume_it(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(
        tmp_path,
        study_id="002-dm-china-us-mortality-attribution",
    )
    output_root = tmp_path / "candidate-packages"

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--one-shot-migration",
            "--study-progress-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dm002_progress.json"),
            "--domain-health-diagnostic-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dhd_dry_run.json"),
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--format",
            "json",
        ]
    )
    first = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    written_files = first["output_manifest"]["written_files"]
    assert len(written_files) == 6
    assert first["output_manifest"]["writes_authority"] is False
    assert first["output_manifest"]["writes_yang_authority"] is False
    assert first["output_manifest"]["writes_yang_ops_candidate_package"] is False
    candidate_manifest_ref = first["output_manifest"]["candidate_manifest_ref"]
    assert Path(candidate_manifest_ref).exists()
    assert Path(first["output_manifest"]["mission_candidate_artifact_delta_ref"]).exists()
    assert Path(first["output_manifest"]["owner_decision_packet_ref"]).exists()
    output_root_for_study = Path(first["output_manifest"]["output_root"])
    candidate_delta_path = output_root_for_study / "mission_candidate_artifact_delta.json"
    owner_decision_packet_path = output_root_for_study / "owner_decision_packet.json"
    assert candidate_delta_path.exists()
    assert owner_decision_packet_path.exists()
    written_candidate_manifest = json.loads(
        Path(candidate_manifest_ref).read_text(encoding="utf-8")
    )
    assert written_candidate_manifest["mission_candidate_sidecar_refs"] == {
        "paper_mission_run": str(output_root_for_study / "paper_mission_run.json"),
        "default_readback": str(output_root_for_study / "default_readback.json"),
        "mission_candidate_artifact_delta": str(candidate_delta_path),
        "owner_decision_packet": str(owner_decision_packet_path),
    }
    candidate_delta = json.loads(candidate_delta_path.read_text(encoding="utf-8"))
    owner_decision_packet = json.loads(
        owner_decision_packet_path.read_text(encoding="utf-8")
    )
    assert candidate_delta["surface_kind"] == "paper_mission_candidate_artifact_delta"
    assert candidate_delta["counts_as_paper_progress"] is True
    assert candidate_delta["candidate_is_authority"] is False
    assert owner_decision_packet["surface_kind"] == "paper_mission_owner_decision_packet"
    assert owner_decision_packet["packet_status"] == "candidate_ready_for_mas_consume"
    assert owner_decision_packet["candidate_is_authority"] is False
    _assert_forbidden_authority_untouched(
        tmp_path,
        study_id="002-dm-china-us-mortality-attribution",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            candidate_manifest_ref,
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--format",
            "json",
        ]
    )
    second = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert second["authority_consume_readback"]["status"] == "accepted_candidate"
    assert second["authority_consume_readback"]["consume_result"]["status"] == "accepted"
    assert second["paper_mission_transaction_readback"]["source"] == "candidate_manifest"
    assert second["transaction_state"] != "not_materialized"
    written_mission = json.loads(
        (output_root_for_study / "paper_mission_run.json").read_text(encoding="utf-8")
    )
    assert (
        second["paper_mission_transaction_readback"]["paper_mission_transaction"][
            "transaction_id"
        ]
        == written_mission["paper_mission_transaction"]["transaction_id"]
    )
    assert second["authority_consume_readback"]["write_plan"]["written_files"] == []
    assert second["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(
        tmp_path,
        study_id="002-dm-china-us-mortality-attribution",
    )


@pytest.mark.parametrize(
    "workspace",
    ("DM-CVD-Mortality-Risk", "NF-PitNET", "Obesity"),
)
def test_paper_mission_output_guards_allow_matching_yang_ops_roots(workspace: str) -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    commands._assert_safe_one_shot_output_root(
        Path(
            f"/Users/gaofeng/workspace/Yang/{workspace}/"
            "ops/medautoscience/paper_mission_one_shot_migration/20260623"
        )
    )
    commands._assert_safe_candidate_package_output_root(
        Path(
            f"/Users/gaofeng/workspace/Yang/{workspace}/"
            "ops/medautoscience/paper_mission_candidate_package/20260623"
        )
    )
    commands._assert_safe_consumption_ledger_output_root(
        Path(
            f"/Users/gaofeng/workspace/Yang/{workspace}/"
            "ops/medautoscience/paper_mission_consumption_ledger/20260623"
        )
    )


def test_paper_mission_output_guards_reject_wrong_non_authority_bucket() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_one_shot_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
                "ops/medautoscience/paper_mission_consumption_ledger/20260623"
            )
        )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_candidate_package_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
                "ops/medautoscience/paper_mission_one_shot_migration/20260623"
            )
        )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_consumption_ledger_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
                "ops/medautoscience/paper_mission_candidate_package/20260623"
            )
        )


def test_paper_mission_drive_yang_output_root_uses_allowed_sibling_buckets(
    tmp_path: Path,
) -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    class Profile:
        workspace_root = tmp_path / "workspace"

    roots = commands._paper_mission_drive_output_roots(
        profile=Profile(),
        output_root=Path(
            "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
            "ops/medautoscience/paper_mission_drive/20260627Tdrive"
        ),
        run_id="20260627Tdrive",
    )

    commands._assert_safe_candidate_package_output_root(roots["candidate_package"])
    commands._assert_safe_consumption_ledger_output_root(roots["consumption_ledger"])
    assert roots["candidate_package"] == Path(
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
        "ops/medautoscience/paper_mission_candidate_package/20260627Tdrive"
    )
    assert roots["consumption_ledger"] == Path(
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
        "ops/medautoscience/paper_mission_consumption_ledger/20260627Tdrive"
    )


def test_one_shot_migration_rejects_yang_authority_and_runtime_output_roots() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_candidate_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/NF-PitNET/"
                "studies/001-lineage-pfs/artifacts/publication_eval"
            )
        )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_candidate_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/Obesity/"
                "runtime/quests/obesity_multicenter_phenotype_atlas/provider_attempt"
            )
        )


def _write_submission_milestone_package(
    *,
    workspace_root: Path,
    study_id: str,
    mission_id: str,
    base_transaction: dict,
    requested_outcome: str = "accepted_candidate",
) -> Path:
    package_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "sat-current"
        / study_id
    )
    package_root.mkdir(parents=True)
    candidate_manifest = {
        "candidate_id": f"paper-mission-candidate::{study_id}::submission",
        "mission_id": mission_id,
        "study_id": study_id,
        "requested_outcome": requested_outcome,
        "candidate_manifest_ref": str(package_root / "candidate_manifest.json"),
        "candidate_artifact_refs": [
            str(package_root / "paper_facing_candidate_delta.json"),
        ],
        "source_readiness_refs": [f"source-readiness:{study_id}"],
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": "one-person-lab",
        "resume_condition": "MAS consumes or routes the milestone package",
        "paper_mission_transaction": base_transaction,
    }
    (package_root / "candidate_manifest.json").write_text(
        json.dumps(candidate_manifest),
        encoding="utf-8",
    )
    (package_root / "owner_blocker_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_owner_blocker_packet",
                "status": "owner_blocker_candidate_ready",
                "blocker_kind": "missing_opl_runtime_readback",
                "study_id": study_id,
                "mission_id": mission_id,
                "next_owner": "one-person-lab",
            }
        ),
        encoding="utf-8",
    )
    package_manifest = {
        "surface_kind": "paper_mission_foreground_candidate_package_manifest",
        "schema_version": 1,
        "mode": "non_authority_candidate_package",
        "milestone_kind": "submission_milestone_candidate",
        "requested_outcome": requested_outcome,
        "study_id": study_id,
        "mission_id": mission_id,
        "counts_as_paper_progress": True,
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "artifact_refs": {
            "candidate_manifest": str(package_root / "candidate_manifest.json"),
            "paper_facing_candidate_delta": str(
                package_root / "paper_facing_candidate_delta.json"
            ),
        },
        "paper_facing_candidate_delta_ref": str(
            package_root / "paper_facing_candidate_delta.json"
        ),
        "owner_consumption_request_ref": str(
            package_root / "owner_consumption_request.json"
        ),
        "owner_blocker_packet_ref": str(package_root / "owner_blocker_packet.json"),
    }
    package_manifest_path = package_root / "package_manifest.json"
    package_manifest_path.write_text(json.dumps(package_manifest), encoding="utf-8")
    return package_manifest_path
