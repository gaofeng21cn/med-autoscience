from __future__ import annotations

import importlib
import json
import zipfile
from pathlib import Path

from tests.test_cli_cases.shared import write_profile
from tests.test_study_delivery_sync_cases.shared import dump_json, make_delivery_workspace, write_text
from tests.control_plane_route_helpers import writable_route_context


def _write_profile_for_workspace(path: Path, *, workspace_root: Path) -> None:
    write_profile(
        path,
        workspace_root=workspace_root,
        med_deepscientist_repo_root=workspace_root.parent / "med-deepscientist",
        hermes_agent_repo_root=workspace_root.parent / "_external" / "hermes-agent",
    )


def test_delivery_inspector_reports_v2_source_mirror_and_read_only_policy(tmp_path: Path) -> None:
    sync_module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    inspector = importlib.import_module("med_autoscience.controllers.delivery_inspector")
    profiles = importlib.import_module("med_autoscience.profiles")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=tmp_path / "repo")

    sync_module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        route_context=writable_route_context(),
    )

    result = inspector.inspect_study_delivery(
        profile=profiles.load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
    )

    assert result["surface"] == "delivery_inspector"
    assert result["mutation_policy"] == {"read_only": True, "writes_package": False}
    assert result["source_package"]["role"] == "controller_authorized_source"
    assert result["source_package"]["root"] == str(paper_root / "submission_minimal")
    assert result["source_package"]["layout_status"] == "v2"
    assert result["source_package"]["legacy_root_file_status"]["status"] == "absent"
    assert result["human_package"]["role"] == "human_facing_mirror"
    assert result["human_package"]["root"] == str(study_root / "manuscript" / "current_package")
    assert result["human_package"]["layout_status"] == "v2"
    assert result["human_package"]["audit_completeness"]["status"] == "complete"
    assert result["human_package"]["reproducibility_completeness"]["status"] == "complete"
    assert result["human_package"]["legacy_root_file_status"]["status"] == "absent"
    assert result["zip"]["path"] == str(study_root / "manuscript" / "current_package.zip")
    assert result["zip"]["exists"] is True
    assert result["freshness"]["verdict"] == "current"
    assert result["source_signature"]["delivery"] == result["source_signature"]["evaluated"]
    assert "medautosci study delivery-sync" in result["next_sync_command"]
    with zipfile.ZipFile(study_root / "manuscript" / "current_package.zip") as archive:
        names = set(archive.namelist())
    assert "audit/submission_manifest.json" in names
    assert "submission_manifest.json" not in names


def test_delivery_inspector_marks_legacy_root_audit_files_without_mutation(tmp_path: Path) -> None:
    inspector = importlib.import_module("med_autoscience.controllers.delivery_inspector")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "repo"
    study_root = workspace_root / "studies" / "001-legacy-delivery"
    paper_root = study_root / "paper"
    source_root = paper_root / "submission_minimal"
    human_root = study_root / "manuscript" / "current_package"
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=workspace_root)
    write_text(study_root / "study.yaml", "study_id: 001-legacy-delivery\n")
    write_text(source_root / "manuscript.docx", "docx")
    write_text(source_root / "paper.pdf", "%PDF-1.4\n")
    dump_json(source_root / "submission_manifest.json", {"schema_version": 1, "source_signature": "legacy-source"})
    dump_json(source_root / "evidence_ledger.json", {"schema_version": 1})
    write_text(human_root / "manuscript.docx", "docx")
    write_text(human_root / "paper.pdf", "%PDF-1.4\n")
    dump_json(human_root / "submission_manifest.json", {"schema_version": 1, "source_signature": "legacy-mirror"})

    result = inspector.inspect_study_delivery(
        profile=profiles.load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
    )

    assert result["freshness"]["verdict"] == "legacy"
    assert result["source_package"]["layout_status"] == "legacy"
    assert result["source_package"]["legacy_root_file_status"]["status"] == "present"
    assert result["human_package"]["layout_status"] == "legacy"
    assert result["human_package"]["legacy_root_file_status"]["status"] == "present"
    assert result["mutation_policy"]["read_only"] is True
    assert not (source_root / "audit").exists()
    assert not (human_root / "audit").exists()


def test_delivery_inspector_cli_supports_public_publication_alias_json(tmp_path: Path, capsys) -> None:
    sync_module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    cli = importlib.import_module("med_autoscience.cli")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=tmp_path / "repo")
    sync_module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        route_context=writable_route_context(),
    )

    exit_code = cli.main(
        [
            "publication",
            "delivery-inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_root.name,
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["freshness"]["verdict"] == "current"
    assert payload["mutation_policy"]["read_only"] is True
    assert payload["human_package"]["role"] == "human_facing_mirror"


def test_delivery_inspector_markdown_names_source_mirror_and_legacy_upgrade(tmp_path: Path) -> None:
    inspector = importlib.import_module("med_autoscience.controllers.delivery_inspector")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "repo"
    study_root = workspace_root / "studies" / "001-legacy-delivery"
    source_root = study_root / "paper" / "submission_minimal"
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=workspace_root)
    write_text(study_root / "study.yaml", "study_id: 001-legacy-delivery\n")
    dump_json(source_root / "submission_manifest.json", {"schema_version": 1})

    result = inspector.inspect_study_delivery(
        profile=profiles.load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
    )
    markdown = inspector.render_delivery_inspection_markdown(result)

    assert "submission_minimal = controller-authorized source" in markdown
    assert "current_package = human-facing mirror" in markdown
    assert "Legacy layout upgrades on the next authorized sync" in markdown
