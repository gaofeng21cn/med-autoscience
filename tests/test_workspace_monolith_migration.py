from __future__ import annotations

import importlib
import json
from pathlib import Path

import yaml


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_profile(path: Path, workspace_root: Path) -> None:
    _write_text(
        path,
        "\n".join(
            [
                'name = "dynamic-fixture"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'managed_runtime_home = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "",
            ]
        ),
    )


def _write_study(
    workspace_root: Path,
    study_id: str,
    *,
    quest_id: str,
    legacy_runtime_root: Path,
    paper_sentinel: str = "original manuscript surface\n",
) -> Path:
    study_root = workspace_root / "studies" / study_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_text(
        study_root / "runtime_binding.yaml",
        "\n".join(
            [
                "schema_version: 1",
                f"study_id: {study_id}",
                f"quest_id: {quest_id}",
                f"runtime_home: {legacy_runtime_root}",
                f"runtime_root: {legacy_runtime_root / 'quests'}",
                f"runtime_quests_root: {legacy_runtime_root / 'quests'}",
                "runtime_backend_id: med_autoscience_runtime_os",
                "last_action: resume",
                "",
            ]
        ),
    )
    _write_text(study_root / "paper" / "current_package" / "manuscript.md", paper_sentinel)
    return study_root


def _write_quest(
    runtime_quests_root: Path,
    quest_id: str,
    *,
    study_id: str | None,
    runtime_state: dict[str, object],
    restore_proof: bool = False,
) -> Path:
    quest_root = runtime_quests_root / quest_id
    lines = [f"quest_id: {quest_id}"]
    if study_id is not None:
        lines.append(f"study_id: {study_id}")
    _write_text(quest_root / "quest.yaml", "\n".join(lines) + "\n")
    _write_json(quest_root / ".ds" / "runtime_state.json", {"quest_id": quest_id, **runtime_state})
    if restore_proof:
        proof_root = quest_root / ".ds" / "cold_archive" / "restore_proof_compaction"
        _write_json(
            proof_root / f"{quest_id}.restore_proof.json",
            {
                "status": "verified",
                "archive_sha256": "sha256-fixture",
                "source_file_count": 3,
                "verified_file_count": 3,
            },
        )
        _write_text(proof_root / f"{quest_id}.tar.gz", "archive bytes\n")
    return quest_root


def _build_fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    legacy_runtime_root = workspace_root / "ops" / "med-deepscientist" / "runtime"
    legacy_quests_root = legacy_runtime_root / "quests"
    _write_profile(profile_path, workspace_root)
    _write_study(
        workspace_root,
        "010-alpha-dynamic",
        quest_id="quest-alpha-dynamic",
        legacy_runtime_root=legacy_runtime_root,
    )
    _write_study(
        workspace_root,
        "011-live-dynamic",
        quest_id="quest-live-dynamic",
        legacy_runtime_root=legacy_runtime_root,
    )
    _write_study(
        workspace_root,
        "012-duplicate-dynamic",
        quest_id="quest-duplicate-a",
        legacy_runtime_root=legacy_runtime_root,
    )
    _write_quest(
        legacy_quests_root,
        "quest-alpha-dynamic",
        study_id="010-alpha-dynamic",
        runtime_state={"status": "completed", "active_run_id": None},
        restore_proof=True,
    )
    _write_quest(
        legacy_quests_root,
        "quest-live-dynamic",
        study_id="011-live-dynamic",
        runtime_state={"status": "running", "active_run_id": "run-live", "worker_running": True},
    )
    _write_quest(
        legacy_quests_root,
        "quest-duplicate-a",
        study_id="012-duplicate-dynamic",
        runtime_state={"status": "manual_hold", "active_run_id": None},
    )
    _write_quest(
        legacy_quests_root,
        "quest-duplicate-b",
        study_id="012-duplicate-dynamic",
        runtime_state={"status": "completed", "active_run_id": None},
    )
    _write_quest(
        legacy_quests_root,
        "quest-orphan-dynamic",
        study_id=None,
        runtime_state={"status": "completed", "active_run_id": None},
    )
    return profile_path, workspace_root


