from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _snapshot(
    *,
    paper_write_allowed: bool = True,
    bundle_build_allowed: bool = True,
) -> dict[str, Any]:
    return {
        "surface": "authority_snapshot",
        "control_state": "ready",
        "canonical_next_action": "continue_bundle_stage",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "runtime_health": {"epoch": "runtime-1"},
        },
        "dispatch_gate": {
            "state": "open",
            "blocking_reasons": [],
        },
        "route_authorization": {
            "authorized": paper_write_allowed and bundle_build_allowed,
            "paper_write_allowed": paper_write_allowed,
            "bundle_build_allowed": bundle_build_allowed,
            "runtime_recovery_allowed": True,
        },
    }


def _publication_gate_report(**overrides: Any) -> dict[str, Any]:
    report: dict[str, Any] = {
        "gate_kind": "publication",
        "paper_root": None,
        "status": "blocked",
        "allow_write": False,
        "blockers": [],
        "missing_non_scalar_deliverables": [],
        "submission_minimal_present": False,
        "draft_handoff_delivery_required": False,
        "draft_handoff_delivery_status": "not_required",
        "draft_handoff_delivery_manifest_path": None,
        "bundle_tasks_downstream_only": True,
        "supervisor_phase": "publishability_gate_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "current_required_action": "return_to_publishability_gate",
        "deferred_downstream_actions": [],
        "controller_stage_note": "blocked",
    }
    report.update(overrides)
    return report


