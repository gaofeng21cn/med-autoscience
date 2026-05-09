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


def test_build_quality_repair_batch_action_for_general_quality_repair_lane(tmp_path: Path) -> None:
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
        "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "claim_evidence_map_missing_or_incomplete",
            "table_catalog_missing_or_incomplete",
        ],
        "bundle_tasks_downstream_only": False,
    }

    action = module.build_quality_repair_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["action_type"] == "route_back_same_line"
    assert action["route_target"] == "review"
    assert action["controller_action_type"] == "run_quality_repair_batch"
    assert action["quality_repair_batch_reason"] == (
        "quality_closure_truth requires deterministic repair; "
        "paper-facing display/reporting blockers are deterministic repair candidates"
    )


def test_build_quality_repair_batch_action_reads_eval_hygiene_quality_summary(tmp_path: Path) -> None:
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
    _write_quality_summary(
        study_root,
        relative_path=Path("artifacts/eval_hygiene/evaluation_summary/latest.json"),
    )
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "claim_evidence_map_missing_or_incomplete",
        ],
    }

    action = module.build_quality_repair_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert not (study_root / "artifacts" / "evaluation_summary" / "latest.json").exists()
    assert action is not None
    assert action["controller_action_type"] == "run_quality_repair_batch"


def test_build_quality_repair_batch_action_allows_upstream_quality_repair_when_bundle_tasks_are_downstream(
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
        "blockers": [
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
            "stale_submission_minimal_authority",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "claim_evidence_map_missing_or_incomplete",
        ],
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
    assert action["route_target"] == "review"
    assert action["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert action["blocking_work_units"][0]["unit_id"] == "analysis_claim_evidence_repair"
    assert action["work_unit_fingerprint"].startswith("publication-blockers::")
    assert action["quality_repair_batch_reason"] == (
        "quality_closure_truth requires deterministic repair; "
        "paper-facing display/reporting blockers are deterministic repair candidates"
    )


def test_build_quality_repair_batch_action_honors_analysis_owner_handoff_for_same_fingerprint(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-003")
    _write_quality_summary(study_root)
    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
            "storyline_evidence_map_missing",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "claim_evidence_consistency_failed",
            "storyline_evidence_map_missing",
        ],
        "blocking_artifact_refs": [
            {
                "blocker": "claim_evidence_consistency_failed",
                "claim_id": "claim_evidence_map",
                "source_path": "paper/claim_evidence_map.json",
            },
            {
                "blocker": "storyline_evidence_map_missing",
                "claim_id": "storyline_evidence_map",
                "source_path": "paper/storyline_evidence_map.json",
            },
        ],
    }
    publication_work_unit_payload = module.publication_work_units.derive_publication_work_units(gate_report)
    assert publication_work_unit_payload["fingerprint"].startswith("publication-blockers::")
    assert publication_work_unit_payload["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    identity = control_intent.build_control_intent_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        route_target="analysis-campaign",
        work_unit_id="analysis_claim_evidence_repair",
        blocker_authority_fingerprint=publication_work_unit_payload["fingerprint"],
        controller_actions=("run_quality_repair_batch",),
        source_kind="controller_decision_authorization",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="owner_handoff",
        payload={
            "reason": "exhausted_for_current_fingerprint",
            "next_owner": "write/ai_reviewer",
            "next_work_unit": "manuscript_story_repair",
        },
        recorded_at="2026-05-09T17:56:42+00:00",
    )

    action = module.build_quality_repair_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-003",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["next_work_unit"]["unit_id"] == "manuscript_story_repair"
    assert action["next_work_unit"]["lane"] == "write"
    assert action["blocking_work_units"][0]["unit_id"] == "manuscript_story_repair"
    assert action["controller_work_unit_owner_handoff"]["from_work_unit"] == "analysis_claim_evidence_repair"
    assert action["controller_work_unit_owner_handoff"]["next_owner"] == "write/ai_reviewer"
    assert action["controller_work_unit_owner_handoff"]["next_work_unit"] == "manuscript_story_repair"


def test_build_quality_repair_batch_action_does_not_promote_downstream_delivery_only_work_when_bundle_tasks_are_downstream(
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
        "blockers": ["stale_study_delivery_mirror"],
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
        "bundle_tasks_downstream_only": True,
    }

    action = module.build_quality_repair_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is None


def test_quality_repair_batch_builds_controller_route_for_submission_minimal_refresh() -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")

    context = module._controller_route_context_for_gate(
        gate_report={
            "status": "blocked",
            "current_required_action": "complete_bundle_stage",
            "blockers": [
                "stale_submission_minimal_authority",
                "submission_hardening_incomplete",
            ],
            "gate_fingerprint": "publication-gate::003",
            "work_unit_fingerprint": "submission-minimal::003",
        },
        source_eval_id="publication-eval::003::latest",
    )

    assert context == {
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": "submission_minimal_refresh",
            "requires_human_confirmation": False,
            "source_eval_id": "publication-eval::003::latest",
            "gate_fingerprint": "publication-gate::003",
            "work_unit_fingerprint": "submission-minimal::003",
        }
    }


