from __future__ import annotations

import importlib
import json
import zipfile
from pathlib import Path

from tests.control_plane_route_helpers import writable_route_context
from tests.profile_test_helpers import write_profile
from tests.test_study_delivery_sync_cases.shared import dump_json, make_delivery_workspace, write_text


def _write_profile_for_workspace(path: Path, *, workspace_root: Path) -> None:
    write_profile(
        path,
        workspace_root=workspace_root,
        med_deepscientist_repo_root=workspace_root.parent / "med-deepscientist",
        hermes_agent_repo_root=workspace_root.parent / "_external" / "hermes-agent",
    )


def _load_profile(profile_path: Path):
    profiles = importlib.import_module("med_autoscience.profiles")
    return profiles.load_profile(profile_path)


def test_export_inspection_package_materializes_blocked_draft_without_submission_authority(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_inspection_export")
    workspace_root = tmp_path / "repo"
    study_root = workspace_root / "studies" / "obesity_multicenter_phenotype_atlas"
    paper_root = study_root / "paper"
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=workspace_root)
    write_text(study_root / "study.yaml", "study_id: obesity_multicenter_phenotype_atlas\n")
    write_text(paper_root / "draft.md", "# Draft\n\nCurrent style for inspection.\n")
    write_text(paper_root / "build" / "review_manuscript.md", "# Review\n\nHuman inspection copy.\n")
    dump_json(paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "status": "blocked"})
    dump_json(paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(paper_root / "evidence_ledger.json", {"schema_version": 1})
    dump_json(paper_root / "review" / "review_ledger.json", {"schema_version": 1})
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1})
    (paper_root / "submission_minimal").mkdir(parents=True)

    result = module.export_inspection_package(
        profile=_load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
        source="test",
    )

    package_root = study_root / "manuscript" / "inspection_package"
    package_zip = study_root / "manuscript" / "inspection_package.zip"
    manifest_path = study_root / "manuscript" / "inspection_package_manifest.json"
    receipt_path = study_root / "artifacts" / "inspection_package" / "latest.json"
    assert result["status"] == "inspection_package_materialized"
    assert result["surface_kind"] == "inspection_package"
    assert result["inspection_only"] is True
    assert result["not_for_submission"] is True
    assert result["gate_blocked_snapshot"] is True
    assert result["can_submit"] is False
    assert result["authority"]["can_authorize_submission"] is False
    assert result["authority"]["can_authorize_publication_quality"] is False
    assert result["authority"]["can_clear_publishability_gate"] is False
    assert result["authority"]["can_dispatch_delivery_sync"] is False
    assert result["source_policy"]["writes_current_package"] is False
    assert result["source_policy"]["writes_submission_minimal"] is False
    assert result["source_policy"]["reads_submission_minimal_as_export_source"] is False
    assert package_root.exists()
    assert package_zip.exists()
    assert manifest_path.exists()
    assert receipt_path.exists()
    assert (study_root / "artifacts" / "inspection_package" / "manifest.json").exists()
    assert (study_root / "artifacts" / "inspection_package" / "source_inventory.json").exists()
    assert (study_root / "artifacts" / "inspection_package" / "checksums.json").exists()
    assert (study_root / "artifacts" / "inspection_package" / "blocked_context.json").exists()
    assert (study_root / "artifacts" / "inspection_package" / "export_receipt.json").exists()
    assert not (study_root / "manuscript" / "current_package").exists()
    assert not (study_root / "manuscript" / "current_package.zip").exists()
    assert not list((paper_root / "submission_minimal").iterdir())
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["surface_kind"] == "inspection_package_export_receipt"
    assert receipt["human_inspection_only"] is True
    assert receipt["can_submit"] is False
    assert receipt["can_authorize_submission"] is False
    assert receipt["can_authorize_publication_quality"] is False
    assert receipt["can_clear_publishability_gate"] is False
    assert receipt["can_dispatch_delivery_sync"] is False
    assert receipt["writes"]["current_package"] is False
    assert receipt["writes"]["submission_minimal"] is False
    with zipfile.ZipFile(package_zip) as archive:
        names = set(archive.namelist())
    assert "paper_snapshot/draft.md" in names
    assert "paper_snapshot/build/review_manuscript.md" in names
    assert "paper_snapshot/paper_bundle_manifest.json" in names
    assert "inspection_package_manifest.json" in names
    assert not any(name.startswith("paper_snapshot/submission_minimal/") for name in names)


