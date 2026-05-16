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
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "profile.local.toml"
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
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "profile.local.toml"
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


def test_workspace_legacy_physical_cleanup_apply_archives_root_and_rewrites_refs(tmp_path: Path) -> None:
    cleanup = importlib.import_module("med_autoscience.controllers.workspace_legacy_physical_cleanup")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    legacy_root = workspace_root / "ops" / "med-deepscientist"
    legacy_quest_root = legacy_root / "runtime" / "quests" / "quest-alpha"
    _write_profile(profile_path, workspace_root)
    _write_text(legacy_quest_root / "quest.yaml", "quest_id: quest-alpha\n")
    binding_path = workspace_root / "studies" / "010-alpha" / "runtime_binding.yaml"
    delivery_path = workspace_root / "studies" / "010-alpha" / "manuscript" / "delivery_manifest.json"
    controller_path = workspace_root / "studies" / "010-alpha" / "artifacts" / "controller_decisions" / "latest.json"
    _write_text(
        binding_path,
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
        delivery_path,
        {"source_paths": [str(legacy_quest_root / "paper" / "submission_minimal" / "manuscript.docx")]},
    )
    _write_json(
        controller_path,
        {"source_refs": [str(legacy_quest_root / "controller_decisions" / "old.json")]},
    )
    _write_json(
        workspace_root / "artifacts" / "runtime" / "monolith_migration" / "latest.json",
        {"source_topology": {"runtime_home": str(legacy_root / "runtime")}},
    )

    dry_run = cleanup.apply_workspace_legacy_physical_cleanup(profile_path=profile_path, apply=False)

    assert dry_run["mode"] == "dry_run"
    assert dry_run["can_apply"] is True
    assert dry_run["archive_plan"]["move_required"] is True
    assert len(dry_run["rewrite_plan"]) == 5
    assert legacy_root.exists()

    applied = cleanup.apply_workspace_legacy_physical_cleanup(profile_path=profile_path, apply=True)

    assert applied["status"] == "applied"
    archive_root = Path(applied["archive_plan"]["archive_root"])
    assert not legacy_root.exists()
    assert archive_root.exists()
    assert (archive_root / "runtime" / "quests" / "quest-alpha" / "quest.yaml").exists()
    tombstone_path = legacy_root.parent / "med-deepscientist.TOMBSTONE.json"
    assert tombstone_path.exists()
    assert str(archive_root) in profile_path.read_text(encoding="utf-8")
    assert str(archive_root) in binding_path.read_text(encoding="utf-8")
    assert str(archive_root) in delivery_path.read_text(encoding="utf-8")
    assert str(archive_root) in controller_path.read_text(encoding="utf-8")
    latest_receipt = workspace_root / "artifacts" / "runtime" / "legacy_physical_cleanup" / "latest.json"
    assert latest_receipt.exists()
    post_audit = cleanup.build_workspace_legacy_physical_cleanup_audit(profile_path=profile_path)
    assert post_audit["legacy_root_candidate"]["exists"] is False
    assert post_audit["legacy_root_candidate"]["reference_counts"] == {}
    assert post_audit["next_required_action"] == "no_legacy_physical_cleanup_required"

    replay = cleanup.apply_workspace_legacy_physical_cleanup(profile_path=profile_path, apply=True)
    assert replay["archive_plan"]["archive_root"] == str(archive_root)
    assert replay["archive_result"]["status"] == "existing_archive_reused"


def test_workspace_legacy_physical_cleanup_apply_creates_tombstone_when_root_absent(tmp_path: Path) -> None:
    cleanup = importlib.import_module("med_autoscience.controllers.workspace_legacy_physical_cleanup")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    legacy_root = workspace_root / "ops" / "med-deepscientist"
    _write_profile(profile_path, workspace_root)

    applied = cleanup.apply_workspace_legacy_physical_cleanup(profile_path=profile_path, apply=True)

    archive_root = Path(applied["archive_plan"]["archive_root"])
    assert applied["status"] == "applied"
    assert applied["archive_result"]["status"] == "legacy_root_absent_tombstone_created"
    assert archive_root.exists()
    assert not legacy_root.exists()
    assert str(archive_root / "runtime") in profile_path.read_text(encoding="utf-8")
    assert (legacy_root.parent / "med-deepscientist.TOMBSTONE.json").exists()


