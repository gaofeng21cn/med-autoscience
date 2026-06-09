from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study, write_text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_profile(path: Path, profile) -> None:
    path.write_text(
        "\n".join(
            [
                f'name = "{profile.name}"',
                f'workspace_root = "{profile.workspace_root}"',
                f'runtime_root = "{profile.runtime_root}"',
                f'studies_root = "{profile.studies_root}"',
                f'portfolio_root = "{profile.portfolio_root}"',
                f'med_deepscientist_runtime_root = "{profile.med_deepscientist_runtime_root}"',
                f'med_deepscientist_repo_root = "{profile.med_deepscientist_repo_root}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_current_inputs(study_root: Path) -> None:
    write_text(study_root / "paper" / "draft.md", "current draft\n")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"surface": "evidence"})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"surface": "review"})


def _write_stage(study_root: Path, stage_id: str = "08-publication_package_handoff") -> Path:
    stage_root = study_root / "artifacts" / "stage_outputs" / stage_id
    _write_json(
        stage_root / "stage_manifest.json",
        {
            "surface_kind": "stage_manifest",
            "stage_id": stage_id,
            "artifact_refs": ["paper/draft.md"],
            "typed_blocker_refs": [f"artifacts/stage_outputs/{stage_id}/receipts/typed_blocker.json"],
        },
    )
    _write_json(
        stage_root / "inputs" / "consumed_artifact_refs.json",
        {"refs": ["paper/draft.md"]},
    )
    _write_json(stage_root / "receipts" / "typed_blocker.json", {"blocker_id": "publication_gate_blocked"})
    _write_json(stage_root / "lineage" / "prov.json", {"stage_id": stage_id})
    _write_json(
        stage_root / "projection" / "current_owner_delta.json",
        {
            "latest_owner_answer_kind": "typed_blocker",
            "latest_owner_answer_ref": f"artifacts/stage_outputs/{stage_id}/receipts/typed_blocker.json",
        },
    )
    return stage_root


