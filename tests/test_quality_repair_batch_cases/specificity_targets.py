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
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Return to the same paper line for deterministic quality repair.",
                "evidence_refs": [str(study_root / "paper")],
                "work_unit_fingerprint": "publication-blockers::generic",
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "lane": "controller",
                    "summary": "Ask the publication gate to identify concrete blocker targets.",
                },
                "blocking_work_units": [
                    {
                        "unit_id": "gate_needs_specificity",
                        "lane": "controller",
                        "summary": "Ask the publication gate to identify concrete blocker targets.",
                    }
                ],
                "specificity_targets": [
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
                        "target_kind": "metric",
                        "target_id": "main_result_metrics",
                        "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
                        "blocking_reason": "medical_publication_surface_blocked",
                    },
                    {
                        "target_kind": "table",
                        "target_id": "submission_table_or_manifest",
                        "source_path": str(
                            study_root / "paper" / "submission_minimal" / "audit" / "submission_manifest.json"
                        ),
                        "blocking_reason": "medical_publication_surface_blocked",
                    },
                    {
                        "target_kind": "source_path",
                        "target_id": "publication_gate_source_path",
                        "source_path": str(
                            study_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
                        ),
                        "blocking_reason": "medical_publication_surface_blocked",
                    },
                ],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return payload


def _write_quality_summary(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": f"evaluation-summary::{study_root.name}::2026-04-22T08:01:00+00:00",
            "study_id": study_root.name,
            "quest_id": "quest-001",
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
        },
    )


