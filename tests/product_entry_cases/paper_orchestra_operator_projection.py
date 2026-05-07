from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_product_entry_surfaces_paper_orchestra_operator_projection_without_runtime_authority(
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
            workspace_supervision_contract={
                "status": "loaded",
                "loaded": True,
                "summary": "Hermes-hosted runtime supervision 已在线。",
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
            "summary": "Hermes-hosted runtime supervision 已在线。",
            "drift_reasons": [],
        },
    )
    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {"id": "quality_os_runtime", "status": "in_progress", "summary": "质量运行面已接入。"},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文写作 DAG 等待质量 gate。",
            "current_blockers": ["pre_draft_quality_gate"],
            "next_system_action": "先关闭 pre-draft quality gate。",
            "paper_orchestra_operator_projection": {
                "surface": "paper_orchestra_operator_projection",
                "read_model": "paper_orchestra_operator_projection_read_model",
                "status": "blocked",
                "current_dag_stage": {
                    "stage_id": "pre_draft_quality_gate",
                    "label": "pre-draft quality gate",
                    "owner": "MAS Quality OS",
                    "surface": "pre_draft_quality_runtime_state",
                },
                "parallel_sections": [
                    {"section_id": "introduction", "owner": "medical_writer", "status": "ready"},
                    {"section_id": "methods", "owner": "methods_writer", "status": "ready"},
                ],
                "parallel_section_count": 2,
                "blocking_gates": [
                    {
                        "gate_id": "pre_draft_quality_gate",
                        "label": "pre-draft quality gate",
                        "owner": "MAS Quality OS",
                        "surface": "pre_draft_quality_runtime_state",
                    }
                ],
                "blocking_gate_count": 1,
                "next_owner": {
                    "owner": "MAS Quality OS",
                    "surface": "pre_draft_quality_runtime_state",
                    "action": "close_pre_draft_quality_gate",
                },
                "pending_integration_surfaces": ["authoring_stage_graph"],
                "authority": {
                    "read_only": True,
                    "creates_runtime_truth": False,
                    "can_mutate_runtime": False,
                    "can_authorize_quality": False,
                    "can_authorize_submission": False,
                },
            },
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {"action_mode": "inspect_progress"},
            "needs_physician_decision": False,
            "needs_user_decision": False,
            "supervision": {
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "task_intake": {},
            "progress_freshness": {"status": "fresh"},
        },
    )

    cockpit = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    entry_status = module.build_product_entry_status(profile=profile, profile_ref=profile_ref)
    markdown = module.render_product_entry_status_markdown(entry_status)

    workspace_projection = cockpit["paper_orchestra_operator_projection"]
    assert workspace_projection["surface_kind"] == "workspace_paper_orchestra_operator_projection"
    assert workspace_projection["authority"] == "observability_only"
    assert workspace_projection["counts"] == {
        "study_count": 1,
        "projection_count": 1,
        "blocked_count": 1,
        "parallel_section_count": 2,
        "blocking_gate_count": 1,
    }
    assert workspace_projection["study_projections"][0]["next_owner"]["owner"] == "MAS Quality OS"
    assert entry_status["workspace_paper_orchestra_operator_projection"] == workspace_projection
    assert "论文写作 DAG" in markdown
    assert "可并行 section 2" in markdown
    assert "阻塞 gate 1" in markdown
    assert "下一责任方: MAS Quality OS" in markdown