def test_workspace_legacy_physical_cleanup_apply_replays_provenance_rewrite_after_archive(
    tmp_path: Path,
) -> None:
    cleanup = importlib.import_module("med_autoscience.controllers.workspace_legacy_physical_cleanup")
    workspace_root = tmp_path / "workspace"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "profile.local.toml"
    legacy_root = workspace_root / "ops" / "med-deepscientist"
    archive_root = workspace_root / "runtime" / "archives" / "legacy_mds" / "stamp" / "med-deepscientist"
    _write_profile(profile_path, workspace_root)
    _write_json(
        legacy_root.parent / "med-deepscientist.TOMBSTONE.json",
        {
            "schema_version": 1,
            "surface_kind": "legacy_mds_physical_root_tombstone",
            "legacy_root": str(legacy_root),
            "archive_root": str(archive_root),
            "status": "moved",
        },
    )
    archive_root.mkdir(parents=True)
    guidance_path = workspace_root / "AGENTS.md"
    storage_path = workspace_root / "storage_audit" / "latest.json"
    lifecycle_path = workspace_root / "artifacts" / "runtime" / "lifecycle_migration" / "latest.json"
    readme_path = workspace_root / "README.md"
    study_path = workspace_root / "studies" / "010-alpha" / "study.yaml"
    evidence_path = workspace_root / "studies" / "010-alpha" / "paper" / "evidence_ledger.json"
    autonomy_path = workspace_root / "studies" / "010-alpha" / "artifacts" / "autonomy" / "ai_doctor_requests" / "req.json"
    eval_path = workspace_root / "studies" / "010-alpha" / "artifacts" / "eval_hygiene" / "latest.json"
    supervision_path = (
        workspace_root
        / "studies"
        / "010-alpha"
        / "artifacts"
        / "runtime"
        / "runtime_supervision"
        / "latest.json"
    )
    scratch_path = workspace_root / "runtime" / "quests" / "quest-alpha" / ".ds" / "codex_homes" / "log.json"
    receipt_path = workspace_root / "artifacts" / "runtime" / "legacy_physical_cleanup" / "latest.json"
    _write_text(guidance_path, "Legacy ops path: ops/med-deepscientist/\n")
    _write_text(readme_path, f"Legacy absolute root: {legacy_root}\n")
    _write_text(study_path, f"legacy_root: {legacy_root}\n")
    _write_json(evidence_path, {"legacy_root": str(legacy_root)})
    _write_json(autonomy_path, {"legacy_root": str(legacy_root)})
    _write_json(eval_path, {"legacy_root": str(legacy_root)})
    _write_json(storage_path, {"legacy_root": str(legacy_root)})
    _write_json(lifecycle_path, {"legacy_runtime": str(legacy_root / "runtime")})
    _write_json(supervision_path, {"legacy_quest_root": str(legacy_root / "runtime" / "quests")})
    _write_json(scratch_path, {"legacy_root": str(legacy_root)})
    _write_json(receipt_path, {"legacy_root": str(legacy_root)})

    dry_run = cleanup.apply_workspace_legacy_physical_cleanup(profile_path=profile_path, apply=False)

    assert dry_run["archive_plan"]["archive_root"] == str(archive_root)
    assert dry_run["archive_plan"]["move_required"] is False
    assert {item["relpath"] for item in dry_run["rewrite_plan"]} == {
        "ops/medautoscience/profiles/profile.local.toml",
        "AGENTS.md",
        "README.md",
        "artifacts/runtime/lifecycle_migration/latest.json",
        "storage_audit/latest.json",
        "studies/010-alpha/artifacts/autonomy/ai_doctor_requests/req.json",
        "studies/010-alpha/artifacts/eval_hygiene/latest.json",
        "studies/010-alpha/artifacts/runtime/runtime_supervision/latest.json",
        "studies/010-alpha/paper/evidence_ledger.json",
        "studies/010-alpha/study.yaml",
    }

    applied = cleanup.apply_workspace_legacy_physical_cleanup(profile_path=profile_path, apply=True)

    assert applied["archive_result"]["status"] == "existing_archive_reused"
    assert "runtime/archives/legacy_mds/stamp/med-deepscientist/" in guidance_path.read_text(encoding="utf-8")
    assert str(archive_root) in storage_path.read_text(encoding="utf-8")
    assert str(archive_root) in lifecycle_path.read_text(encoding="utf-8")
    assert str(archive_root) in readme_path.read_text(encoding="utf-8")
    assert str(archive_root) in study_path.read_text(encoding="utf-8")
    assert str(archive_root) in evidence_path.read_text(encoding="utf-8")
    assert str(archive_root) in autonomy_path.read_text(encoding="utf-8")
    assert str(archive_root) in eval_path.read_text(encoding="utf-8")
    assert str(archive_root) in supervision_path.read_text(encoding="utf-8")
    assert str(archive_root) in profile_path.read_text(encoding="utf-8")
    assert str(legacy_root) in scratch_path.read_text(encoding="utf-8")
    assert str(legacy_root) in receipt_path.read_text(encoding="utf-8")
    post_audit = cleanup.build_workspace_legacy_physical_cleanup_audit(profile_path=profile_path)
    assert post_audit["legacy_root_candidate"]["reference_counts"] == {}
