from __future__ import annotations

from . import shared as _shared
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_reviewer_os

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_quality_repair_batch_route_context_preempts_current_submission_refresh_selection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc-primary-care-phenotype-treatment-gap",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_root = profile.managed_runtime_home / "quests" / quest_id
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-003" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    publication_eval_payload["recommended_actions"][0]["specificity_targets"] = [
        {
            "target_kind": "claim",
            "target_id": "claim_evidence_map",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "table",
            "target_id": "table_catalog",
            "source_path": str(study_root / "paper" / "tables" / "table_catalog.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
        ],
        "current_required_action": "return_to_publishability_gate",
        "medical_publication_surface_status": "blocked",
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
        "bundle_tasks_downstream_only": True,
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated", "repaired_files": []})
    materialize_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda *, paper_root: (materialize_calls.append(paper_root), {"status": "materialized"})[1],
    )
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(AssertionError("analysis repair must not materialize submission package")),
    )
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda **_: (_ for _ in ()).throw(AssertionError("analysis repair must not sync delivery package")),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_submission_minimal_authority"],
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context={
            "authority_snapshot": {
                "surface": "authority_snapshot",
                "control_state": "supervisor_gated",
                "canonical_next_action": "resume_same_study_line",
                "authority_refs": {
                    "study_truth": {"epoch": "truth-1"},
                    "runtime_health": {"epoch": "runtime-1"},
                },
                "dispatch_gate": {
                    "state": "blocked",
                    "blocking_reasons": ["publication_supervisor_state.bundle_tasks_downstream_only"],
                },
                "route_authorization": {
                    "authorized": False,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": False,
                    "runtime_recovery_allowed": False,
                },
            },
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "requires_human_confirmation": False,
                "source_eval_id": publication_eval_payload["eval_id"],
                "work_unit_fingerprint": "publication-blockers::quality-repair",
            },
        },
    )

    assert materialize_calls == [paper_root]
    assert result["selected_publication_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "materialize_display_surface",
    ]


def test_gate_clearing_batch_consumes_current_ai_reviewer_publication_eval_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc-primary-care-phenotype-treatment-gap",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_root = profile.managed_runtime_home / "quests" / quest_id
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-003" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    manuscript_text = "# Draft\n\nCurrent manuscript surface for gate-clearing repair.\n"
    current_manuscript = study_root / "paper" / "draft.md"
    current_manuscript.parent.mkdir(parents=True, exist_ok=True)
    current_manuscript.write_text(manuscript_text, encoding="utf-8")
    stale_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    stale_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Stale eval should not drive the current gate-clearing batch.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", stale_eval_payload)
    current_eval_id = f"publication-eval::{study_root.name}::{quest_id}::2026-05-27T11:10:37+00:00"
    current_eval_payload = {
        **stale_eval_payload,
        "eval_id": current_eval_id,
        "emitted_at": "2026-05-27T11:10:37+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(current_manuscript.resolve())],
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "quality_assessment": {
            dimension: {"status": "blocked", "summary": f"{dimension} requires current repair."}
            for dimension in (
                "clinical_significance",
                "evidence_strength",
                "novelty_positioning",
                "medical_journal_prose_quality",
                "human_review_readiness",
            )
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "The current record is bound to the present manuscript snapshot.",
                "impact_on_claim": "Claims remain scoped to current evidence refs.",
                "required_future_analysis_data_or_design": "Repeat review after substantive changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
            study_root=study_root,
            manuscript_path=current_manuscript,
            manuscript_text=manuscript_text,
            eval_id=current_eval_id,
        ),
        "recommended_actions": [
            {
                "action_id": "return-to-current-claim-alignment",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Use the current AI reviewer record for gate-clearing repair.",
                "route_target": "write",
                "work_unit_fingerprint": "current-gate-clearing-fp",
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair current claim-evidence traceability.",
                },
            }
        ],
    }
    current_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260527T111037Z_publication_eval_record.json"
    )
    _write_json(current_record_path, current_eval_payload)
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked"],
        "current_required_action": "return_to_publishability_gate",
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "study_delivery_status": "current",
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated", "repaired_files": []})
    monkeypatch.setattr(module, "_materialize_display_surface", lambda *, paper_root: {"status": "materialized"})
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["medical_publication_surface_blocked"],
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context={
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "requires_human_confirmation": False,
                "source_eval_id": current_eval_id,
                "work_unit_fingerprint": "current-gate-clearing-fp",
            },
        },
    )

    assert result["source_eval_id"] == current_eval_id
    assert result["explicit_publication_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"


def test_gate_specificity_targets_preempt_publication_gate_replay_for_upstream_paper_repair() -> None:
    currentness = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_currentness")

    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::latest",
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": "publication-blockers::replay",
                "next_work_unit": {
                    "unit_id": "publication_gate_replay",
                    "lane": "controller",
                    "summary": "Replay the publication gate against current authority signatures.",
                },
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": "/workspace/studies/dm002/paper/claim_evidence_map.json",
                        "blocking_reason": "claim_evidence_consistency_failed",
                    },
                    {
                        "target_kind": "metric",
                        "target_id": "main_result_metrics",
                        "source_path": "/workspace/runtime/quests/dm002/artifacts/results/main_result.json",
                        "blocking_reason": "claim_evidence_consistency_failed",
                    },
                    {
                        "target_kind": "figure",
                        "target_id": "figure_catalog",
                        "source_path": "/workspace/studies/dm002/paper/figures/figure_catalog.json",
                        "blocking_reason": "claim_evidence_consistency_failed",
                    },
                    {
                        "target_kind": "table",
                        "target_id": "submission_table_or_manifest",
                        "source_path": "/workspace/studies/dm002/paper/submission_minimal/audit/submission_manifest.json",
                        "blocking_reason": "stale_study_delivery_mirror",
                    },
                    {
                        "target_kind": "source_path",
                        "target_id": "publication_gate_source_path",
                        "source_path": "/workspace/runtime/quests/dm002/artifacts/reports/medical_publication_surface/latest.json",
                        "blocking_reason": "stale_study_delivery_mirror",
                    },
                ],
            }
        ],
    }
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "study_delivery_status": "stale_source_mismatch",
        "blocking_artifact_refs": [
            {
                "blocker": "stale_study_delivery_mirror",
                "artifact_path": "/workspace/studies/dm002/manuscript/delivery_manifest.json",
                "artifact_role": "study_delivery_mirror",
            },
            {
                "blocker": "claim_evidence_consistency_failed",
                "artifact_path": "/workspace/studies/dm002/paper/claim_evidence_map.json",
                "artifact_role": "claim_evidence_map",
            },
        ],
    }

    selection = currentness.publication_work_unit_selection(
        publication_eval_payload=publication_eval_payload,
        latest_batch={},
        gate_report=gate_report,
        authority_settle_delivery_redrive_requested=False,
        direct_submission_delivery_sync_requested=False,
        controller_decision_work_unit=None,
    )

    assert selection["explicit_next_work_unit"]["unit_id"] == "publication_gate_replay"
    assert selection["current_next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert selection["selected_publication_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert selection["terminal_reason"] is None