def test_flat_progress_first_publication_gate_replay_route_context_is_explicit_without_snapshot() -> None:
    module = importlib.import_module("med_autoscience.controllers.authority_write_route")

    _route_context, gate = module.resolve_authority_write_route_context(
        action="delivery_sync",
        context={
            "control_surface": "gate_clearing_batch",
            "controller_action_type": "run_gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "requires_human_confirmation": False,
            "source_eval_id": "publication-eval::003-dpcc::latest",
        },
    )

    assert gate["authorized"] is True
    assert gate["controller_route_gate"]["authorized"] is True
    assert gate["controller_route_gate"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert gate["blocking_reasons"] == []


def test_publication_gate_apply_false_is_read_only_without_snapshot(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate.supervisor_and_cli")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    quest_root.mkdir(parents=True)
    report_path = quest_root / "publication_gate_report.json"
    markdown_path = quest_root / "publication_gate_report.md"

    monkeypatch.setattr(module, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        module,
        "build_gate_report",
        lambda state: _publication_gate_report(
            status="blocked",
            allow_write=False,
            blockers=["scientific_anchor_missing"],
            controller_stage_note="blocked",
        ),
    )
    monkeypatch.setattr(module, "write_gate_files", lambda quest_root, report: (report_path, markdown_path))

    result = module.run_controller(quest_root=quest_root, apply=False)

    assert result["status"] == "blocked"
    assert result["draft_handoff_delivery_sync"] is None
    assert result["study_delivery_stale_sync"] is None
    assert result["journal_package_sync"] is None


def test_publication_gate_apply_true_passes_same_route_context_to_downstream_writes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate.supervisor_and_cli")
    route_context = {"authority_snapshot": _snapshot(bundle_build_allowed=True)}
    paper_root = tmp_path / "study" / "paper"
    study_root = tmp_path / "study"
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    quest_root.mkdir(parents=True)
    report_path = quest_root / "publication_gate_report.json"
    markdown_path = quest_root / "publication_gate_report.md"
    seen: dict[str, Any] = {}
    freshness_calls: list[dict[str, Any]] = []

    class State:
        pass

    state = State()
    state.paper_root = paper_root
    state.quest_root = quest_root
    state.runtime_state = {}

    def build_report(_state: object) -> dict[str, Any]:
        return _publication_gate_report(
            paper_root=str(paper_root),
            status="blocked",
            allow_write=True,
            blockers=[],
            submission_minimal_present=True,
            study_delivery_status="stale_manifest_source_changed",
            study_delivery_stale_reason="delivery_manifest_source_changed",
            study_delivery_missing_source_paths=[],
            primary_journal_target={
                "journal_slug": "journal-a",
                "publication_profile": "general_medical_journal",
            },
            journal_requirements_status="resolved",
            journal_package_status="missing",
            journal_requirements_study_root=str(study_root),
            bundle_tasks_downstream_only=False,
            supervisor_phase="bundle_stage_ready",
            current_required_action="continue_bundle_stage",
            controller_stage_note="ready",
        )

    monkeypatch.setattr(module, "build_gate_state", lambda quest_root: state)
    monkeypatch.setattr(module, "build_gate_report", build_report)
    monkeypatch.setattr(module, "write_gate_files", lambda quest_root, report: (report_path, markdown_path))
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        lambda **kwargs: seen.setdefault("delivery_context", kwargs["authority_route_context"]) or {"status": "synced"},
    )
    monkeypatch.setattr(
        module.journal_package_controller,
        "materialize_journal_package",
        lambda **kwargs: seen.setdefault("journal_context", kwargs["authority_route_context"])
        or {"status": "materialized"},
    )
    monkeypatch.setattr(module, "_materialize_publication_eval_latest", lambda **kwargs: None)

    module.run_controller(
        quest_root=quest_root,
        apply=True,
        enqueue_intervention=False,
        authority_route_context=route_context,
    )

    assert seen["delivery_context"] is route_context
    assert seen["journal_context"] is route_context


def test_publication_gate_apply_does_not_run_delivery_sync_with_upstream_repair_route(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate.supervisor_and_cli")
    route_context = {
        "controller_route_context": {
            "control_surface": "gate_clearing_batch",
            "controller_action_type": "run_gate_clearing_batch",
            "work_unit_id": "analysis_claim_evidence_repair",
            "requires_human_confirmation": False,
            "source_eval_id": "publication-eval::002::latest",
            "gate_fingerprint": "publication-gate::002",
            "work_unit_fingerprint": "publication-blockers::002",
        },
    }
    paper_root = tmp_path / "study" / "paper"
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    quest_root.mkdir(parents=True)
    report_path = quest_root / "publication_gate_report.json"
    markdown_path = quest_root / "publication_gate_report.md"

    class State:
        pass

    state = State()
    state.paper_root = paper_root
    state.quest_root = quest_root
    state.runtime_state = {}

    def build_report(_state: object) -> dict[str, Any]:
        return _publication_gate_report(
            paper_root=str(paper_root),
            status="blocked",
            allow_write=False,
            blockers=[
                "stale_study_delivery_mirror",
                "claim_evidence_consistency_failed",
            ],
            submission_minimal_present=True,
            study_delivery_status="stale_source_changed",
            study_delivery_stale_reason="delivery_manifest_source_changed",
            study_delivery_missing_source_paths=[],
            controller_stage_note="route back to analysis before delivery sync",
        )

    monkeypatch.setattr(module, "build_gate_state", lambda quest_root: state)
    monkeypatch.setattr(module, "build_gate_report", build_report)
    monkeypatch.setattr(module, "write_gate_files", lambda quest_root, report: (report_path, markdown_path))
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("upstream route must not sync delivery")),
    )
    monkeypatch.setattr(module, "_materialize_publication_eval_latest", lambda **kwargs: None)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
        enqueue_intervention=False,
        authority_route_context=route_context,
    )

    stale_sync = result["study_delivery_stale_sync"]
    assert stale_sync["status"] == "skipped_controller_route_not_delivery_authorized"
    assert stale_sync["authority_route_gate"]["authorized"] is False
    assert stale_sync["authority_route_gate"]["controller_route_gate"]["work_unit_id"] == (
        "analysis_claim_evidence_repair"
    )
    assert "controller_route_action_not_allowed_for_work_unit" in stale_sync["authority_route_gate"]["blocking_reasons"]


