from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study, write_text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_paper_authority_clean_migration_dry_run_lists_active_authority_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"legacy": True})
    _write_json(study_root / "artifacts" / "controller_decisions" / "latest.json", {"legacy": True})
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {"status": "fresh", "source_eval_id": "old"},
    )
    write_text(study_root / "manuscript" / "current_package" / "manuscript_submission.md", "# Old\n")
    write_text(study_root / "manuscript" / "current_package.zip", "zip")

    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    study = report["studies"][0]
    assert report["mode"] == "dry_run"
    assert report["authority_boundary"]["legacy_reader_normalization"] is False
    assert study["cutover_required"] is True
    assert {
        item["surface_id"]
        for item in study["active_surfaces"]
    } >= {
        "publication_eval_latest",
        "controller_decision_latest",
        "current_package_freshness_latest",
        "manuscript_current_package",
        "manuscript_current_package_zip",
    }
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json").exists()


def test_paper_authority_clean_migration_apply_archives_active_surfaces_and_requests_ai_reviewer(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"legacy": True})
    _write_json(study_root / "artifacts" / "controller_decisions" / "latest.json", {"legacy": True})
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {"status": "fresh", "source_eval_id": "old"},
    )
    write_text(study_root / "manuscript" / "current_package" / "manuscript_submission.md", "# Old\n")
    write_text(study_root / "manuscript" / "current_package.zip", "zip")

    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    receipt_path = study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))

    assert report["mode"] == "apply"
    assert report["next_required_actions"] == [
        "return_to_ai_reviewer_workflow",
        "publication_gate",
        "sync_study_delivery",
    ]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json").exists()
    assert not (study_root / "manuscript" / "current_package").exists()
    assert not (study_root / "manuscript" / "current_package.zip").exists()
    assert receipt["status"] == "awaiting_new_mas_authority"
    assert receipt["authority_boundary"]["quality_verdict_written"] is False
    assert request["request_kind"] == "return_to_ai_reviewer_workflow"
    assert request["source_surface"] == "paper_authority_clean_migration"
    assert request["required_output"]["writer"] == "ai_reviewer_publication_eval_workflow"
    assert request["paper_authority_cutover_ref"] == str(receipt_path)
    assert all(Path(item["archive_path"]).exists() for item in receipt["archived_surfaces"])


def test_mark_cutover_new_mas_authority_established_closes_pending_cutover(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"legacy": True})

    module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    updated = module.mark_cutover_new_mas_authority_established(
        study_root=study_root,
        publication_eval_ref=str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        eval_id="publication-eval::new",
        recorded_at="2026-05-17T12:00:00+00:00",
    )
    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    receipt = json.loads(
        (study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert updated is not None
    assert receipt["status"] == "new_mas_authority_established"
    assert receipt["new_mas_authority"]["owner"] == "ai_reviewer"
    assert receipt["new_mas_authority"]["eval_id"] == "publication-eval::new"
    assert receipt["authority_boundary"]["quality_verdict_written"] is True
    assert receipt["authority_boundary"]["submission_package_regenerated"] is False
    assert module.cutover_requires_ai_reviewer(study_root=study_root) is False
    assert report["studies"][0]["cutover_required"] is False
    assert report["studies"][0]["active_surfaces"] == []
    assert report["studies"][0]["next_required_actions"] == []


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
