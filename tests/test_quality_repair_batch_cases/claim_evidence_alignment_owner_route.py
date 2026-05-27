from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_reviewer_os
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


def test_run_quality_repair_batch_honors_current_manuscript_claim_alignment_owner_route(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc-primary-care-phenotype-treatment-gap",
        study_archetype="clinical_classifier",
        endpoint_type="cross_sectional_quality_gap",
        manuscript_family="primary_care_diabetes",
    )
    quest_id = "quest-003"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nCurrent manuscript surface.\n", encoding="utf-8")
    _write_claim_alignment_fixture(paper_root)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0]["route_target"] = "write"
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "current_manuscript_claim_evidence_alignment_repair",
        "lane": "write",
        "summary": "Align the current manuscript claim-evidence map and evidence ledger.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
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
        publication_eval_id=publication_eval_payload["eval_id"],
        work_unit_id="current_manuscript_claim_evidence_alignment_repair",
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
    assert (
        seen["gate_context"]["controller_route_context"]["work_unit_id"]
        == "current_manuscript_claim_evidence_alignment_repair"
    )
    assert result["gate_clearing_batch"]["explicit_publication_work_unit"]["unit_id"] == (
        "current_manuscript_claim_evidence_alignment_repair"
    )
    unit_result = result["gate_clearing_batch"]["unit_results"][0]
    assert unit_result["unit_id"] == "current_manuscript_claim_evidence_alignment_repair"
    alignment = unit_result["result"]["claim_evidence_alignment"]
    assert alignment["status"] == "ready"
    ledger = json.loads((paper_root / "evidence_ledger.json").read_text(encoding="utf-8"))
    assert ledger["claims"][0]["evidence"][0]["evidence_id"] == "C1_main_result_observed_gap"
    assert result["repair_execution_evidence"]["evidence_ledger_update_done"] is True


def test_run_quality_repair_batch_consumes_current_ai_reviewer_record(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc-primary-care-phenotype-treatment-gap",
        study_archetype="clinical_classifier",
        endpoint_type="cross_sectional_quality_gap",
        manuscript_family="primary_care_diabetes",
    )
    quest_id = "quest-003"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    current_manuscript_text = "# Draft\n\nCurrent manuscript surface with revised claim-evidence alignment.\n"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text(current_manuscript_text, encoding="utf-8")
    _write_claim_alignment_fixture(paper_root)
    stale_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    stale_eval_payload["recommended_actions"][0]["route_target"] = "write"
    stale_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "current_manuscript_claim_evidence_alignment_repair",
        "lane": "write",
        "summary": "Align the stale manuscript claim-evidence map and evidence ledger.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", stale_eval_payload)
    current_eval_id = f"publication-eval::{study_root.name}::{quest_id}::2026-05-27T11:10:37+00:00"
    current_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260527T111037Z_publication_eval_record.json"
    )
    dimensions = (
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    )
    current_eval_payload = {
        **stale_eval_payload,
        "eval_id": current_eval_id,
        "emitted_at": "2026-05-27T11:10:37+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str((paper_root / "draft.md").resolve())],
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "quality_assessment": {
            dimension: {"status": "blocked", "summary": f"{dimension} requires manuscript repair."}
            for dimension in dimensions
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "The current AI reviewer record is bound to one manuscript snapshot.",
                "impact_on_claim": "Claims must stay tied to the reviewed manuscript and evidence ledger.",
                "required_future_analysis_data_or_design": "Repeat reviewer evaluation after manuscript changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
            study_root=study_root,
            manuscript_path=paper_root / "draft.md",
            manuscript_text=current_manuscript_text,
            eval_id=current_eval_id,
        ),
        "recommended_actions": [
            {
                "action_id": "return-to-write-current-claim-alignment",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Current AI reviewer record routes claim-evidence alignment repair to write.",
                "route_target": "write",
                "work_unit_fingerprint": "current-claim-alignment-fp",
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "current_manuscript_claim_evidence_alignment_repair",
                    "lane": "write",
                    "summary": "Align the current manuscript claim-evidence map and evidence ledger.",
                },
            }
        ],
    }
    _write_json(current_record_path, current_eval_payload)
    _write_quality_summary(study_root)
    route_context = _claim_evidence_alignment_route_context(
        publication_eval_id=current_eval_id,
        work_unit_id="current_manuscript_claim_evidence_alignment_repair",
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
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_kwargs: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "selected_publication_work_unit": {"unit_id": "manuscript_story_repair"},
            "gate_replay": {"status": "blocked", "blockers": ["claim_evidence_alignment_required"]},
            "unit_results": [],
        },
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
    assert result["source_eval_id"] == current_eval_id
    assert result["source_eval_artifact_path"] == str(current_record_path.resolve())
    assert result["repair_execution_evidence"]["review_finding"]["source_eval_id"] == current_eval_id