def test_workspace_monolith_migration_dry_run_discovers_dynamic_studies_and_legacy_inventory(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.workspace_monolith_migration")
    profile_path, workspace_root = _build_fixture(tmp_path)

    report = migration.run_workspace_monolith_migration(profile_path=profile_path, apply=False)

    assert report["surface_kind"] == "workspace_monolith_migration"
    assert report["mode"] == "dry_run"
    assert report["target_topology"]["runtime_home"] == str(workspace_root / "runtime")
    assert report["target_topology"]["runtime_quests_root"] == str(workspace_root / "runtime" / "quests")
    assert {item["study_id"] for item in report["migrated"]} == {"010-alpha-dynamic"}
    assert report["migrated"][0]["reason"] == "legacy_binding_to_mas_runtime_os"
    assert report["migrated"][0]["old_quest_root"].endswith(
        "ops/med-deepscientist/runtime/quests/quest-alpha-dynamic"
    )
    assert report["migrated"][0]["new_quest_root"].endswith("runtime/quests/quest-alpha-dynamic")
    assert {item["study_id"] for item in report["skipped"]} == {"011-live-dynamic"}
    assert report["skipped"][0]["reason"] == "live_study_requires_controller_pause_quiesce_relaunch"
    assert {item["quest_id"] for item in report["orphan"]} == {"quest-orphan-dynamic"}
    assert {item["study_id"] for item in report["duplicate"]} == {"012-duplicate-dynamic"}
    assert report["duplicate"][0]["reason"] == "multiple_quest_roots_for_study"
    assert report["hardcoded_study_id_policy"]["dynamic_discovery_only"] is True
    assert not (workspace_root / "artifacts" / "runtime" / "monolith_migration" / "latest.json").exists()


def test_workspace_monolith_migration_apply_writes_ledger_and_only_migrates_safe_bindings(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.workspace_monolith_migration")
    profile_path, workspace_root = _build_fixture(tmp_path)
    alpha_paper = workspace_root / "studies" / "010-alpha-dynamic" / "paper" / "current_package" / "manuscript.md"
    live_binding = workspace_root / "studies" / "011-live-dynamic" / "runtime_binding.yaml"
    alpha_paper_before = alpha_paper.read_text(encoding="utf-8")
    live_binding_before = live_binding.read_text(encoding="utf-8")

    report = migration.run_workspace_monolith_migration(profile_path=profile_path, apply=True)

    latest_path = workspace_root / "artifacts" / "runtime" / "monolith_migration" / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    history_path = Path(latest["history_path"])
    assert history_path.exists()
    assert latest["mode"] == "apply"
    assert latest["profile_path"] == str(profile_path.resolve())
    assert latest["restore_proofs"][0]["status"] == "verified"
    assert latest["archive_refs"][0]["archive_path"].endswith("quest-alpha-dynamic.tar.gz")
    assert latest["orphan"] == report["orphan"]
    assert latest["duplicate"] == report["duplicate"]
    assert latest["skipped"][0]["next_required_action"] == "controller_pause_quiesce_relaunch"
    migrated_profile_text = profile_path.read_text(encoding="utf-8")
    assert 'runtime_root = "' + str(workspace_root / "runtime" / "quests") + '"' in migrated_profile_text
    assert 'managed_runtime_home = "' + str(workspace_root / "runtime") + '"' in migrated_profile_text
    top_level_profile_text = migrated_profile_text.split("[legacy_diagnostic]", maxsplit=1)[0]
    assert "med_deepscientist_runtime_root" not in top_level_profile_text

    alpha_binding = yaml.safe_load(
        (workspace_root / "studies" / "010-alpha-dynamic" / "runtime_binding.yaml").read_text(encoding="utf-8")
    )
    assert alpha_binding["runtime_home"] == str(workspace_root / "runtime")
    assert alpha_binding["runtime_root"] == str(workspace_root / "runtime" / "quests")
    assert alpha_binding["runtime_quests_root"] == str(workspace_root / "runtime" / "quests")
    assert alpha_binding["legacy_diagnostic"]["read_only"] is True
    assert alpha_binding["legacy_diagnostic"]["old_quest_root"].endswith(
        "ops/med-deepscientist/runtime/quests/quest-alpha-dynamic"
    )

    assert live_binding.read_text(encoding="utf-8") == live_binding_before
    assert alpha_paper.read_text(encoding="utf-8") == alpha_paper_before
    assert not list((workspace_root / "studies").glob("*/paper/current_package/*.tmp"))


def test_workspace_monolith_migration_controller_has_no_hardcoded_fixture_study_ids() -> None:
    source = Path("src/med_autoscience/controllers/workspace_monolith_migration.py").read_text(encoding="utf-8")

    assert "DM002" not in source
    assert "DPCC003" not in source
    assert "NF003" not in source
