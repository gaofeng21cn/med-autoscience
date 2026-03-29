from __future__ import annotations

import importlib
from pathlib import Path


def write_profile(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                'workspace_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤"',
                'runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime/quests"',
                'studies_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/studies"',
                'portfolio_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/portfolio"',
                'deepscientist_runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
                "",
                "[[default_submission_targets]]",
                'publication_profile = "frontiers_family_harvard"',
                "primary = true",
                "package_required = true",
                'story_surface = "general_medical_journal"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_doctor_command_reports_profile_and_paths(tmp_path: Path, capsys) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)

    try:
        cli = importlib.import_module("med_autoscience.cli")
    except ModuleNotFoundError:
        cli = None

    assert cli is not None
    main = getattr(cli, "main", None)
    assert callable(main)

    exit_code = main(["doctor", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "profile: nfpitnet" in captured.out
    assert "workspace_root: /Users/gaofeng/workspace/Yang/无功能垂体瘤" in captured.out
    assert "default_publication_profile: general_medical_journal" in captured.out


def test_show_profile_prints_resolved_contract(tmp_path: Path, capsys) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)

    try:
        cli = importlib.import_module("med_autoscience.cli")
    except ModuleNotFoundError:
        cli = None

    assert cli is not None
    main = getattr(cli, "main", None)
    assert callable(main)

    exit_code = main(["show-profile", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "name: nfpitnet" in captured.out
    assert "default_citation_style: AMA" in captured.out
    assert "default_submission_targets: frontiers_family_harvard" in captured.out
    assert "research_route_bias_policy: high_plasticity_medical" in captured.out
    assert (
        "preferred_study_archetypes: clinical_classifier, clinical_subtype_reconstruction, "
        "external_validation_model_update, gray_zone_triage, llm_agent_clinical_task, "
        "mechanistic_sidecar_extension"
    ) in captured.out
    assert "medical_overlay_scope: workspace" in captured.out


def test_watch_command_dispatches_runtime_watch(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_watch_for_runtime(*, runtime_root: Path, apply: bool) -> dict:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        return {"scanned_quests": ["q001"], "runtime_root": str(runtime_root)}

    monkeypatch.setattr(cli.runtime_watch, "run_watch_for_runtime", fake_run_watch_for_runtime)

    exit_code = cli.main(["watch", "--runtime-root", str(tmp_path / "quests"), "--apply"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["runtime_root"] == tmp_path / "quests"
    assert called["apply"] is True
    assert "q001" in captured.out


def test_init_data_assets_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"private": {"release_count": 1}, "public": {"dataset_count": 0}}

    monkeypatch.setattr(cli.data_assets, "init_data_assets", fake_init)

    exit_code = cli.main(["init-data-assets", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"release_count": 1' in captured.out


def test_data_assets_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"layout_ready": True, "private": {"release_count": 2}}

    monkeypatch.setattr(cli.data_assets, "data_assets_status", fake_status)

    exit_code = cli.main(["data-assets-status", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"layout_ready": true' in captured.out


def test_assess_data_asset_impact_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_assess(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"study_count": 1, "studies": [{"study_id": "002-early-risk", "status": "review_needed"}]}

    monkeypatch.setattr(cli.data_assets, "assess_data_asset_impact", fake_assess)

    exit_code = cli.main(["assess-data-asset-impact", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"review_needed"' in captured.out


def test_diff_private_release_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_diff(*, workspace_root: Path, family_id: str, from_version: str, to_version: str) -> dict:
        called["workspace_root"] = workspace_root
        called["family_id"] = family_id
        called["from_version"] = from_version
        called["to_version"] = to_version
        return {"report_path": "/tmp/report.json", "family_id": family_id}

    monkeypatch.setattr(cli.data_assets, "build_private_release_diff", fake_diff)

    exit_code = cli.main(
        [
            "diff-private-release",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--family-id",
            "master",
            "--from-version",
            "v2026-03-28",
            "--to-version",
            "v2026-04-10",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["family_id"] == "master"
    assert called["from_version"] == "v2026-03-28"
    assert called["to_version"] == "v2026-04-10"
    assert "/tmp/report.json" in captured.out


def test_validate_public_registry_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_validate(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"invalid_dataset_count": 0, "dataset_count": 2}

    monkeypatch.setattr(cli.data_assets, "validate_public_registry", fake_validate)

    exit_code = cli.main(["validate-public-registry", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"dataset_count": 2' in captured.out


def test_startup_data_readiness_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_readiness(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"status": "clear", "study_summary": {"study_count": 2}}

    monkeypatch.setattr(cli.startup_data_readiness_controller, "startup_data_readiness", fake_readiness)

    exit_code = cli.main(["startup-data-readiness", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"study_count": 2' in captured.out


def test_data_asset_gate_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_controller(*, quest_root: Path, apply: bool) -> dict:
        called["quest_root"] = quest_root
        called["apply"] = apply
        return {"status": "blocked", "blockers": ["outdated_private_release"], "report_json": "/tmp/data_gate.json"}

    monkeypatch.setattr(cli.data_asset_gate, "run_controller", fake_run_controller)

    exit_code = cli.main(["data-asset-gate", "--quest-root", str(tmp_path / "q001"), "--apply"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "q001"
    assert called["apply"] is True
    assert '"outdated_private_release"' in captured.out


def test_tooluniverse_status_command_dispatches_adapter(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_detect(*, workspace_root: Path | None = None, tooluniverse_root: Path | None = None) -> dict:
        called["workspace_root"] = workspace_root
        called["tooluniverse_root"] = tooluniverse_root
        return {"available": True, "roles": ["知识检索", "功能分析"]}

    monkeypatch.setattr(cli.tooluniverse_adapter, "detect_tooluniverse", fake_detect)

    exit_code = cli.main(
        [
            "tooluniverse-status",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--tooluniverse-root",
            str(tmp_path / "ToolUniverse"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["tooluniverse_root"] == tmp_path / "ToolUniverse"
    assert '"available": true' in captured.out


def test_export_submission_minimal_command_dispatches_exporter(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_export(*, paper_root: Path, publication_profile: str, citation_style: str) -> dict:
        called["paper_root"] = paper_root
        called["publication_profile"] = publication_profile
        called["citation_style"] = citation_style
        return {"output_root": str(paper_root / "submission_minimal")}

    monkeypatch.setattr(cli.submission_minimal, "create_submission_minimal_package", fake_export)

    exit_code = cli.main(
        [
            "export-submission-minimal",
            "--paper-root",
            str(tmp_path / "paper"),
            "--publication-profile",
            "general_medical_journal",
            "--citation-style",
            "AMA",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["paper_root"] == tmp_path / "paper"
    assert called["publication_profile"] == "general_medical_journal"
    assert called["citation_style"] == "AMA"
    assert "submission_minimal" in captured.out


def test_resolve_submission_targets_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_resolve(
        *,
        profile_path: Path | None = None,
        study_root: Path | None = None,
        quest_root: Path | None = None,
    ) -> dict:
        called["profile_path"] = profile_path
        called["study_root"] = study_root
        called["quest_root"] = quest_root
        return {"status": "resolved", "targets": [{"target_key": "profile:frontiers_family_harvard"}]}

    monkeypatch.setattr(cli.submission_targets_controller, "resolve_submission_targets", fake_resolve)

    exit_code = cli.main(
        [
            "resolve-submission-targets",
            "--profile",
            str(profile_path),
            "--study-root",
            str(tmp_path / "studies" / "002-early-residual-risk"),
            "--quest-root",
            str(tmp_path / "quests" / "002-early-residual-risk"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile_path"] == profile_path
    assert called["study_root"] == tmp_path / "studies" / "002-early-residual-risk"
    assert called["quest_root"] == tmp_path / "quests" / "002-early-residual-risk"
    assert '"status": "resolved"' in captured.out


def test_export_submission_targets_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_export(
        *,
        paper_root: Path | None = None,
        profile_path: Path | None = None,
        study_root: Path | None = None,
        quest_root: Path | None = None,
    ) -> dict:
        called["paper_root"] = paper_root
        called["profile_path"] = profile_path
        called["study_root"] = study_root
        called["quest_root"] = quest_root
        return {"status": "blocked", "blocked_target_count": 1}

    monkeypatch.setattr(cli.submission_targets_controller, "export_submission_targets", fake_export)

    exit_code = cli.main(
        [
            "export-submission-targets",
            "--paper-root",
            str(tmp_path / "paper"),
            "--profile",
            str(profile_path),
            "--study-root",
            str(tmp_path / "studies" / "002-early-residual-risk"),
            "--quest-root",
            str(tmp_path / "quests" / "002-early-residual-risk"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["paper_root"] == tmp_path / "paper"
    assert called["profile_path"] == profile_path
    assert called["study_root"] == tmp_path / "studies" / "002-early-residual-risk"
    assert called["quest_root"] == tmp_path / "quests" / "002-early-residual-risk"
    assert '"blocked_target_count": 1' in captured.out


def test_publication_gate_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_controller(*, quest_root: Path, apply: bool) -> dict:
        called["quest_root"] = quest_root
        called["apply"] = apply
        return {"status": "blocked", "blockers": ["missing_post_main_publishability_gate"]}

    monkeypatch.setattr(cli.publication_gate, "run_controller", fake_run_controller)

    exit_code = cli.main(["publication-gate", "--quest-root", str(tmp_path / "q001"), "--apply"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "q001"
    assert called["apply"] is True
    assert '"status": "blocked"' in captured.out


def test_medical_publication_surface_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_controller(*, quest_root: Path, apply: bool, daemon_url: str | None = None) -> dict:
        called["quest_root"] = quest_root
        called["apply"] = apply
        called["daemon_url"] = daemon_url
        return {"status": "clear", "blockers": []}

    monkeypatch.setattr(cli.medical_publication_surface, "run_controller", fake_run_controller)

    exit_code = cli.main(
        [
            "medical-publication-surface",
            "--quest-root",
            str(tmp_path / "q001"),
            "--apply",
            "--daemon-url",
            "http://127.0.0.1:20999",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "q001"
    assert called["apply"] is True
    assert called["daemon_url"] == "http://127.0.0.1:20999"
    assert '"status": "clear"' in captured.out


def test_sync_study_delivery_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_sync(*, paper_root: Path, stage: str, publication_profile: str = "general_medical_journal") -> dict:
        called["paper_root"] = paper_root
        called["stage"] = stage
        called["publication_profile"] = publication_profile
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {"manuscript_final_root": str(tmp_path / "study" / "final")},
        }

    monkeypatch.setattr(cli.study_delivery_sync, "sync_study_delivery", fake_sync)

    exit_code = cli.main(
        [
            "sync-study-delivery",
            "--paper-root",
            str(tmp_path / "paper"),
            "--stage",
            "finalize",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["paper_root"] == tmp_path / "paper"
    assert called["stage"] == "finalize"
    assert called["publication_profile"] == "general_medical_journal"
    assert '"stage": "finalize"' in captured.out


def test_overlay_status_command_dispatches_installer(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, quest_root: Path | None = None, skill_ids: tuple[str, ...] | None = None) -> dict:
        called["quest_root"] = quest_root
        called["skill_ids"] = skill_ids
        return {"scope": "quest", "quest_root": str(quest_root), "targets": [{"skill_id": "write"}]}

    monkeypatch.setattr(cli.overlay_installer, "describe_medical_overlay", fake_status)

    exit_code = cli.main(["overlay-status", "--quest-root", str(tmp_path / "runtime" / "quests" / "q001")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "runtime" / "quests" / "q001"
    assert called["skill_ids"] is None
    assert '"skill_id": "write"' in captured.out


def test_install_medical_overlay_command_dispatches_installer(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_install(*, quest_root: Path | None = None, skill_ids: tuple[str, ...] | None = None) -> dict:
        called["quest_root"] = quest_root
        called["skill_ids"] = skill_ids
        return {"installed_count": 2, "targets": [{"skill_id": "write", "action": "installed"}]}

    monkeypatch.setattr(cli.overlay_installer, "install_medical_overlay", fake_install)

    exit_code = cli.main(["install-medical-overlay"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] is None
    assert called["skill_ids"] is None
    assert '"installed_count": 2' in captured.out


def test_reapply_medical_overlay_command_dispatches_installer(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_reapply(*, quest_root: Path | None = None, skill_ids: tuple[str, ...] | None = None) -> dict:
        called["quest_root"] = quest_root
        called["skill_ids"] = skill_ids
        return {"installed_count": 2, "targets": [{"skill_id": "finalize", "action": "reapplied"}]}

    monkeypatch.setattr(cli.overlay_installer, "reapply_medical_overlay", fake_reapply)

    exit_code = cli.main(["reapply-medical-overlay", "--quest-root", str(tmp_path / "q001")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "q001"
    assert called["skill_ids"] is None
    assert '"action": "reapplied"' in captured.out


def test_overlay_status_command_dispatches_profile_overlay(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_status(
        *,
        quest_root: Path | None = None,
        skill_ids: tuple[str, ...] | None = None,
        policy_id: str | None = None,
        archetype_ids: tuple[str, ...] | None = None,
        default_submission_targets: tuple[dict[str, object], ...] | None = None,
        default_publication_profile: str | None = None,
        default_citation_style: str | None = None,
    ) -> dict:
        called["quest_root"] = quest_root
        called["skill_ids"] = skill_ids
        called["policy_id"] = policy_id
        called["archetype_ids"] = archetype_ids
        called["default_submission_targets"] = default_submission_targets
        called["default_publication_profile"] = default_publication_profile
        called["default_citation_style"] = default_citation_style
        return {"targets": [{"skill_id": "scout"}], "scope": "global"}

    monkeypatch.setattr(cli.overlay_installer, "describe_medical_overlay", fake_status)

    exit_code = cli.main(["overlay-status", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert called["skill_ids"] == ("scout", "idea", "decision", "write", "finalize")
    assert called["policy_id"] == "high_plasticity_medical"
    assert called["archetype_ids"] == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    )
    assert called["default_submission_targets"] == (
        {
            "publication_profile": "frontiers_family_harvard",
            "primary": True,
            "package_required": True,
            "story_surface": "general_medical_journal",
        },
    )
    assert called["default_publication_profile"] == "general_medical_journal"
    assert called["default_citation_style"] == "AMA"
    assert '"skill_id": "scout"' in captured.out


def test_bootstrap_command_installs_profile_overlay(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    calls: dict[str, object] = {}

    def fake_install(
        *,
        quest_root: Path | None = None,
        skill_ids: tuple[str, ...] | None = None,
        policy_id: str | None = None,
        archetype_ids: tuple[str, ...] | None = None,
        default_submission_targets: tuple[dict[str, object], ...] | None = None,
        default_publication_profile: str | None = None,
        default_citation_style: str | None = None,
    ) -> dict:
        calls["install_quest_root"] = quest_root
        calls["install_skill_ids"] = skill_ids
        calls["install_policy_id"] = policy_id
        calls["install_archetype_ids"] = archetype_ids
        calls["install_default_submission_targets"] = default_submission_targets
        calls["install_default_publication_profile"] = default_publication_profile
        calls["install_default_citation_style"] = default_citation_style
        return {"installed_count": 5}

    def fake_status(
        *,
        quest_root: Path | None = None,
        skill_ids: tuple[str, ...] | None = None,
        policy_id: str | None = None,
        archetype_ids: tuple[str, ...] | None = None,
        default_submission_targets: tuple[dict[str, object], ...] | None = None,
        default_publication_profile: str | None = None,
        default_citation_style: str | None = None,
    ) -> dict:
        calls["status_quest_root"] = quest_root
        calls["status_skill_ids"] = skill_ids
        calls["status_policy_id"] = policy_id
        calls["status_archetype_ids"] = archetype_ids
        calls["status_default_submission_targets"] = default_submission_targets
        calls["status_default_publication_profile"] = default_publication_profile
        calls["status_default_citation_style"] = default_citation_style
        return {"all_targets_ready": True}

    def fake_init_data_assets(*, workspace_root: Path) -> dict:
        calls.setdefault("call_order", []).append("init_data_assets")
        calls["init_data_assets_workspace_root"] = workspace_root
        return {"private": {"release_count": 1}}

    def fake_data_assets_status(*, workspace_root: Path) -> dict:
        calls.setdefault("call_order", []).append("data_assets_status")
        calls["data_assets_status_workspace_root"] = workspace_root
        return {"layout_ready": True}

    def fake_validate_public_registry(*, workspace_root: Path) -> dict:
        calls.setdefault("call_order", []).append("validate_public_registry")
        calls["validate_public_registry_workspace_root"] = workspace_root
        return {"valid_dataset_count": 1}

    def fake_assess_data_asset_impact(*, workspace_root: Path) -> dict:
        calls.setdefault("call_order", []).append("assess_data_asset_impact")
        calls["assess_data_asset_impact_workspace_root"] = workspace_root
        return {
            "study_count": 2,
            "studies": [{"study_id": "002", "status": "review_needed"}],
            "report_path": "/tmp/impact.json",
        }

    def fake_startup_data_readiness(*, workspace_root: Path) -> dict:
        calls.setdefault("call_order", []).append("startup_data_readiness")
        calls["startup_data_readiness_workspace_root"] = workspace_root
        return {"status": "attention_needed", "recommendations": ["screen_valid_public_datasets_for_extension"]}

    monkeypatch.setattr(cli.overlay_installer, "install_medical_overlay", fake_install)
    monkeypatch.setattr(cli.overlay_installer, "describe_medical_overlay", fake_status)
    monkeypatch.setattr(cli.data_assets, "init_data_assets", fake_init_data_assets)
    monkeypatch.setattr(cli.data_assets, "data_assets_status", fake_data_assets_status)
    monkeypatch.setattr(cli.data_assets, "validate_public_registry", fake_validate_public_registry)
    monkeypatch.setattr(cli.data_assets, "assess_data_asset_impact", fake_assess_data_asset_impact)
    monkeypatch.setattr(cli.startup_data_readiness_controller, "startup_data_readiness", fake_startup_data_readiness)

    exit_code = cli.main(["bootstrap", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls["install_skill_ids"] == ("scout", "idea", "decision", "write", "finalize")
    assert calls["install_quest_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert calls["install_policy_id"] == "high_plasticity_medical"
    assert calls["install_archetype_ids"] == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    )
    assert calls["install_default_submission_targets"] == (
        {
            "publication_profile": "frontiers_family_harvard",
            "primary": True,
            "package_required": True,
            "story_surface": "general_medical_journal",
        },
    )
    assert calls["install_default_publication_profile"] == "general_medical_journal"
    assert calls["install_default_citation_style"] == "AMA"
    assert calls["status_skill_ids"] == ("scout", "idea", "decision", "write", "finalize")
    assert calls["status_quest_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert calls["status_policy_id"] == "high_plasticity_medical"
    assert calls["status_archetype_ids"] == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    )
    assert calls["status_default_submission_targets"] == (
        {
            "publication_profile": "frontiers_family_harvard",
            "primary": True,
            "package_required": True,
            "story_surface": "general_medical_journal",
        },
    )
    assert calls["status_default_publication_profile"] == "general_medical_journal"
    assert calls["status_default_citation_style"] == "AMA"
    assert calls["init_data_assets_workspace_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert calls["data_assets_status_workspace_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert calls["validate_public_registry_workspace_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert calls["assess_data_asset_impact_workspace_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert calls["startup_data_readiness_workspace_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert calls["call_order"] == [
        "init_data_assets",
        "validate_public_registry",
        "assess_data_asset_impact",
        "startup_data_readiness",
        "data_assets_status",
    ]
    assert '"installed_count": 5' in captured.out
    assert '"impact_report"' in captured.out
    assert '"startup_data_readiness"' in captured.out
    assert '"studies"' not in captured.out