def test_claim_alignment_repair_materializes_missing_claim_from_ledger_items(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch_upstream")
    study_root = tmp_path / "study"
    paper_root = study_root / "paper"
    paper_root.mkdir(parents=True)
    _write_json(
        paper_root / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "A1_boundary_metric_provenance",
                    "statement": "A1 is retained only as boundary metric-provenance evidence.",
                    "status": "boundary_evidence_only",
                    "paper_role": "main_text",
                    "display_bindings": ["F1"],
                    "sections": ["Results"],
                    "evidence_items": [
                        {
                            "item_id": "a1-metric-provenance-inventory",
                            "support_level": "weakens_claim",
                            "source_paths": ["paper/a1-metric-provenance-inventory.md"],
                            "summary": "Metric provenance inventory weakens the candidate A1 claim.",
                        },
                        {
                            "item_id": "a1-calibration-evidence-audit",
                            "support_level": "weakens_claim",
                            "source_paths": ["paper/a1-calibration-evidence-audit.md"],
                            "summary": "Calibration audit bounds the candidate A1 claim.",
                        },
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
                    "statement": "Another claim is already aligned.",
                    "status": "supported",
                    "submission_scope": "main_text",
                    "evidence": [
                        {
                            "evidence_id": "c1-evidence",
                            "kind": "result",
                            "source_paths": ["paper/c1.md"],
                            "support_level": "primary",
                            "summary": "C1 support.",
                        }
                    ],
                    "gaps": [
                        {
                            "gap_id": "c1-none",
                            "description": "No C1 gap.",
                            "submission_impact": "none",
                        }
                    ],
                    "recommended_actions": [
                        {
                            "action_id": "c1-none",
                            "priority": "none",
                            "description": "No C1 action.",
                        }
                    ],
                }
            ],
            "items": [
                {
                    "item_id": "a1-metric-provenance-inventory",
                    "kind": "analysis_slice",
                    "source_paths": ["paper/a1-metric-provenance-inventory.md"],
                    "result_summary": "No auditable structured discrimination metric provenance was available.",
                    "paper_contract_role": "boundary_negative_evidence",
                },
                {
                    "item_id": "a1-calibration-evidence-audit",
                    "kind": "analysis_slice",
                    "source_paths": ["paper/a1-calibration-evidence-audit.md"],
                    "result_summary": "Calibration evidence is insufficient for a headline A1 claim.",
                    "paper_contract_role": "boundary_negative_evidence",
                },
            ],
        },
    )

    result = module.run_upstream_paper_repair_unit(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-003",
        study_root=study_root,
        gate_report={
            "gate_fingerprint": "publication-gate::claim-alignment",
            "blockers": ["claim_evidence_alignment_required"],
            "medical_publication_surface_named_blockers": ["claim_evidence_alignment_required"],
        },
        work_unit_id="current_manuscript_claim_evidence_alignment_repair",
        source_eval_id="publication-eval::003",
    )

    assert result is not None
    assert result["status"] == "updated"
    repair = result["result"]["claim_evidence_alignment_repair"]
    assert repair["status"] == "updated"
    assert repair["claim_evidence_alignment"]["status"] == "ready"
    ledger = json.loads((paper_root / "evidence_ledger.json").read_text(encoding="utf-8"))
    a1_claim = next(claim for claim in ledger["claims"] if claim["claim_id"] == "A1_boundary_metric_provenance")
    assert [item["evidence_id"] for item in a1_claim["evidence"]] == [
        "a1-metric-provenance-inventory",
        "a1-calibration-evidence-audit",
    ]
    assert a1_claim["submission_scope"] == "main_text"
    assert a1_claim["gaps"][0]["gap_id"] == "A1_boundary_metric_provenance-alignment-resolved"
    assert result["result"]["ai_reviewer_recheck_request_ref"]


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


def _claim_evidence_alignment_route_context(
    *,
    publication_eval_id: str,
    work_unit_id: str = "claim_evidence_alignment_repair",
) -> dict[str, Any]:
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
                "work_unit_id": work_unit_id,
                "blocked_reason": "claim_evidence_alignment_required",
            },
        },
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_id,
            "work_unit_fingerprint": "claim-alignment-fp",
        },
    }
