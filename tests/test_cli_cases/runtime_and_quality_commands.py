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
def test_backend_audit_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_run_backend_audit(profile, *, refresh: bool) -> dict:
        called["profile"] = profile
        called["refresh"] = refresh
        return {"decision": "audit_delta_available", "recommended_actions": ["review_backend_audit_delta_as_oracle_fixture"]}

    monkeypatch.setattr(cli.backend_audit, "run_backend_audit", fake_run_backend_audit)

    exit_code = cli.main(["doctor", "backend-audit", "--profile", str(profile_path), "--refresh"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].med_deepscientist_repo_root == Path("/Users/gaofeng/workspace/med-deepscientist")
    assert called["refresh"] is True
    assert '"decision": "audit_delta_available"' in captured.out


def test_doctor_group_help_surfaces_backend_audit_and_hides_legacy_names(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["doctor"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "backend-audit" in captured.out
    assert "backend-" + "upgrade" not in captured.out
    assert "med-deepscientist-" + "upgrade" not in captured.out


def test_removed_grouped_backend_audit_old_name_is_removed() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit, match=r"Grouped command requires a supported subcommand under `doctor`\.$"):
        cli.main(["doctor", "backend-" + "upgrade", "--profile", "/tmp/profile.toml"])


def test_removed_grouped_med_deepscientist_audit_old_name_is_removed() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit, match=r"Grouped command requires a supported subcommand under `doctor`\.$"):
        cli.main(["doctor", "med-deepscientist-" + "upgrade", "--profile", "/tmp/profile.toml"])


def test_removed_flat_backend_audit_old_name_is_removed(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    removed_command = "med-deepscientist-" + "upgrade-check"

    with pytest.raises(SystemExit) as excinfo:
        cli.main([removed_command, "--profile", "/tmp/profile.toml"])
    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "invalid choice" in captured.err
    assert removed_command in captured.err
def test_removed_grouped_ensure_runtime_command_is_removed(tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    with pytest.raises(SystemExit, match=r"Grouped command requires a supported subcommand under `study`\.$"):
        cli.main(["study", "ensure-runtime", "--profile", str(profile_path), "--study-id", "001-risk"])


def test_launch_study_command_dispatches_product_entry(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_launch_study(
        *,
        profile,
        profile_ref: Path,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        allow_stopped_relaunch: bool,
        explicit_user_wakeup: bool,
        force: bool,
    ) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["allow_stopped_relaunch"] = allow_stopped_relaunch
        called["explicit_user_wakeup"] = explicit_user_wakeup
        called["force"] = force
        return {"surface": "launch_study", "study_id": study_id, "quest_id": study_id}

    monkeypatch.setattr(cli.product_entry, "launch_study", fake_launch_study)
    monkeypatch.setattr(cli.product_entry, "render_launch_study_markdown", lambda payload: json.dumps(payload))

    exit_code = cli.main(
        [
            "launch-study",
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
    assert called["profile_ref"] == profile_path
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] == "full_research"
    assert called["allow_stopped_relaunch"] is True
    assert called["explicit_user_wakeup"] is False
    assert called["force"] is True
    assert '"surface": "launch_study"' in captured.out
def test_progress_projection_command_dispatches_stage_native_study_progress(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fail_old_progress_projection(**_: object) -> dict:
        raise AssertionError("progress-projection must not use legacy domain_status_projection")

    def fake_read_study_progress(
        *,
        profile,
        profile_ref: Path,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        sync_runtime_summary: bool,
        materialize_read_model_artifacts: bool,
    ) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["sync_runtime_summary"] = sync_runtime_summary
        called["materialize_read_model_artifacts"] = materialize_read_model_artifacts
        return {
            "schema_version": 1,
            "study_id": study_id,
            "quest_status": "running",
            "current_stage": "parked",
            "stage_kernel_projection": {
                "surface_kind": "stage_kernel_projection",
                "current_stage": "01-study_intake",
                "current_owner_delta": {
                    "surface_kind": "stage_run_current_owner_delta",
                    "owner": "MedAutoScience",
                    "action": "consume_closeout_and_emit_owner_receipt_or_typed_blocker",
                },
                "authority": {
                    "derived_projection": True,
                    "writes_mas_truth": False,
                    "claims_publication_ready": False,
                },
            },
        }

    monkeypatch.setattr(cli.domain_status_projection, "progress_projection", fail_old_progress_projection)
    monkeypatch.setattr(cli.study_progress, "read_study_progress", fake_read_study_progress)

    exit_code = cli.main(
        [
            "progress-projection",
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
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == profile_path
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert called["sync_runtime_summary"] is False
    assert called["materialize_read_model_artifacts"] is False
    payload = json.loads(captured.out)
    assert payload["quest_status"] == "running"
    assert payload["stage_kernel_projection"]["surface_kind"] == "stage_kernel_projection"
    assert payload["stage_kernel_projection"]["current_owner_delta"]["owner"] == "MedAutoScience"
    assert payload["stage_kernel_projection"]["authority"]["writes_mas_truth"] is False


def test_progress_projection_command_accepts_legacy_json_alias(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_read_study_progress(
        *,
        profile,
        profile_ref: Path,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        sync_runtime_summary: bool,
        materialize_read_model_artifacts: bool,
    ) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["sync_runtime_summary"] = sync_runtime_summary
        called["materialize_read_model_artifacts"] = materialize_read_model_artifacts
        return {"decision": "noop", "study_id": study_id, "quest_status": "running"}

    monkeypatch.setattr(cli.study_progress, "read_study_progress", fake_read_study_progress)

    exit_code = cli.main(
        [
            "progress-projection",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == profile_path
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert called["sync_runtime_summary"] is False
    assert called["materialize_read_model_artifacts"] is False
    assert json.loads(captured.out)["quest_status"] == "running"


def test_progress_projection_command_serializes_typed_controller_result(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")

    monkeypatch.setattr(
        cli.study_progress,
        "read_study_progress",
        lambda **kwargs: typed_surface.ProgressProjectionStatus.from_payload(
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
            "progress-projection",
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
def test_progress_projection_command_serializes_nested_path_values(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        cli.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "decision": "blocked",
            "study_id": kwargs["study_id"],
            "publication_supervisor_state": {
                "surface_refs": [
                    {
                        "path": tmp_path / "workspace" / "studies" / "001-risk" / "paper" / "draft.md",
                    }
                ],
            },
        },
    )

    exit_code = cli.main(
        [
            "progress-projection",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
        ]
    )
    captured = capsys.readouterr()

    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["publication_supervisor_state"]["surface_refs"][0]["path"].endswith(
        "/workspace/studies/001-risk/paper/draft.md"
    )


def test_quality_repair_batch_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
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


def test_gate_clearing_batch_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}
    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_root": str(tmp_path / "workspace" / "studies" / "001-risk"),
            "quest_id": "quest-001",
        },
    )

    def fake_run_gate_clearing_batch(
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

    monkeypatch.setattr(cli.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    exit_code = cli.main(
        [
            "study",
            "gate-clearing-batch",
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
            "opl_runtime_owner_handoff_summary": {},
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
def test_grouped_progress_projection_alias_dispatches_stage_native_study_progress(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fail_old_progress_projection(**_: object) -> dict:
        raise AssertionError("progress-projection alias must not use legacy domain_status_projection")

    def fake_read_study_progress(
        *,
        profile,
        profile_ref: Path,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        sync_runtime_summary: bool,
        materialize_read_model_artifacts: bool,
    ) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["sync_runtime_summary"] = sync_runtime_summary
        called["materialize_read_model_artifacts"] = materialize_read_model_artifacts
        return {"decision": "noop", "study_id": study_id, "quest_status": "running"}

    monkeypatch.setattr(cli.domain_status_projection, "progress_projection", fail_old_progress_projection)
    monkeypatch.setattr(cli.study_progress, "read_study_progress", fake_read_study_progress)

    exit_code = cli.main(
        [
            "study", "progress-projection",
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
    assert called["profile"].name == "nfpitnet"
    assert called["profile_ref"] == profile_path
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert called["sync_runtime_summary"] is False
    assert called["materialize_read_model_artifacts"] is False
    assert json.loads(captured.out)["quest_status"] == "running"
def test_retired_workspace_cockpit_group_command_fails_closed(tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    with pytest.raises(SystemExit, match="Grouped command requires a supported subcommand under `workspace`"):
        cli.main(["workspace", "cockpit", "--profile", str(profile_path), "--format", "json"])
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
                "opl_runtime_owner_handoff_required_count": 0,
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
@pytest.mark.parametrize(
    "argv",
    [
        ["product", "entry_status"],
        ["product", "preflight"],
        ["product", "start"],
        ["product", "skill-catalog"],
        ["product", "build-entry"],
    ],
)
def test_retired_product_group_commands_fail_closed(argv: list[str], tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    with pytest.raises(SystemExit, match="Grouped command requires a supported subcommand under `product`"):
        cli.main([*argv, "--profile", str(profile_path), "--format", "json"])


def test_retired_product_entry_status_name_fails_closed(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["product-" + "front" + "desk", "--profile", "profile.local.toml", "--format", "json"])
    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "invalid choice" in captured.err
    assert "product-entry-status" not in captured.err
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
        explicit_user_wakeup: bool,
        force: bool,
    ) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["allow_stopped_relaunch"] = allow_stopped_relaunch
        called["explicit_user_wakeup"] = explicit_user_wakeup
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
            "--explicit-user-wakeup",
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
    assert called["explicit_user_wakeup"] is True
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
        profile_ref: Path,
        study_id: str | None,
        study_root: Path | None,
        task_intent: str,
        task_intake_kind: str | None,
        entry_mode: str | None,
        journal_target: str | None,
        constraints: tuple[str, ...],
        evidence_boundary: tuple[str, ...],
        trusted_inputs: tuple[str, ...],
        reference_papers: tuple[str, ...],
        first_cycle_outputs: tuple[str, ...],
    ) -> dict:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["task_intent"] = task_intent
        called["task_intake_kind"] = task_intake_kind
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
    assert called["profile_ref"] == profile_path
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["task_intent"] == "持续推进到投稿态"
    assert called["task_intake_kind"] is None
    assert called["entry_mode"] == "full_research"
    assert called["journal_target"] == "JAMA"
    assert called["constraints"] == ("中文汇报",)
    assert called["evidence_boundary"] == ("外部验证必须补齐",)
    assert called["trusted_inputs"] == ("study.yaml",)
    assert called["reference_papers"] == ("PMID:123456",)
    assert called["first_cycle_outputs"] == ("study-progress",)
    assert json.loads(captured.out)["task_intent"] == "持续推进到投稿态"
