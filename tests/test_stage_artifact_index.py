from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.stage_artifact_index import (
    ALLOWED_ARTIFACT_STATUSES,
    build_stage_artifact_index,
)

PAPER_STUDY_STAGE_PACK_REF = "contracts/mas-paper-study-stage-pack.json"
EXPECTED_PAPER_STUDY_STAGE_IDS = (
    "01-study_intake",
    "02-protocol_and_analysis_plan",
    "03-data_asset_and_cohort_build",
    "04-analysis_execution",
    "05-evidence_synthesis",
    "06-manuscript_authoring",
    "07-independent_review_and_revision",
    "08-publication_package_handoff",
)
EXPECTED_AUTHORITY_FUNCTIONS = (
    "study_truth",
    "source_readiness",
    "reviewer_quality",
    "publication_gate",
    "artifact_package_authority",
    "memory_accept_reject",
    "typed_blocker",
    "medical_owner_receipt",
)
EXPECTED_LEGACY_ROUTE_IDS = (
    "scout",
    "idea",
    "baseline",
    "experiment",
    "analysis-campaign",
    "write",
    "review",
    "finalize",
    "decision",
    "journal-resolution",
)

STUDY_INTAKE_REFS = [
    "artifacts/stage_outputs/01-study_intake/study_truth_snapshot.json",
    "artifacts/stage_outputs/01-study_intake/source_readiness_assessment.json",
    "artifacts/stage_outputs/01-study_intake/study_intake_owner_receipt.json",
]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str = "content\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_stage_native_contract(
    study_root: Path,
    *,
    stage_id: str,
    refs: list[str],
) -> None:
    base = study_root / "artifacts" / "stage_outputs" / stage_id
    _write_json(
        base / "stage_artifact_manifest.json",
        {
            "surface_kind": "stage_artifact_manifest",
            "schema_version": 1,
            "stage_id": stage_id,
            "artifact_refs": refs,
        },
    )
    _write_json(
        base / "owner_receipt.json",
        {
            "surface_kind": "stage_artifact_owner_receipt",
            "schema_version": 1,
            "stage_id": stage_id,
            "owner": stage_id,
            "receipt_kind": "stage_artifact_delta",
            "artifact_refs": refs,
        },
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
    assert study_intake["manifest_requirements"]["ref"].endswith("/stage_artifact_manifest.json")
    assert study_intake["receipt_requirements"]["ref"].endswith("/owner_receipt.json")
    assert study_intake["artifact_classification"]["status"] == "missing"
    assert study_intake["next_missing_surface"] == study_intake["required_output_refs"][0]["ref"]
    assert study_intake["freshness"]["status"] == "red_missing"


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
    assert index["next_owner_action"]["manifest_ref"].endswith("/stage_artifact_manifest.json")
    assert index["next_owner_action"]["receipt_ref"].endswith("/owner_receipt.json")


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
    assert study_intake["next_missing_surface"] is None
    assert index["current_stage"]["stage_id"] == "02-protocol_and_analysis_plan"
    assert index["next_owner_action"]["owner"] == "02-protocol_and_analysis_plan"


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
        base / "stage_artifact_manifest.json",
        {
            "surface_kind": "stage_artifact_manifest",
            "schema_version": 1,
            "stage_id": "01-study_intake",
            "artifact_refs": STUDY_INTAKE_REFS,
        },
    )
    _write_json(
        base / "owner_receipt.json",
        {
            "surface_kind": "stage_artifact_owner_receipt",
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
