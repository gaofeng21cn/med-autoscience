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
