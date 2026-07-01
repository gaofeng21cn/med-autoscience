from __future__ import annotations

from tests.test_publication_gate_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_build_gate_report_classifies_science_reporting_bundle_and_human_metadata_blockers(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_unmanaged_submission_surface=True,
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="blocked",
        medical_publication_surface_report={
            "blockers": [
                "methods_completeness_incomplete",
                "statistical_reporting_incomplete",
                "table_figure_claim_map_missing_or_incomplete",
                "clinical_actionability_incomplete",
            ],
            "structured_reporting_checklist": {
                "methods_completeness": {"status": "blocked", "missing_items": ["validation"]},
                "clinical_actionability": {"status": "blocked", "missing_items": ["treatment_gap"]},
            },
        },
        submission_checklist={
            "handoff_ready": True,
            "blocking_items": [
                {"id": "author_metadata"},
                {"id": "ethics_statement"},
                {"id": "funding_statement"},
                {"id": "conflict_of_interest_statement"},
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    assert "unmanaged_submission_surface_present" in report["blockers"]
    assert "submission_checklist_contains_unclassified_blocking_items" not in report["blockers"]
    science_reporting_blockers = report["blocker_taxonomy"]["science_reporting_blockers"]
    for blocker in [
        "medical_publication_surface_blocked",
        "methods_completeness_incomplete",
        "statistical_reporting_incomplete",
        "table_figure_claim_map_missing_or_incomplete",
        "clinical_actionability_incomplete",
    ]:
        assert blocker in science_reporting_blockers
    assert "unmanaged_submission_surface_present" in report["blocker_taxonomy"]["bundle_package_blockers"]
    assert report["blocker_taxonomy"]["human_metadata_admin_todos"] == [
        "author_metadata",
        "ethics_statement",
        "funding_statement",
        "conflict_of_interest_statement",
    ]
    assert report["non_scientific_handoff_gaps"] == [
        "author_metadata",
        "ethics_statement",
        "funding_statement",
        "conflict_of_interest_statement",
    ]
    assert report["publication_reporting_checklist"]["clinical_actionability"]["missing_items"] == ["treatment_gap"]
