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
                f'portfolio_root = "{workspace_root / "memory" / "portfolio"}"',
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
                "runtime_backend_id: med_deepscientist",
                "runtime_backend: med_deepscientist",
                "runtime_engine_id: med-deepscientist",
                "research_backend_id: med_deepscientist",
                "research_backend: med_deepscientist",
                "research_engine_id: med-deepscientist",
                f"med_deepscientist_runtime_root: {legacy_runtime_root}",
                "legacy_diagnostic:",
                f"  med_deepscientist_runtime_root: {legacy_runtime_root}",
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
    lines = [
        f"quest_id: {quest_id}",
        f"quest_root: {quest_root}",
        f"runtime_root: {runtime_quests_root}",
    ]
    if study_id is not None:
        lines.append(f"study_id: {study_id}")
    lines.extend(
        [
            "confirmed_baseline_ref:",
            "  baseline_id: baseline-001",
            "  variant_id: imported",
            "  baseline_root_rel_path: baselines/imported/baseline-001",
            "  metric_contract_json_rel_path: baselines/imported/baseline-001/json/metric_contract.json",
            f"  baseline_path: {quest_root / 'baselines' / 'imported' / 'baseline-001'}",
            f"  metric_contract_json_path: {quest_root / 'baselines' / 'imported' / 'baseline-001' / 'json' / 'metric_contract.json'}",
            "  source_mode: historical_fixture_ref",
            "legacy_runtime_metadata:",
            f"  baseline_path: {quest_root / 'baselines' / 'imported' / 'baseline-001'}",
            f"  metric_contract_json_path: {quest_root / 'baselines' / 'imported' / 'baseline-001' / 'json' / 'metric_contract.json'}",
        ]
    )
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
    ops_readme = workspace_root / "ops" / "medautoscience" / "README.md"
    _write_text(
        ops_readme,
        "\n".join(
            [
                "# Legacy Entry",
                "- `bin/install-watch-runtime-service`",
                "- `bin/watch-runtime-service-status`",
                "- `bin/uninstall-watch-runtime-service`",
                "",
            ]
        ),
    )
    launchd_readme = workspace_root / "ops" / "medautoscience" / "supervisor" / "launchd" / "README.md"
    _write_text(launchd_readme, "ops/medautoscience/bin/install-watch-runtime-service --manager launchd\n")
    for name in (
        "install-watch-runtime-service",
        "watch-runtime-service-status",
        "uninstall-watch-runtime-service",
        "watch-runtime-service-runner",
    ):
        _write_text(
            workspace_root / "ops" / "medautoscience" / "bin" / name,
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n'
            "runtime ensure-supervision\n",
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
    assert report["migrated"][0]["reason"] == "legacy_binding_to_opl_provider_stage_runtime_and_mas_domain_refs"
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
    assert not (workspace_root / "runtime" / "artifacts" / "monolith_migration" / "latest.json").exists()


def test_workspace_monolith_migration_apply_writes_ledger_and_only_migrates_safe_bindings(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.workspace_monolith_migration")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_contracts = importlib.import_module("med_autoscience.workspace_contracts")
    profile_path, workspace_root = _build_fixture(tmp_path)
    alpha_paper = workspace_root / "studies" / "010-alpha-dynamic" / "paper" / "current_package" / "manuscript.md"
    live_binding = workspace_root / "studies" / "011-live-dynamic" / "runtime_binding.yaml"
    alpha_paper_before = alpha_paper.read_text(encoding="utf-8")
    live_binding_before = live_binding.read_text(encoding="utf-8")

    report = migration.run_workspace_monolith_migration(profile_path=profile_path, apply=True)

    latest_path = workspace_root / "runtime" / "artifacts" / "monolith_migration" / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    history_path = Path(latest["history_path"])
    assert history_path.exists()
    assert latest["mode"] == "apply"
    assert latest["post_apply"]["remaining_binding_refresh_count"] == 0
    assert latest["profile_path"] == str(profile_path.resolve())
    assert latest["restore_proofs"][0]["status"] == "verified"
    assert latest["archive_refs"][0]["archive_path"].endswith("quest-alpha-dynamic.tar.gz")
    assert latest["orphan"] == report["orphan"]
    assert latest["duplicate"] == report["duplicate"]
    assert latest["skipped"][0]["next_required_action"] == "controller_pause_quiesce_relaunch"
    migrated_profile_text = profile_path.read_text(encoding="utf-8")
    assert 'runtime_root = "' + str(workspace_root / "runtime" / "quests") + '"' in migrated_profile_text
    assert 'managed_runtime_home = "' + str(workspace_root / "runtime") + '"' in migrated_profile_text
    top_level_profile_text = migrated_profile_text.split("[historical_fixture_ref]", maxsplit=1)[0]
    assert "med_deepscientist_runtime_root" not in top_level_profile_text
    assert "[legacy_diagnostic]" not in migrated_profile_text

    alpha_binding = yaml.safe_load(
        (workspace_root / "studies" / "010-alpha-dynamic" / "runtime_binding.yaml").read_text(encoding="utf-8")
    )
    assert alpha_binding["runtime_home"] == str(workspace_root / "runtime")
    assert alpha_binding["runtime_root"] == str(workspace_root / "runtime" / "quests")
    assert alpha_binding["runtime_quests_root"] == str(workspace_root / "runtime" / "quests")
    assert alpha_binding["runtime_substrate"] == "opl_hosted_stage_runtime"
    assert alpha_binding["opl_runtime_ref"] == "opl_hosted_stage_runtime"
    assert alpha_binding["runtime_ref"] == "opl_hosted_stage_runtime"
    assert alpha_binding["runtime_engine_id"] == "opl-hosted-stage-runtime"
    assert alpha_binding["research_backend_id"] == "mas_domain_intent_adapter"
    assert alpha_binding["research_backend"] == "mas_domain_intent_adapter"
    assert alpha_binding["research_engine_id"] == "mas-domain-intent-adapter"
    assert "runtime_backend_id" not in alpha_binding
    assert "runtime_backend" not in alpha_binding
    assert "med_deepscientist_runtime_root" not in alpha_binding
    assert "legacy_diagnostic" not in alpha_binding
    assert alpha_binding["historical_fixture_ref"]["read_only"] is True
    assert alpha_binding["historical_fixture_ref"]["old_quest_root"].endswith(
        "ops/med-deepscientist/runtime/quests/quest-alpha-dynamic"
    )
    assert alpha_binding["historical_fixture_ref"]["old_runtime_root"].endswith("ops/med-deepscientist/runtime")
    migrated_quest_root = workspace_root / "runtime" / "quests" / "quest-alpha-dynamic"
    migrated_quest = yaml.safe_load((migrated_quest_root / "quest.yaml").read_text(encoding="utf-8"))
    migrated_runtime_handoff = json.loads(
        (migrated_quest_root / "artifacts" / "runtime" / "opl_runtime_state_migration_handoff.json").read_text(
            encoding="utf-8"
        )
    )
    assert not (migrated_quest_root / ".ds" / "runtime_state.json").exists()
    assert migrated_quest["quest_id"] == "quest-alpha-dynamic"
    assert migrated_quest["study_id"] == "010-alpha-dynamic"
    assert migrated_quest["quest_root"] == str(migrated_quest_root)
    assert migrated_quest["runtime_root"] == str(workspace_root / "runtime" / "quests")
    assert migrated_quest["historical_fixture_ref"]["read_only"] is True
    assert migrated_quest["historical_fixture_ref"]["old_quest_root"].endswith(
        "ops/med-deepscientist/runtime/quests/quest-alpha-dynamic"
    )
    assert migrated_quest["confirmed_baseline_ref"] == {
        "baseline_id": "baseline-001",
        "variant_id": "imported",
        "baseline_root_rel_path": "baselines/imported/baseline-001",
        "metric_contract_json_rel_path": "baselines/imported/baseline-001/json/metric_contract.json",
        "source_mode": "historical_fixture_ref",
    }
    assert "baseline_path" not in migrated_quest["confirmed_baseline_ref"]
    assert "metric_contract_json_path" not in migrated_quest["confirmed_baseline_ref"]
    assert migrated_quest["historical_fixture_ref"]["old_confirmed_baseline_ref"]["baseline_path"].endswith(
        "ops/med-deepscientist/runtime/quests/quest-alpha-dynamic/baselines/imported/baseline-001"
    )
    assert migrated_quest["historical_fixture_ref"]["old_confirmed_baseline_ref"][
        "metric_contract_json_path"
    ].endswith(
        "ops/med-deepscientist/runtime/quests/quest-alpha-dynamic/baselines/imported/baseline-001/json/metric_contract.json"
    )
    assert migrated_runtime_handoff["surface_kind"] == "opl_runtime_state_migration_handoff"
    assert migrated_runtime_handoff["effect"] == "refs_only"
    assert migrated_runtime_handoff["queue_owner"] == "one-person-lab"
    assert migrated_runtime_handoff["mas_writes_runtime_state"] is False
    assert migrated_runtime_handoff["status"] == "completed"
    assert migrated_runtime_handoff["active_run_id"] is None
    assert migrated_runtime_handoff["worker_running"] is False
    assert migrated_runtime_handoff["historical_fixture_ref"]["read_only"] is True
    assert migrated_runtime_handoff["historical_fixture_ref"]["old_quest_root"].endswith(
        "ops/med-deepscientist/runtime/quests/quest-alpha-dynamic"
    )
    mas_bin_root = workspace_root / "ops" / "mas" / "bin"
    behavior_gate = workspace_root / "ops" / "mas" / "behavior_equivalence_gate.yaml"
    assert mas_bin_root.is_dir()
    assert (mas_bin_root / "_shared.sh").is_file()
    assert (mas_bin_root / "status").is_file()
    assert (mas_bin_root / "stop").is_file()
    assert behavior_gate.read_text(encoding="utf-8") == (
        "schema_version: v1\nphase_25_ready: true\ncritical_overrides: []\n"
    )
    med_readme_text = (workspace_root / "ops" / "medautoscience" / "README.md").read_text(encoding="utf-8")
    assert "install-watch-runtime-service" not in med_readme_text
    assert "watch-runtime-service-status" not in med_readme_text
    assert "uninstall-watch-runtime-service" not in med_readme_text
    assert "OPL current_control_state refs-only handoff" in med_readme_text
    assert "medautosci runtime ensure-supervision --profile <profile>" not in med_readme_text
    assert "medautosci runtime supervision-status --profile <profile>" not in med_readme_text
    assert "medautosci runtime remove-supervision --profile <profile>" not in med_readme_text
    assert not (workspace_root / "ops" / "medautoscience" / "supervisor" / "launchd" / "README.md").exists()
    for name in (
        "install-watch-runtime-service",
        "watch-runtime-service-status",
        "uninstall-watch-runtime-service",
        "watch-runtime-service-runner",
    ):
        assert not (workspace_root / "ops" / "medautoscience" / "bin" / name).exists()
    contracts = workspace_contracts.inspect_workspace_contracts(profiles.load_profile(profile_path))
    assert contracts["runtime_contract"]["ready"] is True
    assert contracts["launcher_contract"]["ready"] is True
    assert contracts["behavior_gate"]["ready"] is True
    assert contracts["overall_ready"] is True

    assert live_binding.read_text(encoding="utf-8") == live_binding_before
    assert alpha_paper.read_text(encoding="utf-8") == alpha_paper_before
    assert not list((workspace_root / "studies").glob("*/paper/current_package/*.tmp"))


def test_workspace_monolith_migration_refreshes_already_migrated_target_binding_without_replaying_legacy(
    tmp_path: Path,
) -> None:
    migration = importlib.import_module("med_autoscience.controllers.workspace_monolith_migration")
    profile_path, workspace_root = _build_fixture(tmp_path)
    legacy_runtime_root = workspace_root / "ops" / "med-deepscientist" / "runtime"
    target_quest_root = workspace_root / "runtime" / "quests" / "quest-alpha-dynamic"
    _write_quest(
        workspace_root / "runtime" / "quests",
        "quest-alpha-dynamic",
        study_id="010-alpha-dynamic",
        runtime_state={"status": "active", "active_run_id": None, "worker_running": False},
    )
    target_quest_yaml = target_quest_root / "quest.yaml"
    target_runtime_state = target_quest_root / ".ds" / "runtime_state.json"
    target_quest_yaml_before = target_quest_yaml.read_text(encoding="utf-8")
    target_runtime_state_before = target_runtime_state.read_text(encoding="utf-8")
    binding_path = workspace_root / "studies" / "010-alpha-dynamic" / "runtime_binding.yaml"
    binding_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "engine: opl-provider-backed-stage-runtime",
                "runtime_backend_id: opl_provider_backed_stage_runtime",
                "runtime_backend: opl_provider_backed_stage_runtime",
                "runtime_engine_id: opl-provider-backed-stage-runtime",
                "research_backend_id: mas_runtime_core",
                "research_backend: mas_runtime_core",
                "research_engine_id: mas-runtime-core",
                f"runtime_home: {workspace_root / 'runtime'}",
                "study_id: 010-alpha-dynamic",
                f"study_root: {workspace_root / 'studies' / '010-alpha-dynamic'}",
                "quest_id: quest-alpha-dynamic",
                f"runtime_root: {workspace_root / 'runtime' / 'quests'}",
                f"runtime_quests_root: {workspace_root / 'runtime' / 'quests'}",
                "historical_fixture_ref:",
                f"  old_quest_root: {legacy_runtime_root / 'quests' / 'quest-alpha-dynamic'}",
                f"  old_runtime_root: {legacy_runtime_root}",
                "  read_only: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    dry_run = migration.run_workspace_monolith_migration(profile_path=profile_path, apply=False)

    assert dry_run["migrated"] == []
    assert dry_run["binding_refreshes"][0]["study_id"] == "010-alpha-dynamic"
    assert dry_run["binding_refreshes"][0]["reason"] == "refresh_runtime_binding_to_opl_hosted_stage_runtime"
    assert dry_run["binding_refreshes"][0]["runtime_status"] == "active"

    report = migration.run_workspace_monolith_migration(profile_path=profile_path, apply=True)
    refreshed_binding = yaml.safe_load(binding_path.read_text(encoding="utf-8"))

    assert report["post_apply"]["remaining_binding_refresh_count"] == 0
    assert refreshed_binding["runtime_substrate"] == "opl_hosted_stage_runtime"
    assert refreshed_binding["opl_runtime_ref"] == "opl_hosted_stage_runtime"
    assert refreshed_binding["runtime_ref"] == "opl_hosted_stage_runtime"
    assert refreshed_binding["runtime_engine_id"] == "opl-hosted-stage-runtime"
    assert refreshed_binding["research_backend_id"] == "mas_domain_intent_adapter"
    assert refreshed_binding["research_backend"] == "mas_domain_intent_adapter"
    assert refreshed_binding["research_engine_id"] == "mas-domain-intent-adapter"
    assert "runtime_backend_id" not in refreshed_binding
    assert "runtime_backend" not in refreshed_binding
    assert refreshed_binding["historical_fixture_ref"]["old_quest_root"].endswith(
        "ops/med-deepscientist/runtime/quests/quest-alpha-dynamic"
    )
    assert target_quest_yaml.read_text(encoding="utf-8") == target_quest_yaml_before
    assert target_runtime_state.read_text(encoding="utf-8") == target_runtime_state_before


def test_workspace_monolith_migration_controller_has_no_hardcoded_fixture_study_ids() -> None:
    source = Path("src/med_autoscience/controllers/workspace_monolith_migration.py").read_text(encoding="utf-8")

    assert "DM002" not in source
    assert "DPCC003" not in source
    assert "NF003" not in source
