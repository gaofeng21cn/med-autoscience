from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import (
    DM_CANARY_FIXTURE_ROOT,
    FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
    _assert_forbidden_authority_untouched,
    _paper_mission_forbidden_write_guard,
    _paper_mission_transaction_payload,
    _write_candidate_manifest,
    _write_matching_domain_gate_closeout,
    _write_paper_source_fixture,
    _write_profile_with_study,
    _write_submission_milestone_package,
)


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


def test_paper_mission_consume_candidate_counts_accepted_package_delta_as_semantic_progress(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::gate-clearing::accepted-package"
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
    )
    stale_owner_request_ref = str(
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "stale-prior-run"
        / study_id
        / "owner_consumption_request.json"
    )
    package_manifest = json.loads(package_path.read_text(encoding="utf-8"))
    package_manifest["owner_consumption_request_ref"] = stale_owner_request_ref
    package_path.write_text(json.dumps(package_manifest), encoding="utf-8")
    stale_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    stale_transaction["idempotency"]["idempotency_key"] = (
        f"{study_id}::submission_milestone_candidate::"
        f"submission-milestone-candidate-consumed::{stale_owner_request_ref}::"
        "candidate-ref-missing::transaction-ref-missing"
    )
    stale_readback = {
        "surface_kind": "paper_mission_materialized_readback",
        "paper_mission_transaction": stale_transaction,
    }
    (package_path.parent / "paper_mission_readback.json").write_text(
        json.dumps(stale_readback),
        encoding="utf-8",
    )
    owner_blocker_packet = json.loads(
        (package_path.parent / "owner_blocker_packet.json").read_text(
            encoding="utf-8"
        )
    )
    owner_blocker_packet["blocker_kind"] = "route_back_without_blocker"
    owner_blocker_packet["current_terminal_decision"] = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": (
            "MAS mission executor consumed route-back/domain-gate evidence as a "
            "fresh paper-facing candidate and is continuing the PaperMission stage."
        ),
        "route_command": "resume_stage",
        "route_target": "paper_mission_stage_route_domain_gate_pending",
    }
    (package_path.parent / "owner_blocker_packet.json").write_text(
        json.dumps(owner_blocker_packet),
        encoding="utf-8",
    )
    package_manifest["artifact_refs"] = {
        **package_manifest.get("artifact_refs", {}),
        "paper_mission_readback": str(package_path.parent / "paper_mission_readback.json"),
    }
    package_path.write_text(json.dumps(package_manifest), encoding="utf-8")

    for ledger_id in ("accepted-first", "accepted-second"):
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

    paper_delta_ref = str(
        package_path.parent / "paper_facing_candidate_delta.json"
    )
    assert "non_advancing_route_back" not in payload
    assert "requires_mas_owned_executor_delta" not in payload
    assert payload["authority_consume_readback"]["consume_result"][
        "canonical_paper_or_artifact_delta_ref"
    ] == paper_delta_ref
    assert payload["authority_consume_readback"]["consume_result"][
        "authority_materialized"
    ] is False
    assert payload["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    idempotency_key = payload["paper_mission_transaction"]["idempotency"][
        "idempotency_key"
    ]
    carrier = payload["opl_runtime_carrier"]
    assert str(package_path) in idempotency_key
    assert stale_owner_request_ref not in idempotency_key
    assert carrier["idempotency_key"] == idempotency_key
    assert str(package_path) in carrier["attempt_idempotency_key"]
    assert stale_owner_request_ref not in carrier["attempt_idempotency_key"]
    assert payload["opl_route_command"]["target"] == (
        "paper_mission_stage_route_domain_gate_pending"
    )
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_preserves_canonical_next_action_transaction(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::paper_mission_import::one-shot-migration"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    transaction["transaction_id"] = (
        f"paper-mission-transaction::{study_id}::write::{mission_id}::followthrough::canonical"
    )
    transaction["stage_id"] = "write"
    transaction["stage_run_ref"] = (
        f"paper-mission-followthrough://{study_id}/write/"
        "medical-methods-and-registry-reporting-repair"
    )
    transaction["stage_terminal_decision"] = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": "MAS canonical next action requests the current owner work unit.",
        "next_owner": "write",
        "next_work_unit": "medical_methods_and_registry_reporting_repair",
        "recommended_next_action": "request_opl_stage_attempt",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_methods_and_registry_reporting_repair"
        ),
        "source_next_action_ref": (
            "domain-transition::route_back_same_line::"
            "medical_methods_and_registry_reporting_repair"
        ),
    }
    transaction["opl_route_command"] = {
        "command_kind": "resume_stage",
        "target": "medical_methods_and_registry_reporting_repair",
        "reason": "MAS canonical next action requests the current owner work unit.",
        "source_terminal_decision_ref": (
            f"{transaction['transaction_id']}#stage_terminal_decision"
        ),
        "stage_run_ref": transaction["stage_run_ref"],
        "runtime_owner": "one-person-lab",
    }
    transaction["idempotency"]["idempotency_key"] = (
        f"{study_id}::write::medical_methods_and_registry_reporting_repair"
    )
    transaction["idempotency"]["transaction_fingerprint"] = (
        f"{mission_id}::write::continue_same_stage::accepted_submission_milestone_candidate"
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=transaction,
    )
    owner_blocker_packet = json.loads(
        (package_path.parent / "owner_blocker_packet.json").read_text(
            encoding="utf-8"
        )
    )
    owner_blocker_packet["blocker_kind"] = "domain_gate"
    owner_blocker_packet["current_terminal_decision"] = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": "Old submission milestone followthrough.",
        "next_owner": "mission_executor",
        "next_work_unit": "submission_milestone_candidate::followthrough::followthrough-01",
    }
    (package_path.parent / "owner_blocker_packet.json").write_text(
        json.dumps(owner_blocker_packet),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "canonical-next-action"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
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
    assert payload["paper_mission_transaction"]["stage_id"] == "write"
    assert "::write::" in payload["paper_mission_transaction"]["transaction_id"]
    assert payload["stage_terminal_decision"]["next_owner"] == "write"
    assert payload["stage_terminal_decision"]["next_work_unit"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert payload["opl_route_command"]["target"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert payload["opl_runtime_carrier"]["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert "submission_milestone_candidate::followthrough" not in (
        payload["paper_mission_transaction"]["transaction_id"]
    )
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_refreshes_typed_blocker_package_artifacts(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::paper_mission_import::one-shot-migration"
    stale_delta_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "paper_mission_drive"
        / study_id
        / "paper_facing_candidate_delta.json"
    )
    stale_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    stale_transaction["artifact_delta_refs"] = [
        {
            "ref_id": "submission_milestone_artifact::stale",
            "ref_kind": "submission_milestone_candidate_artifact",
            "uri": str(stale_delta_ref),
        }
    ]
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=stale_transaction,
    )
    package_root = package_path.parent
    package_manifest = json.loads(package_path.read_text(encoding="utf-8"))
    package_manifest["artifact_refs"] = {
        **package_manifest.get("artifact_refs", {}),
        "paper_mission_readback": str(package_root / "paper_mission_readback.json"),
        "mission_candidate_artifact_delta": str(
            package_root / "mission_candidate_artifact_delta.json"
        ),
        "owner_decision_packet": str(package_root / "owner_decision_packet.json"),
    }
    package_path.write_text(json.dumps(package_manifest), encoding="utf-8")
    (package_root / "paper_mission_readback.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_materialized_readback",
                "paper_mission_transaction": stale_transaction,
            }
        ),
        encoding="utf-8",
    )
    owner_blocker_packet = json.loads(
        (package_root / "owner_blocker_packet.json").read_text(encoding="utf-8")
    )
    owner_blocker_packet["blocker_kind"] = "typed_blocker"
    owner_blocker_packet["current_terminal_decision"] = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": (
            "MAS mission executor consumed route-back/domain-gate evidence as a "
            "fresh paper-facing candidate and is continuing the PaperMission stage."
        ),
        "next_owner": "mission_executor",
        "next_work_unit": "paper_mission_import::next",
        "route_command": "resume_stage",
        "route_target": "paper_mission_import::next",
    }
    (package_root / "owner_blocker_packet.json").write_text(
        json.dumps(owner_blocker_packet),
        encoding="utf-8",
    )
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "foreground-20260630T171704Z"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
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
    transaction_refs = [
        item["uri"] for item in payload["paper_mission_transaction"]["artifact_delta_refs"]
    ]
    assert str(package_root / "paper_facing_candidate_delta.json") in transaction_refs
    assert str(package_root / "mission_candidate_artifact_delta.json") in transaction_refs
    assert str(package_root / "owner_decision_packet.json") in transaction_refs
    assert str(stale_delta_ref) not in transaction_refs
    consume_readback = json.loads(
        Path(payload["consume_output_manifest"]["consume_readback_ref"]).read_text(
            encoding="utf-8"
        )
    )
    ledger_refs = [
        item["uri"]
        for item in consume_readback["paper_mission_transaction"]["artifact_delta_refs"]
    ]
    assert ledger_refs == transaction_refs
    assert payload["authority_consume_readback"]["consume_result"][
        "paper_facing_delta_ref"
    ] == str(package_root / "paper_facing_candidate_delta.json")
    assert payload["consume_output_manifest"]["writes_authority"] is False
    assert payload["consume_output_manifest"]["writes_yang_authority"] is False
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
    assert consume_readback["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
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
    assert guard["mas_owned_executor_stage"]["stage_type"] == (
        "paper_mission_semantic_progress_executor"
    )
    assert guard["mas_owned_executor_stage"]["required_outputs"] == [
        "owner_decision_packet",
        "human_gate_question",
        "paper_facing_delta",
        "typed_blocker_materialization",
    ]
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
