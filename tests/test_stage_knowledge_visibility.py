from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers import portfolio_memory
from med_autoscience.controllers import stage_knowledge_plane
from med_autoscience.controllers import stage_knowledge_visibility
from med_autoscience.controllers.progress_portal_parts import build_study_workbench_payload, render_study_workbench_sections


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _progress_payload(study_root: Path, study_id: str = "S1") -> dict[str, object]:
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "user_visible_projection": {
            "schema_version": 2,
            "writer_state": "live",
            "user_next": "wait",
            "reason": "stage_knowledge",
            "state_label": "Stage loop active",
            "state_summary": "Stage knowledge loop is visible.",
            "current_stage": "review",
            "paper_stage": "revision",
            "next_system_action": "Route review closeout.",
            "current_blockers": [],
            "needs_physician_decision": False,
        },
        "progress_freshness": {"status": "fresh"},
        "supervision": {"active_run_id": "run-S1"},
        "refs": {"study_root": str(study_root)},
    }


def _materialize_stage_loop_fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "S1"
    portfolio_memory.init_portfolio_memory(workspace_root=workspace_root)
    _write_json(study_root / "artifacts" / "reference_context" / "latest.json", {"status": "present"})
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {"status": "present", "failed_path_refs": ["analysis:sparse-endpoint"]},
    )
    _write_json(study_root / "paper" / "evidence_ledger.json", {"status": "present"})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"status": "present"})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"status": "present"})

    stage_knowledge_plane.materialize_stage_knowledge_packet(
        study_id="S1",
        stage="review",
        study_root=study_root,
        workspace_root=workspace_root,
    )
    closeout = stage_knowledge_plane.materialize_stage_memory_closeout_packet(
        study_id="S1",
        stage="review",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "review-closeout",
            "source_refs": ["review:matrix-1"],
            "citation_gaps": [{"write_id": "citation-gap-1", "gap": "Need guideline citation."}],
            "failed_paths": [{"write_id": "failed-path-1", "reason": "Review repair exhausted."}],
            "claim_boundary_decisions": [{"write_id": "claim-boundary-1", "decision": "downgrade"}],
            "reusable_lessons": [
                {
                    "write_id": "claim-specific",
                    "scope": "study_specific_claim",
                    "lesson": "Only true for this paper.",
                }
            ],
        },
    )
    stage_knowledge_plane.route_stage_memory_closeout(
        closeout_packet=closeout,
        study_root=study_root,
        workspace_root=workspace_root,
    )
    return workspace_root, study_root


def test_stage_knowledge_visibility_projects_entry_closeout_receipt_and_route_impact(tmp_path: Path) -> None:
    _, study_root = _materialize_stage_loop_fixture(tmp_path)

    visibility = stage_knowledge_visibility.build_stage_knowledge_visibility(study_root=study_root, study_id="S1")

    assert visibility["surface"] == "stage_knowledge_visibility"
    assert visibility["status"] == "partial"
    assert "artifacts/stage_knowledge/review/latest.json" in visibility["stage_knowledge_packet_refs"]
    assert visibility["closeout_receipt_refs"] == [
        "artifacts/stage_knowledge/memory_write_router_receipts/review-closeout.json"
    ]
    accepted_by_id = {item["write_id"]: item for item in visibility["accepted_writes"]}
    rejected_by_id = {item["write_id"]: item for item in visibility["rejected_writes"]}
    assert accepted_by_id["citation-gap-1"]["owner_target"] == "literature_provider"
    assert accepted_by_id["failed-path-1"]["owner_target"] == "mas_controller"
    assert accepted_by_id["claim-boundary-1"]["destination"] == "claim_boundary_controller_decision_request"
    assert rejected_by_id["claim-specific"]["reason"] == "study_specific_claim_not_workspace_memory"
    assert visibility["next_owner"] in {"mas_controller", "literature_provider"}
    assert visibility["authority_boundary"]["can_authorize_publication_quality"] is False


def test_progress_portal_workbench_renders_stage_knowledge_visibility(tmp_path: Path) -> None:
    _, study_root = _materialize_stage_loop_fixture(tmp_path)

    payload = build_study_workbench_payload(
        progress=_progress_payload(study_root),
        cockpit={},
        runtime={"study_id": "S1", "active_run_id": "run-S1"},
        package={"study_id": "S1"},
        study_id="S1",
    )
    html = render_study_workbench_sections(payload)

    stage_knowledge = payload["stage_knowledge"]
    assert stage_knowledge["status"] == "partial"
    assert any(tab["id"] == "stage_knowledge" for tab in payload["tabs"])
    assert "stage_knowledge:missing_stage_knowledge_packet:scout" in payload["conditions"]["missing"]
    assert "Stage Knowledge" in html
    assert "citation-gap-1" in html
    assert "claim-specific" in html
    assert "Route impact" in html