def test_publication_gate_apply_derives_delivery_sync_controller_route_when_snapshot_absent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate.supervisor_and_cli")
    paper_root = tmp_path / "study" / "paper"
    study_root = tmp_path / "study"
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    quest_root.mkdir(parents=True)
    report_path = quest_root / "publication_gate_report.json"
    markdown_path = quest_root / "publication_gate_report.md"
    seen: dict[str, Any] = {}
    freshness_calls: list[dict[str, Any]] = []

    class State:
        pass

    state = State()
    state.paper_root = paper_root
    state.quest_root = quest_root
    state.study_root = study_root
    state.runtime_state = {}
    state.submission_minimal_manifest = {"publication_profile": "general_medical_journal"}

    def build_report(_state: object) -> dict[str, Any]:
        return _publication_gate_report(
            paper_root=str(paper_root),
            status="blocked",
            allow_write=False,
            blockers=["stale_study_delivery_mirror"],
            submission_minimal_present=True,
            study_delivery_status="stale_source_changed",
            study_delivery_stale_reason="delivery_manifest_source_changed",
            study_delivery_missing_source_paths=[],
            submission_minimal_authority_status="current",
            submission_minimal_evaluated_source_signature="source::abc",
            submission_minimal_authority_source_signature="source::abc",
            gate_fingerprint="publication-gate::001",
            work_unit_fingerprint="publication-blockers::001",
            bundle_tasks_downstream_only=False,
            supervisor_phase="bundle_stage_blocked",
            current_required_action="complete_bundle_stage",
            controller_stage_note="bundle-stage blockers are now on the critical path",
        )

    monkeypatch.setattr(module, "build_gate_state", lambda quest_root: state)
    monkeypatch.setattr(module, "build_gate_report", build_report)
    monkeypatch.setattr(module, "write_gate_files", lambda quest_root, report: (report_path, markdown_path))
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda paper_root: True)

    def sync_study_delivery(**kwargs: Any) -> dict[str, str]:
        seen["delivery_context"] = kwargs["authority_route_context"]
        return {
            "status": "synced",
            "source_signature": "source::abc",
            "authority_source_signature": "source::abc",
            "current_package_root": str(study_root / "manuscript" / "current_package"),
            "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
            "submission_manifest_path": str(paper_root / "submission_minimal" / "submission_manifest.json"),
            "delivery_manifest_path": str(study_root / "manuscript" / "delivery_manifest.json"),
        }

    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        sync_study_delivery,
    )
    monkeypatch.setattr(
        module.gate_clearing_batch_package_freshness,
        "write_current_package_freshness_proof",
        lambda **kwargs: freshness_calls.append(kwargs) or {"status": "fresh"},
    )
    monkeypatch.setattr(module, "_materialize_publication_eval_latest", lambda **kwargs: None)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
        enqueue_intervention=False,
    )

    delivery_context = seen["delivery_context"]
    assert result["study_delivery_stale_sync"]["status"] == "synced"
    assert delivery_context["controller_route_context"]["work_unit_id"] == "publication_gate_replay"
    assert delivery_context["controller_route_context"]["controller_action_type"] == "run_gate_clearing_batch"
    assert delivery_context["controller_route_context"]["control_surface"] == "gate_clearing_batch"
    assert delivery_context["controller_route_context"]["source_eval_id"] is None
    assert len(freshness_calls) == 1
    assert freshness_calls[0]["study_root"] == study_root
    assert freshness_calls[0]["unit_results"] == [
        {
            "unit_id": "sync_submission_minimal_delivery",
            "status": "synced",
            "result": result["study_delivery_stale_sync"],
        }
    ]


def test_quality_repair_batch_derives_route_context_from_runtime_status(
    monkeypatch: pytest.MonkeyPatch,
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
    _write_json(
        profile.runtime_root / quest_id / "quest.yaml",
        {"quest_id": quest_id, "study_id": study_root.name},
    )
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_root.name}::{quest_id}::2026-04-22T08:00:00+00:00",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-22T08:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "risk stratification validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Generated delivery mirror is stale.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "delivery mirror is stale",
                "evidence_refs": [str(study_root / "paper")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::quality-repair::2026-04-22T08:00:00+00:00",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Refresh generated delivery mirror through controller-owned surfaces.",
                "route_target": "review",
                "route_key_question": "Which deterministic publication-surface repair is still blocking?",
                "route_rationale": "Package freshness must be repaired before publication gate replay.",
                "evidence_refs": [str(study_root / "paper")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": f"evaluation-summary::{study_root.name}::2026-04-22T08:01:00+00:00",
            "quality_closure_truth": {"state": "quality_repair_required"},
            "quality_execution_lane": {"lane_id": "general_quality_repair"},
        },
    )
    route_context = {"authority_snapshot": _snapshot(bundle_build_allowed=True)}
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **kwargs: {
            "study_id": kwargs["study_id"],
            "study_root": str(kwargs["study_root"]),
            "quest_id": quest_id,
            **route_context,
        },
    )
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

    assert seen["gate_context"] == route_context
    assert result["authority_route_gate"]["allowed"] is True
    assert result["authority_route_gate"]["snapshot_ref"]["surface"] == "authority_snapshot"


