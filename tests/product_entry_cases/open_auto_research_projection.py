from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_product_entry_surfaces_workspace_open_auto_research_projection(
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
            "current_stage": {"id": "auto_research_projection", "status": "in_progress"},
            "current_program_phase": {
                "id": "auto_research_projection",
                "status": "in_progress",
                "summary": "Open Auto Research projection is being wired.",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "Open Auto Research surfaces are visible.",
            "current_blockers": [],
            "next_system_action": "Inspect Open Auto Research projection.",
            "open_auto_research_projection": {
                "surface": "open_auto_research_projection",
                "status": "needs_review",
                "summary": "3 ready, 1 needs review.",
                "counts": {"ready": 3, "blocked": 0, "needs_review": 1, "total": 4},
                "capabilities": {
                    "literature_evidence_graph": {"status": "ready"},
                    "evaluation_rubric_tree": {"status": "needs_review"},
                    "runtime_trajectory_proof": {"status": "ready"},
                    "candidate_path_graph": {"status": "ready"},
                },
                "actions": [
                    {
                        "action_id": "review_rubric_gaps",
                        "status": "needs_review",
                        "surface": "paperbench_style_hierarchical_rubric_tree",
                    }
                ],
                "authority": {"read_only": True, "can_authorize_publication_quality": False},
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
            "supervision": {"health_status": "live", "supervisor_tick_status": "fresh"},
            "task_intake": {},
            "progress_freshness": {"status": "fresh"},
        },
    )

    cockpit = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    frontdesk = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)
    markdown = module.render_product_frontdesk_markdown(frontdesk)

    workspace_projection = cockpit["open_auto_research_projection"]
    assert workspace_projection["surface_kind"] == "workspace_open_auto_research_projection"
    assert workspace_projection["authority"] == "observability_only"
    assert workspace_projection["counts"] == {
        "study_count": 1,
        "projection_count": 1,
        "ready": 3,
        "blocked": 0,
        "needs_review": 1,
    }
    assert workspace_projection["study_projections"][0]["actions"][0]["action_id"] == "review_rubric_gaps"
    assert frontdesk["workspace_open_auto_research_projection"] == workspace_projection
    assert "Open Auto Research" in markdown
    assert "review_rubric_gaps" in markdown
