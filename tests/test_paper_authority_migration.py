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


def test_paper_authority_clean_migration_ignores_noncanonical_study_residue(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    write_text(study_root / "manuscript" / "current_package" / "manuscript_submission.md", "# Old\n")

    residue_root = profile.studies_root / "paper-run-dfcc79d2"
    write_text(residue_root / "manuscript" / "current_package" / "manuscript_submission.md", "# Residue\n")

    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(),
        apply=False,
    )

    assert [study["study_id"] for study in report["studies"]] == [study_id]
    assert report["noncanonical_paper_authority_residue_dirs"] == [
        {
            "study_id": "paper-run-dfcc79d2",
            "path": str(residue_root.resolve()),
            "reason": "paper_authority_surface_without_study_marker",
            "surface_ids": ["manuscript_current_package"],
        }
    ]


def test_paper_authority_clean_migration_rejects_selected_noncanonical_residue(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    write_text(
        profile.studies_root / "idea-idea-3839d99b" / "manuscript" / "current_package" / "manuscript_submission.md",
        "# Residue\n",
    )

    try:
        module.run_paper_authority_clean_migration(
            profile_path=profile_path,
            study_ids=("idea-idea-3839d99b",),
            apply=False,
        )
    except ValueError as exc:
        assert "Unknown canonical paper authority study_id" in str(exc)
        assert "idea-idea-3839d99b" in str(exc)
    else:
        raise AssertionError("selected noncanonical residue was accepted as a study")


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
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::new",
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        },
    )
    refreshed_report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )
    assert module.new_mas_authority_eval_current(study_root=study_root) is True
    assert module.cutover_requires_ai_reviewer(study_root=study_root) is False
    assert refreshed_report["studies"][0]["cutover_required"] is False
    assert refreshed_report["studies"][0]["active_surfaces"] == []
    assert refreshed_report["studies"][0]["next_required_actions"] == []


def test_new_mas_authority_established_keeps_interim_eval_consumable_by_ai_reviewer(
    tmp_path: Path,
) -> None:
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
    module.mark_cutover_new_mas_authority_established(
        study_root=study_root,
        publication_eval_ref=str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        eval_id="publication-eval::clean-migration-interim",
        recorded_at="2026-05-18T03:45:29+00:00",
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::clean-migration-interim",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
                "mechanical_projection_used_as_quality_authority": False,
            },
            "verdict": {
                "overall_verdict": "blocked",
                "summary": "Clean migration requires a fresh AI reviewer pass before quality closure or delivery.",
            },
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "Medical journal prose must be reviewed before quality closure.",
                }
            },
            "gaps": [
                {
                    "gap_id": "paper-authority-clean-migration",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "New MAS owners must rebuild authority surfaces.",
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "paper-authority-clean-migration-rebuild",
                    "action_type": "return_to_controller",
                }
            ],
            "future_facing_limitations_plan": [
                {
                    "limitation": "This clean-migration assessment only re-establishes authority.",
                    "impact_on_claim": "Publication claims remain provisional until publication gate reruns.",
                    "required_future_analysis_data_or_design": "Rerun publication gate and delivery sync.",
                    "current_manuscript_wording_must_be_restrained": True,
                }
            ],
        },
    )

    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    study = report["studies"][0]
    assert module.new_mas_authority_eval_current(study_root=study_root) is True
    assert module.cutover_requires_ai_reviewer(study_root=study_root) is False
    assert study["cutover_required"] is False
    assert study["active_surfaces"] == []
    assert study["next_required_actions"] == []