def test_run_quality_repair_batch_wraps_gate_clearing_and_writes_record(monkeypatch, tmp_path: Path) -> None:
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
    quality_summary = _write_quality_summary(study_root)
    gate_result = {
        "ok": True,
        "status": "executed",
        "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        "gate_replay": {
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        },
        "unit_results": [{"unit_id": "materialize_display_surface", "status": "updated"}],
        "execution_summary": {
            "parallel_wave_count": 1,
            "parallel_unit_count": 1,
            "sequential_unit_count": 0,
            "skipped_dependency_unit_count": 0,
        },
    }
    seen: dict[str, object] = {}
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (seen.setdefault("kwargs", kwargs), gate_result)[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    assert seen["kwargs"].pop("control_plane_route_context")["control_plane_snapshot"]["surface"] == (
        "control_plane_snapshot"
    )
    assert seen["kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    assert result["source_summary_id"] == quality_summary["summary_id"]
    assert result["gate_clearing_batch"]["gate_replay"]["status"] == "blocked"
    assert result["gate_clearing_execution_summary"] == gate_result["execution_summary"]
    record = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert record["quality_closure_state"] == "quality_repair_required"
    assert record["quality_execution_lane_id"] == "general_quality_repair"
    assert record["gate_clearing_execution_summary"] == gate_result["execution_summary"]


def test_run_quality_repair_batch_builds_gate_state_from_managed_runtime_quest_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = make_profile(tmp_path)
    profile = profiles.WorkspaceProfile(
        **{
            **profile.__dict__,
            "runtime_root": profile.workspace_root / "runtime" / "quests",
            "med_deepscientist_runtime_root": profile.workspace_root / "legacy" / "mds-runtime",
        }
    )
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    _write_quality_summary(study_root)
    seen: dict[str, Path] = {}

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda quest_root: (
            seen.setdefault("quest_root", quest_root),
            type("GateState", (), {"paper_root": study_root / "paper"})(),
        )[1],
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": [
                "claim_evidence_map_missing_or_incomplete",
            ],
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "gate_replay": {"status": "blocked", "blockers": ["claim_evidence_consistency_failed"]},
            "unit_results": [{"unit_id": "materialize_display_surface", "status": "updated"}],
        },
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    assert seen["quest_root"] == profile.managed_runtime_quests_root / "quest-001"


def test_run_quality_repair_batch_records_eval_hygiene_summary_path(monkeypatch, tmp_path: Path) -> None:
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
    quality_summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    quality_summary = _write_quality_summary(
        study_root,
        relative_path=Path("artifacts/eval_hygiene/evaluation_summary/latest.json"),
    )
    gate_result = {
        "ok": True,
        "status": "executed",
        "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        "gate_replay": {"status": "blocked", "blockers": ["claim_evidence_consistency_failed"]},
        "unit_results": [{"unit_id": "materialize_display_surface", "status": "updated"}],
    }
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: gate_result,
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    record = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    assert result["source_summary_id"] == quality_summary["summary_id"]
    assert record["source_summary_artifact_path"] == str(quality_summary_path.resolve())


