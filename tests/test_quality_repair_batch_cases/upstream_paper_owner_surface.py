from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_blocked_publication_eval(study_root: Path, *, quest_id: str) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_root.name}::{quest_id}::2026-04-22T08:00:00+00:00",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-22T08:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Current paper needs deterministic quality repair before the gate can be trusted.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "claim_evidence_map_missing_or_incomplete",
                "evidence_refs": [str(study_root / "paper")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::quality-repair::2026-04-22T08:00:00+00:00",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Return to the same paper line for deterministic quality repair.",
                "route_target": "review",
                "route_key_question": "Which deterministic quality repair is still blocking publishability?",
                "route_rationale": "Structured quality blockers remain before publishability gate replay.",
                "evidence_refs": [str(study_root / "paper")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return payload


def _write_quality_summary(study_root: Path, *, relative_path: Path | None = None) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "summary_id": f"evaluation-summary::{study_root.name}::2026-04-22T08:01:00+00:00",
        "study_id": study_root.name,
        "quest_id": "quest-001",
        "emitted_at": "2026-04-22T08:01:00+00:00",
        "quality_closure_truth": {
            "state": "quality_repair_required",
            "summary": "Hard publication-quality blockers remain open.",
            "current_required_action": "return_to_publishability_gate",
            "route_target": "review",
        },
        "quality_execution_lane": {
            "lane_id": "general_quality_repair",
            "lane_label": "General quality repair",
            "repair_mode": "deterministic_batch",
            "route_target": "review",
            "route_key_question": "Which deterministic claim-evidence/display repair is still blocking publishability?",
            "summary": "Run deterministic repair units, then replay the publishability gate.",
            "why_now": "The paper gate is blocked by structured quality surfaces.",
        },
    }
    _write_json(study_root / (relative_path or Path("artifacts/evaluation_summary/latest.json")), payload)
    return payload

def _mark_publication_eval_as_specific_upstream_repair(
    study_root: Path,
    publication_eval_payload: dict[str, Any],
) -> dict[str, Any]:
    action = publication_eval_payload["recommended_actions"][0]
    action["action_type"] = "return_to_controller"
    action.pop("route_target", None)
    action.pop("route_key_question", None)
    action.pop("route_rationale", None)
    action["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    action["specificity_targets"] = [
        {
            "target_kind": "claim",
            "target_id": "claim_evidence_map",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "table",
            "target_id": "table_catalog",
            "source_path": str(study_root / "paper" / "tables" / "table_catalog.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "missing_publication_anchor",
        },
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    return publication_eval_payload


def _paper_write_supervisor_route_context() -> dict[str, Any]:
    return {
        "control_plane_snapshot": {
            "surface": "control_plane_snapshot",
            "control_state": "supervisor_gated",
            "canonical_next_action": "resume_same_study_line",
            "authority_refs": {"study_truth": {"epoch": "truth-1"}, "runtime_health": {"epoch": "runtime-1"}},
            "dispatch_gate": {
                "state": "blocked",
                "blocking_reasons": ["publication_supervisor_state.bundle_tasks_downstream_only"],
            },
            "route_authorization": {
                "paper_write_allowed": True,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
        }
    }


def test_run_quality_repair_batch_prefers_same_line_paper_repair_over_stale_bundle_gate(
    monkeypatch,
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
    _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_quality_summary(
        study_root,
        relative_path=Path("artifacts/eval_hygiene/evaluation_summary/latest.json"),
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["quality_closure_truth"] = {
        **dict(summary.get("quality_closure_truth") or {}),
        "state": "quality_repair_required",
        "current_required_action": "return_to_analysis_campaign",
        "route_target": "analysis-campaign",
    }
    summary["quality_execution_lane"] = {
        **dict(summary.get("quality_execution_lane") or {}),
        "lane_id": "general_quality_repair",
        "route_target": "analysis-campaign",
    }
    _write_json(summary_path, summary)
    gate_report = {
        "status": "blocked",
        "current_required_action": "complete_bundle_stage",
        "blockers": [
            "stale_submission_minimal_authority",
            "submission_hardening_incomplete",
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "claim_evidence_map_missing_or_incomplete",
        ],
        "blocking_artifact_refs": [
            {
                "blocker": "claim_evidence_consistency_failed",
                "claim_id": "mortality_attribution_claim",
                "source_path": "paper/claim_evidence_map.json",
            }
        ],
        "gate_fingerprint": "publication-gate::dm002",
        "work_unit_fingerprint": "submission-minimal::dm002",
    }
    route_context = {
        "control_plane_snapshot": {
            "surface": "control_plane_snapshot",
            "control_state": "blocked_runtime_escalation",
            "canonical_next_action": "resume_same_study_line",
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "dispatch_gate": {
                "state": "blocked",
                "blocking_reasons": [
                    "execution_owner_guard.supervisor_only",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": True,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": False,
            },
        }
    }
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "study_id": kwargs["study_id"],
            "study_root": str(kwargs["study_root"]),
            "quest_id": quest_id,
            **route_context,
        },
    )
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_state", lambda _quest_root: object())
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_report", lambda _state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("gate_context", kwargs["control_plane_route_context"]),
            {"ok": True, "status": "executed", "unit_results": []},
        )[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert result["control_plane_route_gate"]["allowed"] is True
    assert result["control_plane_route_gate"]["action"] == "paper_write"
    assert result["control_plane_route_gate"]["controller_route_gate"]["work_unit_id"] == (
        "analysis_claim_evidence_repair"
    )
    assert seen["gate_context"]["controller_route_context"]["work_unit_id"] == "analysis_claim_evidence_repair"


def test_run_quality_repair_batch_uses_task_intake_override_over_raw_bundle_summary(
    monkeypatch,
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
    _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::002::bundle-only",
            "study_id": study_root.name,
            "quest_id": quest_id,
            "emitted_at": "2026-05-10T16:19:41+00:00",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
            },
            "quality_review_loop": {
                "closure_state": "bundle_only_remaining",
                "blocking_issue_count": 2,
            },
            "study_quality_truth": {
                "reviewer_first": {
                    "ready": False,
                    "status": "blocked",
                    "open_concern_count": 1,
                },
            },
            "quality_assessment": {"human_review_readiness": {"status": "blocked"}},
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "schema_version": 1,
            "task_id": "study-task::002::reviewer-revision",
            "study_id": study_root.name,
            "emitted_at": "2026-04-27T02:05:48+00:00",
            "entry_mode": "full_research",
            "task_intent": (
                "Reviewer revision: explicit user feedback reopens the same paper line and requires "
                "补充分析 before any submission-ready/finalize closeout."
            ),
            "constraints": ["Do not keep previous submission-ready/finalize parking as current truth."],
            "first_cycle_outputs": [
                "paper/rebuttal/review_matrix.md and action_plan.md covering all reviewer feedback items."
            ],
        },
    )
    gate_report = {
        "status": "blocked",
        "current_required_action": "complete_bundle_stage",
        "blockers": [
            "stale_submission_minimal_authority",
            "submission_hardening_incomplete",
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "claim_evidence_map_missing_or_incomplete",
        ],
        "blocking_artifact_refs": [
            {
                "blocker": "claim_evidence_consistency_failed",
                "claim_id": "mortality_attribution_claim",
                "source_path": "paper/claim_evidence_map.json",
            }
        ],
        "gate_fingerprint": "publication-gate::dm002",
        "work_unit_fingerprint": "submission-minimal::dm002",
    }
    route_context = {
        "control_plane_snapshot": {
            "surface": "control_plane_snapshot",
            "control_state": "blocked_runtime_escalation",
            "canonical_next_action": "resume_same_study_line",
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "dispatch_gate": {
                "state": "blocked",
                "blocking_reasons": [
                    "execution_owner_guard.supervisor_only",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": True,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": False,
            },
        }
    }
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "study_id": kwargs["study_id"],
            "study_root": str(kwargs["study_root"]),
            "quest_id": quest_id,
            **route_context,
        },
    )
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_state", lambda _quest_root: object())
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_report", lambda _state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("gate_context", kwargs["control_plane_route_context"]),
            {"ok": True, "status": "executed", "unit_results": []},
        )[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert result["control_plane_route_gate"]["allowed"] is True
    assert result["control_plane_route_gate"]["action"] == "paper_write"
    assert result["quality_closure_state"] == "quality_repair_required"
    assert result["quality_execution_lane_id"] == "general_quality_repair"
    assert seen["gate_context"]["controller_route_context"]["work_unit_id"] == "analysis_claim_evidence_repair"


def test_run_quality_repair_batch_materializes_canonical_paper_owner_surface_for_upstream_repair(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    publication_gate = importlib.import_module("med_autoscience.controllers.publication_gate")
    paper_artifacts = importlib.import_module("med_autoscience.runtime_protocol.paper_artifacts")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_id = "quest-001"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    (quest_root / "paper" / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "draft.md").write_text("# Draft\n\nRuntime projected draft shell.\n", encoding="utf-8")
    _write_json(quest_root / "paper" / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(quest_root / "paper" / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(quest_root / "paper" / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(quest_root / "paper" / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(quest_root / "paper" / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(quest_root / "paper" / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(quest_root / "paper" / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    publication_eval_payload = _mark_publication_eval_as_specific_upstream_repair(
        study_root,
        _write_blocked_publication_eval(study_root, quest_id=quest_id),
    )
    _write_quality_summary(study_root)

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context=_paper_write_supervisor_route_context(),
    )

    canonical_paper_root = study_root / "paper"
    assert result["status"] != "blocked_no_paper_root"
    assert result["paper_owner_surface_prepare"]["status"] == "materialized"
    assert canonical_paper_root.is_dir()
    assert paper_artifacts.resolve_latest_paper_root(quest_root) == canonical_paper_root.resolve()
    gate_state = publication_gate.build_gate_state(quest_root)
    assert gate_state.paper_root == canonical_paper_root.resolve()
    assert (canonical_paper_root / "paper_bundle_manifest.json").is_file()
    assert (canonical_paper_root / "paper_line_state.json").is_file()
    assert (canonical_paper_root / "claim_evidence_map.json").is_file()
    assert (canonical_paper_root / "figures" / "figure_catalog.json").is_file()
    assert not (canonical_paper_root / "submission_minimal" / "submission_manifest.json").exists()


def test_run_quality_repair_batch_does_not_materialize_paper_owner_surface_without_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_id = "quest-001"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    publication_eval_payload = _mark_publication_eval_as_specific_upstream_repair(
        study_root,
        _write_blocked_publication_eval(study_root, quest_id=quest_id),
    )
    _write_quality_summary(study_root)

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context=_paper_write_supervisor_route_context(),
    )

    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    assert result["status"] == "blocked_no_paper_root"
    assert result["paper_owner_surface_prepare"]["status"] == "blocked_missing_projection"
    assert not (study_root / "paper").exists()


def test_run_quality_repair_batch_materializes_owner_surface_from_hydration_projection_inputs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    publication_gate = importlib.import_module("med_autoscience.controllers.publication_gate")
    paper_artifacts = importlib.import_module("med_autoscience.runtime_protocol.paper_artifacts")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_id = "quest-001"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    _write_json(quest_root / "paper" / "medical_analysis_contract.json", {"schema_version": 1})
    _write_json(quest_root / "paper" / "medical_reporting_contract.json", {"schema_version": 1})
    _write_json(quest_root / "paper" / "display_registry.json", {"schema_version": 1, "displays": []})
    _write_json(quest_root / "paper" / "figures" / "cohort_flow.shell.json", {"schema_version": 1})
    _write_json(quest_root / "paper" / "tables" / "baseline_characteristics.shell.json", {"schema_version": 1})
    _write_json(
        quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json",
        {
            "schema_version": 1,
            "status": "hydrated",
            "written_files": [
                str(quest_root / "paper" / "medical_analysis_contract.json"),
                str(quest_root / "paper" / "medical_reporting_contract.json"),
                str(quest_root / "paper" / "display_registry.json"),
            ],
        },
    )
    publication_eval_payload = _mark_publication_eval_as_specific_upstream_repair(
        study_root,
        _write_blocked_publication_eval(study_root, quest_id=quest_id),
    )
    _write_quality_summary(study_root)

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context=_paper_write_supervisor_route_context(),
    )

    canonical_paper_root = study_root / "paper"
    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    assert result["status"] != "blocked_no_paper_root"
    assert result["paper_owner_surface_prepare"]["status"] == "materialized"
    assert result["paper_owner_surface_prepare"]["projection_input_status"] == "hydration_projection_present"
    assert paper_artifacts.resolve_latest_paper_root(quest_root) == canonical_paper_root.resolve()
    gate_state = publication_gate.build_gate_state(quest_root)
    assert gate_state.paper_root == canonical_paper_root.resolve()
    assert (canonical_paper_root / "paper_bundle_manifest.json").is_file()
    assert (canonical_paper_root / "paper_line_state.json").is_file()
    assert (canonical_paper_root / "display_registry.json").is_file()
    assert (canonical_paper_root / "claim_evidence_map.json").is_file()
    assert (canonical_paper_root / "figures" / "figure_catalog.json").is_file()
    assert not (canonical_paper_root / "submission_minimal" / "submission_manifest.json").exists()


def test_quality_repair_batch_upstream_work_unit_writes_canonical_delta_and_ai_reviewer_request(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="descriptive",
        manuscript_family="observational",
    )
    quest_id = "quest-001"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nClinical draft surface.\n", encoding="utf-8")
    _write_json(
        paper_root / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "cohort-boundary",
                    "statement": "The study can support a bounded descriptive cohort claim.",
                    "status": "partially_supported",
                    "paper_role": "claim_guardrail",
                    "display_bindings": ["F1"],
                    "sections": ["results"],
                    "evidence_items": [
                        {
                            "item_id": "cohort-flow",
                            "support_level": "direct",
                            "source_paths": ["paper/figures/figure_catalog.json"],
                        }
                    ],
                    "limitations": ["Table 1 and quantitative result surfaces remain pending."],
                }
            ],
        },
    )
    _write_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "status": "analysis_claim_evidence_repair_f1_bound",
            "claims": [
                {
                    "claim_id": "cohort-boundary",
                    "statement": "The study can support a bounded descriptive cohort claim.",
                    "status": "partially_supported",
                    "submission_scope": "main_text_candidate_after_display_restoration",
                    "evidence": [
                        {
                            "evidence_id": "cohort-flow",
                            "kind": "display",
                            "source_paths": ["paper/figures/figure_catalog.json"],
                            "support_level": "direct",
                            "summary": "F1 supports cohort-boundary wording.",
                        }
                    ],
                    "gaps": [
                        {
                            "gap_id": "table1-active-display-missing",
                            "description": "Baseline Table 1 is still pending.",
                            "submission_impact": "Do not finalize table-supported Results prose.",
                        }
                    ],
                    "recommended_actions": [
                        {
                            "action_id": "restore-table1",
                            "priority": "before_release",
                            "description": "Restore audited Table 1 before final Results prose.",
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
    publication_eval_payload = _mark_publication_eval_as_specific_upstream_repair(
        study_root,
        _write_blocked_publication_eval(study_root, quest_id=quest_id),
    )
    _write_quality_summary(study_root)

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
            "blockers": [
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
            ],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": [
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
            ],
            "blocking_artifact_refs": [
                {
                    "blocker": "claim_evidence_consistency_failed",
                    "artifact_path": str(paper_root / "claim_evidence_map.json"),
                    "artifact_role": "claim_evidence_map",
                    "source_path": str(paper_root / "claim_evidence_map.json"),
                },
                {
                    "blocker": "reviewer_first_concerns_unresolved",
                    "artifact_path": str(paper_root / "review" / "review_ledger.json"),
                    "artifact_role": "review_ledger",
                    "source_path": str(paper_root / "review" / "review_ledger.json"),
                },
            ],
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::blocked",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "selected_publication_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "blockers": ["claim_evidence_consistency_failed"],
            },
            "unit_results": [
                {
                    "unit_id": "materialize_display_surface",
                    "status": "already_current",
                    "result": {"status": "already_current"},
                }
            ],
        },
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context=_paper_write_supervisor_route_context(),
    )

    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    evidence = result["repair_execution_evidence"]
    assert evidence["canonical_artifact_delta"]["status"] == "fresh"
    assert evidence["evidence_ledger_update_done"] is True
    assert evidence["review_ledger_update_done"] is True
    assert evidence["ai_reviewer_recheck_done"] is True
    assert "canonical_artifact_delta_missing" not in evidence["blockers"]
    changed_paths = {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in evidence["canonical_artifact_delta"]["artifact_refs"]
    }
    assert {
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/review_ledger.json",
    }.issubset(changed_paths)
    review_ledger = json.loads((paper_root / "review" / "review_ledger.json").read_text(encoding="utf-8"))
    assert review_ledger["schema_version"] == 1
    assert review_ledger["concerns"][0]["status"] == "resolved"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["request_owner"] == "ai_reviewer"
    assert request["input_contract"]["required_refs"]["review_ledger"]["present"] is True