def test_study_workspace_status_apply_materializes_stage_index_and_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_workspace_status")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_current_inputs(study_root)
    stage_root = _write_stage(study_root)

    dry_run = module.run_study_workspace_status(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    dry_study = dry_run["studies"][0]
    assert dry_study["status"] == "needs_materialization"
    assert dry_study["stage_index"]["current_stage_id"] == "08-publication_package_handoff"
    assert dry_study["validation"]["stage_native"]["blockers"] == []
    assert "stage_required_dir_missing:08-publication_package_handoff:outputs" in dry_study["validation"][
        "stage_native"
    ]["materialization_gaps"]
    assert (study_root / "control" / "stage_index.json").exists() is False

    result = module.run_study_workspace_status(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    study = result["studies"][0]
    stage_index = json.loads((study_root / "control" / "stage_index.json").read_text(encoding="utf-8"))
    validation = json.loads((study_root / "_archive" / "migration_manifest" / "validation_result.json").read_text())
    assert study["status"] == "ready"
    assert stage_index["schema_version"] == "mas.study_stage_index.v1"
    assert stage_index["current_stage_id"] == "08-publication_package_handoff"
    assert stage_index["current_stage"]["typed_blocker_ref"].endswith("receipts/typed_blocker.json")
    assert (stage_root / "outputs").is_dir()
    assert (stage_root / "role_artifacts").is_dir()
    assert (study_root / "STUDY_STATUS.md").is_file()
    assert (study_root / "paper.yaml").is_file()
    assert (study_root / "control" / "next_action.json").is_file()
    assert (study_root / "publication" / "current_package" / "STATUS.json").is_file()
    assert (study_root / "_archive" / "migration_manifest" / "current_truth_map.json").is_file()
    assert (study_root / "_archive" / "migration_manifest" / "legacy_provenance_map.json").is_file()
    assert validation["target_state_reference_doc"] == "docs/source/study_workspace_target_state.md"


def test_study_workspace_status_routes_blocked_clean_room_surface_to_quality_repair(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_workspace_status")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_current_inputs(study_root)
    _write_stage(study_root)
    _write_json(
        study_root / "artifacts" / "supervision" / "paper_clean_room_rebuild" / "latest.json",
        {"status": "ready", "clean_workspace_root": str(study_root / "clean-room")},
    )
    _write_json(
        study_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json",
        {
            "gate_kind": "medical_publication_surface_control",
            "status": "blocked",
            "blockers": [
                "missing_medical_story_contract",
                "statistical_reviewer_audit_missing_or_incomplete",
            ],
        },
    )

    result = module.run_study_workspace_status(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    next_action = result["studies"][0]["next_action"]
    persisted = json.loads((study_root / "control" / "next_action.json").read_text(encoding="utf-8"))
    assert next_action["action_id"] == "stage-native-next-action::run_quality_repair_batch"
    assert next_action["action_type"] == "run_quality_repair_batch"
    assert next_action["owner"] == "write"
    assert next_action["source_surface"] == "artifacts/reports/medical_publication_surface/latest.json"
    assert next_action["next_work_unit"] == "medical_publication_surface_blocked_write_repair"
    assert persisted == next_action


def test_study_workspace_status_fails_closed_for_runtime_root_as_study_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_workspace_status")
    profile = make_profile(tmp_path)
    study_id = "runtime-root-study"
    runtime_root = profile.runtime_root / study_id
    write_text(runtime_root / "study.yaml", "study_id: runtime-root-study\n")
    _write_current_inputs(runtime_root)
    _write_stage(runtime_root)

    result = module.build_study_workspace_status(
        profile=profile,
        study_id=study_id,
        study_root=runtime_root,
        apply=False,
    )

    assert result["status"] == "blocked"
    assert "study_root_not_under_profile_studies_root" in result["blockers"]
    assert "runtime_quest_root_cannot_be_canonical_study_root" in result["blockers"]


def test_study_workspace_status_fails_closed_when_current_stage_lacks_manifest_or_answer(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_workspace_status")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_current_inputs(study_root)
    stage_root = study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff"
    (stage_root / "inputs").mkdir(parents=True)
    (stage_root / "projection").mkdir(parents=True)

    result = module.build_study_workspace_status(
        profile=profile,
        study_id=study_id,
        apply=False,
    )

    assert result["status"] == "blocked"
    assert "current_stage_manifest_missing:08-publication_package_handoff" in result["blockers"]
    assert "current_stage_owner_receipt_or_typed_blocker_missing:08-publication_package_handoff" in result["blockers"]


def test_study_workspace_status_apply_materializes_workspace_index_and_migration_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_workspace_status")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "obesity_multicenter_phenotype_atlas"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_current_inputs(study_root)

    dry_run = module.run_study_workspace_status(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )
    dry_study = dry_run["studies"][0]
    assert dry_study["status"] == "blocked"
    assert "stage_outputs_root_missing" in dry_study["blockers"]
    assert (study_root / "control" / "stage_index.json").exists() is False

    result = module.run_study_workspace_status(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    study = result["studies"][0]
    stage_id = "00-workspace_target_state_migration"
    stage_root = study_root / "artifacts" / "stage_outputs" / stage_id
    workspace_index = json.loads((profile.workspace_root / "workspace_index.json").read_text(encoding="utf-8"))
    stage_index = json.loads((study_root / "control" / "stage_index.json").read_text(encoding="utf-8"))
    blocker = json.loads((stage_root / "receipts" / "typed_blocker.json").read_text(encoding="utf-8"))
    package_status = json.loads((study_root / "publication" / "current_package" / "STATUS.json").read_text())

    assert study["status"] == "typed_blocked"
    assert study["blockers"] == ["workspace_target_state_migration_required"]
    assert stage_index["current_stage_id"] == stage_id
    assert stage_index["current_stage"]["typed_blocker_ref"].endswith("receipts/typed_blocker.json")
    assert blocker["blocker_id"] == "workspace_target_state_migration_required"
    assert blocker["authority_boundary"]["paper_body_mutation_allowed"] is False
    assert package_status["status"] == "not_ready"
    assert workspace_index["schema_version"] == "mas.workspace_index.v1"
    assert workspace_index["studies"][0]["canonical_study_root"] == f"studies/{study_id}"
    assert workspace_index["studies"][0]["runtime_root_is_current_paper_truth"] is False
    assert (profile.workspace_root / "WORKSPACE_STATUS.md").is_file()
    assert (profile.workspace_root / "workspace.yaml").is_file()


def test_study_workspace_status_apply_keeps_missing_inputs_as_blockers_inside_migration_stage(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_workspace_status")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "001-lineage-pfs"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)

    result = module.run_study_workspace_status(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    study = result["studies"][0]
    blocker = json.loads(
        (
            study_root
            / "artifacts"
            / "stage_outputs"
            / "00-workspace_target_state_migration"
            / "receipts"
            / "typed_blocker.json"
        ).read_text(encoding="utf-8")
    )
    assert study["status"] == "blocked"
    assert "current_manuscript_missing" in study["blockers"]
    assert "workspace_target_state_migration_required" in study["blockers"]
    assert blocker["hard_blockers"] == []
    assert "current_manuscript_missing" in blocker["original_blockers"]
    assert (study_root / "STUDY_STATUS.md").is_file()