def test_build_quality_repair_batch_action_uses_publication_eval_specificity_targets_for_generic_gate_blocker(
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
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    _write_quality_summary(study_root)
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
    }

    action = module.build_quality_repair_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["controller_action_type"] == "run_quality_repair_batch"
    assert action["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert action["specificity_targets"] == publication_eval_payload["recommended_actions"][0]["specificity_targets"]
    assert "non_executable_reason" not in action["next_work_unit"]


def test_run_quality_repair_batch_prefers_latest_controller_decision_over_stale_runtime_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "quest-003"
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
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
    _write_quality_summary(study_root)
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_id": "decision-003-current",
            "study_id": study_root.name,
            "quest_id": quest_id,
            "emitted_at": "2026-05-11T11:02:57+00:00",
            "decision_type": "route_back_same_line",
            "charter_ref": {
                "charter_id": f"charter::{study_root.name}::v1",
                "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            },
            "runtime_escalation_ref": {
                "record_id": f"runtime-escalation::{study_root.name}::{quest_id}::publication_quality_gap",
                "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
            "publication_eval_ref": {
                "eval_id": publication_eval_payload["eval_id"],
                "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "requires_human_confirmation": False,
            "controller_actions": [
                {
                    "action_type": "run_quality_repair_batch",
                    "payload_ref": str(decision_path),
                }
            ],
            "reason": "Run controller-owned quality repair for concrete publication targets.",
            "route_target": "write",
            "route_key_question": "MAS/MDS-supervised revised manuscript package",
            "route_rationale": "Specificity targets are present; execute the upstream paper repair work unit.",
            "work_unit_fingerprint": "publication-blockers::current",
            "next_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
            },
            "blocking_work_units": [
                {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                }
            ],
        },
    )
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
        "gate_fingerprint": "publication-gate::003",
    }
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **kwargs: {
            "study_id": kwargs["study_id"],
            "study_root": str(kwargs["study_root"]),
            "quest_id": quest_id,
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
                    "blocking_reasons": [
                        "publication_supervisor_state.bundle_tasks_downstream_only",
                        "runtime_recovery_retry_budget_exhausted",
                    ],
                },
                "route_authorization": {
                    "authorized": False,
                    "paper_write_allowed": True,
                    "bundle_build_allowed": False,
                    "runtime_recovery_allowed": False,
                },
            },
            "last_controller_decision_authorization": {
                "source": "owner_route_reconcile_platform_repair",
                "decision_id": "decision-003-stale",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": "publication-blockers::stale",
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "lane": "controller",
                    "summary": "Ask the gate to provide concrete targets.",
                },
                "control_intent_identity": {
                    "work_unit_id": "gate_needs_specificity",
                    "blocker_authority_fingerprint": "publication-blockers::stale",
                },
            },
        },
    )
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_state", lambda _quest_root: object())
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_report", lambda _state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("gate_context", kwargs["authority_route_context"]),
            {"ok": True, "status": "executed"},
        )[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert result["authority_route_gate"]["allowed"] is True
    assert result["authority_route_gate"]["action"] == "paper_write"
    assert result["authority_route_gate"]["controller_route_gate"]["work_unit_id"] == (
        "analysis_claim_evidence_repair"
    )
    assert seen["gate_context"]["controller_route_context"]["work_unit_id"] == "analysis_claim_evidence_repair"


def test_run_quality_repair_batch_uses_paper_write_for_medical_prose_methodology_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_id = "quest-002"
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_quality_summary(study_root)
    work_unit_id = "medical_prose_quality_analysis_source_documentation_repair"
    route_context = {
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
                "runtime_recovery_allowed": True,
            },
        },
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": (
                "domain-transition::ai_reviewer_re_eval::medical_prose_quality_route_back_analysis"
            ),
        },
    }
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
        "gate_fingerprint": "publication-gate::002",
    }
    seen: dict[str, object] = {}

    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_state", lambda _quest_root: object())
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_report", lambda _state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("gate_context", kwargs["authority_route_context"]),
            {
                "ok": True,
                "status": "executed",
                "selected_publication_work_unit": {"unit_id": work_unit_id},
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

    assert result["authority_route_gate"]["allowed"] is True
    assert result["authority_route_gate"]["action"] == "paper_write"
    assert result["authority_route_gate"]["controller_route_gate"]["work_unit_id"] == work_unit_id
    assert seen["gate_context"]["controller_route_context"]["work_unit_id"] == work_unit_id


def test_run_quality_repair_batch_overrides_stale_bundle_route_for_medical_prose_write_repair(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "quest-003"
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "route_key_question": "Repair current AI reviewer medical-prose findings.",
            "route_rationale": "The current prose review requires same-line write repair.",
            "work_unit_fingerprint": "medical-prose-routeback::write::current",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair the manuscript body against current AI reviewer prose findings.",
            },
            "blocking_work_units": [
                {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript body against current AI reviewer prose findings.",
                }
            ],
        }
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    stale_bundle_context = {
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
                "blocking_reasons": [
                    "publication_supervisor_state.bundle_tasks_downstream_only",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": False,
            },
        },
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": "submission_minimal_refresh",
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "submission-minimal::stale",
        },
    }
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
        "gate_fingerprint": "publication-gate::003",
    }
    seen: dict[str, object] = {}

    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_state", lambda _quest_root: object())
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_report", lambda _state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("gate_context", kwargs["authority_route_context"]),
            {
                "ok": True,
                "status": "executed",
                "selected_publication_work_unit": {"unit_id": "medical_prose_write_repair"},
            },
        )[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=stale_bundle_context,
    )

    assert result["authority_route_gate"]["allowed"] is True
    assert result["authority_route_gate"]["action"] == "paper_write"
    assert result["authority_route_gate"]["controller_route_gate"]["work_unit_id"] == "medical_prose_write_repair"
    gate_context = seen["gate_context"]
    assert isinstance(gate_context, dict)
    assert gate_context["controller_route_context"]["work_unit_id"] == "medical_prose_write_repair"
    assert gate_context["controller_route_context"]["work_unit_fingerprint"] == (
        "medical-prose-routeback::write::current"
    )