def test_paper_authority_clean_migration_apply_is_idempotent_after_new_mas_authority(
    tmp_path: Path,
) -> None:
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
    module.mark_cutover_new_mas_authority_established(
        study_root=study_root,
        publication_eval_ref=str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        eval_id="publication-eval::new",
        recorded_at="2026-05-17T12:00:00+00:00",
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::new",
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {"decision": "new-mas-controller-surface"},
    )

    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    receipt = json.loads(
        (study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    active_eval = json.loads(
        (study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "new_mas_authority_established"
    assert receipt["new_mas_authority"]["eval_id"] == "publication-eval::new"
    assert active_eval["eval_id"] == "publication-eval::new"
    assert (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert module.new_mas_authority_eval_current(study_root=study_root) is True
    assert report["studies"][0]["cutover_required"] is False
    assert report["studies"][0]["active_surfaces"] == []
    assert report["post_apply"]["active_surface_count"] == 0


def test_pending_cutover_retains_new_mas_non_authoritative_projection(tmp_path: Path) -> None:
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
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::clean-migration-blocked",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
                "mechanical_projection_used_as_quality_authority": False,
            },
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "AI reviewer must judge medical journal prose before closure.",
                }
            },
            "gaps": [
                {
                    "gap_id": "paper-authority-clean-migration",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "New MAS owners must rebuild authority surfaces.",
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "paper-authority-clean-migration-rebuild",
                    "action_type": "return_to_controller",
                }
            ],
            "reviewer_operating_system": {
                "currentness_checks": {
                    "medical_prose_review": {
                        "status": "requested",
                        "authority_source_signature": "paper_authority_clean_migration",
                    },
                    "current_package_freshness": {
                        "status": "fresh",
                        "authority_source_signature": "paper_authority_clean_migration",
                    },
                }
            },
        },
    )

    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    study = report["studies"][0]
    assert study["cutover_required"] is False
    assert study["active_surfaces"] == []
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert study["cutover_receipt"]["status"] == "awaiting_new_mas_authority"
    assert study["next_required_actions"] == [
        "return_to_ai_reviewer_workflow",
        "publication_gate",
        "sync_study_delivery",
    ]


def test_pending_cutover_retains_non_authoritative_publication_gate_projection(
    tmp_path: Path,
) -> None:
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
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "policy_id": "publication_gate_projection_v1",
                "ai_reviewer_required": True,
                "mechanical_projection_used_as_quality_authority": False,
            },
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "ready",
                    "summary": "Projection text cannot authorize quality closure.",
                }
            },
            "recommended_actions": [
                {
                    "action_type": "route_back_same_line",
                    "requires_controller_decision": True,
                }
            ],
        },
    )

    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    study = report["studies"][0]
    assert study["cutover_required"] is False
    assert study["active_surfaces"] == []
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert study["next_required_actions"] == [
        "return_to_ai_reviewer_workflow",
        "publication_gate",
        "sync_study_delivery",
    ]


def test_pending_cutover_still_archives_unknown_publication_eval_reintroduced_after_receipt(
    tmp_path: Path,
) -> None:
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
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"legacy": True})

    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    study = report["studies"][0]
    assert study["cutover_required"] is True
    assert [item["surface_id"] for item in study["active_surfaces"]] == ["publication_eval_latest"]
    assert study["next_required_actions"] == [
        "archive_legacy_paper_authority_surfaces",
        "return_to_ai_reviewer_workflow",
        "publication_gate",
        "sync_study_delivery",
    ]


def test_new_mas_authority_established_fails_closed_when_active_eval_is_overwritten(
    tmp_path: Path,
) -> None:
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
    module.mark_cutover_new_mas_authority_established(
        study_root=study_root,
        publication_eval_ref=str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        eval_id="publication-eval::new",
        recorded_at="2026-05-17T12:00:00+00:00",
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::mechanical",
            "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        },
    )
    report = module.run_paper_authority_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    assert module.new_mas_authority_eval_current(study_root=study_root) is False
    assert module.cutover_requires_ai_reviewer(study_root=study_root) is True
    assert module.cutover_publication_eval_payload(study_root=study_root)["assessment_provenance"]["owner"] == (
        "paper_authority_cutover"
    )
    assert report["studies"][0]["cutover_required"] is True
    assert report["studies"][0]["active_surfaces"] == []
    assert report["studies"][0]["next_required_actions"] == [
        "return_to_ai_reviewer_workflow",
        "publication_gate",
        "sync_study_delivery",
    ]


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
