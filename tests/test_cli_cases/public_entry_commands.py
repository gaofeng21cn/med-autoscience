from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

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

    exit_code = main(["doctor", "report", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "profile: nfpitnet" in captured.out
    assert "workspace_root: /Users/gaofeng/workspace/Yang/NF-PitNET" in captured.out
    assert "hermes_agent_repo_root: /Users/gaofeng/workspace/_external/hermes-agent" in captured.out
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

    exit_code = main(["doctor", "profile", "--profile", str(profile_path)])
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
    assert "hermes_home_root: " in captured.out
    assert "autofigure" not in captured.out.lower()
def test_doctor_hermes_runtime_grouped_command_is_retired(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["doctor", "hermes-runtime", "--profile", str(tmp_path / "profile.toml")])
    captured = capsys.readouterr()

    assert excinfo.value.code == "Grouped command requires a supported subcommand under `doctor`."
    assert captured.err == ""
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

    exit_code = main(["doctor", "profile", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["name"] == "nfpitnet"
    assert payload["workspace_root"] == "/Users/gaofeng/workspace/Yang/NF-PitNET"
    assert "med_deepscientist_runtime_root" not in payload
    assert "med_deepscientist_repo_root" not in payload
    assert payload["source_provenance"]["surface_kind"] == "source_provenance"
    assert payload["historical_fixture_ref"]["read_only"] is True
    assert payload["explicit_archive_import_ref"]["read_only"] is True
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
def test_show_profile_does_not_require_display_surface_dependencies(tmp_path: Path, monkeypatch, capsys) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)

    sys.modules.pop("med_autoscience.cli", None)
    sys.modules.pop("med_autoscience.controllers.display_surface_materialization", None)

    real_import = builtins.__import__
    blocked_modules = ("matplotlib", "packaging", "pandas")

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if any(name == module_name or name.startswith(f"{module_name}.") for module_name in blocked_modules):
            root_name = name.split(".", 1)[0]
            raise ModuleNotFoundError(f"No module named '{root_name}'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["doctor", "profile", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "name: nfpitnet" in captured.out
def test_public_help_does_not_require_doctor_runtime_dependencies(monkeypatch, capsys) -> None:
    sys.modules.pop("med_autoscience.cli", None)
    sys.modules.pop("med_autoscience.doctor", None)

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "opl_harness_shared" or name.startswith("opl_harness_shared."):
            raise ModuleNotFoundError("No module named 'opl_harness_shared'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["--help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Usage: medautosci <group> <command> [options]" in captured.out
def test_public_help_prints_grouped_surface(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["--help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Usage: medautosci <group> <command> [options]" in captured.out
    assert "doctor" in captured.out
    assert "publication" in captured.out
    assert "product manifest" in captured.out
def test_group_help_lists_subcommands(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["study"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Usage: medautosci study <command> [options]" in captured.out
    assert "progress" in captured.out
    assert "runtime-status" in captured.out


def test_publication_group_help_lists_route_memory_inventory(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["publication"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Usage: medautosci publication <command> [options]" in captured.out
    assert "route-memory-inventory" in captured.out


def test_shell_argv_grouped_subcommand_dispatches(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)
    calls: dict[str, object] = {}

    def fake_read_study_progress(
        *,
        profile,
        profile_ref,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
    ) -> dict[str, object]:
        calls["profile"] = profile
        calls["profile_ref"] = profile_ref
        calls["study_id"] = study_id
        calls["study_root"] = study_root
        calls["entry_mode"] = entry_mode
        return {
            "study_id": "001-risk",
            "current_stage": "writing",
            "current_stage_summary": "shell argv grouped command works.",
        }

    monkeypatch.setattr(cli.study_progress, "read_study_progress", fake_read_study_progress)
    monkeypatch.setattr(
        cli.study_progress,
        "render_study_progress_markdown",
        lambda payload: "# 研究进度\n\nshell argv grouped command works.\n",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "medautosci",
            "study",
            "progress",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
        ],
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls["profile"].name == "nfpitnet"
    assert calls["profile_ref"] == profile_path
    assert calls["study_id"] == "001-risk"
    assert calls["study_root"] is None
    assert calls["entry_mode"] is None
    assert "shell argv grouped command works." in captured.out
def test_shell_argv_grouped_subcommand_help_uses_grouped_prog(monkeypatch, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    monkeypatch.setattr(sys, "argv", ["medautosci", "publication", "gate", "--help"])

    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    captured = capsys.readouterr()

    assert excinfo.value.code == 0
    assert "usage: medautosci publication gate" in captured.out

def test_show_stage_route_contract_outputs_canonical_payload(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["doctor", "stage-route-contract"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out) == render_stage_route_contract_payload()


def test_show_stage_route_contract_is_only_public_route_contract_command(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["doctor", "stage-route-contract"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out) == render_stage_route_contract_payload()


def test_old_entry_modes_alias_is_removed(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["doctor", "entry-modes"])
    captured = capsys.readouterr()

    assert str(excinfo.value) == "Grouped command requires a supported subcommand under `doctor`."
    assert captured.out == ""
    assert captured.err == ""
def test_sync_agent_entry_assets_command_writes_four_files(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    expected_assets = {
        "docs/runtime/contracts/stage_route_contract.md": render_stage_route_contract_guide(),
        "templates/stage_route_contract.yaml": render_public_yaml(),
        "templates/codex/medautoscience-entry.SKILL.md": render_codex_entry_skill(),
        "templates/openclaw/medautoscience-entry.prompt.md": render_openclaw_entry_prompt(),
    }

    exit_code = cli.main(["doctor", "sync-entry-assets", "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["written_count"] == 4
    assert set(payload["written_files"]) == {str(tmp_path / path) for path in expected_assets}
    for relative_path, expected_content in expected_assets.items():
        output_path = tmp_path / relative_path
        assert output_path.is_file()
        assert output_path.read_text(encoding="utf-8") == expected_content
def test_preflight_changes_command_outputs_json(monkeypatch, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    monkeypatch.setattr(cli.dev_preflight, "collect_changed_files", lambda **kwargs: ["README.md"])
    monkeypatch.setattr(
        cli.dev_preflight,
        "run_preflight",
        lambda **kwargs: cli.dev_preflight.PreflightResult(
            input_mode="files",
            changed_files=("README.md",),
            matched_categories=("documentation_review_only",),
            unclassified_changes=(),
            planned_commands=(),
            results=(),
            ok=True,
        ),
    )

    exit_code = cli.main(["doctor", "preflight", "--files", "README.md", "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["ok"] is True
    assert payload["changed_files"] == ["README.md"]
    assert payload["matched_categories"] == ["documentation_review_only"]


def test_preflight_base_ref_command_uses_ci_preflight(monkeypatch, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_ci_preflight(**kwargs):
        called.update(kwargs)
        return cli.dev_preflight.PreflightResult(
            input_mode="ci-base_ref",
            changed_files=("src/med_autoscience/new.py",),
            matched_categories=("generic_python_regression_surface",),
            unclassified_changes=(),
            planned_commands=("make test-regression",),
            results=(),
            ok=True,
        )

    monkeypatch.setattr(cli.dev_preflight, "run_ci_preflight", fake_run_ci_preflight)

    exit_code = cli.main(["doctor", "preflight", "--base-ref", "HEAD~1", "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["base_ref"] == "HEAD~1"
    payload = json.loads(captured.out)
    assert payload["input_mode"] == "ci-base_ref"
    assert payload["planned_commands"] == ["make test-regression"]
def test_preflight_changes_command_rejects_multiple_change_sources() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit):
        cli.main(["doctor", "preflight", "--files", "README.md", "--staged"])
def test_watch_command_dispatches_runtime_watch(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
        apply_supervisor_platform_repair: bool = False,
    ) -> dict:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        called["apply_supervisor_platform_repair"] = apply_supervisor_platform_repair
        return {"scanned_quests": ["q001"], "runtime_root": str(runtime_root)}

    monkeypatch.setattr(cli.runtime_watch, "run_watch_for_runtime", fake_run_watch_for_runtime)

    exit_code = cli.main(["runtime", "watch", "--runtime-root", str(tmp_path / "quests"), "--apply"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["runtime_root"] == tmp_path / "quests"
    assert called["apply"] is True
    assert called["profile"] is None
    assert called["ensure_study_runtimes"] is False
    assert called["apply_supervisor_platform_repair"] is False
    assert "q001" in captured.out
def test_study_progress_command_dispatches_controller_and_renders_markdown(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_read_study_progress(
        *,
        profile,
        profile_ref,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        return {
            "study_id": "001-risk",
            "current_stage": "waiting_user_decision",
            "current_stage_summary": "系统已经推进到需要用户确认的节点。",
        }

    monkeypatch.setattr(cli.study_progress, "read_study_progress", fake_read_study_progress)
    monkeypatch.setattr(
        cli.study_progress,
        "render_study_progress_markdown",
        lambda payload: "# 研究进度\n\n系统已经推进到需要用户确认的节点。\n",
    )

    exit_code = cli.main(
        [
            "study",
            "progress",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == profile_path
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert "# 研究进度" in captured.out
    assert "用户确认" in captured.out
def test_medical_reporting_audit_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
        called["quest_root"] = quest_root
        called["apply"] = apply
        return {"status": "clear", "quest_root": str(quest_root)}

    monkeypatch.setattr(cli.medical_reporting_audit, "run_controller", fake_run_controller)

    exit_code = cli.main(["publication", "reporting-audit", "--quest-root", str(tmp_path / "quest")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "quest"
    assert called["apply"] is False
    assert '"status": "clear"' in captured.out


def test_migration_audit_command_dispatches_read_only_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_migration_audit(*, workspace_roots, dry_run: bool) -> dict[str, object]:
        called["workspace_roots"] = list(workspace_roots)
        called["dry_run"] = dry_run
        return {
            "surface": "control_plane_migration_audit",
            "report_id": "control-plane-migration-audit::mock",
            "recorded_at": "1970-01-01T00:00:00+00:00",
            "workspace_fingerprint": "workspace-migration-audit::mock",
            "study_fingerprint": "study-migration-audit::mock",
            "dry_run": dry_run,
            "workspace_count": len(list(workspace_roots)),
            "study_count": 2,
            "unclassified_authority_surface": 0,
            "delivery_projection_completion_plan_count": 1,
            "action_counts": {"apply": 0, "delete": 0, "write": 0, "mutating": 0},
            "mutating_actions": [],
            "studies": [
                {
                    "study_id": "001-risk",
                    "study_fingerprint": "study-migration-audit::001",
                    "workspace_fingerprint": "workspace-migration-audit::001",
                    "recorded_at": "1970-01-01T00:00:00+00:00",
                    "authority_classification": "controller_authorized",
                    "lifecycle_classification": "package_and_submission_ready",
                    "delivery_projection_completeness_reason": "current_package_and_submission_minimal_present",
                    "delivery_projection_completion_plan": None,
                }
            ],
        }

    monkeypatch.setattr(cli.control_plane_migration_audit, "run_migration_audit", fake_run_migration_audit)

    exit_code = cli.main(
        [
            "control-plane-migration-audit",
            "--workspace-root",
            str(tmp_path / "DM-CVD-Mortality-Risk"),
            "--workspace-root",
            str(tmp_path / "NF-PitNET"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "workspace_roots": [
            tmp_path / "DM-CVD-Mortality-Risk",
            tmp_path / "NF-PitNET",
        ],
        "dry_run": True,
    }
    payload = json.loads(captured.out)
    assert payload["dry_run"] is True
    assert payload["report_id"] == "control-plane-migration-audit::mock"
    assert payload["workspace_fingerprint"] == "workspace-migration-audit::mock"
    assert payload["study_fingerprint"] == "study-migration-audit::mock"
    assert payload["delivery_projection_completion_plan_count"] == 1
    assert payload["action_counts"]["mutating"] == 0
    assert payload["mutating_actions"] == []


def test_cleanup_apply_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_cleanup_apply(*, workspace_roots, apply: bool, control_plane_snapshot=None) -> dict[str, object]:
        called["workspace_roots"] = list(workspace_roots)
        called["apply"] = apply
        called["control_plane_snapshot"] = control_plane_snapshot
        return {
            "surface": "control_plane_cleanup_apply",
            "apply": apply,
            "status": "planned",
            "workspace_count": len(list(workspace_roots)),
            "action_counts": {"planned": 1, "blocked": 0, "applied": 0, "mutating": 0},
            "apply_plan": [{"action": "delete-safe-cache"}],
            "applied_actions": [],
        }

    monkeypatch.setattr(cli.control_plane_cleanup_apply, "run_cleanup_apply", fake_run_cleanup_apply)

    exit_code = cli.main(
        [
            "control-plane-cleanup-apply",
            "--workspace-root",
            str(tmp_path / "workspace"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "workspace_roots": [tmp_path / "workspace"],
        "apply": False,
        "control_plane_snapshot": None,
    }
    payload = json.loads(captured.out)
    assert payload["surface"] == "control_plane_cleanup_apply"
    assert payload["apply"] is False
    assert payload["action_counts"]["mutating"] == 0


def test_lifecycle_report_command_dispatches_read_only_controller_options(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_lifecycle_operations_report(*, workspace_roots, deep: bool, max_files: int, max_seconds: float) -> dict[str, object]:
        called["workspace_roots"] = list(workspace_roots)
        called["deep"] = deep
        called["max_files"] = max_files
        called["max_seconds"] = max_seconds
        return {
            "surface": "control_plane_lifecycle_report",
            "workspace_count": len(list(workspace_roots)),
            "scan_policy": {
                "deep_scan_enabled": deep,
                "max_files": max_files,
                "max_seconds": max_seconds,
            },
            "mutation_policy": {"read_only": True, "physical_cleanup_performed": False},
        }

    monkeypatch.setattr(
        cli.artifact_lifecycle_operations_report,
        "run_lifecycle_operations_report",
        fake_run_lifecycle_operations_report,
    )

    exit_code = cli.main(
        [
            "control-plane-lifecycle-report",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--deep",
            "--max-files",
            "7",
            "--max-seconds",
            "1.5",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "workspace_roots": [tmp_path / "workspace"],
        "deep": True,
        "max_files": 7,
        "max_seconds": 1.5,
    }
    payload = json.loads(captured.out)
    assert payload["surface"] == "control_plane_lifecycle_report"
    assert payload["scan_policy"]["deep_scan_enabled"] is True
    assert payload["scan_policy"]["max_files"] == 7
    assert payload["scan_policy"]["max_seconds"] == 1.5
    assert payload["mutation_policy"]["physical_cleanup_performed"] is False


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
        apply_supervisor_platform_repair: bool = False,
    ) -> dict:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        called["apply_supervisor_platform_repair"] = apply_supervisor_platform_repair
        return {"managed_study_actions": [{"study_id": "001-risk", "decision": "create_and_start"}]}

    monkeypatch.setattr(cli.runtime_watch, "run_watch_for_runtime", fake_run_watch_for_runtime)

    exit_code = cli.main(
        [
            "runtime",
            "watch",
            "--runtime-root",
            str(tmp_path / "quests"),
            "--profile",
            str(profile_path),
            "--ensure-study-runtimes",
            "--apply-supervisor-platform-repair",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["runtime_root"] == tmp_path / "quests"
    assert called["apply"] is True
    assert called["profile"].name == "nfpitnet"
    assert called["ensure_study_runtimes"] is True
    assert called["apply_supervisor_platform_repair"] is True
    assert '"study_id": "001-risk"' in captured.out
from .runtime_storage_commands import (
    test_runtime_maintain_storage_command_dispatches_controller,
    test_runtime_storage_audit_command_dispatches_controller,
)

from .domain_slo_scheduler_projection_commands import (
    test_runtime_ensure_supervision_command_defaults_to_opl_replacement_manager,
    test_runtime_ensure_supervision_command_rejects_retired_hermes_manager,
    test_runtime_ensure_supervision_command_rejects_retired_local_manager,
    test_runtime_remove_supervision_command_defaults_to_opl_replacement_manager,
    test_runtime_supervision_status_command_dispatches_scheduler_facade,
    test_runtime_supervision_cli_rejects_retired_workspace_local_managers,
)


def test_watch_command_rejects_retired_loop_parameter(tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit):
        cli.main(
            [
                "runtime",
                "watch",
                "--runtime-root",
                str(tmp_path / "quests"),
                "--loop",
            ]
        )
def test_resolve_journal_shortlist_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_resolve(*, study_root: Path) -> dict[str, object]:
        called["study_root"] = study_root
        return {"status": "resolved", "shortlist": ["Heart"], "candidate_count": 1}

    monkeypatch.setattr(cli.journal_shortlist_controller, "resolve_journal_shortlist", fake_resolve)

    exit_code = cli.main(["publication", "resolve-journal-shortlist", "--study-root", str(tmp_path / "study")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == tmp_path / "study"
    assert '"status": "resolved"' in captured.out


def test_publication_aftercare_plan_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_aftercare(*, study_root: Path, quest_root: Path | None = None) -> dict[str, object]:
        called["study_root"] = study_root
        called["quest_root"] = quest_root
        return {
            "surface_kind": "mas_publication_aftercare_plan",
            "analysis_queue_entry": {"status": "ready"},
        }

    monkeypatch.setattr(cli.publication_aftercare, "build_publication_aftercare_plan", fake_aftercare)

    exit_code = cli.main(
        [
            "publication",
            "aftercare-plan",
            "--study-root",
            str(tmp_path / "study"),
            "--quest-root",
            str(tmp_path / "quest"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == tmp_path / "study"
    assert called["quest_root"] == tmp_path / "quest"
    assert '"surface_kind": "mas_publication_aftercare_plan"' in captured.out


def test_resolve_journal_requirements_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_resolve(
        *,
        study_root: Path,
        journal_name: str | None = None,
        journal_slug: str | None = None,
        official_guidelines_url: str | None = None,
        publication_profile: str | None = None,
        requirements_payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        called["study_root"] = study_root
        called["journal_name"] = journal_name
        called["journal_slug"] = journal_slug
        called["official_guidelines_url"] = official_guidelines_url
        called["publication_profile"] = publication_profile
        called["requirements_payload"] = requirements_payload
        return {"status": "resolved", "journal_slug": "rheumatology-international"}

    monkeypatch.setattr(cli.journal_requirements_controller, "resolve_journal_requirements", fake_resolve)

    exit_code = cli.main(
        [
            "publication",
            "resolve-journal-requirements",
            "--study-root",
            str(tmp_path / "study"),
            "--journal-name",
            "Rheumatology International",
            "--official-guidelines-url",
            "https://example.org/ri-guide",
            "--publication-profile",
            "general_medical_journal",
            "--requirements-json",
            '{"abstract_word_cap": 250}',
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == tmp_path / "study"
    assert called["journal_name"] == "Rheumatology International"
    assert called["official_guidelines_url"] == "https://example.org/ri-guide"
    assert called["publication_profile"] == "general_medical_journal"
    assert called["requirements_payload"] == {"abstract_word_cap": 250}
    assert '"journal_slug": "rheumatology-international"' in captured.out
def test_init_portfolio_memory_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {"portfolio_memory_root": str(workspace_root / "portfolio" / "research_memory"), "created_files": []}

    monkeypatch.setattr(cli.portfolio_memory_controller, "init_portfolio_memory", fake_init)

    exit_code = cli.main(["data", "init-memory", "--workspace-root", str(tmp_path / "workspace")])
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

    exit_code = cli.main(["data", "memory-status", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"asset_count": 3' in captured.out
def test_init_workspace_literature_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {
            "workspace_literature_root": str(workspace_root / "portfolio" / "research_memory" / "literature"),
            "created_files": [],
        }

    monkeypatch.setattr(cli.workspace_literature_controller, "init_workspace_literature", fake_init)

    exit_code = cli.main(["data", "init-literature", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"workspace_literature_root"' in captured.out
def test_workspace_literature_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {"workspace_literature_exists": True, "record_count": 7}

    monkeypatch.setattr(cli.workspace_literature_controller, "workspace_literature_status", fake_status)

    exit_code = cli.main(["data", "literature-status", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"record_count": 7' in captured.out
