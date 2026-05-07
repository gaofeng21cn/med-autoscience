from __future__ import annotations

import importlib


def test_submission_revision_operating_catalog_covers_platform_incident_guards() -> None:
    contract_module = importlib.import_module("med_autoscience.submission_revision_operating_contract")

    catalog = contract_module.build_submission_revision_operating_catalog()
    states = {item["state"] for item in catalog["supported_states"]}

    assert states == {
        "reviewer_revision",
        "manual_finishing",
        "manuscript_fast_lane",
        "bundle_only_closeout",
        "submission_package_refresh",
    }
    assert set(catalog["incident_guard_types"]) == {
        "duplicate_figure_legends",
        "study_specific_hardcoding_in_platform_code",
        "projection_as_authority",
        "stale_submission_source",
        "wrong_milestone_claim",
    }
    for item in catalog["supported_states"]:
        assert item["owner"] == "MedAutoScience controller"
        assert item["completion_claim_policy"]["projection_exists_equals_submission_ready"] is False
        assert item["completion_claim_policy"]["requires_ai_reviewer_backed_quality_record"] is True


def test_manuscript_fast_lane_intake_exposes_controller_visible_contract() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "entry_mode": "manuscript_fast_lane",
        "task_intent": (
            "Reviewer feedback asks for text-only manuscript revision during manual finishing. "
            "Use existing evidence only and revise controller-authorized canonical paper sources."
        ),
        "constraints": [
            "runtime must be inactive or foreground takeover must be allowed before editing",
            "edit only canonical paper/ manuscript text and structure",
            "all claims must come from existing evidence; do not run new analysis",
        ],
        "first_cycle_outputs": [
            "controller-visible intake and handoff, canonical paper patch, export/sync, QC and package consistency checks"
        ],
    }

    summary = module.summarize_task_intake(payload)
    override = module.build_task_intake_progress_override(payload)

    assert module.task_intake_requests_manuscript_fast_lane(payload) is True
    assert summary["manuscript_fast_lane"]["status"] == "requested"
    assert summary["manuscript_fast_lane"]["execution_owner"] == "codex_foreground_under_mas_controller"
    assert "runtime_inactive_or_takeover_allowed" in summary["manuscript_fast_lane"]["required_conditions"]
    assert summary["revision_intake"]["manuscript_fast_lane"]["status"] == "requested"
    assert override["current_required_action"] == "run_manuscript_fast_lane"
    assert override["quality_execution_lane"]["lane_id"] == "manuscript_fast_lane"
    assert override["manuscript_fast_lane"]["canonical_write_surface"] == "paper/"
