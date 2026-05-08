from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


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
