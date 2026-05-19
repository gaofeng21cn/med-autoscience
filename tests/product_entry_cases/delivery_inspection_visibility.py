from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _delivery_inspection(study_id: str = "001-risk") -> dict[str, object]:
    return {
        "surface_kind": "study_delivery_inspection_projection",
        "study_id": study_id,
        "status": "layout_migration_pending_sync",
        "summary": "Delivery package is visible; layout migration still needs the next authorized sync.",
        "source_labels": {
            "submission_minimal": "controller-authorized source",
            "current_package": "human-facing mirror",
        },
        "layout_migration_pending_sync": True,
        "layout_migration_upgrade_note": "layout migration 会在下一次 authorized sync 升级",
        "authority": "observability_projection_only",
        "can_authorize_submission": False,
        "can_authorize_publication_quality": False,
        "can_dispatch_delivery_sync": False,
    }


def test_product_entry_surfaces_delivery_inspection_in_cockpit_and_entry_status(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: SimpleNamespace(
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            med_deepscientist_runtime_exists=True,
            medical_overlay_ready=True,
            external_runtime_contract={"ready": True},
            workspace_domain_route_contract={
                "status": "loaded",
                "loaded": True,
                "summary": "Runtime supervision online.",
                "drift_reasons": [],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect_workspace_supervision",
        lambda profile: {
            "manager": "launchd",
            "status": "loaded",
            "loaded": True,
            "job_exists": True,
            "summary": "Runtime supervision online.",
            "drift_reasons": [],
        },
    )
    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {"id": "delivery_visibility", "status": "in_progress"},
            "current_program_phase": {
                "id": "delivery_visibility",
                "status": "in_progress",
                "summary": "Delivery visibility projection is being wired.",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "Delivery inspection is visible.",
            "current_blockers": [],
            "next_system_action": "Inspect delivery mirrors.",
            "delivery_inspection": _delivery_inspection("001-risk"),
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {"action_mode": "inspect_progress"},
            "needs_physician_decision": False,
            "needs_user_decision": False,
            "supervision": {"health_status": "live", "supervisor_tick_status": "fresh"},
            "task_intake": {},
            "progress_freshness": {"status": "fresh"},
        },
    )

    cockpit = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    entry_status = module.build_product_entry_status(profile=profile, profile_ref=profile_ref)

    cockpit_state = cockpit["delivery_inspection_state"]
    assert cockpit_state["authority"] == "observability_projection_only"
    assert cockpit_state["counts"] == {
        "study_count": 1,
        "projected_count": 1,
        "attention_required": 1,
        "layout_migration_pending_sync": 1,
    }
    assert cockpit_state["studies"][0]["source_labels"]["submission_minimal"] == "controller-authorized source"
    assert cockpit["studies"][0]["delivery_inspection"]["layout_migration_upgrade_note"] == (
        "layout migration 会在下一次 authorized sync 升级"
    )
    assert "legacy_layout_upgrade_note" not in cockpit["studies"][0]["delivery_inspection"]

    entry_status_state = entry_status["workspace_delivery_inspection"]
    assert entry_status_state["counts"]["layout_migration_pending_sync"] == 1
    assert "legacy_layout_pending_sync" not in entry_status_state["counts"]
    assert entry_status_state["studies"][0]["source_labels"]["current_package"] == "human-facing mirror"

    cockpit_markdown = module.render_workspace_cockpit_markdown(cockpit)
    entry_status_markdown = module.render_product_entry_status_markdown(entry_status)
    for markdown in (cockpit_markdown, entry_status_markdown):
        assert markdown.strip()


def test_product_entry_exposes_publication_inspection_package_operator_surface(tmp_path: Path) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()
    manifest = module.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    entry_status = module.build_product_entry_status(profile=profile, profile_ref=profile_ref)

    profile_arg = str(profile_ref.resolve())
    expected_command = (
        "uv run python -m med_autoscience.cli publication export-inspection-package --profile "
        + profile_arg
        + " --study-id <study_id>"
    )

    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    inspection_action = cli_projection["export_inspection_package"]
    assert inspection_action["effect"] == "read_only"
    assert inspection_action["command"] == expected_command
    assert inspection_action["surface_kind"] == "publication_inspection_package_export"
    assert "human inspection only" in inspection_action["summary"]
    assert "not current_package" in inspection_action["summary"]
    assert "not submission_minimal authority" in inspection_action["summary"]
    mcp_projection = {
        item["name"]: item for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
    }
    assert mcp_projection["export_inspection_package"]["descriptor_only"] is True
    assert mcp_projection["export_inspection_package"]["public_runtime"] is False
    assert "export_inspection_package" not in {tool["name"] for tool in mcp_server.build_tool_manifest()}

    shell_surface = manifest["product_entry_shell"]["export_inspection_package"]
    assert shell_surface["command"] == expected_command
    assert shell_surface["surface_kind"] == "publication_inspection_package_export"
    assert shell_surface["purpose"] == inspection_action["summary"]
    assert shell_surface["authority_boundary"]["surface_authority"] == "human_inspection_only"
    assert shell_surface["authority_boundary"]["can_write_current_package"] is False
    assert shell_surface["authority_boundary"]["can_write_submission_minimal"] is False

    operator_action = manifest["operator_loop_actions"]["export_inspection_package"]
    assert operator_action["command"] == expected_command
    assert operator_action["surface_kind"] == "publication_inspection_package_export"
    assert operator_action["requires"] == ["study_id"]
    assert operator_action["authority"] == "human_inspection_only"
    assert operator_action["can_write_current_package"] is False
    assert operator_action["can_write_submission_minimal"] is False
    assert operator_action["can_authorize_publication_quality"] is False
    assert operator_action["can_authorize_submission_readiness"] is False

    quickstart_step = manifest["product_entry_quickstart"]["steps"][-1]
    assert quickstart_step["step_id"] == "export_inspection_package"
    assert quickstart_step["command"] == expected_command
    assert quickstart_step["authority"] == "human_inspection_only"
    assert quickstart_step["can_write_current_package"] is False
    assert quickstart_step["can_write_submission_minimal"] is False

    assert entry_status["entry_surfaces"]["export_inspection_package"]["command"] == expected_command
    assert entry_status["entry_surfaces"]["export_inspection_package"]["surface_kind"] == (
        "publication_inspection_package_export"
    )
    assert entry_status["operator_loop_actions"]["export_inspection_package"] == operator_action


def test_product_entry_counts_layout_migration_even_when_stale_status_is_primary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: SimpleNamespace(
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            med_deepscientist_runtime_exists=True,
            medical_overlay_ready=True,
            external_runtime_contract={"ready": True},
            workspace_domain_route_contract={},
        ),
    )
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: {})
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", lambda: {})
    stale_projection = _delivery_inspection("001-risk")
    stale_projection["status"] = "stale"
    stale_projection["summary"] = "delivery status: stale_source_changed"
    stale_projection["layout_migration_pending_sync"] = True
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_blockers": [],
            "delivery_inspection": stale_projection,
            "recommended_commands": [],
        },
    )

    cockpit = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    counts = cockpit["delivery_inspection_state"]["counts"]
    assert counts["attention_required"] == 1
    assert counts["layout_migration_pending_sync"] == 1
    assert "legacy_layout_pending_sync" not in counts
    assert cockpit["delivery_inspection_state"]["studies"][0]["status"] == "stale"


def test_product_entry_does_not_normalize_retired_delivery_projection_input(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: SimpleNamespace(
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            med_deepscientist_runtime_exists=True,
            medical_overlay_ready=True,
            external_runtime_contract={"ready": True},
            workspace_domain_route_contract={},
        ),
    )
    monkeypatch.setattr(module, "_inspect_workspace_supervision", lambda profile: {})
    monkeypatch.setattr(module.mainline_status, "read_mainline_status", lambda: {})
    legacy_projection = _delivery_inspection("001-risk")
    legacy_projection.pop("layout_migration_pending_sync", None)
    legacy_projection["status"] = "legacy_layout_pending_sync"
    legacy_projection["legacy_layout_pending_sync"] = True
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_blockers": [],
            "delivery_inspection": legacy_projection,
            "recommended_commands": [],
        },
    )

    with pytest.raises(ValueError, match="legacy_layout_pending_sync is retired"):
        module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
