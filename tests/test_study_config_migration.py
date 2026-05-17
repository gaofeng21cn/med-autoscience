from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def test_study_config_clean_migration_apply_renames_retired_manual_finish_guard(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_config_migration")
    manual_finish = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "001-risk"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8")
        + "\n".join(
            [
                "",
                "manual_finish:",
                "  status: active",
                "  summary: 当前 study 进入旧字段人工收尾。",
                "  next_action_summary: 等待人工完成最后核对。",
                "  compatibility_guard_only: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="manual_finish.compatibility_guard_only is retired"):
        manual_finish.resolve_study_manual_finish_contract(study_root=study_root)

    report = module.run_study_config_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
    )

    migrated_text = study_yaml_path.read_text(encoding="utf-8")
    receipt_path = study_root / "artifacts" / "migration" / "study_config_clean_migration" / "latest.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    contract = manual_finish.resolve_study_manual_finish_contract(study_root=study_root)

    assert report["mode"] == "apply"
    assert report["authority_boundary"]["legacy_reader_compatibility"] is False
    assert "compatibility_guard_only" not in migrated_text
    assert "manual_finish_guard_only: true" in migrated_text
    assert receipt["status"] == "applied"
    assert receipt["authority_boundary"]["reader_fail_closed_for_retired_field"] is True
    assert receipt["field_migrations"][0]["field_path"] == "manual_finish.compatibility_guard_only"
    assert contract is not None
    assert contract.manual_finish_guard_only is True
    assert report["post_apply"]["remaining_migration_required_count"] == 0


def test_study_config_clean_migration_dry_run_does_not_change_reader_fail_closed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_config_migration")
    manual_finish = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "001-risk"
    study_root = write_study(profile.workspace_root, study_id)
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8")
        + "\nmanual_finish:\n  status: active\n  summary: Legacy guard.\n  compatibility_guard_only: true\n",
        encoding="utf-8",
    )

    report = module.run_study_config_clean_migration(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
    )

    assert report["mode"] == "dry_run"
    assert report["studies"][0]["migration_required"] is True
    assert report["studies"][0]["apply_allowed"] is True
    assert "compatibility_guard_only: true" in study_yaml_path.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="manual_finish.compatibility_guard_only is retired"):
        manual_finish.resolve_study_manual_finish_contract(study_root=study_root)


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