def test_quality_repair_batch_uses_paper_route_for_upstream_repair_under_downstream_bundle_gate(
    monkeypatch: pytest.MonkeyPatch,
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
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::latest",
            "study_id": study_root.name,
            "quest_id": quest_id,
            "emitted_at": "2026-04-22T08:00:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": f"charter::{study_root.name}::v1",
                "publication_objective": "risk stratification validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"),
                "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "Claim evidence repair is still required.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-claim-evidence",
                    "gap_type": "reporting",
                    "severity": "must_fix",
                    "summary": "claim_evidence_consistency_failed",
                    "evidence_refs": [str(study_root / "paper")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::quality-repair::latest",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Repair claim-evidence blockers through controller-owned surfaces.",
                    "route_target": "analysis-campaign",
                    "route_key_question": "Which deterministic claim-evidence repair is still blocking?",
                    "route_rationale": "Run deterministic repair units, then replay the publishability gate.",
                    "evidence_refs": [str(study_root / "paper")],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::latest",
            "quality_closure_truth": {"state": "quality_repair_required"},
            "quality_execution_lane": {"lane_id": "general_quality_repair"},
        },
    )
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
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
        }
    }
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_map_missing_or_incomplete"],
        "bundle_tasks_downstream_only": True,
    }
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **kwargs: {
            "study_id": kwargs["study_id"],
            "study_root": str(kwargs["study_root"]),
            "quest_id": quest_id,
            **route_context,
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda quest_root: object(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda gate_state: gate_report,
    )
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
    assert result["authority_route_gate"]["blocking_reasons"] == []
    assert seen["gate_context"]["controller_route_context"]["work_unit_id"] == "analysis_claim_evidence_repair"


def test_quality_repair_batch_uses_runtime_authorization_for_submission_refresh_under_supervisor_gate(
    monkeypatch: pytest.MonkeyPatch,
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
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::003-dpcc::quest-003::latest",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-22T08:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "primary care phenotype treatment gap",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Submission package authority refresh is still required.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-submission-refresh",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "stale_submission_minimal_authority",
                "evidence_refs": [str(study_root / "paper" / "submission_minimal")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::submission-refresh::latest",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Refresh generated submission surfaces through controller-owned work unit.",
                "route_target": "finalize",
                "route_key_question": "Which submission package authority surface is stale?",
                "route_rationale": "The same study line needs deterministic submission package refresh.",
                "evidence_refs": [str(study_root / "paper" / "submission_minimal")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::003-dpcc::latest",
            "quality_closure_truth": {"state": "quality_repair_required"},
            "quality_execution_lane": {"lane_id": "general_quality_repair"},
        },
    )
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["stale_submission_minimal_authority", "submission_hardening_incomplete"],
        "gate_fingerprint": "publication-gate::003",
        "bundle_tasks_downstream_only": False,
    }
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
                "blocking_reasons": [
                    "execution_owner_guard.supervisor_only",
                    "live_worker_meaningful_artifact_delta_timeout",
                    "same_fingerprint_loop",
                ],
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": False,
            },
        },
        "last_controller_decision_authorization": {
            "source": "paper_mission_owner_surface_opl_runtime_handoff",
            "decision_id": "decision-003-current",
            "work_unit_id": "submission_minimal_refresh",
            "work_unit_fingerprint": "publication-blockers::current",
            "next_work_unit": {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh the stale submission_minimal package.",
            },
        },
    }
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
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
    assert result["authority_route_gate"]["action"] == "bundle_build"
    assert result["authority_route_gate"]["controller_route_gate"]["work_unit_id"] == (
        "submission_minimal_refresh"
    )
    gate_context = seen["gate_context"]
    assert isinstance(gate_context, dict)
    assert gate_context["controller_route_context"] == {
        "control_surface": "quality_repair_batch",
        "controller_action_type": "run_quality_repair_batch",
        "work_unit_id": "submission_minimal_refresh",
        "requires_human_confirmation": False,
        "source_eval_id": publication_eval_payload["eval_id"],
        "work_unit_fingerprint": "publication-blockers::current",
    }
