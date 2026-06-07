from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
)
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
    _write_json(stage_root / "inputs" / "consumed_artifact_refs.json", {"refs": ["paper/draft.md"]})
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


def test_paper_clean_room_rebuild_apply_materializes_verified_input_workspace(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_clean_room_rebuild")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    write_text(study_root / "paper" / "draft.md", "## Results\n\nCurrent accepted result text.\n")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"surface": "evidence_ledger", "claims": []})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"surface": "review_ledger"})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"surface": "claim_evidence_map"})
    _write_json(study_root / "paper" / "figures" / "figure_catalog.json", {"figures": [{"id": "F1"}]})
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"eval_id": "eval-current"})
    _write_json(study_root / "artifacts" / "controller_decisions" / "latest.json", {"decision": "revise"})
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {"status": "blocked", "blockers": ["medical_publication_surface_blocked"]},
    )
    _write_stage(study_root)
    write_text(study_root / ".ds" / "runs" / "stale" / "stdout.jsonl", "{}\n")

    dry_run = module.run_paper_clean_room_rebuild(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    dry_study = dry_run["studies"][0]
    clean_root = Path(dry_study["clean_workspace_root"])
    assert dry_run["mode"] == "dry_run"
    assert clean_root.exists() is False
    assert dry_study["status"] == "ready"
    assert dry_study["missing_required_refs"] == []
    assert dry_study["legacy_residue_policy"]["legacy_runtime_or_ds_residue_imported"] is False

    result = module.run_paper_clean_room_rebuild(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    study = result["studies"][0]
    latest_path = Path(study["descriptor_path"])
    clean_root = Path(study["clean_workspace_root"])
    descriptor = json.loads(latest_path.read_text(encoding="utf-8"))
    assert result["mode"] == "apply"
    assert study["status"] == "ready"
    assert descriptor["surface_kind"] == "paper_clean_room_rebuild"
    assert descriptor["study_workspace_status_ref"].endswith("_archive/migration_manifest/validation_result.json")
    assert descriptor["stage_index_ref"].endswith("control/stage_index.json")
    assert descriptor["target_state_reference_doc"] == "docs/source/study_workspace_target_state.md"
    assert descriptor["stage_native_contract"]["current_stage_receipt_or_typed_blocker_required"] is True
    assert descriptor["authority_boundary"]["promote_to_current_authority_allowed"] is False
    assert descriptor["authority_boundary"]["old_runtime_residue_import_allowed"] is False
    assert (clean_root / "verified_inputs" / "paper" / "draft.md").read_text(encoding="utf-8") == (
        "## Results\n\nCurrent accepted result text.\n"
    )
    assert (clean_root / "verified_inputs" / "paper" / "figures" / "figure_catalog.json").is_file()
    assert not (clean_root / "verified_inputs" / ".ds").exists()
    assert (study_root / "paper" / "draft.md").is_file()
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").is_file()
    assert descriptor["next_required_actions"] == [
        "run_medical_publication_surface_from_clean_room",
        "publishability_gate_replay",
        "route_to_write_review_or_finalize_owner",
        "promote_only_after_publication_gate_passes",
    ]
    next_action = json.loads((study_root / "control" / "next_action.json").read_text(encoding="utf-8"))
    assert next_action["action_id"] == "run_medical_publication_surface_from_clean_room"
    assert next_action["source_surface"] == "artifacts/supervision/paper_clean_room_rebuild/latest.json"


def test_paper_clean_room_rebuild_prefers_stage_authority_current_body(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_clean_room_rebuild")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    current_body = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    write_text(study_root / "paper" / "draft.md", "legacy root draft\n")
    write_text(current_body / "draft.md", "stage authority draft\n")
    _write_json(current_body / "evidence_ledger.json", {"surface": "stage_current_evidence_ledger"})
    _write_json(current_body / "review" / "review_ledger.json", {"surface": "stage_current_review_ledger"})
    _write_stage(study_root)

    result = module.run_paper_clean_room_rebuild(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    study = result["studies"][0]
    clean_root = Path(study["clean_workspace_root"])
    descriptor = json.loads(Path(study["descriptor_path"]).read_text(encoding="utf-8"))
    refs = {ref["surface_id"]: ref for ref in descriptor["verified_input_refs"]}
    assert study["status"] == "ready"
    assert (clean_root / "verified_inputs" / "paper" / "draft.md").read_text(encoding="utf-8") == (
        "stage authority draft\n"
    )
    assert json.loads(
        (clean_root / "verified_inputs" / "paper" / "evidence_ledger.json").read_text(encoding="utf-8")
    ) == {"surface": "stage_current_evidence_ledger"}
    assert refs["current_manuscript"]["source_relative_path"].endswith("current_body/paper/draft.md")
    assert refs["evidence_ledger"]["source_relative_path"].endswith("current_body/paper/evidence_ledger.json")
    assert refs["review_ledger"]["destination_relative_path"] == "paper/review/review_ledger.json"


def test_paper_clean_room_rebuild_uses_artifact_evidence_ledger_fallback(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_clean_room_rebuild")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    write_text(study_root / "paper" / "draft.md", "current root draft\n")
    _write_json(study_root / "artifacts" / "evidence_ledger.json", {"surface": "artifact_evidence_ledger"})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"surface": "review_ledger"})
    _write_stage(study_root)

    result = module.run_paper_clean_room_rebuild(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    study = result["studies"][0]
    clean_root = Path(study["clean_workspace_root"])
    descriptor = json.loads(Path(study["descriptor_path"]).read_text(encoding="utf-8"))
    refs = {ref["surface_id"]: ref for ref in descriptor["verified_input_refs"]}
    assert study["status"] == "ready"
    assert refs["evidence_ledger"]["source_relative_path"] == "artifacts/evidence_ledger.json"
    assert refs["evidence_ledger"]["destination_relative_path"] == "paper/evidence_ledger.json"
    assert json.loads(
        (clean_root / "verified_inputs" / "paper" / "evidence_ledger.json").read_text(encoding="utf-8")
    ) == {"surface": "artifact_evidence_ledger"}


def test_paper_clean_room_rebuild_blocks_when_evidence_ledger_candidates_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_clean_room_rebuild")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    write_text(study_root / "paper" / "draft.md", "current root draft\n")
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"surface": "review_ledger"})
    _write_stage(study_root)

    result = module.run_paper_clean_room_rebuild(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    study = result["studies"][0]
    assert study["status"] == "blocked_study_workspace_status"
    assert study["missing_required_refs"] == ["evidence_ledger"]
    assert "evidence_ledger_missing" in study["workspace_blockers"]


def test_domain_owner_dispatch_executes_paper_clean_room_rebuild_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    write_text(study_root / "paper" / "draft.md", "## Discussion\n\nA current paper delta.\n")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"surface": "evidence_ledger"})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"surface": "review_ledger"})
    _write_stage(study_root)
    route = _owner_route(
        study_id=study_id,
        action_type="paper_clean_room_rebuild_required",
        owner="MedAutoScience",
    )
    route.update(
        {
            "failure_signature": "paper_clean_room_rebuild_required",
            "owner_reason": "paper_clean_room_rebuild_required",
            "source_refs": {
                "work_unit_id": "paper_clean_room_rebuild",
                "work_unit_fingerprint": "paper-clean-room::dm003::current",
                "runtime_health_epoch": "runtime-health::dm003::clean-room",
            },
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "paper_clean_room_rebuild_required.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="paper_clean_room_rebuild_required",
            owner="MedAutoScience",
            required_output_surface="artifacts/supervision/paper_clean_room_rebuild/latest.json",
            owner_route=route,
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("paper_clean_room_rebuild_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    descriptor_path = study_root / "artifacts" / "supervision" / "paper_clean_room_rebuild" / "latest.json"
    assert result["executed_count"] == 1
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_result"]["descriptor_path"] == str(descriptor_path)
    assert descriptor_path.is_file()
