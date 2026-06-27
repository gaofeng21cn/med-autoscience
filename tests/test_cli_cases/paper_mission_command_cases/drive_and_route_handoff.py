from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.test_cli_cases.shared import write_profile
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


@pytest.fixture(autouse=True)
def _disable_default_opl_live_probe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_BIN", str(tmp_path / "missing-opl"))


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
    transaction["stage_terminal_decision"]["target_stage_id"] = (
        "paper_mission_stage_route_domain_gate_pending"
    )
    transaction["stage_terminal_decision"]["repair_scope"] = (
        "MAS authority kernel observed a domain gate terminal closeout; mission "
        "executor must revise the paper mission candidate or submit a concrete "
        "owner answer shape before OPL can advance."
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
    assert enqueues[1]["payload"]["route_target"] == (
        "paper_mission_stage_route_domain_gate_pending"
    )
    assert (
        "MAS authority kernel observed"
        not in enqueues[1]["payload"]["route_target"]
    )
    assert enqueues[1]["payload"]["mission_id"] == mission_id
    assert "::followthrough" not in enqueues[1]["payload"]["mission_id"]
    followthrough_transaction = payload["consume_readback"][
        "paper_mission_transaction_readback"
    ][
        "paper_mission_transaction"
    ]
    assert followthrough_transaction["mission_id"] == mission_id
    assert (
        followthrough_transaction["transaction_id"]
        == enqueues[1]["payload"]["paper_mission_transaction_ref"]
    )
    assert (
        followthrough_transaction["transaction_id"]
        != payload["mission_id"]
    )
    assert payload["consume_readback"]["contract_validation"]["status"] == "validated"
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
