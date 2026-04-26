from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

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
            "data",
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

    exit_code = cli.main(["data", "external-research-status", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"prompt_file_count": 1' in captured.out
def test_backend_upgrade_check_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_run_upgrade_check(profile, *, refresh: bool) -> dict:
        called["profile"] = profile
        called["refresh"] = refresh
        return {"decision": "upgrade_available", "recommended_actions": ["pull_origin_main_then_reapply_medical_overlay"]}

    monkeypatch.setattr(cli.med_deepscientist_upgrade_check, "run_upgrade_check", fake_run_upgrade_check)

    exit_code = cli.main(["doctor", "backend-upgrade", "--profile", str(profile_path), "--refresh"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].med_deepscientist_repo_root == Path("/Users/gaofeng/workspace/med-deepscientist")
    assert called["refresh"] is True
    assert '"decision": "upgrade_available"' in captured.out
def test_doctor_group_help_surfaces_backend_upgrade_and_hides_legacy_name(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["doctor"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "backend-upgrade" in captured.out
    assert "med-deepscientist-upgrade" not in captured.out
def test_legacy_grouped_backend_upgrade_alias_is_removed() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit, match=r"Grouped command requires a supported subcommand under `doctor`\.$"):
        cli.main(["doctor", "med-deepscientist-upgrade", "--profile", "/tmp/profile.toml"])
def test_legacy_flat_backend_upgrade_alias_is_removed(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["med-deepscientist-upgrade-check", "--profile", "/tmp/profile.toml"])
    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "invalid choice" in captured.err
    assert "med-deepscientist-upgrade-check" in captured.err
def test_ensure_study_runtime_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_ensure(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        allow_stopped_relaunch: bool,
        force: bool,
        source: str,
    ) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["allow_stopped_relaunch"] = allow_stopped_relaunch
        called["force"] = force
        called["source"] = source
        return {"decision": "create_and_start", "study_id": study_id, "quest_id": study_id}

    monkeypatch.setattr(cli.study_runtime_router, "ensure_study_runtime", fake_ensure)

    exit_code = cli.main(
        [
            "study",
            "ensure-runtime",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--entry-mode",
            "full_research",
            "--allow-stopped-relaunch",
            "--force",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] == "full_research"
    assert called["allow_stopped_relaunch"] is True
    assert called["force"] is True
    assert called["source"] == "cli"
    assert '"decision": "create_and_start"' in captured.out
def test_ensure_study_runtime_command_serializes_typed_controller_result(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")

    monkeypatch.setattr(
        cli.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: typed_surface.StudyRuntimeStatus.from_payload(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "study_root": "/tmp/studies/001-risk",
                "entry_mode": "full_research",
                "execution": {"quest_id": "001-risk", "auto_resume": True},
                "quest_id": "001-risk",
                "quest_root": "/tmp/runtime/quests/001-risk",
                "quest_exists": True,
                "quest_status": "created",
                "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
                "runtime_binding_exists": True,
                "study_completion_contract": {},
                "decision": "create_and_start",
                "reason": "quest_missing",
            }
        ),
    )

    exit_code = cli.main(
        [
            "study",
            "ensure-runtime",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"decision": "create_and_start"' in captured.out
    assert '"study_id": "001-risk"' in captured.out
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
def test_study_runtime_status_command_serializes_typed_controller_result(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: typed_surface.StudyRuntimeStatus.from_payload(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "study_root": "/tmp/studies/001-risk",
                "entry_mode": "full_research",
                "execution": {"quest_id": "001-risk", "auto_resume": True},
                "quest_id": "001-risk",
                "quest_root": "/tmp/runtime/quests/001-risk",
                "quest_exists": True,
                "quest_status": "created",
                "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
                "runtime_binding_exists": True,
                "study_completion_contract": {},
                "decision": "noop",
                "reason": "quest_missing",
            }
        ),
    )

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
    assert '"decision": "noop"' in captured.out
    assert '"study_id": "001-risk"' in captured.out
def test_quality_repair_batch_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "study_id": kwargs["study_id"],
            "study_root": str(tmp_path / "workspace" / "studies" / "001-risk"),
            "quest_id": "quest-001",
        },
    )

    def fake_run_quality_repair_batch(
        *,
        profile,
        study_id: str,
        study_root: Path,
        quest_id: str,
        source: str,
    ) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["quest_id"] = quest_id
        called["source"] = source
        return {"ok": True, "status": "executed", "quest_id": quest_id}

    monkeypatch.setattr(cli.quality_repair_batch, "run_quality_repair_batch", fake_run_quality_repair_batch)

    exit_code = cli.main(
        [
            "study",
            "quality-repair-batch",
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
    assert called["study_root"] == tmp_path / "workspace" / "studies" / "001-risk"
    assert called["quest_id"] == "quest-001"
    assert called["source"] == "cli"
    assert json.loads(captured.out)["status"] == "executed"
def test_study_profile_cycle_command_dispatches_profiler(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    def fake_profile_study_cycle(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        since: str | None,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["since"] = since
        return {
            "study_id": study_id,
            "study_root": str(study_root or profile.studies_root / str(study_id)),
            "quest_id": "quest-001",
            "quest_root": str(profile.runtime_root / "quest-001"),
            "profiling_window": {"since": since},
            "category_windows": {},
            "runtime_transition_summary": {},
            "controller_decision_fingerprints": {"top_repeats": []},
            "gate_blocker_summary": {"current_blockers": []},
            "package_currentness": {"status": "fresh"},
            "bottlenecks": [],
            "optimization_recommendations": [],
        }

    monkeypatch.setattr(cli.study_cycle_profiler, "profile_study_cycle", fake_profile_study_cycle)

    exit_code = cli.main(
        [
            "study",
            "profile-cycle",
            "--profile",
            str(profile_path),
            "--study-root",
            str(study_root),
            "--since",
            "2026-04-25T00:00:00Z",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] is None
    assert called["study_root"] == study_root
    assert called["since"] == "2026-04-25T00:00:00Z"
    assert json.loads(captured.out)["profiling_window"]["since"] == "2026-04-25T00:00:00Z"
def test_study_group_help_surfaces_profile_cycle(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["study"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "profile-cycle" in captured.out
def test_legacy_grouped_study_runtime_status_alias_is_removed() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit, match=r"Grouped command requires a supported subcommand under `study`\.$"):
        cli.main(["study", "runtime-status", "--profile", "/tmp/profile.toml", "--study-id", "001-risk"])
def test_workspace_cockpit_command_dispatches_product_entry_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_read_workspace_cockpit(*, profile, profile_ref) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        return {"workspace_status": "ready", "workspace_alerts": [], "studies": []}

    monkeypatch.setattr(cli.product_entry, "read_workspace_cockpit", fake_read_workspace_cockpit)

    exit_code = cli.main(["workspace", "cockpit", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == Path(profile_path)
    assert json.loads(captured.out)["workspace_status"] == "ready"
def test_workspace_profile_cycles_command_dispatches_profiler(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_profile_workspace_cycles(*, profile, since: str | None) -> dict[str, object]:
        called["profile"] = profile
        called["since"] = since
        return {
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "study_count": 0,
            "workspace_totals": {
                "repeated_controller_dispatch_count": 0,
                "runtime_recovery_churn_count": 0,
                "runtime_flapping_transition_count": 0,
                "package_stale_seconds": 0,
            },
            "studies": [],
        }

    monkeypatch.setattr(cli.study_cycle_profiler, "profile_workspace_cycles", fake_profile_workspace_cycles)

    exit_code = cli.main(
        [
            "workspace",
            "profile-cycles",
            "--profile",
            str(profile_path),
            "--since",
            "2026-04-25T00:00:00Z",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["since"] == "2026-04-25T00:00:00Z"
    assert json.loads(captured.out)["profile_name"] == "nfpitnet"
def test_product_frontdesk_command_dispatches_product_entry_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_build_product_frontdesk(*, profile, profile_ref) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        return {"surface_kind": "product_frontdesk", "summary": {"frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk"}}

    monkeypatch.setattr(cli.product_entry, "build_product_frontdesk", fake_build_product_frontdesk)

    exit_code = cli.main(["product", "frontdesk", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == Path(profile_path)
    assert json.loads(captured.out)["surface_kind"] == "product_frontdesk"
def test_product_preflight_command_dispatches_product_entry_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_build_product_entry_preflight(*, profile, profile_ref) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        return {"surface_kind": "product_entry_preflight", "ready_to_try_now": True}

    monkeypatch.setattr(cli.product_entry, "build_product_entry_preflight", fake_build_product_entry_preflight)

    exit_code = cli.main(["product", "preflight", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == Path(profile_path)
    assert json.loads(captured.out)["surface_kind"] == "product_entry_preflight"
def test_product_start_command_dispatches_product_entry_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_build_product_entry_start(*, profile, profile_ref) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        return {"surface_kind": "product_entry_start", "recommended_mode_id": "open_frontdesk"}

    monkeypatch.setattr(cli.product_entry, "build_product_entry_start", fake_build_product_entry_start)

    exit_code = cli.main(["product", "start", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == Path(profile_path)
    assert json.loads(captured.out)["surface_kind"] == "product_entry_start"
def test_product_skill_catalog_command_dispatches_product_entry_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_build_skill_catalog(*, profile, profile_ref) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        return {"surface_kind": "skill_catalog", "skills": [{"skill_id": "mas_workspace_cockpit"}]}

    monkeypatch.setattr(cli.product_entry, "build_skill_catalog", fake_build_skill_catalog)

    exit_code = cli.main(["product", "skill-catalog", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == Path(profile_path)
    assert json.loads(captured.out)["surface_kind"] == "skill_catalog"
def test_mainline_status_command_dispatches_controller(monkeypatch, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_read_mainline_status() -> dict:
        called["read"] = True
        return {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {"id": "f4_blocker_closeout", "status": "in_progress"},
        }

    monkeypatch.setattr(cli.mainline_status, "read_mainline_status", fake_read_mainline_status)

    exit_code = cli.main(["doctor", "mainline-status", "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["read"] is True
    assert json.loads(captured.out)["current_stage"]["id"] == "f4_blocker_closeout"
def test_mainline_phase_command_dispatches_controller(monkeypatch, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_read_mainline_phase_status(selector: str) -> dict:
        called["selector"] = selector
        return {
            "program_id": "research-foundry-medical-mainline",
            "phase": {"id": "phase_2_user_product_loop", "status": "pending"},
        }

    monkeypatch.setattr(cli.mainline_status, "read_mainline_phase_status", fake_read_mainline_phase_status)

    exit_code = cli.main(["doctor", "mainline-phase", "--phase", "next", "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["selector"] == "next"
    assert json.loads(captured.out)["phase"]["id"] == "phase_2_user_product_loop"
def test_launch_study_command_dispatches_product_entry_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_launch(
        *,
        profile,
        profile_ref,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        allow_stopped_relaunch: bool,
        force: bool,
    ) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["allow_stopped_relaunch"] = allow_stopped_relaunch
        called["force"] = force
        return {
            "study_id": study_id,
            "runtime_status": {"decision": "resume"},
            "progress": {"current_stage": "publication_supervision"},
            "commands": {},
        }

    monkeypatch.setattr(cli.product_entry, "launch_study", fake_launch)

    exit_code = cli.main(
        [
            "study",
            "launch",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--entry-mode",
            "full_research",
            "--allow-stopped-relaunch",
            "--force",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == Path(profile_path)
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] == "full_research"
    assert called["allow_stopped_relaunch"] is True
    assert called["force"] is True
    assert json.loads(captured.out)["runtime_status"]["decision"] == "resume"
def test_submit_study_task_command_dispatches_product_entry_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_submit(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        task_intent: str,
        entry_mode: str | None,
        journal_target: str | None,
        constraints: tuple[str, ...],
        evidence_boundary: tuple[str, ...],
        trusted_inputs: tuple[str, ...],
        reference_papers: tuple[str, ...],
        first_cycle_outputs: tuple[str, ...],
    ) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["task_intent"] = task_intent
        called["entry_mode"] = entry_mode
        called["journal_target"] = journal_target
        called["constraints"] = constraints
        called["evidence_boundary"] = evidence_boundary
        called["trusted_inputs"] = trusted_inputs
        called["reference_papers"] = reference_papers
        called["first_cycle_outputs"] = first_cycle_outputs
        return {
            "study_id": study_id,
            "task_intent": task_intent,
            "artifacts": {"latest_json": "/tmp/latest.json", "latest_markdown": "/tmp/latest.md"},
        }

    monkeypatch.setattr(cli.product_entry, "submit_study_task", fake_submit)

    exit_code = cli.main(
        [
            "study",
            "submit-task",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--task-intent",
            "持续推进到投稿态",
            "--entry-mode",
            "full_research",
            "--journal-target",
            "JAMA",
            "--constraint",
            "中文汇报",
            "--evidence-boundary",
            "外部验证必须补齐",
            "--trusted-input",
            "study.yaml",
            "--reference-paper",
            "PMID:123456",
            "--first-cycle-output",
            "study-progress",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["task_intent"] == "持续推进到投稿态"
    assert called["entry_mode"] == "full_research"
    assert called["journal_target"] == "JAMA"
    assert called["constraints"] == ("中文汇报",)
    assert called["evidence_boundary"] == ("外部验证必须补齐",)
    assert called["trusted_inputs"] == ("study.yaml",)
    assert called["reference_papers"] == ("PMID:123456",)
    assert called["first_cycle_outputs"] == ("study-progress",)
    assert json.loads(captured.out)["task_intent"] == "持续推进到投稿态"
def test_build_product_entry_command_dispatches_product_entry_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_build(
        *,
        profile,
        profile_ref,
        study_id: str | None,
        study_root: Path | None,
        direct_entry_mode: str,
    ) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["direct_entry_mode"] = direct_entry_mode
        return {
            "target_domain_id": "med-autoscience",
            "entry_mode": direct_entry_mode,
            "task_intent": "持续推进到投稿态",
        }

    monkeypatch.setattr(cli.product_entry, "build_product_entry", fake_build)

    exit_code = cli.main(
        [
            "product",
            "build-entry",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--entry-mode",
            "opl-handoff",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == Path(profile_path)
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["direct_entry_mode"] == "opl-handoff"
    assert json.loads(captured.out)["entry_mode"] == "opl-handoff"
def test_init_data_assets_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"private": {"release_count": 1}, "public": {"dataset_count": 0}}

    monkeypatch.setattr(cli.data_assets, "init_data_assets", fake_init)

    exit_code = cli.main(["data", "init-assets", "--workspace-root", str(tmp_path / "workspace")])
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
        hermes_agent_repo_root: Path | None,
        hermes_home_root: Path | None,
        initialize_git: bool,
    ) -> dict:
        called["workspace_root"] = workspace_root
        called["workspace_name"] = workspace_name
        called["dry_run"] = dry_run
        called["force"] = force
        called["default_publication_profile"] = default_publication_profile
        called["default_citation_style"] = default_citation_style
        called["hermes_agent_repo_root"] = hermes_agent_repo_root
        called["hermes_home_root"] = hermes_home_root
        called["initialize_git"] = initialize_git
        return {
            "workspace_root": str(workspace_root),
            "workspace_name": workspace_name,
            "dry_run": dry_run,
            "force": force,
            "initialize_git": initialize_git,
        }

    monkeypatch.setattr(cli.workspace_init_controller, "init_workspace", fake_init_workspace)

    exit_code = cli.main(
        [
            "workspace",
            "init",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--workspace-name",
            "diabetes",
            "--dry-run",
            "--force",
            "--hermes-agent-repo-root",
            str(tmp_path / "_external" / "hermes-agent"),
            "--hermes-home-root",
            str(tmp_path / ".hermes"),
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
    assert called["hermes_agent_repo_root"] == tmp_path / "_external" / "hermes-agent"
    assert called["hermes_home_root"] == tmp_path / ".hermes"
    assert called["initialize_git"] is True
    assert '"workspace_name": "diabetes"' in captured.out
    assert '"initialize_git": true' in captured.out

    exit_code = cli.main(
        [
            "workspace",
            "init",
            "--workspace-root",
            str(tmp_path / "workspace-no-git"),
            "--workspace-name",
            "diabetes",
            "--no-git",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace-no-git"
    assert called["initialize_git"] is False
    assert '"initialize_git": false' in captured.out
def test_data_assets_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"layout_ready": True, "private": {"release_count": 2}}

    monkeypatch.setattr(cli.data_assets, "data_assets_status", fake_status)

    exit_code = cli.main(["data", "assets-status", "--workspace-root", str(tmp_path / "workspace")])
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

    exit_code = cli.main(["data", "assess-asset-impact", "--workspace-root", str(tmp_path / "workspace")])
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
            "data",
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

    exit_code = cli.main(["data", "validate-public-registry", "--workspace-root", str(tmp_path / "workspace")])
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
            "data",
            "apply-asset-update",
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
