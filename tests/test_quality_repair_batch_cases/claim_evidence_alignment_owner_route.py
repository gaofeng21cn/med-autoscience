from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch_cases.upstream_paper_owner_surface import (
    _paper_write_supervisor_route_context,
    _write_blocked_publication_eval,
    _write_json,
    _write_quality_summary,
)


def test_run_quality_repair_batch_honors_claim_evidence_alignment_owner_route(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm-china-us-mortality-attribution",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="mortality_attribution",
    )
    quest_id = "quest-002"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nCurrent manuscript surface.\n", encoding="utf-8")
    _write_claim_alignment_fixture(paper_root)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_quality_summary(study_root)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": publication_eval_payload["eval_id"],
            "status": "handoff_ready",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
            },
        },
    )
    route_context = _claim_evidence_alignment_route_context(
        publication_eval_id=publication_eval_payload["eval_id"]
    )

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["claim_evidence_alignment_required"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["claim_evidence_alignment_required"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::claim-alignment",
        },
    )
    seen: dict[str, Any] = {}
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("gate_context", kwargs["authority_route_context"]),
            {
                "ok": True,
                "status": "executed",
                "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
                "selected_publication_work_unit": {"unit_id": "manuscript_story_repair"},
                "gate_replay": {"status": "blocked", "blockers": ["claim_evidence_alignment_required"]},
                "unit_results": [],
            },
        )[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=route_context,
    )

    assert result["status"] == "executed"
    assert "writer_worker_handoff" not in result
    assert seen["gate_context"]["controller_route_context"]["work_unit_id"] == "claim_evidence_alignment_repair"
    ledger = json.loads((paper_root / "evidence_ledger.json").read_text(encoding="utf-8"))
    assert ledger["claims"][0]["evidence"][0]["evidence_id"] == "C1_main_result_observed_gap"
    alignment = result["gate_clearing_batch"]["unit_results"][0]["result"]["claim_evidence_alignment"]
    assert alignment["status"] == "ready"
    assert result["repair_execution_evidence"]["evidence_ledger_update_done"] is True


def _write_claim_alignment_fixture(paper_root: Path) -> None:
    _write_json(
        paper_root / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The validation cohort has a bounded observed mortality contrast.",
                    "status": "supported_with_limitations",
                    "paper_role": "main_text",
                    "display_bindings": ["T1"],
                    "sections": ["Results"],
                    "evidence_items": [
                        {
                            "item_id": "C1_main_result_observed_gap",
                            "support_level": "primary",
                            "source_paths": ["paper/cohort_flow.json"],
                            "summary": "Claim-map item id is the current canonical evidence id.",
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The validation cohort has a bounded observed mortality contrast.",
                    "status": "supported_with_limitations",
                    "submission_scope": "main_text",
                    "evidence": [
                        {
                            "evidence_id": "legacy_observed_gap",
                            "kind": "result",
                            "source_paths": ["paper/cohort_flow.json"],
                            "support_level": "primary",
                            "summary": "The source path overlaps the claim-map evidence item.",
                        }
                    ],
                    "gaps": [
                        {
                            "gap_id": "alignment-gap",
                            "description": "Evidence ids must match the claim map.",
                            "submission_impact": "AI reviewer must fail closed until ids align.",
                        }
                    ],
                    "recommended_actions": [
                        {
                            "action_id": "align-evidence-id",
                            "priority": "required",
                            "description": "Align evidence_id with the claim-map item_id.",
                        }
                    ],
                }
            ],
        },
    )
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})


def _claim_evidence_alignment_route_context(*, publication_eval_id: str) -> dict[str, Any]:
    return {
        **_paper_write_supervisor_route_context(),
        "current_owner_route": {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "truth_epoch": "truth-event-1",
            "runtime_health_epoch": "runtime-health-1",
            "work_unit_fingerprint": "claim-alignment-fp",
            "failure_signature": "claim_evidence_alignment_required",
            "route_epoch": "truth-event-1",
            "source_fingerprint": "claim-alignment-fp",
            "current_owner": "mas_controller",
            "next_owner": "write",
            "owner_reason": "claim_evidence_alignment_required",
            "active_run_id": None,
            "allowed_actions": ["run_quality_repair_batch"],
            "blocked_actions": ["return_to_ai_reviewer_workflow"],
            "idempotency_scope": "study_quest_owner_route",
            "idempotency_key": "owner-route::dm002::write::claim-evidence",
            "source_refs": {
                "work_unit_id": "claim_evidence_alignment_repair",
                "blocked_reason": "claim_evidence_alignment_required",
            },
        },
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": "claim_evidence_alignment_repair",
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_id,
            "work_unit_fingerprint": "claim-alignment-fp",
        },
    }
