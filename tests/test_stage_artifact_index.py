from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.stage_artifact_index import (
    ALLOWED_ARTIFACT_STATUSES,
    build_stage_artifact_index,
)
from med_autoscience.controllers.stage_artifact_materializer import (
    materialize_stage_artifact_delta,
)
from med_autoscience.controllers.stage_run_kernel import (
    stage_run_kernel_projection_from_stage_folder,
)
from med_autoscience.runtime_protocol import domain_authority_refs_index
from tests.stage_artifact_index_cases.shared import (
    EXPECTED_AUTHORITY_FUNCTIONS,
    EXPECTED_LEGACY_ROUTE_IDS,
    EXPECTED_PAPER_STUDY_STAGE_IDS,
    PAPER_STUDY_STAGE_PACK_REF,
    STUDY_INTAKE_REFS,
    write_json as _write_json,
    write_opl_physical_stage_attempt as _write_opl_physical_stage_attempt,
    write_stage_native_contract as _write_stage_native_contract,
    write_text as _write_text,
)


def test_stage_artifact_index_builds_requirements_from_paper_study_stage_pack(tmp_path: Path) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    assert (Path(__file__).resolve().parents[1] / PAPER_STUDY_STAGE_PACK_REF).exists()
    assert index["surface_kind"] == "stage_artifact_index"
    assert index["schema_version"] == 1
    assert index["study_id"] == "001-risk"
    assert index["stage_model"] == "paper_study_artifact_stage_pack"
    assert index["domain_stage_pack_ref"] == PAPER_STUDY_STAGE_PACK_REF
    assert index["artifact_native_contract_ref"] == "mas-opl-stage-native-artifact-contract.v1"
    assert index["physical_stage_folder_kernel"]["contract_ref"] == (
        "contracts/opl-framework/stage-artifact-runtime-contract.json"
    )
    assert index["physical_stage_folder_kernel"]["locator"] == {
        "domain_id": "med-autoscience",
        "program_id": "mas-paper-study",
        "topic_id": "001-risk",
        "deliverable_id": "paper-study",
    }
    assert tuple(index["authority_boundary"]["mas_authority_functions"]) == EXPECTED_AUTHORITY_FUNCTIONS
    assert index["authority_boundary"]["artifact_first_can_determine_stage_progress"] is True
    assert index["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert index["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert index["authority_boundary"]["can_authorize_submission_readiness"] is False
    assert index["authority_boundary"]["can_write_mas_truth"] is False
    assert index["authority_boundary"]["provider_completion_is_paper_progress"] is False
    assert index["current_stage"]["stage_id"] == "01-study_intake"
    assert index["next_owner_action"]["owner"] == "01-study_intake"
    assert index["next_owner_action"]["next_owner"] == "01-study_intake"
    assert index["next_owner_action"]["action_type"] == "materialize_stage_artifact_delta"
    assert index["next_owner_action"]["required_output_surface"]
    assert index["next_owner_action"]["artifact_native_contract_ref"] == (
        "mas-opl-stage-native-artifact-contract.v1"
    )
    assert index["next_owner_action"]["manifest_ref"].endswith("/stage_manifest.json")
    assert index["next_owner_action"]["receipt_ref"].endswith("/receipts/owner_receipt.json")
    assert set(index["allowed_artifact_statuses"]) == set(ALLOWED_ARTIFACT_STATUSES)
    assert [stage["stage_id"] for stage in index["stages"]] == list(EXPECTED_PAPER_STUDY_STAGE_IDS)

    for stage in index["stages"]:
        assert stage["domain_stage_pack_ref"] == PAPER_STUDY_STAGE_PACK_REF
        assert stage["required_output_refs"]
        assert stage["authority_boundary"]["mas_authority_functions"] == list(EXPECTED_AUTHORITY_FUNCTIONS)
        for artifact_ref in stage["required_output_refs"]:
            assert artifact_ref["role"]
            assert artifact_ref["role_contract_ref"].startswith(
                f"{PAPER_STUDY_STAGE_PACK_REF}#/stages/"
            )
            assert artifact_ref["interface_is_artifact_role"] is True
            assert artifact_ref["ref_is_locator_only"] is True
            assert artifact_ref["body_included"] is False
            assert artifact_ref["source"] == "mas_paper_study_stage_pack_stable_role"

    study_intake = index["stages"][0]
    assert study_intake["stage_id"] == "01-study_intake"
    assert study_intake["artifact_status"] == "missing"
    assert study_intake["stage_progress_status"] == "artifact_required"
    assert study_intake["stage_folder_contract"]["stage_folder_ref"] == (
        "artifacts/stage_outputs/01-study_intake"
    )
    assert study_intake["manifest_requirements"]["ref"].endswith("/stage_manifest.json")
    assert study_intake["receipt_requirements"]["ref"].endswith("/receipts/owner_receipt.json")
    assert study_intake["artifact_classification"]["status"] == "missing"
    assert study_intake["next_missing_surface"] == study_intake["required_output_refs"][0]["ref"]
    assert study_intake["freshness"]["status"] == "red_missing"


def test_paper_study_stage_pack_defines_publication_handoff_done_gate() -> None:
    stage_pack_path = Path(__file__).resolve().parents[1] / PAPER_STUDY_STAGE_PACK_REF
    stage_pack = json.loads(stage_pack_path.read_text(encoding="utf-8"))
    terminal_stage = next(
        stage
        for stage in stage_pack["stages"]
        if stage["stage_id"] == "08-publication_package_handoff"
    )

    assert stage_pack["machine_boundary"]["physical_study_file_migration_required"] is True
    assert stage_pack["machine_boundary"]["physical_study_file_migration_target"] == (
        "artifacts/stage_outputs/_body_authority/paper_authority_cutover"
    )
    assert terminal_stage["done_definition"]["publication_ready_claim_requires"]
    assert terminal_stage["done_definition"]["valid_terminal_outcomes"] == [
        "ready_for_human_submission_handoff",
        "human_gate_required",
        "route_back_with_concrete_owner_action",
        "typed_blocker_or_stop_loss",
    ]
    assert terminal_stage["quality_gate"]["publication_ready_authority"]
    assert terminal_stage["advance_gate"]["terminal_stage"] is True
    assert terminal_stage["advance_gate"]["completion_signal"] == "handoff_owner_receipt"


def test_stage_artifact_index_consumes_opl_physical_stage_folder_kernel(
    monkeypatch,
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    physical = _write_opl_physical_stage_attempt(
        tmp_path / "opl-state",
        study_id="001-risk",
        stage_id="01-study_intake",
        attempt_id="attempt-001",
        output_ref="study_truth_snapshot.json",
    )
    _write_json(
        study_root / "artifacts" / "stage_outputs" / "scout" / "route_recommendation.json",
        {"route": "baseline"},
    )
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    assert index["stage_artifact_runtime_contract_ref"] == (
        "contracts/opl-framework/stage-artifact-runtime-contract.json"
    )
    assert index["physical_stage_folder_kernel"]["status"] == "observed"
    assert index["physical_stage_folder_kernel"]["locator"] == {
        "domain_id": "med-autoscience",
        "program_id": "mas-paper-study",
        "topic_id": "001-risk",
        "deliverable_id": "paper-study",
    }
    assert index["physical_stage_folder_kernel"]["deliverable_root"] == physical["deliverable_root"]
    study_intake = index["stages"][0]
    assert study_intake["physical_stage_folder_kernel"]["status"] == "observed"
    assert study_intake["stage_folder_contract"]["source_of_truth"] == "opl_physical_stage_folder_kernel"
    assert study_intake["stage_folder_contract"]["stage_folder_ref"] == physical["stage_root"]
    assert study_intake["stage_folder_contract"]["attempt_root"] == physical["attempt_root"]
    assert study_intake["stage_folder_contract"]["current_pointer_ref"] == physical["current_pointer_ref"]
    assert study_intake["stage_folder_contract"]["latest_pointer_ref"] == physical["latest_pointer_ref"]
    assert study_intake["manifest_requirements"]["ref"] == physical["manifest_ref"]
    assert study_intake["receipt_requirements"]["ref"] == physical["receipt_ref"]
    assert study_intake["artifact_classification"]["source_of_truth"] == (
        "opl_physical_stage_folder_kernel"
    )
    assert study_intake["artifact_classification"]["current"] == ["study_truth_snapshot.json"]
    assert study_intake["artifact_classification"]["manifest_hash_refs"] == [
        {
            "kind": "output",
            "path": "study_truth_snapshot.json",
            "sha256": "0" * 64,
        }
    ]
    assert study_intake["artifact_classification"]["owner_receipt_refs"] == [
        "mas-owner-receipt:01-study_intake:attempt-001"
    ]
    assert study_intake["artifact_classification"]["conformance_refs"] == {
        "current_pointer_ref": physical["current_pointer_ref"],
        "latest_pointer_ref": physical["latest_pointer_ref"],
        "stage_json_ref": str(Path(physical["stage_root"]) / "stage.json"),
        "attempt_json_ref": str(Path(physical["attempt_root"]) / "attempt.json"),
        "manifest_ref": physical["manifest_ref"],
        "lineage_events_ref": str(Path(physical["deliverable_root"]) / "lineage" / "events.jsonl"),
        "lineage_graph_ref": str(Path(physical["deliverable_root"]) / "lineage" / "graph.json"),
    }
    assert study_intake["artifact_classification"]["promotion"]["state"] == (
        "current_pointer_promoted"
    )
    assert study_intake["artifact_classification"]["semantic_validation"]["status"] == "accepted"
    assert study_intake["artifact_classification"]["consumability"]["status"] == "passed"
    assert study_intake["artifact_classification"]["lineage"]["status"] == "observed"
    assert study_intake["artifact_classification"]["retention"]["status"] == "covered"
    assert study_intake["current_pointer"]["pointer_ref"] == physical["current_pointer_ref"]
    assert study_intake["current_pointer"]["attempt_id"] == "attempt-001"
    assert study_intake["legacy_observed_artifact_refs"][0]["classification"] == (
        "migration_historical_declared_ref"
    )
    assert study_intake["legacy_observed_artifact_refs"][0]["counts_as_current_artifact_delta"] is False


def test_stage_artifact_index_rejects_physical_stage_without_current_pointer_promotion(
    monkeypatch,
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    physical = _write_opl_physical_stage_attempt(
        tmp_path / "opl-state",
        study_id="001-risk",
        stage_id="01-study_intake",
        attempt_id="attempt-001",
        output_ref="study_truth_snapshot.json",
    )
    _write_json(
        Path(physical["current_pointer_ref"]),
        {
            "surface_kind": "opl_stage_artifact_runtime_current",
            "current_stage": {
                "stage_id": "01-study_intake",
                "status": "success",
                "latest_attempt_id": "stale-attempt",
            },
        },
    )
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    study_intake = index["stages"][0]
    assert study_intake["artifact_classification"]["status"] == "missing"
    assert study_intake["artifact_classification"]["fail_closed"] is True
    assert study_intake["artifact_classification"]["promotion"]["state"] == (
        "current_pointer_stale"
    )
    assert study_intake["artifact_classification"]["fail_closed_reason"] == (
        "current_pointer_stale"
    )
    assert study_intake["observed_artifact_refs"] == []


def test_stage_artifact_index_rejects_physical_stage_without_domain_receipt_or_retention(
    monkeypatch,
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    physical = _write_opl_physical_stage_attempt(
        tmp_path / "opl-state",
        study_id="001-risk",
        stage_id="01-study_intake",
        attempt_id="attempt-001",
        output_ref="study_truth_snapshot.json",
    )
    manifest_path = Path(physical["manifest_ref"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["decision_receipt_refs"] = []
    manifest["restore_refs"] = []
    manifest["retention_refs"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    study_intake = index["stages"][0]
    assert study_intake["artifact_classification"]["status"] == "missing"
    assert study_intake["artifact_classification"]["promotion"]["state"] == (
        "current_pointer_promoted"
    )
    assert study_intake["artifact_classification"]["semantic_validation"]["status"] == (
        "missing_domain_receipt"
    )
    assert study_intake["artifact_classification"]["retention"]["status"] == (
        "restore_contract_required"
    )
    assert study_intake["artifact_classification"]["consumability"]["failed_checks"] == [
        "retention_restore",
        "domain_validation",
    ]
    assert study_intake["observed_artifact_refs"] == []


def test_stage_artifact_index_exposes_legacy_taxonomy_migration_without_dual_current_truth(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    migration = index["legacy_taxonomy_migration"]
    assert migration["surface_kind"] == "mas_paper_study_legacy_taxonomy_migration"
    assert migration["status"] == "migration_manifest"
    assert migration["current_truth_policy"] == {
        "workbench_must_not_display_two_current_truths": True,
        "legacy_route_is_current_truth": False,
        "current_truth_surface": "paper_study_stage_pack",
        "legacy_semantics": "tombstone_backfilled_current_pointer",
    }
    assert [item["legacy_route_id"] for item in migration["mappings"]] == list(
        EXPECTED_LEGACY_ROUTE_IDS
    )
    assert {item["target_stage_id"] for item in migration["mappings"]} == set(
        EXPECTED_PAPER_STUDY_STAGE_IDS
    )
    assert all(item["legacy_route_is_current_truth"] is False for item in migration["mappings"])
    assert all(
        item["migration_semantics"] == "tombstone_backfilled_current_pointer"
        for item in migration["mappings"]
    )
    assert all(
        item["workbench_display_current_truth"] == "paper_study_stage_pack"
        for item in migration["mappings"]
    )
    assert set(index["legacy_taxonomy_migration"]["role_mapping"].keys()) == set(
        EXPECTED_PAPER_STUDY_STAGE_IDS
    )
    assert not set(EXPECTED_LEGACY_ROUTE_IDS).intersection(
        {stage["stage_id"] for stage in index["stages"]}
    )
    by_stage = {stage["stage_id"]: stage for stage in index["stages"]}
    assert all("legacy_taxonomy_migration_read_model" in stage for stage in index["stages"])
    intake_migration = by_stage["01-study_intake"]["legacy_taxonomy_migration_read_model"]
    assert intake_migration["surface_kind"] == "legacy_stage_taxonomy_migration_stage_read_model"
    assert intake_migration["legacy_route_ids"] == ["scout"]
    assert intake_migration["stage_native_stage_id"] == "01-study_intake"
    assert intake_migration["migration_status"] == "current_pointer_backfill_required"
    assert intake_migration["backfilled_current_pointer"] == {
        "status": "missing",
        "pointer_ref": "artifacts/stage_outputs/01-study_intake/current_pointer.json",
        "promotion_state": "attempt_output_required",
    }
    assert intake_migration["tombstone_or_provenance_required"] is True
    assert intake_migration["tombstone_or_provenance_ref"] == (
        f"{PAPER_STUDY_STAGE_PACK_REF}#/legacy_taxonomy_migration/mappings/scout"
    )
    assert intake_migration["workbench_dual_truth_forbidden"] is True
    assert intake_migration["legacy_route_is_current_truth"] is False
    assert intake_migration["current_truth_surface"] == "paper_study_stage_pack"
    assert intake_migration["fail_closed"] is True
    assert intake_migration["fail_closed_reason"] == "current_pointer_backfill_required"
    assert intake_migration["next_owner_action"]["action_type"] == "materialize_stage_artifact_delta"
    assert intake_migration["next_owner_action"]["owner"] == "01-study_intake"
    assert intake_migration["authority"]["writes_mas_truth"] is False
    assert intake_migration["body_included"] is False
    review_migration = by_stage["07-independent_review_and_revision"][
        "legacy_taxonomy_migration_read_model"
    ]
    assert review_migration["legacy_route_ids"] == ["review", "decision"]
    assert {
        item["legacy_route_id"]: item["stage_native_stage_id"]
        for item in review_migration["legacy_stage_mappings"]
    } == {
        "review": "07-independent_review_and_revision",
        "decision": "07-independent_review_and_revision",
    }
    assert review_migration["tombstone_or_provenance_refs"] == [
        f"{PAPER_STUDY_STAGE_PACK_REF}#/legacy_taxonomy_migration/mappings/review",
        f"{PAPER_STUDY_STAGE_PACK_REF}#/legacy_taxonomy_migration/mappings/decision",
    ]


def test_stage_artifact_index_does_not_count_existing_files_without_manifest_and_receipt_as_current(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    _write_json(
        study_root / "artifacts" / "stage_outputs" / "scout" / "route_recommendation.json",
        {"route": "baseline"},
    )
    _write_json(
        study_root / "artifacts" / "stage_outputs" / "baseline" / "baseline_artifact_set.json",
        {"status": "ready"},
    )
    _write_text(study_root / "artifacts" / "stage_outputs" / "baseline" / "baseline_summary.md")
    _write_json(
        study_root / "artifacts" / "stage_outputs" / "baseline" / "next_route_recommendation.json",
        {"next_route": "analysis-campaign"},
    )

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    by_stage = {stage["stage_id"]: stage for stage in index["stages"]}
    assert by_stage["01-study_intake"]["artifact_status"] == "missing_manifest_or_receipt"
    assert by_stage["01-study_intake"]["stage_progress_status"] == "artifact_contract_required"
    assert by_stage["01-study_intake"]["observed_artifact_refs"] == []
    assert by_stage["01-study_intake"]["legacy_observed_artifact_refs"]
    assert by_stage["01-study_intake"]["legacy_observed_artifact_refs"][0][
        "migration_semantics"
    ] == "tombstone_backfilled_current_pointer"
    assert by_stage["01-study_intake"]["legacy_observed_artifact_refs"][0][
        "counts_as_current_artifact_delta"
    ] is False
    assert by_stage["01-study_intake"]["artifact_classification"]["status"] == (
        "missing_manifest_or_receipt"
    )
    assert by_stage["01-study_intake"]["artifact_classification"]["historical"] == [
        "artifacts/stage_outputs/scout/route_recommendation.json"
    ]
    assert by_stage["01-study_intake"]["artifact_classification"]["current"] == []
    assert by_stage["03-data_asset_and_cohort_build"]["artifact_status"] == (
        "missing_manifest_or_receipt"
    )
    assert by_stage["03-data_asset_and_cohort_build"]["stage_progress_status"] == (
        "artifact_contract_required"
    )
    assert by_stage["03-data_asset_and_cohort_build"]["artifact_classification"]["status"] == (
        "missing_manifest_or_receipt"
    )
    assert by_stage["03-data_asset_and_cohort_build"]["artifact_classification"]["current"] == []
    assert index["current_stage"]["stage_id"] == "01-study_intake"
    assert index["next_owner_action"]["owner"] == "01-study_intake"
    assert index["next_owner_action"]["artifact_native_contract_ref"] == (
        "mas-opl-stage-native-artifact-contract.v1"
    )
    assert index["next_owner_action"]["manifest_ref"].endswith("/stage_manifest.json")
    assert index["next_owner_action"]["receipt_ref"].endswith("/receipts/owner_receipt.json")


def test_stage_artifact_index_counts_manifest_receipt_and_required_outputs_as_current(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    for ref in STUDY_INTAKE_REFS:
        if ref.endswith(".json"):
            _write_json(study_root / ref, {"status": "ready"})
        else:
            _write_text(study_root / ref)
    _write_stage_native_contract(
        study_root,
        stage_id="01-study_intake",
        refs=STUDY_INTAKE_REFS,
    )

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    study_intake = index["stages"][0]
    assert study_intake["artifact_status"] == "artifact_delta_present"
    assert study_intake["stage_progress_status"] == "artifact_delta_present"
    assert study_intake["artifact_classification"]["status"] == "current"
    assert study_intake["artifact_classification"]["current"] == sorted(STUDY_INTAKE_REFS)
    assert study_intake["artifact_classification"]["fail_closed"] is False
    assert {item["classification"] for item in study_intake["observed_artifact_refs"]} == {
        "current"
    }
    assert study_intake["legacy_taxonomy_migration_read_model"]["migration_status"] == (
        "backfilled_current_pointer_present"
    )
    assert study_intake["legacy_taxonomy_migration_read_model"]["fail_closed"] is False
    assert study_intake["legacy_taxonomy_migration_read_model"]["next_owner_action"] == {}
    assert study_intake["next_missing_surface"] is None
    assert index["current_stage"]["stage_id"] == "02-protocol_and_analysis_plan"
    assert index["next_owner_action"]["owner"] == "02-protocol_and_analysis_plan"


def test_stage_artifact_materializer_backfills_stage_native_refs_without_copying_legacy_bodies(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk", "title": "Risk"})
    _write_text(study_root / "brief.md", "question\n")
    _write_text(study_root / "protocol.md", "protocol\n")
    _write_json(study_root / "data_input" / "dataset_manifest.yaml", {"datasets": []})
    _write_json(study_root / "paper" / "baseline_inventory.json", {"status": "ready"})
    _write_json(study_root / "paper" / "evidence_ledger.json", {"claims": []})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claims": []})
    _write_text(study_root / "paper" / "draft.md", "draft\n")
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"verdict": {}})
    _write_json(study_root / "artifacts" / "controller_decisions" / "latest.json", {"decision": "continue"})

    before = build_stage_artifact_index(study_id="001-risk", study_root=study_root)
    assert before["current_stage"]["stage_id"] == "01-study_intake"
    assert before["stages"][0]["artifact_status"] == "missing"

    result = materialize_stage_artifact_delta(
        study_id="001-risk",
        study_root=study_root,
        workspace_root=workspace_root,
        apply=True,
    )

    assert result["status"] == "materialized"
    assert result["body_policy"] == {
        "refs_only": True,
        "legacy_body_copied": False,
        "paper_or_package_mutated": False,
        "publication_truth_mutated": False,
    }
    assert result["materialized_stage_count"] == 8
    assert result["stages"][0]["stage_id"] == "01-study_intake"
    assert result["stages"][0]["status"] == "materialized"

    after = build_stage_artifact_index(study_id="001-risk", study_root=study_root)
    assert after["current_stage"]["stage_id"] == "08-publication_package_handoff"
    assert after["stages"][0]["artifact_status"] == "artifact_delta_present"
    assert after["stages"][-1]["artifact_status"] == "artifact_delta_present"
    assert after["next_owner_action"]["action_type"] == "publication_handoff_owner_gate"
    assert after["next_owner_action"]["required_delta_kind"] == (
        "publication_handoff_owner_receipt_or_typed_blocker"
    )
    assert after["stages"][0]["artifact_classification"]["current"] == sorted(STUDY_INTAKE_REFS)
    first_ref_path = study_root / STUDY_INTAKE_REFS[0]
    first_ref = json.loads(first_ref_path.read_text(encoding="utf-8"))
    assert first_ref["surface_kind"] == "stage_artifact_ref_bundle"
    assert first_ref["body_included"] is False
    assert first_ref["legacy_body_copied"] is False
    assert first_ref["source_refs"]
    assert all("content" not in item for item in first_ref["source_refs"])

    manifest = json.loads(
        (
            study_root
            / "artifacts"
            / "stage_outputs"
            / "01-study_intake"
            / "stage_manifest.json"
        ).read_text(encoding="utf-8")
    )
    receipt = json.loads(
        (
            study_root
            / "artifacts"
            / "stage_outputs"
            / "01-study_intake"
            / "receipts/owner_receipt.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["artifact_refs"] == STUDY_INTAKE_REFS
    assert manifest["source_artifact_refs_are_locators_only"] is True
    assert manifest["surface_kind"] == "stage_manifest"
    assert manifest["owner_receipt_refs"] == ["receipts/owner_receipt.json"]
    assert manifest["required_input_artifact_refs"] == ["inputs/consumed_artifact_refs.json"]
    assert manifest["lineage_refs"] == ["lineage/prov.json"]
    assert manifest["projection_refs"] == ["projection/current_owner_delta.json"]
    assert receipt["receipt_kind"] == "stage_artifact_delta"
    assert receipt["surface_kind"] == "mas_stage_owner_receipt"
    assert receipt["owner"] == "MedAutoScience"
    assert receipt["authority_type"] == "medical_owner_receipt"
    assert receipt["can_authorize_publication_ready"] is False
    assert receipt["can_authorize_submission_ready"] is False
    stage_run = stage_run_kernel_projection_from_stage_folder(
        study_root / "artifacts" / "stage_outputs" / "01-study_intake"
    )
    assert stage_run["status"] == "DomainAccepted"
    assert stage_run["completion_authority"] == "owner_receipt"
    assert stage_run["current_owner_delta"]["action"] == "advance_stage_from_stage_artifact_receipt"

    sqlite_path = domain_authority_refs_index.workspace_authority_refs_index_path(workspace_root)
    inspection = domain_authority_refs_index.inspect_authority_refs_index(sqlite_path)
    assert inspection["status"] == "ready"
    assert inspection["tables"]["paper_work_unit_receipts"] == 8


def test_stage_artifact_materializer_keeps_terminal_publication_handoff_gate_open(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk", "title": "Risk"})
    _write_text(study_root / "brief.md", "question\n")

    result = materialize_stage_artifact_delta(
        study_id="001-risk",
        study_root=study_root,
        workspace_root=workspace_root,
        apply=True,
    )

    terminal = result["stages"][-1]
    assert terminal["stage_id"] == "08-publication_package_handoff"
    assert terminal["stage_closeout"] == {
        "minimum_durable_output_present": True,
        "owner_receipt_present": True,
        "nonterminal_stage_can_advance": False,
        "publishability_required_for_stage_advance": True,
        "submission_readiness_required_for_stage_advance": True,
        "terminal_publication_handoff": True,
    }
    stage_root = study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff"
    manifest = json.loads((stage_root / "stage_manifest.json").read_text(encoding="utf-8"))
    assert manifest["projection_refs"] == []
    assert manifest["projection_authority"] == {
        "surface_kind": "stage_artifact_projection_authority",
        "stage_id": "08-publication_package_handoff",
        "materializer_can_write_current_owner_delta": False,
        "owner_answer_projection_required": True,
        "owner_answer_projection_ref": "projection/current_owner_delta.json",
        "owner_answer_projection_writer": "publication_handoff_stage_projection.py",
        "stage_run_current_authority": "opl_stage_transition_authority_only",
    }
    assert not (stage_root / "projection" / "current_owner_delta.json").exists()
    stage_run = stage_run_kernel_projection_from_stage_folder(stage_root)
    assert stage_run["status"] == "Terminalizing"
    assert stage_run["completion_authority"] is None
    assert stage_run["current_owner_delta"] == {
        "owner": "publication_gate_owner",
        "action": "publication_handoff_owner_gate",
        "reason": "terminal_stage_artifact_delta_materialized",
        "source_ref": str((stage_root / "receipts" / "owner_receipt.json").resolve()),
        "source_kind": "stage_artifact_receipt",
    }

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)
    assert index["current_stage"]["stage_id"] == "08-publication_package_handoff"
    assert index["next_owner_action"]["action_type"] == "publication_handoff_owner_gate"
    assert index["next_owner_action"]["required_delta_kind"] == (
        "publication_handoff_owner_receipt_or_typed_blocker"
    )
    assert index["next_owner_action"]["can_authorize_publication_readiness"] is False
    assert index["next_owner_action"]["can_authorize_submission_readiness"] is False


def test_stage_artifact_materializer_nonterminal_stage_closeout_does_not_require_publishability(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk"})
    _write_text(study_root / "brief.md", "question\n")

    result = materialize_stage_artifact_delta(
        study_id="001-risk",
        study_root=study_root,
        workspace_root=tmp_path / "workspace",
        stage_ids=("01-study_intake",),
        apply=True,
    )

    receipt_ref = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "01-study_intake"
        / "receipts/owner_receipt.json"
    )
    receipt = json.loads(receipt_ref.read_text(encoding="utf-8"))
    assert result["stages"][0]["stage_closeout"] == {
        "minimum_durable_output_present": True,
        "owner_receipt_present": True,
        "nonterminal_stage_can_advance": True,
        "publishability_required_for_stage_advance": False,
        "submission_readiness_required_for_stage_advance": False,
        "terminal_publication_handoff": False,
    }
    assert receipt["stage_closeout"] == result["stages"][0]["stage_closeout"]

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)
    assert index["current_stage"]["stage_id"] == "02-protocol_and_analysis_plan"
    assert index["stages"][0]["artifact_status"] == "artifact_delta_present"


def test_stage_artifact_materializer_bounds_directory_source_ref_sampling(tmp_path: Path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk"})
    intake_root = study_root / "artifacts" / "intake"
    for index in range(75):
        _write_text(intake_root / f"source-{index:03d}.json", "{}\n")

    result = materialize_stage_artifact_delta(
        study_id="001-risk",
        study_root=study_root,
        workspace_root=tmp_path / "workspace",
        stage_ids=("01-study_intake",),
        apply=True,
    )

    source_readiness = next(
        bundle
        for bundle in result["stages"][0]["role_bundles"]
        if bundle["role"] == "source_readiness_assessment"
    )
    assert len(source_readiness["source_refs"]) == 20
    assert all(item["body_included"] is False for item in source_readiness["source_refs"])


def test_stage_artifact_index_projects_opl_artifact_operating_contract_fields(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    for ref in STUDY_INTAKE_REFS:
        if ref.endswith(".json"):
            _write_json(study_root / ref, {"status": "ready"})
        else:
            _write_text(study_root / ref)
    _write_stage_native_contract(
        study_root,
        stage_id="01-study_intake",
        refs=STUDY_INTAKE_REFS,
    )

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    assert index["operating_contract"] == {
        "contract_ref": "contracts/opl-framework/artifact-operating-contract.json",
        "contract_id": "opl-artifact-operating-contract.v1",
        "version": 1,
        "progress_basis": [
            "current_pointer",
            "accepted_receipt",
            "valid_manifest",
            "existing_artifacts",
        ],
        "manifest_validity_is_semantic_receipt_validity": False,
        "controller_read_model_currentness_role": "repair_projection_diagnostic_only",
    }
    assert index["promotion_protocol"] == [
        "attempt_output",
        "manifest_valid",
        "receipt_accepted",
        "current_pointer_promoted",
        "projection_rebuilt",
    ]
    assert index["consumability_gate"]["required_checks"] == [
        "role",
        "hash",
        "source",
        "current_truth",
        "receipt_authority",
        "lineage",
        "retention_restore",
        "domain_validation",
    ]
    study_intake = index["stages"][0]
    assert study_intake["current_pointer"]["promotion_state"] == "current_pointer_promoted"
    assert study_intake["current_pointer"]["basis"] == {
        "existing_artifacts": True,
        "manifest_valid": True,
        "receipt_accepted": True,
    }
    assert study_intake["consumability_gate"]["status"] == "ready_for_consumability_validation"
    assert study_intake["consumability_gate"]["checks"]["retention_restore"]["required_before_cleanup"] is True
    assert study_intake["consumability_gate"]["checks"]["domain_validation"]["authority"] == (
        "mas_domain_owner"
    )


def test_stage_artifact_index_does_not_promote_current_pointer_from_manifest_validity_only(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    for ref in STUDY_INTAKE_REFS:
        if ref.endswith(".json"):
            _write_json(study_root / ref, {"status": "ready"})
        else:
            _write_text(study_root / ref)
    base = study_root / "artifacts" / "stage_outputs" / "01-study_intake"
    _write_json(
        base / "stage_manifest.json",
        {
            "surface_kind": "stage_manifest",
            "schema_version": 1,
            "stage_id": "01-study_intake",
            "artifact_refs": STUDY_INTAKE_REFS,
        },
    )
    _write_json(
        base / "receipts/owner_receipt.json",
        {
            "surface_kind": "mas_stage_owner_receipt",
            "schema_version": 1,
            "stage_id": "01-study_intake",
            "receipt_kind": "stage_artifact_delta",
            "artifact_refs": STUDY_INTAKE_REFS,
        },
    )

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    study_intake = index["stages"][0]
    assert study_intake["artifact_classification"]["status"] == "broken"
    assert study_intake["current_pointer"]["basis"] == {
        "existing_artifacts": True,
        "manifest_valid": True,
        "receipt_accepted": False,
    }
    assert study_intake["current_pointer"]["promotion_state"] == "receipt_required"
    assert study_intake["current_pointer"]["manifest_validity_is_semantic_receipt_validity"] is False
    assert study_intake["consumability_gate"]["status"] == "blocked"


def test_stage_artifact_index_classifies_uncontracted_stage_file_as_orphan(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    for ref in STUDY_INTAKE_REFS:
        if ref.endswith(".json"):
            _write_json(study_root / ref, {"status": "ready"})
        else:
            _write_text(study_root / ref)
    _write_text(
        study_root / "artifacts" / "stage_outputs" / "01-study_intake" / "scratch.md"
    )
    _write_stage_native_contract(
        study_root,
        stage_id="01-study_intake",
        refs=STUDY_INTAKE_REFS,
    )

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    study_intake = index["stages"][0]
    assert study_intake["artifact_status"] == "blocked_by_required_artifact"
    assert study_intake["stage_progress_status"] == "artifact_contract_broken"
    assert study_intake["observed_artifact_refs"] == []
    assert study_intake["artifact_classification"]["status"] == "orphan"
    assert study_intake["artifact_classification"]["orphan"] == [
        "artifacts/stage_outputs/01-study_intake/scratch.md"
    ]
    assert study_intake["artifact_classification"]["fail_closed"] is True
    assert study_intake["artifact_classification"]["fail_closed_reason"] == "orphan"


def test_stage_artifact_index_marks_stale_platform_repair_without_counting_as_progress(tmp_path: Path) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    _write_json(
        study_root / "artifacts" / "stage_outputs" / "write" / "manuscript_draft.json",
        {"artifact_path": "paper/draft.md"},
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {"controller_action": "run_gate_clearing_batch"},
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"current_required_action": "route_back_same_line"},
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {"provider_attempt": "completed"},
    )

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    manuscript_stage = next(
        stage for stage in index["stages"] if stage["stage_id"] == "06-manuscript_authoring"
    )
    assert manuscript_stage["artifact_status"] == "missing_manifest_or_receipt"
    assert manuscript_stage["observed_artifact_refs"] == []
    assert manuscript_stage["legacy_observed_artifact_refs"][0]["ref"].endswith(
        "manuscript_draft.json"
    )
    assert {item["source"] for item in index["stale_platform_repairs"]} == {
        "controller_decisions/latest.json",
        "publication_eval/latest.json",
        "runtime/provider_liveness",
    }
    assert all(item["counts_as_paper_progress"] is False for item in index["stale_platform_repairs"])
    assert index["provider_liveness"]["provider_completion_is_paper_progress"] is False


def test_stage_artifact_index_rejects_unknown_artifact_status() -> None:
    assert set(ALLOWED_ARTIFACT_STATUSES) == {
        "missing",
        "missing_manifest_or_receipt",
        "partial",
        "artifact_delta_present",
        "ready_for_review",
        "blocked_by_required_artifact",
        "terminal_delivered",
    }