def test_run_quality_repair_batch_uses_specificity_targets_for_missing_publication_anchor_route(
    monkeypatch,
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
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0]["action_type"] = "return_to_controller"
    publication_eval_payload["recommended_actions"][0].pop("route_target", None)
    publication_eval_payload["recommended_actions"][0].pop("route_key_question", None)
    publication_eval_payload["recommended_actions"][0].pop("route_rationale", None)
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    publication_eval_payload["recommended_actions"][0]["work_unit_fingerprint"] = "publication-blockers::anchor"
    publication_eval_payload["recommended_actions"][0]["specificity_targets"] = [
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
            "target_id": "submission_manifest",
            "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
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
    _write_quality_summary(study_root)
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["missing_publication_anchor"],
        "anchor_kind": "missing",
        "paper_root": None,
        "main_result_path": None,
        "bundle_tasks_downstream_only": True,
        "gate_fingerprint": "publication-gate::anchor",
        "blocking_artifact_refs": [],
    }
    route_context = {
        "control_plane_snapshot": {
            "surface": "control_plane_snapshot",
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

    assert result["control_plane_route_gate"]["allowed"] is True
    assert result["control_plane_route_gate"]["action"] == "paper_write"
    assert result["control_plane_route_gate"]["controller_route_gate"]["work_unit_id"] == (
        "analysis_claim_evidence_repair"
    )
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


def test_run_quality_repair_batch_reruns_same_eval_after_failed_gate_clearing_batch(
    monkeypatch,
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
    _write_json(
        module.stable_quality_repair_batch_path(study_root=study_root),
        {
            "schema_version": 1,
            "source_eval_id": publication_eval_payload["eval_id"],
            "status": "executed",
            "ok": True,
            "gate_clearing_batch": {
                "schema_version": 1,
                "source_eval_id": publication_eval_payload["eval_id"],
                "status": "executed",
                "unit_results": [
                    {
                        "unit_id": "repair_paper_live_paths",
                        "status": "failed",
                        "error": "[Errno 2] No such file or directory: '/ABS/PATH/TO/ds'",
                    },
                    {
                        "unit_id": "create_submission_minimal_package",
                        "status": "skipped_failed_dependency",
                        "failed_dependencies": ["repair_paper_live_paths"],
                    },
                ],
                "gate_replay": {
                    "status": "blocked",
                    "blockers": [
                        "stale_submission_minimal_authority",
                        "submission_hardening_incomplete",
                    ],
                },
            },
        },
    )
    gate_result = {
        "ok": True,
        "status": "executed",
        "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        "gate_replay": {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
        },
        "unit_results": [{"unit_id": "create_submission_minimal_package", "status": "ready"}],
        "execution_summary": {
            "parallel_wave_count": 0,
            "parallel_unit_count": 0,
            "sequential_unit_count": 1,
            "skipped_dependency_unit_count": 0,
        },
    }
    seen: dict[str, object] = {}
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (seen.setdefault("kwargs", kwargs), gate_result)[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    assert seen["kwargs"]["study_id"] == "001-risk"
    assert result["status"] == "executed"
    assert result["gate_clearing_batch"]["gate_replay"]["status"] == "clear"


def test_study_outer_loop_executes_quality_repair_batch_controller_action(monkeypatch, tmp_path: Path) -> None:
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    runtime_protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "controller" / "study_charter.json",
        {
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        outer_loop.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "publication_quality_gap",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-22T08:00:00+00:00",
                "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
        },
    )
    monkeypatch.setattr(
        outer_loop,
        "_resolve_runtime_escalation_record",
        lambda **_: (
            runtime_protocol.RuntimeEscalationRecordRef(
                record_id="runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-22T08:00:00+00:00",
                artifact_path=str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            ),
            None,
        ),
    )
    monkeypatch.setattr(
        outer_loop.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **kwargs: (
            seen.setdefault("batch_kwargs", kwargs),
            {"ok": True, "status": "executed"},
        )[1],
    )

    result = outer_loop.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref={
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        publication_eval_ref={
            "eval_id": publication_eval_payload["eval_id"],
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        decision_type="route_back_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "run_quality_repair_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Quality repair batch should run before resuming the same paper line.",
        source="test-source",
        recorded_at="2026-04-22T08:02:00+00:00",
    )

    assert seen["batch_kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert result["executed_controller_action"]["action_type"] == "run_quality_repair_batch"
    assert result["executed_controller_action"]["result"] == {"ok": True, "status": "executed"}
