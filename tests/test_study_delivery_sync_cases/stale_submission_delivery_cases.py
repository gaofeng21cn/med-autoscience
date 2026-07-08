from __future__ import annotations

from tests.test_study_delivery_sync_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_materialize_submission_delivery_stale_notice_blocks_without_snapshot(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    result = module.materialize_submission_delivery_stale_notice(
        paper_root=paper_root,
        stale_reason="current_submission_source_missing",
        missing_source_paths=[str(paper_root / "submission_minimal" / "submission_manifest.json")],
    )

    assert result["status"] == "authority_route_blocked"
    assert result["authority_route_gate"]["action"] == "submission_notice_materialize"
    assert "authority_snapshot_missing" in result["authority_route_gate"]["blocking_reasons"]
    assert not (study_root / "manuscript" / "delivery_status.json").exists()


def test_materialize_submission_delivery_stale_notice_allows_open_snapshot(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    result = module.materialize_submission_delivery_stale_notice(
        paper_root=paper_root,
        stale_reason="current_submission_source_missing",
        route_context={
            "authority_snapshot": {
                "surface": "authority_snapshot",
                "dispatch_gate": {
                    "state": "open",
                    "dispatch_allowed": True,
                    "blocking_reasons": [],
                },
                "route_authorization": {
                    "authorized": True,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": True,
                    "runtime_recovery_allowed": True,
                },
                "authority_refs": {
                    "study_truth": {"epoch": "truth-1"},
                    "runtime_health": {"epoch": "runtime-1"},
                },
            },
        },
    )

    assert result["status"] == "stale_source_missing"
    assert result["authority_route_gate"]["authorized"] is True
    assert (study_root / "manuscript" / "delivery_status.json").exists()


def test_materialize_submission_delivery_stale_notice_blocks_projection_only_write(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    result = module.materialize_submission_delivery_stale_notice(
        paper_root=paper_root,
        stale_reason="current_submission_source_missing",
        route_context={"projection_only": True},
    )

    assert result["status"] == "authority_route_blocked"
    assert result["authority_route_gate"]["projection_only"] is True
    assert "projection_only_write_blocked" in result["authority_route_gate"]["blocking_reasons"]
    assert not (study_root / "manuscript" / "delivery_status.json").exists()