def test_run_quality_repair_batch_records_hard_unit_harmonization_handoff_without_generic_completion(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_id = "quest-002"
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0]["specificity_targets"] = [
        {
            "target_kind": "claim",
            "target_id": "transported_score_claim",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "figure",
            "target_id": "risk_distribution_collapse_figure",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "table",
            "target_id": "table_2_validation_performance",
            "source_path": str(study_root / "paper" / "tables" / "table_catalog.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
        {
            "target_kind": "metric",
            "target_id": "hdl_unit_standardized_sensitivity",
            "source_path": str(study_root / "artifacts" / "reports" / "harmonization_route_back" / "latest.md"),
            "blocking_reason": "unit_standardized_model_application_or_sensitivity",
        },
        {
            "target_kind": "source_path",
            "target_id": "publication_gate_source_path",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "medical_publication_surface_blocked",
        },
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
        "gate_fingerprint": "publication-gate::002",
    }

    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_state", lambda _quest_root: object())
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_report", lambda _state: gate_report)
    def fail_if_gate_clearing_batch_runs(**_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("hard unit-harmonization target must not run generic gate-clearing batch")

    def fail_if_paper_owner_surface_prepares(**_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("hard unit-harmonization target must not mutate paper owner surface")

    monkeypatch.setattr(module.gate_clearing_batch, "run_gate_clearing_batch", fail_if_gate_clearing_batch_runs)
    monkeypatch.setattr(
        module.quality_repair_paper_owner_surface,
        "prepare_canonical_paper_owner_surface_for_upstream_repair",
        fail_if_paper_owner_surface_prepares,
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert result["status"] == "blocked"
    assert result["ok"] is False
    assert result["blocked_reason"] == "unit_harmonized_rerun_required"
    assert result["next_owner"] == "analysis_harmonization_owner"
    assert result["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert result["hard_methodology_target"]["target_id"] == "hdl_unit_standardized_sensitivity"
    assert result["gate_clearing_batch"]["status"] == "not_run"
    assert result["paper_owner_surface_prepare"]["status"] == "not_applicable"
    record = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert record["blocked_reason"] == "unit_harmonized_rerun_required"
    assert record["quality_gate_relaxation_allowed"] is False
    assert record["current_package_write_allowed"] is False


def test_run_quality_repair_batch_hard_handoff_reads_incomplete_upstream_specificity_targets(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_id = "quest-002"
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    action = publication_eval_payload["recommended_actions"][0]
    action["action_type"] = "bounded_analysis"
    action["route_target"] = "analysis-campaign"
    action["route_key_question"] = "unit-harmonized rerun or typed blocker"
    action["route_rationale"] = "HDL harmonization is a hard methodology prerequisite."
    action["next_work_unit"] = {
        "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
        "lane": "analysis-campaign",
        "summary": "Close or type-block evidence gaps before prose clearance.",
    }
    action["blocking_work_units"] = [
        {
            "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
            "lane": "analysis-campaign",
            "summary": "Materialize or type-block HDL harmonization evidence.",
        }
    ]
    action["specificity_targets"] = [
        {
            "target_kind": "metric",
            "target_id": "c_index_confidence_intervals",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "Prediction-model validation reporting is incomplete without uncertainty.",
        },
        {
            "target_kind": "source_path",
            "target_id": "hdL_unit_standardized_sensitivity",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "The HDL shift cannot be interpreted without unit/assay/transformation checks.",
        },
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
        "gate_fingerprint": "publication-gate::002",
    }

    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_state", lambda _quest_root: object())
    monkeypatch.setattr(module.gate_clearing_batch.publication_gate, "build_gate_report", lambda _state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("incomplete hard target must not run generic gate-clearing batch")
        ),
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "unit_harmonized_rerun_required"
    assert result["next_owner"] == "analysis_harmonization_owner"
    assert result["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert result["hard_methodology_target"]["target_id"] == "hdL_unit_standardized_sensitivity"
    assert result["gate_clearing_batch"]["status"] == "not_run"
