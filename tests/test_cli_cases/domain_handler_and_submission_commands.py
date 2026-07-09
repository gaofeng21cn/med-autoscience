from __future__ import annotations

import types

from tests.test_cli_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_cli_runtime_facing_controller_proxies_are_named_currentness_surfaces(monkeypatch) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    proxy_targets = {
        "domain_status_projection": "domain_status_projection",
        "gate_clearing_batch": "gate_clearing_batch",
        "quality_repair_batch": "quality_repair_batch",
        "runtime_health_kernel": "runtime_health_kernel",
    }
    assert not hasattr(cli, "study_progress")

    for attr_name, module_basename in proxy_targets.items():
        module_name = f"med_autoscience.controllers.{module_basename}"
        proxy = getattr(cli, attr_name)
        assert object.__getattribute__(proxy, "_module_name") == module_name

        first_module = types.ModuleType(module_name)
        first_module.currentness_marker = f"{module_basename}:first"
        second_module = types.ModuleType(module_name)
        second_module.currentness_marker = f"{module_basename}:second"

        monkeypatch.setitem(sys.modules, module_name, first_module)
        assert proxy.currentness_marker == f"{module_basename}:first"
        monkeypatch.setitem(sys.modules, module_name, second_module)
        assert proxy.currentness_marker == f"{module_basename}:second"


