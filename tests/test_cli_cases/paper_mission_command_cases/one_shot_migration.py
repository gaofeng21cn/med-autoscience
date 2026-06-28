from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


DM_CANARY_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[2] / "fixtures" / "paper_mission_dm_canary"
)


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
            "--diagnostic-payload",
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
            "--diagnostic-payload",
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
