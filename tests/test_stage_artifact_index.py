from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.stage_artifact_index import (
    ALLOWED_ARTIFACT_STATUSES,
    build_stage_artifact_index,
)
from med_autoscience.stage_surface_contract import MAIN_STAGE_ROUTE_IDS


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


def test_stage_artifact_index_builds_requirements_from_route_contract(tmp_path: Path) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    assert index["surface_kind"] == "stage_artifact_index"
    assert index["schema_version"] == 1
    assert index["study_id"] == "001-risk"
    assert index["artifact_native_contract_ref"] == "mas-opl-stage-native-artifact-contract.v1"
    assert index["authority_boundary"] == {
        "artifact_first_can_determine_stage_progress": True,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "can_write_mas_truth": False,
        "provider_completion_is_paper_progress": False,
    }
    assert index["current_stage"]["stage_id"] == "scout"
    assert index["next_owner_action"]["owner"] == "scout"
    assert index["next_owner_action"]["action_type"] == "materialize_stage_artifact_delta"
    assert index["next_owner_action"]["required_output_surface"]
    assert set(index["allowed_artifact_statuses"]) == set(ALLOWED_ARTIFACT_STATUSES)
    assert [stage["stage_id"] for stage in index["stages"]] == list(MAIN_STAGE_ROUTE_IDS)

    scout = index["stages"][0]
    assert scout["stage_id"] == "scout"
    assert scout["artifact_status"] == "missing"
    assert scout["stage_progress_status"] == "artifact_required"
    assert scout["stage_folder_contract"]["stage_folder_ref"] == "artifacts/stage_outputs/scout"
    assert scout["manifest_requirements"]["ref"].endswith("/stage_artifact_manifest.json")
    assert scout["receipt_requirements"]["ref"].endswith("/owner_receipt.json")
    assert scout["artifact_classification"]["status"] == "missing"
    assert scout["required_output_refs"]
    assert scout["next_missing_surface"] == scout["required_output_refs"][0]["ref"]
    assert scout["freshness"]["status"] == "red_missing"


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
    assert by_stage["scout"]["artifact_status"] == "missing_manifest_or_receipt"
    assert by_stage["scout"]["stage_progress_status"] == "artifact_contract_required"
    assert by_stage["scout"]["observed_artifact_refs"] == []
    assert by_stage["scout"]["legacy_observed_artifact_refs"]
    assert by_stage["scout"]["artifact_classification"]["status"] == "missing_manifest_or_receipt"
    assert by_stage["scout"]["artifact_classification"]["historical"] == [
        "artifacts/stage_outputs/scout/route_recommendation.json"
    ]
    assert by_stage["scout"]["artifact_classification"]["current"] == []
    assert by_stage["baseline"]["artifact_status"] == "missing_manifest_or_receipt"
    assert by_stage["baseline"]["stage_progress_status"] == "artifact_contract_required"
    assert by_stage["baseline"]["artifact_classification"]["status"] == "missing_manifest_or_receipt"
    assert by_stage["baseline"]["artifact_classification"]["current"] == []
    assert index["current_stage"]["stage_id"] == "scout"
    assert index["next_owner_action"]["owner"] == "scout"
    assert index["next_owner_action"]["artifact_native_contract_ref"] == (
        "mas-opl-stage-native-artifact-contract.v1"
    )
    assert index["next_owner_action"]["manifest_ref"].endswith("/stage_artifact_manifest.json")
    assert index["next_owner_action"]["receipt_ref"].endswith("/owner_receipt.json")


def test_stage_artifact_index_counts_manifest_receipt_and_required_outputs_as_current(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    scout_refs = [
        "artifacts/stage_outputs/scout/scout_note.md",
        "artifacts/stage_outputs/scout/literature_scout_os.json",
        "artifacts/stage_outputs/scout/route_recommendation.json",
        "artifacts/stage_outputs/scout/open_questions.json",
    ]
    for ref in scout_refs:
        if ref.endswith(".json"):
            _write_json(study_root / ref, {"status": "ready"})
        else:
            _write_text(study_root / ref)
    _write_stage_native_contract(study_root, stage_id="scout", refs=scout_refs)

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    scout = index["stages"][0]
    assert scout["artifact_status"] == "artifact_delta_present"
    assert scout["stage_progress_status"] == "artifact_delta_present"
    assert scout["artifact_classification"]["status"] == "current"
    assert scout["artifact_classification"]["current"] == sorted(scout_refs)
    assert scout["artifact_classification"]["fail_closed"] is False
    assert {item["classification"] for item in scout["observed_artifact_refs"]} == {"current"}
    assert scout["next_missing_surface"] is None
    assert index["current_stage"]["stage_id"] == "idea"
    assert index["next_owner_action"]["owner"] == "idea"


def test_stage_artifact_index_classifies_uncontracted_stage_file_as_orphan(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    scout_refs = [
        "artifacts/stage_outputs/scout/scout_note.md",
        "artifacts/stage_outputs/scout/literature_scout_os.json",
        "artifacts/stage_outputs/scout/route_recommendation.json",
        "artifacts/stage_outputs/scout/open_questions.json",
    ]
    for ref in scout_refs:
        if ref.endswith(".json"):
            _write_json(study_root / ref, {"status": "ready"})
        else:
            _write_text(study_root / ref)
    _write_text(study_root / "artifacts" / "stage_outputs" / "scout" / "scratch.md")
    _write_stage_native_contract(study_root, stage_id="scout", refs=scout_refs)

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    scout = index["stages"][0]
    assert scout["artifact_status"] == "blocked_by_required_artifact"
    assert scout["stage_progress_status"] == "artifact_contract_broken"
    assert scout["observed_artifact_refs"] == []
    assert scout["artifact_classification"]["status"] == "orphan"
    assert scout["artifact_classification"]["orphan"] == [
        "artifacts/stage_outputs/scout/scratch.md"
    ]
    assert scout["artifact_classification"]["fail_closed"] is True
    assert scout["artifact_classification"]["fail_closed_reason"] == "orphan"


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

    write_stage = next(stage for stage in index["stages"] if stage["stage_id"] == "write")
    assert write_stage["artifact_status"] == "missing_manifest_or_receipt"
    assert write_stage["observed_artifact_refs"] == []
    assert write_stage["legacy_observed_artifact_refs"][0]["ref"].endswith("manuscript_draft.json")
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
