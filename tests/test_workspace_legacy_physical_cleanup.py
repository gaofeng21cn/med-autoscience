from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_profile(path: Path, workspace_root: Path) -> None:
    _write_text(
        path,
        "\n".join(
            [
                'name = "cleanup-fixture"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "runtime" / "quests"}"',
                f'managed_runtime_home = "{workspace_root / "runtime"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "",
                "[historical_fixture_ref]",
                f'runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
                "",
                "[explicit_archive_import_ref]",
                f'runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
                f'controlled_backend_repo_root = "{workspace_root / "ops" / "med-deepscientist" / "repo"}"',
                "",
            ]
        ),
    )


def test_workspace_legacy_physical_cleanup_blocks_legacy_root_when_refs_remain(tmp_path: Path) -> None:
    cleanup = importlib.import_module("med_autoscience.controllers.workspace_legacy_physical_cleanup")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    legacy_root = workspace_root / "ops" / "med-deepscientist"
    legacy_quest_root = legacy_root / "runtime" / "quests" / "quest-alpha"
    _write_profile(profile_path, workspace_root)
    _write_text(legacy_quest_root / "quest.yaml", "quest_id: quest-alpha\n")
    _write_text(
        workspace_root / "studies" / "010-alpha" / "runtime_binding.yaml",
        "\n".join(
            [
                "schema_version: 1",
                "study_id: 010-alpha",
                "quest_id: quest-alpha",
                f"runtime_home: {workspace_root / 'runtime'}",
                f"runtime_root: {workspace_root / 'runtime' / 'quests'}",
                "historical_fixture_ref:",
                f"  old_quest_root: {legacy_quest_root}",
                "",
            ]
        ),
    )
    _write_json(
        workspace_root / "studies" / "010-alpha" / "manuscript" / "delivery_manifest.json",
        {
            "source_paths": [
                str(legacy_quest_root / ".ds" / "worktrees" / "paper" / "submission_minimal" / "manuscript.docx")
            ]
        },
    )
    _write_json(
        workspace_root / "artifacts" / "runtime" / "monolith_migration" / "latest.json",
        {"source_topology": {"runtime_home": str(legacy_root / "runtime")}},
    )

    report = cleanup.build_workspace_legacy_physical_cleanup_audit(profile_path=profile_path)

    assert report["surface_kind"] == "workspace_legacy_physical_cleanup_audit"
    assert report["authority_boundary"]["read_only"] is True
    assert report["authority_boundary"]["physical_cleanup_performed"] is False
    assert report["replacement_proof"]["replacement_ready_for_cleanup_audit"] is True
    candidate = report["legacy_root_candidate"]
    assert candidate["exists"] is True
    assert candidate["physical_cleanup_allowed"] is False
    assert candidate["candidate_action"] == "blocked_archive_or_tombstone_required"
    assert "current_truth_or_delivery_refs_still_point_to_legacy_root" in candidate["blockers"]
    assert "legacy_root_has_retained_references" in candidate["blockers"]
    assert candidate["reference_counts"]["current_truth_or_delivery_ref"] == 1
    assert candidate["reference_counts"]["migration_ledger_provenance_ref"] == 1
    assert report["next_required_action"] == "archive_or_tombstone_references_before_physical_delete"


def test_workspace_legacy_physical_cleanup_reports_safe_wrapper_without_deleting(tmp_path: Path) -> None:
    cleanup = importlib.import_module("med_autoscience.controllers.workspace_legacy_physical_cleanup")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    wrapper = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    _write_profile(profile_path, workspace_root)
    _write_text(
        wrapper,
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
        "runtime ensure-supervision\n",
    )

    report = cleanup.build_workspace_legacy_physical_cleanup_audit(profile_path=profile_path)

    wrappers = report["retired_workspace_service_wrappers"]
    assert wrappers["candidate_count"] == 4
    assert wrappers["cleanup_ready_count"] == 1
    assert wrappers["items"][0]["candidate_action"] == "delete_safe"
    assert wrapper.exists()
    assert report["authority_boundary"]["writes_workspace"] is False
