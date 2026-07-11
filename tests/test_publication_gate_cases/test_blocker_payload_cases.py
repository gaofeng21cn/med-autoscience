from __future__ import annotations

import pytest

from tests.test_publication_gate_cases.shared import (
    importlib,
    make_quest,
    study_root_for_quest,
    write_journal_requirements_snapshot,
    write_primary_target,
)


def test_build_gate_report_canonicalizes_malformed_surface_blockers_without_crashing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="blocked",
        medical_publication_surface_report={
            "blockers": [
                {
                    "id": "table_figure_claim_map_missing_or_incomplete",
                    "source_path": "paper/figures/figure_catalog.json",
                    "figure_id": "F1",
                },
                ["ai_reviewer_required"],
                {"source_path": "paper/claim_evidence_map.json"},
                None,
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    science_reporting_blockers = report["blocker_taxonomy"]["science_reporting_blockers"]
    assert "table_figure_claim_map_missing_or_incomplete" in science_reporting_blockers
    assert "invalid_blocker_payload" in science_reporting_blockers
    invalid_refs = [
        item for item in report["blocking_artifact_refs"] if item["blocker"] == "invalid_blocker_payload"
    ]
    assert invalid_refs == [
        {
            "blocker": "invalid_blocker_payload",
            "artifact_path": "paper/claim_evidence_map.json",
            "artifact_role": "malformed_publication_surface_blocker",
            "stale_reason": "missing_blocker_id",
            "source_path": "paper/claim_evidence_map.json",
        }
    ]


@pytest.mark.parametrize(
    (
        "quest_kwargs",
        "journal_setup",
        "projection_field",
        "projection_item_field",
        "expected_projection",
        "expected_blocker",
    ),
    [
        pytest.param(
            {"include_submission_minimal": True},
            "target_only",
            "journal_requirements_status",
            None,
            "missing",
            "missing_journal_requirements",
            id="missing-journal-requirements",
        ),
        pytest.param(
            {"include_submission_minimal": True},
            "target_and_requirements",
            "journal_package_status",
            None,
            "missing",
            "missing_journal_package",
            id="missing-journal-package",
        ),
        pytest.param(
            {
                "include_submission_minimal": False,
                "include_main_result": False,
                "runtime_status": "waiting_for_user",
                "submission_checklist": {
                    "overall_status": "display_materialized_draft_bundle_not_submission_ready",
                    "blocking_items": [{"key": "full_manuscript_pageproof"}],
                    "handoff_ready": True,
                },
            },
            None,
            "non_scientific_handoff_gaps",
            None,
            ["full_manuscript_pageproof"],
            None,
            id="non-scientific-handoff-gap",
        ),
        pytest.param(
            {
                "include_submission_minimal": False,
                "include_main_result": False,
                "runtime_status": "waiting_for_user",
                "submission_checklist": {
                    "overall_status": "draft_bundle_with_unresolved_method_gap",
                    "blocking_items": [{"key": "methods_completeness"}],
                    "handoff_ready": True,
                },
            },
            None,
            "submission_checklist_unclassified_blocking_items",
            None,
            ["methods_completeness"],
            "submission_checklist_contains_unclassified_blocking_items",
            id="unclassified-submission-checklist-item",
        ),
        pytest.param(
            {
                "include_submission_minimal": True,
                "include_main_result": False,
                "runtime_status": "waiting_for_user",
                "include_current_medical_publication_surface_report": True,
                "medical_publication_surface_report": {
                    "status": "blocked",
                    "blockers": ["charter_expectation_closure_incomplete"],
                    "charter_expectation_closure_summary": {
                        "status": "blocked",
                        "blocking_items": [
                            {
                                "expectation_key": "minimum_sci_ready_evidence_package",
                                "expectation_text": "Archive the evidence package.",
                                "ledger_name": "evidence_ledger",
                                "ledger_path": "paper/evidence_ledger.json",
                                "contract_json_pointer": (
                                    "/paper_quality_contract/evidence_expectations/"
                                    "minimum_sci_ready_evidence_package"
                                ),
                                "closure_status": "blocked",
                                "recorded": True,
                                "record_count": 1,
                                "blocker": True,
                            }
                        ],
                    },
                },
            },
            None,
            "medical_publication_surface_expectation_gaps",
            "expectation_key",
            ["minimum_sci_ready_evidence_package"],
            "charter_expectation_closure_incomplete",
            id="medical-publication-surface-expectation-gap",
        ),
        pytest.param(
            {
                "include_submission_minimal": True,
                "include_main_result": False,
                "runtime_status": "waiting_for_user",
                "include_current_medical_publication_surface_report": True,
                "paper_line_state": {
                    "open_supplementary_count": 1,
                    "recommended_action": "complete_required_supplementary",
                    "blocking_reasons": ["required supplementary pending"],
                },
            },
            None,
            "paper_line_open_supplementary_count",
            None,
            1,
            "paper_line_required_supplementary_pending",
            id="required-supplementary-blocker",
        ),
    ],
)
def test_build_gate_report_preserves_unique_publication_gate_owners(
    tmp_path: Path,
    quest_kwargs: dict[str, object],
    journal_setup: str | None,
    projection_field: str,
    projection_item_field: str | None,
    expected_projection: object,
    expected_blocker: str | None,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, **quest_kwargs)
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    study_root = study_root_for_quest(quest_root)
    if journal_setup in {"target_only", "target_and_requirements"}:
        write_primary_target(paper_root)
    if journal_setup == "target_and_requirements":
        write_journal_requirements_snapshot(study_root)

    report = module.build_gate_report(module.build_gate_state(quest_root))
    projection = report[projection_field]
    if projection_item_field is not None:
        projection = [item[projection_item_field] for item in projection]

    assert projection == expected_projection
    if expected_blocker is None:
        assert report["blockers"] == []
    else:
        assert expected_blocker in report["blockers"]
