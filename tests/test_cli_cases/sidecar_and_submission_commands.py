from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


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


def test_delivery_inspect_command_dispatches_read_only_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_inspect(**kwargs) -> dict:
        called.update(kwargs)
        return {
            "surface": "delivery_inspector",
            "mutation_policy": {"read_only": True, "writes_package": False},
            "freshness": {"verdict": "current"},
        }

    monkeypatch.setattr(cli.delivery_inspector, "inspect_study_delivery", fake_inspect)

    exit_code = cli.main(
        [
            "publication",
            "delivery-inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["profile_ref"] == profile_path
    payload = json.loads(captured.out)
    assert payload["mutation_policy"]["read_only"] is True
    assert payload["freshness"]["verdict"] == "current"
def test_startup_data_readiness_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_readiness(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"status": "clear", "study_summary": {"study_count": 2}}

    monkeypatch.setattr(cli.startup_data_readiness_controller, "startup_data_readiness", fake_readiness)

    exit_code = cli.main(["data", "startup-readiness", "--workspace-root", str(tmp_path / "workspace")])
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

    exit_code = cli.main(["data", "asset-gate", "--quest-root", str(tmp_path / "q001"), "--apply"])
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
            "data",
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
            "publication",
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
            "publication",
            "resolve-targets",
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
            "study",
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

    exit_code = cli.main(["publication", "gate", "--quest-root", str(tmp_path / "q001"), "--apply"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == tmp_path / "q001"
    assert called["apply"] is True
    assert '"status": "blocked"' in captured.out
def test_materialize_journal_package_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_materialize(
        *,
        paper_root: Path,
        study_root: Path,
        journal_slug: str,
        publication_profile: str | None = None,
        confirmed_target: bool = False,
    ) -> dict[str, object]:
        called["paper_root"] = paper_root
        called["study_root"] = study_root
        called["journal_slug"] = journal_slug
        called["publication_profile"] = publication_profile
        called["confirmed_target"] = confirmed_target
        return {"status": "materialized", "journal_slug": journal_slug}

    monkeypatch.setattr(cli.journal_package_controller, "materialize_journal_package", fake_materialize)

    exit_code = cli.main(
        [
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
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["paper_root"] == tmp_path / "paper"
    assert called["study_root"] == tmp_path / "study"
    assert called["journal_slug"] == "rheumatology-international"
    assert called["publication_profile"] == "general_medical_journal"
    assert called["confirmed_target"] is False
    assert '"status": "materialized"' in captured.out


def test_materialize_journal_package_command_accepts_confirmed_target_flag(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_materialize(
        *,
        paper_root: Path,
        study_root: Path,
        journal_slug: str,
        publication_profile: str | None = None,
        confirmed_target: bool = False,
    ) -> dict[str, object]:
        called["confirmed_target"] = confirmed_target
        return {"status": "materialized", "journal_slug": journal_slug}

    monkeypatch.setattr(cli.journal_package_controller, "materialize_journal_package", fake_materialize)

    exit_code = cli.main(
        [
            "publication",
            "materialize-journal-package",
            "--paper-root",
            str(tmp_path / "paper"),
            "--study-root",
            str(tmp_path / "study"),
            "--journal-slug",
            "rheumatology-international",
            "--confirmed-target",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["confirmed_target"] is True
    assert '"status": "materialized"' in captured.out


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
            "publication",
            "surface",
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

    monkeypatch.setattr(cli.study_runtime_router, "study_runtime_status", fake_status)
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
def test_sync_study_delivery_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict:
        called["paper_root"] = paper_root
        called["stage"] = stage
        called["publication_profile"] = publication_profile
        called["promote_to_final"] = promote_to_final
        return {
            "stage": stage,
            "publication_profile": publication_profile,
            "targets": {"manuscript_root": str(tmp_path / "study" / "manuscript")},
        }

    monkeypatch.setattr(cli.study_delivery_sync, "sync_study_delivery", fake_sync)

    exit_code = cli.main(
        [
            "study",
            "delivery-sync",
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
    assert called["promote_to_final"] is False
    assert '"stage": "finalize"' in captured.out
def test_overlay_status_command_dispatches_installer(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, quest_root: Path | None = None, skill_ids: tuple[str, ...] | None = None) -> dict:
        called["quest_root"] = quest_root
        called["skill_ids"] = skill_ids
        return {"scope": "quest", "quest_root": str(quest_root), "targets": [{"skill_id": "write"}]}

    monkeypatch.setattr(cli.overlay_installer, "describe_medical_overlay", fake_status)

    exit_code = cli.main(["runtime", "overlay-status", "--quest-root", str(tmp_path / "runtime" / "quests" / "q001")])
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

    exit_code = cli.main(["runtime", "install-overlay"])
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

    exit_code = cli.main(["runtime", "reapply-overlay", "--quest-root", str(tmp_path / "q001")])
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
        med_deepscientist_repo_root: Path | None = None,
        skill_ids: tuple[str, ...] | None = None,
        policy_id: str | None = None,
        archetype_ids: tuple[str, ...] | None = None,
        default_submission_targets: tuple[dict[str, object], ...] | None = None,
        default_publication_profile: str | None = None,
        default_citation_style: str | None = None,
    ) -> dict:
        called["quest_root"] = quest_root
        called["med_deepscientist_repo_root"] = med_deepscientist_repo_root
        called["skill_ids"] = skill_ids
        called["policy_id"] = policy_id
        called["archetype_ids"] = archetype_ids
        called["default_submission_targets"] = default_submission_targets
        called["default_publication_profile"] = default_publication_profile
        called["default_citation_style"] = default_citation_style
        return {"targets": [{"skill_id": "scout"}], "scope": "global"}

    monkeypatch.setattr(cli.overlay_installer, "describe_medical_overlay", fake_status)

    exit_code = cli.main(["runtime", "overlay-status", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["quest_root"] == Path("/Users/gaofeng/workspace/Yang/NF-PitNET")
    assert called["med_deepscientist_repo_root"] is None
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
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(cli.overlay_installer, "ensure_medical_overlay", fake_ensure)
    monkeypatch.setattr(cli.data_asset_updates_controller, "refresh_data_assets", fake_refresh_data_assets)
    monkeypatch.setattr(
        cli.domain_slo_scheduler_projection,
        "ensure_supervision",
        lambda **kwargs: {
            "surface_kind": "workspace_runtime_supervision_replacement_result",
            "action": "delegated_to_opl_provider_scheduler",
            "manager": kwargs["manager"],
            "trigger_now": kwargs["trigger_now"],
            "write_install_proof": False,
            "requested_write_install_proof": kwargs["write_install_proof"],
        },
    )

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
            "publication_profile": "frontiers_family_harvard",
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
    assert '"trigger_now": false' in captured.out
    assert '"write_install_proof": true' not in captured.out
    assert '"requested_write_install_proof": true' in captured.out
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
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(
        cli.data_asset_updates_controller,
        "refresh_data_assets",
        lambda *, workspace_root: {"status": {"layout_ready": True}},
    )
    monkeypatch.setattr(
        cli.domain_slo_scheduler_projection,
        "ensure_supervision",
        lambda **kwargs: {"surface_kind": "workspace_runtime_supervision_install_result", "action": "installed"},
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
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(cli.overlay_installer, "ensure_medical_overlay", fake_ensure)
    monkeypatch.setattr(
        cli.data_asset_updates_controller,
        "refresh_data_assets",
        lambda *, workspace_root: {"status": {"layout_ready": True}},
    )
    monkeypatch.setattr(
        cli.domain_slo_scheduler_projection,
        "ensure_supervision",
        lambda **kwargs: {"surface_kind": "workspace_runtime_supervision_install_result", "action": "installed"},
    )

    exit_code = cli.main(["workspace", "bootstrap", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls["mode"] == "status_only"
    assert '"selected_action": "status_only"' in captured.out
