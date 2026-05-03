from __future__ import annotations

from tests.product_entry_cases import shared as _shared
from tests.product_entry_cases import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from tests.product_entry_cases import frontdesk_focus_cases as _frontdesk_focus_cases


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_frontdesk_focus_cases)


def test_workspace_cockpit_projects_ai_first_cross_study_completion_runtime_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    write_study(profile.workspace_root, "002-ready")

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
            "current_stage": {
                "id": "quality_os_runtime",
                "status": "in_progress",
                "summary": "质量运行面已接入。",
            },
        },
    )

    def _fake_progress(**kwargs):
        study_id = kwargs["study_root"].name
        if study_id == "001-risk":
            return {
                "study_id": "001-risk",
                "current_stage": "publication_supervision",
                "current_blockers": ["AI-first completion 仍需处理。"],
                "next_system_action": "close_feedback_dispatch_and_artifact_proof",
                "ai_first_feedback_state": {
                    "surface": "ai_first_feedback_state",
                    "status": "attention_required",
                    "summary": "1 个 AI-first feedback 仍打开。",
                    "primary_action": {
                        "action_id": "repair-artifact-proof",
                        "summary": "刷新 artifact proof。",
                    },
                    "user_view": {
                        "next_action": "刷新 artifact proof。",
                        "human_review_required": True,
                    },
                    "counts": {"open_feedback_count": 1},
                },
                "dispatch_ledger": {
                    "surface": "ai_first_action_dispatch_ledger",
                    "dispatches": [
                        {"action_id": "repair-artifact-proof", "status": "open"},
                        {"action_id": "verify-package", "status": "closed"},
                    ],
                },
                "publication_eval": {
                    "assessment_provenance": {
                        "owner": "mechanical_projection",
                        "ai_reviewer_required": True,
                    }
                },
                "ai_first_default_entry_state": {
                    "artifact_proof": {
                        "surface": "artifact_runtime_proof",
                        "rebuild_status": "blocked",
                        "current_package_from_canonical_source": False,
                        "rebuild_pending": True,
                        "blockers": ["current_package_not_refreshed"],
                    },
                    "ai_reviewer_workflow": {"trace_complete": False},
                },
                "external_owner": "external-statistician",
                "needs_user_decision": True,
                "needs_physician_decision": False,
                "supervision": {"supervisor_tick_status": "fresh"},
                "progress_freshness": {"status": "fresh"},
            }
        return {
            "study_id": "002-ready",
            "current_stage": "bundle_stage_ready",
            "next_system_action": "continue_current_route",
            "ai_first_feedback_state": {
                "surface": "ai_first_feedback_state",
                "status": "closed",
                "user_view": {"next_action": "continue_current_route"},
                "counts": {"open_feedback_count": 0},
            },
            "dispatch_ledger": {
                "surface": "ai_first_action_dispatch_ledger",
                "dispatches": [{"action_id": "verify-package", "status": "closed"}],
            },
            "publication_eval": {
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "reviewer_operating_system": {"trace_id": "reviewer-os-002"},
            },
            "ai_first_default_entry_state": {
                "artifact_proof": {
                    "surface": "artifact_runtime_proof",
                    "rebuild_status": "current",
                    "current_package_from_canonical_source": True,
                    "rebuild_pending": False,
                    "blockers": [],
                },
                "ai_reviewer_workflow": {"trace_complete": True},
            },
            "external_owner": "none",
            "needs_user_decision": False,
            "needs_physician_decision": False,
            "supervision": {"supervisor_tick_status": "fresh"},
            "progress_freshness": {"status": "fresh"},
        }

    monkeypatch.setattr(module.study_progress, "read_study_progress", _fake_progress)

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    markdown = module.render_workspace_cockpit_markdown(payload)

    projection = payload["ai_first_cross_study_completion_projection"]
    risk = next(item for item in projection["studies"] if item["study_id"] == "001-risk")
    ready = next(item for item in projection["studies"] if item["study_id"] == "002-ready")

    assert projection["surface"] == "ai_first_cross_study_completion_projection"
    assert projection["read_model"] == "ai_first_cross_study_completion_read_model"
    assert projection["status"] == "attention_required"
    assert projection["user_view"]["study_count"] == 2
    assert projection["user_view"]["attention_required_count"] == 1
    assert projection["user_view"]["human_review_required_count"] == 1
    assert projection["maintainer_view"]["insufficient_observability_count"] == 0
    assert projection["authority_contract"]["can_mutate_runtime"] is False

    assert risk["status"] == "attention_required"
    assert risk["maintainer_view"]["feedback"]["open_feedback_count"] == 1
    assert risk["maintainer_view"]["dispatch"]["open_action_count"] == 1
    assert risk["maintainer_view"]["dispatch"]["total_action_count"] == 2
    assert risk["maintainer_view"]["ai_reviewer_authority"]["owner"] == "mechanical_projection"
    assert risk["maintainer_view"]["ai_reviewer_authority"]["reviewer_backed"] is False
    assert risk["maintainer_view"]["artifact_proof"]["rebuild_pending"] is True
    assert risk["maintainer_view"]["human_review"]["required"] is True
    assert risk["maintainer_view"]["external_owner"]["owner"] == "external-statistician"
    assert risk["authority_contract"]["can_authorize_quality"] is False

    assert ready["status"] == "on_track"
    assert ready["maintainer_view"]["dispatch"]["open_action_count"] == 0
    assert ready["maintainer_view"]["ai_reviewer_authority"]["reviewer_backed"] is True
    assert ready["maintainer_view"]["artifact_proof"]["current_package_from_canonical_source"] is True
    assert ready["maintainer_view"]["human_review"]["required"] is False

    assert "AI-first Cross-Study Completion" in markdown
    assert "`001-risk` completion: attention_required" in markdown
    assert "feedback: 1 open；dispatch: 1 open / 2 total" in markdown
    assert "AI reviewer: mechanical_projection (not backed)" in markdown
    assert "artifact proof: blocked；human gate: open；external owner: external-statistician" in markdown
    assert "`002-ready` completion: on_track" in markdown
    assert "AI reviewer: ai_reviewer (backed)" in markdown
    assert "artifact proof: current；human gate: closed；external owner: none" in markdown