def test_removed_provider_specific_aris_sidecar_commands_are_rejected(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    for command in (
        "recommend-aris-sidecar",
        "provision-aris-sidecar",
        "import-aris-sidecar",
        "recommend-sidecar",
        "provision-sidecar",
        "import-sidecar",
    ):
        with pytest.raises(SystemExit) as excinfo:
            cli.main([command, "--quest-root", "/tmp/quest"])
        captured = capsys.readouterr()

        assert excinfo.value.code == 2
        assert "invalid choice" in captured.err
        assert command in captured.err


def _run_cli_dispatch_case(
    cli,
    monkeypatch,
    capsys,
    *,
    target_attr,
    function_name,
    args,
    result,
    expected_call,
    output_contains,
    ignore_call_keys=(),
    default_call_values=None,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_dispatch(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return result

    monkeypatch.setattr(getattr(cli, target_attr), function_name, fake_dispatch)

    exit_code = cli.main(args)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert len(calls) == 1
    actual_call = {key: value for key, value in calls[0].items() if key not in ignore_call_keys}
    if default_call_values:
        actual_call = {**default_call_values, **actual_call}
    assert actual_call == expected_call
    for expected in output_contains:
        assert expected in captured.out


def test_simple_cli_commands_dispatch_to_expected_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    cases = (
        {
            "target_attr": "delivery_inspector",
            "function_name": "inspect_study_delivery",
            "args": [
                "publication",
                "delivery-inspect",
                "--profile",
                str(profile_path),
                "--study-id",
                "001-risk",
                "--format",
                "json",
            ],
            "result": {
                "surface": "delivery_inspector",
                "mutation_policy": {"read_only": True, "writes_package": False},
                "freshness": {"verdict": "current"},
            },
            "expected_call": {"study_id": "001-risk", "study_root": None, "profile_ref": profile_path},
            "ignore_call_keys": ("profile", "publication_profile"),
            "output_contains": ('"read_only": true', '"verdict": "current"'),
        },
        {
            "target_attr": "startup_data_readiness_controller",
            "function_name": "startup_data_readiness",
            "args": ["data", "startup-readiness", "--workspace-root", str(tmp_path / "workspace")],
            "result": {"status": "clear", "study_summary": {"study_count": 2}},
            "expected_call": {"workspace_root": tmp_path / "workspace"},
            "output_contains": ('"study_count": 2',),
        },
        {
            "target_attr": "data_asset_gate",
            "function_name": "run_controller",
            "args": ["data", "asset-gate", "--quest-root", str(tmp_path / "q001"), "--apply"],
            "result": {
                "status": "blocked",
                "blockers": ["outdated_private_release"],
                "report_json": "/tmp/data_gate.json",
            },
            "expected_call": {"quest_root": tmp_path / "q001", "apply": True},
            "output_contains": ('"outdated_private_release"',),
        },
        {
            "target_attr": "tooluniverse_adapter",
            "function_name": "detect_tooluniverse",
            "args": [
                "data",
                "tooluniverse-status",
                "--workspace-root",
                str(tmp_path / "workspace"),
                "--tooluniverse-root",
                str(tmp_path / "ToolUniverse"),
            ],
            "result": {"available": True, "roles": ["知识检索", "功能分析"]},
            "expected_call": {"workspace_root": tmp_path / "workspace", "tooluniverse_root": tmp_path / "ToolUniverse"},
            "output_contains": ('"available": true',),
        },
        {
            "target_attr": "submission_package_builder",
            "function_name": "create_submission_minimal_package",
            "args": [
                "publication",
                "export-submission-minimal",
                "--paper-root",
                str(tmp_path / "paper"),
                "--publication-profile",
                "general_medical_journal",
                "--citation-style",
                "AMA",
            ],
            "result": {"output_root": str(tmp_path / "paper" / "submission_minimal")},
            "expected_call": {
                "paper_root": tmp_path / "paper",
                "publication_profile": "general_medical_journal",
                "citation_style": "AMA",
            },
            "output_contains": ("submission_minimal",),
        },
        {
            "target_attr": "submission_targets_controller",
            "function_name": "resolve_submission_targets",
            "args": [
                "publication",
                "resolve-targets",
                "--profile",
                str(profile_path),
                "--study-root",
                str(tmp_path / "studies" / "002-early-residual-risk"),
                "--quest-root",
                str(tmp_path / "quests" / "002-early-residual-risk"),
            ],
            "result": {"status": "resolved", "targets": [{"target_key": "profile:frontiers_family_harvard"}]},
            "expected_call": {
                "profile_path": profile_path,
                "study_root": tmp_path / "studies" / "002-early-residual-risk",
                "quest_root": tmp_path / "quests" / "002-early-residual-risk",
            },
            "output_contains": ('"status": "resolved"',),
        },
        {
            "target_attr": "submission_targets_controller",
            "function_name": "export_submission_targets",
            "args": [
                "publication",
                "export-targets",
                "--paper-root",
                str(tmp_path / "paper"),
                "--profile",
                str(profile_path),
                "--study-root",
                str(tmp_path / "studies" / "002-early-residual-risk"),
                "--quest-root",
                str(tmp_path / "quests" / "002-early-residual-risk"),
            ],
            "result": {"status": "blocked", "blocked_target_count": 1},
            "expected_call": {
                "paper_root": tmp_path / "paper",
                "profile_path": profile_path,
                "study_root": tmp_path / "studies" / "002-early-residual-risk",
                "quest_root": tmp_path / "quests" / "002-early-residual-risk",
            },
            "output_contains": ('"blocked_target_count": 1',),
        },
        {
            "target_attr": "reference_papers_controller",
            "function_name": "resolve_reference_papers",
            "args": [
                "study",
                "resolve-reference-papers",
                "--quest-root",
                str(tmp_path / "quests" / "002-early-residual-risk"),
            ],
            "result": {"status": "resolved", "paper_count": 2},
            "expected_call": {"quest_root": tmp_path / "quests" / "002-early-residual-risk"},
            "output_contains": ('"paper_count": 2',),
        },
        {
            "target_attr": "publication_gate",
            "function_name": "run_controller",
            "args": ["publication", "gate", "--quest-root", str(tmp_path / "q001"), "--apply"],
            "result": {"status": "blocked", "blockers": ["missing_post_main_publishability_gate"]},
            "expected_call": {"quest_root": tmp_path / "q001", "apply": True},
            "output_contains": ('"status": "blocked"',),
        },
        {
            "target_attr": "journal_package_controller",
            "function_name": "materialize_journal_package",
            "args": [
                "publication",
                "materialize-journal-package",
                "--paper-root",
                str(tmp_path / "paper"),
                "--study-root",
                str(tmp_path / "study"),
                "--journal-slug",
                "rheumatology-international",
                "--publication-profile",
                "general_medical_journal",
            ],
            "result": {"status": "materialized", "journal_slug": "rheumatology-international"},
            "expected_call": {
                "paper_root": tmp_path / "paper",
                "study_root": tmp_path / "study",
                "journal_slug": "rheumatology-international",
                "publication_profile": "general_medical_journal",
                "confirmed_target": False,
            },
            "output_contains": ('"status": "materialized"',),
        },
        {
            "target_attr": "journal_package_controller",
            "function_name": "materialize_journal_package",
            "args": [
                "publication",
                "materialize-journal-package",
                "--paper-root",
                str(tmp_path / "paper"),
                "--study-root",
                str(tmp_path / "study"),
                "--journal-slug",
                "rheumatology-international",
                "--confirmed-target",
            ],
            "result": {"status": "materialized", "journal_slug": "rheumatology-international"},
            "expected_call": {
                "paper_root": tmp_path / "paper",
                "study_root": tmp_path / "study",
                "journal_slug": "rheumatology-international",
                "publication_profile": None,
                "confirmed_target": True,
            },
            "output_contains": ('"status": "materialized"',),
        },
        {
            "target_attr": "medical_publication_controller",
            "function_name": "run_controller",
            "args": [
                "publication",
                "surface",
                "--quest-root",
                str(tmp_path / "q001"),
                "--apply",
                "--daemon-url",
                "http://127.0.0.1:20999",
            ],
            "result": {"status": "clear", "blockers": []},
            "expected_call": {
                "quest_root": tmp_path / "q001",
                "apply": True,
                "daemon_url": "http://127.0.0.1:20999",
            },
            "output_contains": ('"status": "clear"',),
        },
        {
            "target_attr": "study_delivery_sync",
            "function_name": "sync_study_delivery",
            "args": ["study", "delivery-sync", "--paper-root", str(tmp_path / "paper"), "--stage", "finalize"],
            "result": {
                "stage": "finalize",
                "publication_profile": "general_medical_journal",
                "targets": {"manuscript_root": str(tmp_path / "study" / "manuscript")},
            },
            "expected_call": {
                "paper_root": tmp_path / "paper",
                "stage": "finalize",
                "publication_profile": "general_medical_journal",
                "promote_to_final": False,
            },
            "output_contains": ('"stage": "finalize"',),
        },
        {
            "target_attr": "overlay_installer",
            "function_name": "describe_medical_overlay",
            "args": ["runtime", "overlay-status", "--quest-root", str(tmp_path / "runtime" / "quests" / "q001")],
            "result": {
                "scope": "quest",
                "quest_root": str(tmp_path / "runtime" / "quests" / "q001"),
                "targets": [{"skill_id": "write"}],
            },
            "expected_call": {"quest_root": tmp_path / "runtime" / "quests" / "q001", "skill_ids": None},
            "output_contains": ('"skill_id": "write"',),
        },
        {
            "target_attr": "overlay_installer",
            "function_name": "install_medical_overlay",
            "args": ["runtime", "install-overlay"],
            "result": {"installed_count": 2, "targets": [{"skill_id": "write", "action": "installed"}]},
            "expected_call": {"quest_root": None, "skill_ids": None},
            "output_contains": ('"installed_count": 2',),
        },
        {
            "target_attr": "overlay_installer",
            "function_name": "reapply_medical_overlay",
            "args": ["runtime", "reapply-overlay", "--quest-root", str(tmp_path / "q001")],
            "result": {"installed_count": 2, "targets": [{"skill_id": "finalize", "action": "reapplied"}]},
            "expected_call": {"quest_root": tmp_path / "q001", "skill_ids": None},
            "output_contains": ('"action": "reapplied"',),
        },
        {
            "target_attr": "overlay_installer",
            "function_name": "describe_medical_overlay",
            "args": ["runtime", "overlay-status", "--profile", str(profile_path)],
            "result": {"targets": [{"skill_id": "scout"}], "scope": "global"},
            "expected_call": {
                "quest_root": Path("/Users/gaofeng/workspace/Yang/NF-PitNET"),
                "med_deepscientist_repo_root": None,
                "skill_ids": ("scout", "idea", "decision", "write", "finalize"),
                "policy_id": "high_plasticity_medical",
                "archetype_ids": (
                    "clinical_classifier",
                    "clinical_subtype_reconstruction",
                    "external_validation_model_update",
                    "gray_zone_triage",
                    "llm_agent_clinical_task",
                    "mechanistic_sidecar_extension",
                ),
                "default_submission_targets": (
                    {
                        "exporter_profile": "frontiers_family_harvard",
                        "primary": True,
                        "package_required": True,
                        "story_surface": "general_medical_journal",
                    },
                ),
                "default_publication_profile": "general_medical_journal",
                "default_citation_style": "AMA",
            },
            "default_call_values": {"med_deepscientist_repo_root": None},
            "output_contains": ('"skill_id": "scout"',),
        },
    )

    for case in cases:
        _run_cli_dispatch_case(cli, monkeypatch, capsys, **case)


def test_materialize_ai_medical_prose_review_command_uses_validator_surface(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    payload_file = tmp_path / "ai_reviewer_response.json"
    payload_file.write_text(
        json.dumps(
            {
                "overall_style_verdict": "revise",
                "summary": "The manuscript still reads like a method memo rather than a medical original article.",
                "section_level_diagnosis": {
                    "introduction": "The clinical problem and objective are identifiable.",
                    "methods": "Methods reproducibility needs fuller cohort and model detail.",
                    "results": "Results need numeric estimates and uncertainty before interpretive claims.",
                    "discussion": "Discussion should reduce defensive repetition and state principal findings.",
                },
                "representative_bad_sentences": ["The second research question is answered directly."],
                "representative_rewrites": [
                    {
                        "before": "The second research question is answered directly.",
                        "after": "External validation showed weaker discrimination in the US cohort than in the development cohort.",
                    }
                ],
                "route_back_recommendation": {
                    "route_target": "write",
                    "reason": "Rewrite the manuscript into a results-driven IMRAD article.",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def fake_status(**kwargs) -> dict:
        called["status_kwargs"] = kwargs
        return {
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "study_root": str(tmp_path / "studies" / "002-dm"),
        }

    def fake_materialize(**kwargs) -> dict:
        called.update(kwargs)
        return {
            "surface": "medical_prose_review",
            "artifact_path": str(tmp_path / "studies" / "002-dm" / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        }

    monkeypatch.setattr(cli.domain_status_projection, "progress_projection", fake_status)
    monkeypatch.setattr(cli, "materialize_ai_medical_prose_review_from_response", fake_materialize)

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-medical-prose-review",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm",
            "--payload-file",
            str(payload_file),
            "--request-ref",
            "artifacts/publication_eval/medical_prose_review_request.json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == tmp_path / "studies" / "002-dm"
    assert called["request_ref"] == "artifacts/publication_eval/medical_prose_review_request.json"
    assert called["response_payload"]["overall_style_verdict"] == "revise"
    assert called["response_payload"]["route_back_recommendation"]["route_target"] == "write"
    assert '"status": "materialized"' in captured.out
    assert '"assessment_owner": "ai_reviewer"' in captured.out


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
            "publication",
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


def test_bootstrap_command_ensures_profile_overlay(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    med_deepscientist_repo_root = tmp_path / "med-deepscientist"
    hermes_agent_repo_root = tmp_path / "hermes-agent"
    write_profile(
        profile_path,
        workspace_root=workspace_root,
        med_deepscientist_repo_root=med_deepscientist_repo_root,
        hermes_agent_repo_root=hermes_agent_repo_root,
    )
    calls: dict[str, object] = {}

    def fake_ensure(
        *,
        quest_root: Path | None = None,
        med_deepscientist_repo_root: Path | None = None,
        skill_ids: tuple[str, ...] | None = None,
        mode: str = "ensure_ready",
        policy_id: str | None = None,
        archetype_ids: tuple[str, ...] | None = None,
        default_submission_targets: tuple[dict[str, object], ...] | None = None,
        default_publication_profile: str | None = None,
        default_citation_style: str | None = None,
    ) -> dict:
        calls["ensure_quest_root"] = quest_root
        calls["ensure_med_deepscientist_repo_root"] = med_deepscientist_repo_root
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
                "recommendations": ["screen_and_materialize_valid_public_datasets_for_extension"],
            },
        }

    monkeypatch.setattr(
        cli.analysis_bundle_controller,
        "ensure_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(
        cli.workspace_python_environment_controller,
        "ensure_workspace_python_environment",
        lambda *, workspace_root: {"status": "ready", "ready": True, "workspace_root": str(workspace_root)},
    )
    monkeypatch.setattr(cli.overlay_installer, "ensure_medical_overlay", fake_ensure)
    monkeypatch.setattr(cli.data_asset_updates_controller, "refresh_data_assets", fake_refresh_data_assets)

    exit_code = cli.main(["workspace", "bootstrap", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls["ensure_skill_ids"] == ("scout", "idea", "decision", "write", "finalize")
    assert calls["ensure_quest_root"] == workspace_root
    assert calls["ensure_med_deepscientist_repo_root"] is None
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
            "exporter_profile": "frontiers_family_harvard",
            "primary": True,
            "package_required": True,
            "story_surface": "general_medical_journal",
        },
    )
    assert calls["ensure_default_publication_profile"] == "general_medical_journal"
    assert calls["ensure_default_citation_style"] == "AMA"
    assert calls["refresh_data_assets_workspace_root"] == workspace_root
    assert '"selected_action": "noop"' in captured.out
    assert '"supervision_bootstrap"' in captured.out
    assert '"manager": "opl"' in captured.out
    assert '"effect": "refs_only"' in captured.out
    assert '"trigger_now": false' in captured.out
    assert '"mas_runtime_scheduler_not_active_callable"' in captured.out
    assert '"write_install_proof": true' not in captured.out
    assert '"requested_write_install_proof": true' not in captured.out
    assert '"impact_report"' in captured.out
    assert '"startup_data_readiness"' in captured.out
    assert '"studies"' not in captured.out


def test_bootstrap_command_maintains_workspace_local_mas_stage_skills_without_home_global_writes(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    home = tmp_path / "home"
    write_profile(
        profile_path,
        workspace_root=workspace_root,
        hermes_agent_repo_root=tmp_path / "hermes-agent",
    )
    profile_text = profile_path.read_text(encoding="utf-8").replace(
        'hermes_home_root = "~/.hermes"',
        f'hermes_home_root = "{home / ".hermes"}"',
    )
    profile_path.write_text(profile_text, encoding="utf-8")

    monkeypatch.setattr(cli, "build_doctor_report", lambda profile: None, raising=False)
    monkeypatch.setattr(
        cli.analysis_bundle_controller,
        "ensure_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(
        cli.workspace_python_environment_controller,
        "ensure_workspace_python_environment",
        lambda *, workspace_root: {"status": "ready", "ready": True, "workspace_root": str(workspace_root)},
    )
    monkeypatch.setattr(
        cli.data_asset_updates_controller,
        "refresh_data_assets",
        lambda *, workspace_root: {"status": {"layout_ready": True}},
    )
    monkeypatch.setenv("HOME", str(home))

    exit_code = cli.main(["workspace", "bootstrap", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"scope": "quest"' in captured.out
    for skill_id in ("scout", "idea", "decision", "write", "finalize", "journal-resolution"):
        assert (
            workspace_root / ".codex" / "skills" / f"medical-research-{skill_id}" / "SKILL.md"
        ).exists()
    assert not any((workspace_root / ".codex" / "skills").glob("deepscientist-*"))
    assert not (home / ".codex" / "skills").exists()


def test_bootstrap_command_honors_status_only_overlay_mode(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(
        profile_path,
        workspace_root=tmp_path / "workspace",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        hermes_agent_repo_root=tmp_path / "hermes-agent",
    )
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
        "ensure_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(
        cli.workspace_python_environment_controller,
        "ensure_workspace_python_environment",
        lambda *, workspace_root: {"status": "ready", "ready": True, "workspace_root": str(workspace_root)},
    )
    monkeypatch.setattr(cli.overlay_installer, "ensure_medical_overlay", fake_ensure)
    monkeypatch.setattr(
        cli.data_asset_updates_controller,
        "refresh_data_assets",
        lambda *, workspace_root: {"status": {"layout_ready": True}},
    )

    exit_code = cli.main(["workspace", "bootstrap", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls["mode"] == "status_only"
    assert '"selected_action": "status_only"' in captured.out
