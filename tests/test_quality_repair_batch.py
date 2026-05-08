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