def test_export_inspection_package_includes_chinese_residual_reviewer_issues(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_inspection_export")
    reviewer_fixtures = importlib.import_module("tests.test_reviewer_refinement_loop")
    workspace_root = tmp_path / "repo"
    study_root = workspace_root / "studies" / "001-risk"
    paper_root = study_root / "paper"
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=workspace_root)
    write_text(study_root / "study.yaml", "study_id: 001-risk\n")
    write_text(paper_root / "draft.md", "# Draft\n\nCurrent style for inspection.\n")
    write_text(paper_root / "build" / "review_manuscript.md", "# Review\n\nHuman inspection copy.\n")
    dump_json(paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "status": "blocked"})
    dump_json(paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(paper_root / "evidence_ledger.json", {"schema_version": 1})
    dump_json(
        paper_root / "review" / "review_ledger.json",
        {
            "schema_version": 1,
            "status": "open",
            "review_repair_cycle": {"current_round": 3},
            "concerns": [
                {
                    "concern_id": "claim-strength",
                    "reviewer_id": "ai_reviewer",
                    "summary": "Claim strength exceeds the current evidence ledger.",
                    "severity": "major",
                    "status": "in_progress",
                    "owner_action": "bounded_review_repair",
                    "repeat_count": 3,
                    "revision_links": [
                        {
                            "revision_id": "review-repair-round-3",
                            "revision_log_path": str(paper_root / "review" / "review_ledger.json"),
                        }
                    ],
                }
            ],
        },
    )
    payload = reviewer_fixtures._blocking_payload(study_root)
    dump_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)

    result = module.export_inspection_package(
        profile=_load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
        source="test",
    )

    package_root = study_root / "manuscript" / "inspection_package"
    package_zip = study_root / "manuscript" / "inspection_package.zip"
    residual_markdown = package_root / "residual_reviewer_issues.md"
    residual_json = package_root / "residual_reviewer_issues.json"
    assert result["residual_user_review"]["required"] is True
    assert result["residual_user_review"]["language"] == "zh-CN"
    assert result["residual_user_review"]["issue_count"] == 3
    assert result["residual_user_review_targets"] == {
        "residual_user_review_markdown": str(residual_markdown.resolve()),
        "residual_user_review_json": str(residual_json.resolve()),
    }
    markdown = residual_markdown.read_text(encoding="utf-8")
    assert "# 残留 reviewer 意见人工审阅表" in markdown
    assert "它们不应继续卡住论文进入下一阶段" in markdown
    payload_json = json.loads(residual_json.read_text(encoding="utf-8"))
    assert payload_json["status"] == "pending_user_review"
    with zipfile.ZipFile(package_zip) as archive:
        names = set(archive.namelist())
    assert "residual_reviewer_issues.md" in names
    assert "residual_reviewer_issues.json" in names
    receipt = json.loads(
        (study_root / "artifacts" / "inspection_package" / "latest.json").read_text(encoding="utf-8")
    )
    assert receipt["residual_user_review"]["required"] is True
    assert receipt["can_authorize_submission"] is False


def test_export_inspection_package_reuses_current_authorized_package_when_current(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_inspection_export")
    sync_module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=tmp_path / "repo")
    sync_module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        route_context=writable_route_context(),
    )

    result = module.export_inspection_package(
        profile=_load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
        source="test",
    )

    assert result["status"] == "authorized_current_package_available"
    assert result["surface_kind"] == "inspection_package"
    assert result["recommended_human_review_path"] == str(
        (study_root / "manuscript" / "current_package.zip").resolve()
    )
    assert result["inspection_only"] is True
    assert result["can_submit"] is False
    assert not (study_root / "manuscript" / "inspection_package.zip").exists()
    receipt = json.loads(
        (study_root / "artifacts" / "inspection_package" / "latest.json").read_text(encoding="utf-8")
    )
    assert receipt["receipt_status"] == "authorized_current_package_available"
    assert receipt["human_inspection_only"] is True
    assert receipt["writes"]["current_package"] is False
    manifest = json.loads(
        (study_root / "manuscript" / "inspection_package_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["source_package_status"] == "authorized_current_package"
    assert manifest["authority"]["can_authorize_submission_dispatch"] is False
