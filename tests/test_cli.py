from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

import pytest

from med_autoscience.agent_entry.renderers import (
    render_codex_entry_skill,
    render_entry_modes_guide,
    render_entry_modes_payload,
    render_openclaw_entry_prompt,
    render_public_yaml,
)
from med_autoscience.figure_routes import (
    FIGURE_ROUTE_ILLUSTRATION_PROGRAM,
    FIGURE_ROUTE_SCRIPT_FIX,
    build_figure_route,
)


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
                'deepscientist_repo_root = "/Users/gaofeng/workspace/DeepScientist"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
                'medical_overlay_bootstrap_mode = "ensure_ready"',
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
    assert "autofigure" not in captured.out.lower()


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
    assert "autofigure" not in captured.out.lower()

def test_show_profile_json_exports_machine_readable_contract(tmp_path: Path, capsys) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)

    try:
        cli = importlib.import_module("med_autoscience.cli")
    except ModuleNotFoundError:
        cli = None

    assert cli is not None
    main = getattr(cli, "main", None)
    assert callable(main)

    exit_code = main(["show-profile", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["name"] == "nfpitnet"
    assert payload["workspace_root"] == "/Users/gaofeng/workspace/Yang/无功能垂体瘤"
    assert payload["publication"]["default_publication_profile"] == "general_medical_journal"
    assert payload["publication"]["default_citation_style"] == "AMA"
    assert payload["publication"]["default_submission_targets"][0]["publication_profile"] == "frontiers_family_harvard"
    assert payload["overlay"]["enable_medical_overlay"] is True
    assert payload["overlay"]["medical_overlay_scope"] == "workspace"
    assert payload["overlay"]["medical_overlay_skills"][0] == "scout"
    assert payload["overlay"]["medical_overlay_bootstrap_mode"] == "ensure_ready"
    assert payload["policy"]["research_route_bias_policy"] == "high_plasticity_medical"
    assert payload["archetype"]["preferred_study_archetypes"][0] == "clinical_classifier"
    assert "autofigure" not in json.dumps(payload, ensure_ascii=False).lower()


def test_show_agent_entry_modes_outputs_canonical_payload(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["show-agent-entry-modes"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out) == render_entry_modes_payload()


def test_sync_agent_entry_assets_command_writes_four_files(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    expected_assets = {
        "guides/agent_entry_modes.md": render_entry_modes_guide(),
        "templates/agent_entry_modes.yaml": render_public_yaml(),
        "templates/codex/medautoscience-entry.SKILL.md": render_codex_entry_skill(),
        "templates/openclaw/medautoscience-entry.prompt.md": render_openclaw_entry_prompt(),
    }

    exit_code = cli.main(["sync-agent-entry-assets", "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["written_count"] == 4
    assert set(payload["written_files"]) == {str(tmp_path / path) for path in expected_assets}
    for relative_path, expected_content in expected_assets.items():
        output_path = tmp_path / relative_path
        assert output_path.is_file()
        assert output_path.read_text(encoding="utf-8") == expected_content


def test_watch_command_dispatches_runtime_watch(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
    ) -> dict:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        return {"scanned_quests": ["q001"], "runtime_root": str(runtime_root)}

    monkeypatch.setattr(cli.runtime_watch, "run_watch_for_runtime", fake_run_watch_for_runtime)

    exit_code = cli.main(["watch", "--runtime-root", str(tmp_path / "quests"), "--apply"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["runtime_root"] == tmp_path / "quests"
    assert called["apply"] is True
    assert called["profile"] is None
    assert called["ensure_study_runtimes"] is False
    assert "q001" in captured.out


def test_watch_command_can_ensure_managed_studies_before_runtime_scan(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
    ) -> dict:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        return {"managed_study_actions": [{"study_id": "001-risk", "decision": "create_and_start"}]}

    monkeypatch.setattr(cli.runtime_watch, "run_watch_for_runtime", fake_run_watch_for_runtime)

    exit_code = cli.main(
        [
            "watch",
            "--runtime-root",
            str(tmp_path / "quests"),
            "--profile",
            str(profile_path),
            "--ensure-study-runtimes",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["runtime_root"] == tmp_path / "quests"
    assert called["apply"] is True
    assert called["profile"].name == "nfpitnet"
    assert called["ensure_study_runtimes"] is True
    assert '"study_id": "001-risk"' in captured.out


def test_resolve_journal_shortlist_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_resolve(*, study_root: Path) -> dict[str, object]:
        called["study_root"] = study_root
        return {"status": "resolved", "shortlist": ["Heart"], "candidate_count": 1}

    monkeypatch.setattr(cli.journal_shortlist_controller, "resolve_journal_shortlist", fake_resolve)

    exit_code = cli.main(["resolve-journal-shortlist", "--study-root", str(tmp_path / "study")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == tmp_path / "study"
    assert '"status": "resolved"' in captured.out


def test_init_portfolio_memory_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {"portfolio_memory_root": str(workspace_root / "portfolio" / "research_memory"), "created_files": []}

    monkeypatch.setattr(cli.portfolio_memory_controller, "init_portfolio_memory", fake_init)

    exit_code = cli.main(["init-portfolio-memory", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"portfolio_memory_root"' in captured.out


def test_portfolio_memory_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {"portfolio_memory_exists": True, "asset_count": 3}

    monkeypatch.setattr(cli.portfolio_memory_controller, "portfolio_memory_status", fake_status)

    exit_code = cli.main(["portfolio-memory-status", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"asset_count": 3' in captured.out


def test_prepare_external_research_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_prepare(*, workspace_root: Path, as_of_date: str | None) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        called["as_of_date"] = as_of_date
        return {"status": "ready", "prompt_path": str(workspace_root / "portfolio" / "research_memory" / "prompts" / "x.md")}

    monkeypatch.setattr(cli.external_research_controller, "prepare_external_research", fake_prepare)

    exit_code = cli.main(
        [
            "prepare-external-research",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--as-of-date",
            "2026-03-30",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["as_of_date"] == "2026-03-30"
    assert '"status": "ready"' in captured.out


def test_external_research_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {"optional_module_ready": True, "prompt_file_count": 1}

    monkeypatch.setattr(cli.external_research_controller, "external_research_status", fake_status)

    exit_code = cli.main(["external-research-status", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"prompt_file_count": 1' in captured.out


def test_deepscientist_upgrade_check_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_run_upgrade_check(profile, *, refresh: bool) -> dict:
        called["profile"] = profile
        called["refresh"] = refresh
        return {"decision": "upgrade_available", "recommended_actions": ["pull_origin_main_then_reapply_medical_overlay"]}

    monkeypatch.setattr(cli.deepscientist_upgrade_check, "run_upgrade_check", fake_run_upgrade_check)

    exit_code = cli.main(["deepscientist-upgrade-check", "--profile", str(profile_path), "--refresh"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].deepscientist_repo_root == Path("/Users/gaofeng/workspace/DeepScientist")
    assert called["refresh"] is True
    assert '"decision": "upgrade_available"' in captured.out


def test_ensure_study_runtime_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_ensure(*, profile, study_id: str | None, study_root: Path | None, entry_mode: str | None, force: bool, source: str) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["force"] = force
        called["source"] = source
        return {"decision": "create_and_start", "study_id": study_id, "quest_id": study_id}

    monkeypatch.setattr(cli.study_runtime_router, "ensure_study_runtime", fake_ensure)

    exit_code = cli.main(
        [
            "ensure-study-runtime",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--entry-mode",
            "full_research",
            "--force",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] == "full_research"
    assert called["force"] is True
    assert called["source"] == "cli"
    assert '"decision": "create_and_start"' in captured.out


def test_study_runtime_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_status(*, profile, study_id: str | None, study_root: Path | None, entry_mode: str | None) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        return {"decision": "noop", "study_id": study_id, "quest_status": "running"}

    monkeypatch.setattr(cli.study_runtime_router, "study_runtime_status", fake_status)

    exit_code = cli.main(
        [
            "study-runtime-status",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert '"quest_status": "running"' in captured.out


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


def test_init_workspace_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init_workspace(
        *,
        workspace_root: Path,
        workspace_name: str,
        dry_run: bool,
        force: bool,
        default_publication_profile: str,
        default_citation_style: str,
    ) -> dict:
        called["workspace_root"] = workspace_root
        called["workspace_name"] = workspace_name
        called["dry_run"] = dry_run
        called["force"] = force
        called["default_publication_profile"] = default_publication_profile
        called["default_citation_style"] = default_citation_style
        return {
            "workspace_root": str(workspace_root),
            "workspace_name": workspace_name,
            "dry_run": dry_run,
            "force": force,
        }

    monkeypatch.setattr(cli.workspace_init_controller, "init_workspace", fake_init_workspace)

    exit_code = cli.main(
        [
            "init-workspace",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--workspace-name",
            "diabetes",
            "--dry-run",
            "--force",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["workspace_name"] == "diabetes"
    assert called["dry_run"] is True
    assert called["force"] is True
    assert called["default_publication_profile"] == "general_medical_journal"
    assert called["default_citation_style"] == "AMA"
    assert '"workspace_name": "diabetes"' in captured.out


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


def test_apply_data_asset_update_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    payload_file = tmp_path / "payload.json"
    payload_file.write_text('{"action":"refresh_all"}\n', encoding="utf-8")

    def fake_apply(*, workspace_root: Path, payload: dict) -> dict:
        called["workspace_root"] = workspace_root
        called["payload"] = payload
        return {"status": "applied", "action": payload["action"]}

    monkeypatch.setattr(cli.data_asset_updates_controller, "apply_data_asset_update", fake_apply)

    exit_code = cli.main(
        [
            "apply-data-asset-update",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--payload-file",
            str(payload_file),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["payload"] == {"action": "refresh_all"}
    assert '"action": "refresh_all"' in captured.out


def test_load_json_payload_from_args_rejects_non_object_payload_json() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    args = argparse.Namespace(payload_file=None, payload_json='["not", "an", "object"]')
    with pytest.raises(SystemExit, match="JSON payload must be an object"):
        cli._load_json_payload_from_args(args)


def test_load_json_payload_from_args_accepts_object_payload_json() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    args = argparse.Namespace(payload_file=None, payload_json='{"action":"refresh_all"}')
    assert cli._load_json_payload_from_args(args) == {"action": "refresh_all"}


def test_recommend_aris_sidecar_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    payload_file = tmp_path / "recommend.json"
    payload_file.write_text(
        '{"requires_algorithmic_innovation": true, "task_definition_ready": true, "data_contract_frozen": true, '
        '"evaluation_contract_ready": true, "compute_budget_available": true, "baseline_available": true}\n',
        encoding="utf-8",
    )

    def fake_recommend(*, quest_root: Path, payload: dict) -> dict:
        called["quest_root"] = quest_root
        called["payload"] = payload
        return {"status": "recommended", "recommendation": "request_user_confirmation"}

    monkeypatch.setattr(cli.aris_sidecar_controller, "recommend_aris_sidecar", fake_recommend)

    exit_code = cli.main(
        [
            "recommend-aris-sidecar",
            "--quest-root",
            str(tmp_path / "runtime" / "quests" / "q001"),
            "--payload-file",
            str(payload_file),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "runtime" / "quests" / "q001"
    assert called["payload"]["baseline_available"] is True
    assert '"recommended"' in captured.out


def test_provision_aris_sidecar_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    payload_file = tmp_path / "contract.json"
    payload_file.write_text(
        '{"problem_anchor": {"clinical_question": "q", "research_object": "o", "endpoint": "e", "task_type": "t"}, '
        '"data_contract": {"dataset_version": "v1", "modalities": ["ct"], "splits": "locked", '
        '"external_validation_required": true, "preprocessing_boundary": "v1"}, '
        '"evaluation_contract": {"primary_metric": "auroc", "secondary_metrics": ["auprc"], '
        '"required_baselines": ["b1"], "statistics": ["bootstrap_ci"], "compute_budget": {"gpu_hours": 8}}, '
        '"innovation_scope": {"allowed": ["fusion"], "forbidden": ["endpoint_redefinition"]}, '
        '"writing_questions": ["a", "b", "c", "d"], '
        '"optional_context": {}, '
        '"user_confirmation": {"confirmed": true, "confirmed_by": "human", "confirmed_at": "2026-03-29T12:00:00+00:00"}}\n',
        encoding="utf-8",
    )

    def fake_provision(*, quest_root: Path, payload: dict) -> dict:
        called["quest_root"] = quest_root
        called["payload"] = payload
        return {"status": "contract_frozen", "sidecar_root": str(quest_root / "sidecars" / "aris")}

    monkeypatch.setattr(cli.aris_sidecar_controller, "provision_aris_sidecar", fake_provision)

    exit_code = cli.main(
        [
            "provision-aris-sidecar",
            "--quest-root",
            str(tmp_path / "runtime" / "quests" / "q001"),
            "--payload-file",
            str(payload_file),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "runtime" / "quests" / "q001"
    assert called["payload"]["user_confirmation"]["confirmed"] is True
    assert '"contract_frozen"' in captured.out


def test_import_aris_sidecar_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_import(*, quest_root: Path) -> dict:
        called["quest_root"] = quest_root
        return {"status": "imported", "artifact_root": str(quest_root / "artifacts" / "algorithm_research" / "aris")}

    monkeypatch.setattr(cli.aris_sidecar_controller, "import_aris_sidecar_result", fake_import)

    exit_code = cli.main(
        [
            "import-aris-sidecar",
            "--quest-root",
            str(tmp_path / "runtime" / "quests" / "q001"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "runtime" / "quests" / "q001"
    assert '"imported"' in captured.out


def test_recommend_sidecar_command_dispatches_generic_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    payload_file = tmp_path / "recommend.json"
    payload_file.write_text(
        '{"figure_id": "F3C", "figure_ticket_open": true, "storyboard_ready": true, '
        '"source_artifacts_ready": true, "paper_role_allowed": true, "non_evidence_figure": true, '
        '"editable_svg_required": true}\n',
        encoding="utf-8",
    )

    def fake_recommend(*, quest_root: Path, provider_id: str, payload: dict, instance_id: str | None = None) -> dict:
        called["quest_root"] = quest_root
        called["provider_id"] = provider_id
        called["payload"] = payload
        called["instance_id"] = instance_id
        return {"status": "recommended", "provider": provider_id, "instance_id": "F3C"}

    monkeypatch.setattr(cli.sidecar_provider_controller, "recommend_sidecar", fake_recommend)

    exit_code = cli.main(
        [
            "recommend-sidecar",
            "--provider",
            "aris",
            "--quest-root",
            str(tmp_path / "runtime" / "quests" / "q001"),
            "--payload-file",
            str(payload_file),
            "--instance-id",
            "F3C",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["provider_id"] == "aris"
    assert called["instance_id"] == "F3C"
    assert called["payload"]["figure_ticket_open"] is True
    assert '"recommended"' in captured.out


def test_import_sidecar_command_dispatches_generic_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_import(*, quest_root: Path, provider_id: str, instance_id: str | None = None) -> dict:
        called["quest_root"] = quest_root
        called["provider_id"] = provider_id
        called["instance_id"] = instance_id
        return {
            "status": "imported",
            "artifact_root": str(quest_root / "artifacts" / "algorithm_research" / "aris"),
        }

    monkeypatch.setattr(cli.sidecar_provider_controller, "import_sidecar_result", fake_import)

    exit_code = cli.main(
        [
            "import-sidecar",
            "--provider",
            "aris",
            "--quest-root",
            str(tmp_path / "runtime" / "quests" / "q001"),
            "--instance-id",
            "F3C",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["provider_id"] == "aris"
    assert called["instance_id"] == "F3C"
    assert '"imported"' in captured.out


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


def test_resolve_reference_papers_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_resolve(*, quest_root: Path) -> dict:
        called["quest_root"] = quest_root
        return {"status": "resolved", "paper_count": 2}

    monkeypatch.setattr(cli.reference_papers_controller, "resolve_reference_papers", fake_resolve)

    exit_code = cli.main(
        [
            "resolve-reference-papers",
            "--quest-root",
            str(tmp_path / "quests" / "002-early-residual-risk"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "quests" / "002-early-residual-risk"
    assert '"paper_count": 2' in captured.out


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


def test_figure_loop_guard_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_controller(
        *,
        quest_root: Path,
        apply: bool,
        outbox_path: Path | None = None,
        daemon_url: str | None = None,
        accepted_figures: dict[str, str] | None = None,
        figure_tickets: dict[str, str] | None = None,
        required_routes: list[str] | None = None,
        min_figure_mentions: int = 12,
        min_reference_count: int = 12,
        recent_window: int = 120,
        source: str = "medautosci-figure-loop-guard",
    ) -> dict:
        called["quest_root"] = quest_root
        called["apply"] = apply
        called["accepted_figures"] = accepted_figures
        called["figure_tickets"] = figure_tickets
        called["required_routes"] = required_routes
        called["min_figure_mentions"] = min_figure_mentions
        called["min_reference_count"] = min_reference_count
        called["recent_window"] = recent_window
        called["source"] = source
        return {"status": "blocked", "blockers": ["figure_loop_budget_exceeded"]}

    monkeypatch.setattr(cli.figure_loop_guard, "run_controller", fake_run_controller)

    exit_code = cli.main(
        [
            "figure-loop-guard",
            "--quest-root",
            str(tmp_path / "q001"),
            "--apply",
            "--accepted-figure",
            "F4B=teacher accepted",
            "--figure-ticket",
            "F3C=text overflow",
            "--required-route",
            "literature_scout",
            "--required-route",
            build_figure_route(FIGURE_ROUTE_SCRIPT_FIX, "F3C"),
            "--required-route",
            build_figure_route(FIGURE_ROUTE_ILLUSTRATION_PROGRAM, "F5A"),
            "--min-figure-mentions",
            "3",
            "--min-reference-count",
            "12",
            "--recent-window",
            "120",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "q001"
    assert called["apply"] is True
    assert called["accepted_figures"] == {"F4B": "teacher accepted"}
    assert called["figure_tickets"] == {"F3C": "text overflow"}
    assert called["required_routes"] == [
        "literature_scout",
        build_figure_route(FIGURE_ROUTE_SCRIPT_FIX, "F3C"),
        build_figure_route(FIGURE_ROUTE_ILLUSTRATION_PROGRAM, "F5A"),
    ]
    assert called["min_figure_mentions"] == 3
    assert called["min_reference_count"] == 12
    assert called["recent_window"] == 120
    assert '"figure_loop_budget_exceeded"' in captured.out


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


def test_bootstrap_command_ensures_profile_overlay(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    calls: dict[str, object] = {}

    def fake_ensure(
        *,
        quest_root: Path | None = None,
        skill_ids: tuple[str, ...] | None = None,
        mode: str = "ensure_ready",
        policy_id: str | None = None,
        archetype_ids: tuple[str, ...] | None = None,
        default_submission_targets: tuple[dict[str, object], ...] | None = None,
        default_publication_profile: str | None = None,
        default_citation_style: str | None = None,
    ) -> dict:
        calls["ensure_quest_root"] = quest_root
        calls["ensure_skill_ids"] = skill_ids
        calls["ensure_mode"] = mode
        calls["ensure_policy_id"] = policy_id
        calls["ensure_archetype_ids"] = archetype_ids
        calls["ensure_default_submission_targets"] = default_submission_targets
        calls["ensure_default_publication_profile"] = default_publication_profile
        calls["ensure_default_citation_style"] = default_citation_style
        return {
            "mode": mode,
            "selected_action": "noop",
            "pre_status": {"all_targets_ready": True},
            "post_status": {"all_targets_ready": True},
            "action_result": None,
        }

    def fake_refresh_data_assets(*, workspace_root: Path) -> dict:
        calls["refresh_data_assets_workspace_root"] = workspace_root
        return {
            "init": {"private": {"release_count": 1}},
            "status": {"layout_ready": True},
            "public_validation": {"valid_dataset_count": 1},
            "impact_report": {"study_count": 2, "report_path": "/tmp/impact.json"},
            "startup_data_readiness": {
                "status": "attention_needed",
                "recommendations": ["screen_valid_public_datasets_for_extension"],
            },
        }

    monkeypatch.setattr(
        cli.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(cli.overlay_installer, "ensure_medical_overlay", fake_ensure)
    monkeypatch.setattr(cli.data_asset_updates_controller, "refresh_data_assets", fake_refresh_data_assets)

    exit_code = cli.main(["bootstrap", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls["ensure_skill_ids"] == ("scout", "idea", "decision", "write", "finalize")
    assert calls["ensure_quest_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert calls["ensure_mode"] == "ensure_ready"
    assert calls["ensure_policy_id"] == "high_plasticity_medical"
    assert calls["ensure_archetype_ids"] == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    )
    assert calls["ensure_default_submission_targets"] == (
        {
            "publication_profile": "frontiers_family_harvard",
            "primary": True,
            "package_required": True,
            "story_surface": "general_medical_journal",
        },
    )
    assert calls["ensure_default_publication_profile"] == "general_medical_journal"
    assert calls["ensure_default_citation_style"] == "AMA"
    assert calls["refresh_data_assets_workspace_root"] == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert '"selected_action": "noop"' in captured.out
    assert '"impact_report"' in captured.out
    assert '"startup_data_readiness"' in captured.out
    assert '"studies"' not in captured.out


def test_bootstrap_command_honors_status_only_overlay_mode(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    profile_text = profile_path.read_text(encoding="utf-8").replace(
        'medical_overlay_bootstrap_mode = "ensure_ready"',
        'medical_overlay_bootstrap_mode = "status_only"',
    )
    profile_path.write_text(profile_text, encoding="utf-8")
    calls: dict[str, object] = {}

    def fake_ensure(*, mode: str = "ensure_ready", **kwargs) -> dict:
        calls["mode"] = mode
        calls["kwargs"] = kwargs
        return {
            "mode": mode,
            "selected_action": "status_only",
            "pre_status": {"all_targets_ready": False},
            "post_status": {"all_targets_ready": False},
            "action_result": None,
        }

    monkeypatch.setattr(
        cli.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(cli.overlay_installer, "ensure_medical_overlay", fake_ensure)
    monkeypatch.setattr(
        cli.data_asset_updates_controller,
        "refresh_data_assets",
        lambda *, workspace_root: {"status": {"layout_ready": True}},
    )

    exit_code = cli.main(["bootstrap", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls["mode"] == "status_only"
    assert '"selected_action": "status_only"' in captured.out
