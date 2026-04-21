from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_runtime_escalation_record(module: object, quest_root: Path, study_root: Path) -> dict[str, str]:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    record = protocol.RuntimeEscalationRecord(
        schema_version=1,
        record_id="runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T05:55:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T05:55:00+00:00",
        trigger=protocol.RuntimeEscalationTrigger(
            trigger_id="startup_boundary_not_ready_for_resume",
            source="startup_boundary_gate",
        ),
        scope="quest",
        severity="quest",
        reason="startup_boundary_not_ready_for_resume",
        recommended_actions=("refresh_startup_hydration", "controller_review_required"),
        evidence_refs=(str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),),
        runtime_context_refs={"launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json")},
        summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
    )
    return protocol.write_runtime_escalation_record(quest_root=quest_root, record=record).ref().to_dict()


def _write_runtime_event_record(
    quest_root: Path,
    study_root: Path,
    *,
    quest_id: str = "quest-001",
    quest_status: str = "paused",
    decision: str = "blocked",
    reason: str = "startup_boundary_not_ready_for_resume",
    active_run_id: str | None = None,
    runtime_liveness_status: str | None = "none",
    worker_running: bool | None = False,
    supervisor_tick_status: str | None = "fresh",
    runtime_escalation_ref: dict[str, str] | None = None,
) -> dict[str, str]:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    record = protocol.RuntimeEventRecord(
        schema_version=1,
        event_id=f"runtime-event::001-risk::{quest_id}::status_observed::2026-04-05T05:56:00+00:00",
        study_id="001-risk",
        quest_id=quest_id,
        emitted_at="2026-04-05T05:56:00+00:00",
        event_source="study_runtime_status",
        event_kind="status_observed",
        summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        status_snapshot={
            "quest_status": quest_status,
            "decision": decision,
            "reason": reason,
            "active_run_id": active_run_id,
            "runtime_liveness_status": runtime_liveness_status,
            "worker_running": worker_running,
            "continuation_policy": None,
            "continuation_reason": None,
            "supervisor_tick_status": supervisor_tick_status,
            "controller_owned_finalize_parking": False,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
        outer_loop_input={
            "quest_status": quest_status,
            "decision": decision,
            "reason": reason,
            "active_run_id": active_run_id,
            "runtime_liveness_status": runtime_liveness_status,
            "worker_running": worker_running,
            "supervisor_tick_status": supervisor_tick_status,
            "controller_owned_finalize_parking": False,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    return protocol.write_runtime_event_record(quest_root=quest_root, record=record).ref().to_dict()


def _write_charter(study_root: Path) -> dict[str, str]:
    payload = {
        "charter_id": "charter::001-risk::v1",
        "publication_objective": "risk stratification external validation",
    }
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", payload)
    return {
        "charter_id": payload["charter_id"],
        "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
    }


def _write_publication_eval(study_root: Path, quest_root: Path) -> dict[str, str]:
    payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T05:58:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "summary": "Primary claim is ready to continue on the same line.",
            "stop_loss_pressure": "none",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "important",
                "summary": "External validation can still improve robustness.",
                "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "continue_same_line",
                "priority": "now",
                "reason": "Controller should continue the same study line.",
                "route_target": "write",
                "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
                "route_rationale": "The publication gate is clear and the current paper line can continue through same-line manuscript work.",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return {
        "eval_id": payload["eval_id"],
        "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }


def test_study_outer_loop_tick_writes_decision_record_and_executes_next_controller_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: (
            seen.setdefault("ensure_kwargs", kwargs),
            {
                "decision": "resume",
                "reason": "quest_paused",
            },
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Publication eval keeps the study on the same line.",
        source="test-source",
        recorded_at="2026-04-05T06:00:00+00:00",
    )

    assert seen["ensure_kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "force": False,
        "source": "test-source",
    }
    assert result["study_id"] == "001-risk"
    assert result["quest_id"] == "quest-001"
    assert result["runtime_status"] == {
        "decision": "blocked",
        "reason": "startup_boundary_not_ready_for_resume",
    }
    assert result["runtime_escalation_ref"] == runtime_escalation_ref
    assert result["controller_confirmation_summary_ref"] is None
    assert result["executed_controller_action"]["action_type"] == "ensure_study_runtime"
    assert result["executed_controller_action"]["result"] == {
        "decision": "resume",
        "reason": "quest_paused",
    }

    artifact_path = Path(result["study_decision_ref"]["artifact_path"])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    latest_payload = json.loads((artifact_path.parent / "latest.json").read_text(encoding="utf-8"))
    assert payload["charter_ref"] == charter_ref
    assert payload["publication_eval_ref"] == publication_eval_ref
    assert payload["runtime_escalation_ref"] == runtime_escalation_ref
    assert payload["decision_type"] == "continue_same_line"
    assert payload["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime",
            "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        }
    ]
    assert payload["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert payload["family_event_envelope"]["target_domain_id"] == "medautoscience"
    assert payload["family_event_envelope"]["session"]["study_id"] == "001-risk"
    assert payload["family_event_envelope"]["session"]["quest_id"] == "quest-001"
    assert payload["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert payload["family_checkpoint_lineage"]["producer"]["event_envelope_id"] == payload["family_event_envelope"]["envelope_id"]
    assert payload["family_human_gates"] == []
    assert latest_payload == payload
    assert not (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").exists()


def test_study_outer_loop_tick_fails_closed_when_managed_runtime_status_lacks_runtime_escalation_ref(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, profile.med_deepscientist_runtime_root / "quests" / "quest-001")

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "decision": "resume",
            "reason": "quest_paused",
        },
    )

    with pytest.raises(ValueError, match="runtime_escalation_ref"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval keeps the study on the same line.",
        )


def test_study_outer_loop_tick_reads_runtime_escalation_ref_from_runtime_event_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        runtime_escalation_ref=runtime_escalation_ref,
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
            "runtime_event_ref": runtime_event_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "decision": "resume",
            "reason": "quest_paused",
        },
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Publication eval keeps the study on the same line.",
    )

    assert result["runtime_escalation_ref"] == runtime_escalation_ref
    assert result["runtime_status"]["runtime_event_id"] == runtime_event_ref["event_id"]


def test_study_outer_loop_tick_falls_back_to_status_surface_when_runtime_event_ref_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "decision": "resume",
            "reason": "publication_quality_gap",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "decision": "resume",
            "reason": "quest_paused",
        },
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Publication eval keeps the study on the same line.",
    )

    assert result["runtime_escalation_ref"] == runtime_escalation_ref
    assert result["runtime_status"] == {
        "decision": "resume",
        "reason": "publication_quality_gap",
    }


def test_study_outer_loop_tick_fails_closed_when_runtime_event_quest_identity_mismatches_status(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        quest_id="quest-other",
        runtime_escalation_ref=runtime_escalation_ref,
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
            "runtime_event_ref": runtime_event_ref,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    with pytest.raises(ValueError, match="quest_id mismatch"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval keeps the study on the same line.",
        )


def test_study_outer_loop_tick_fails_closed_when_runtime_event_supervisor_tick_is_not_fresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        supervisor_tick_status="stale",
        runtime_escalation_ref=runtime_escalation_ref,
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
            },
            "runtime_event_ref": runtime_event_ref,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    with pytest.raises(ValueError, match="supervisor_tick_status"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval keeps the study on the same line.",
        )


def test_study_outer_loop_tick_rejects_publication_eval_ref_outside_eval_owned_latest_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    with pytest.raises(ValueError, match="eval-owned latest artifact"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref={
                "eval_id": "publication-eval::external-surface",
                "artifact_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval must stay on the eval-owned latest artifact surface.",
        )


def test_study_outer_loop_tick_fails_closed_when_runtime_escalation_artifact_mismatches_status_ref(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    runtime_escalation_ref["record_id"] = "runtime-escalation::mismatch"
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    with pytest.raises(ValueError, match="record_id mismatch"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=False,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="Publication eval keeps the study on the same line.",
        )


def test_study_outer_loop_tick_reexports_from_router(monkeypatch) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    sentinel = {"status": "delegated"}

    monkeypatch.setattr(outer_loop, "study_outer_loop_tick", lambda **kwargs: {**sentinel, **kwargs})

    result = router.study_outer_loop_tick(test_key="value")

    assert result == {"status": "delegated", "test_key": "value"}


def test_study_outer_loop_tick_blocks_dispatch_when_human_confirmation_is_required(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router.managed_runtime_transport,
        "stop_quest",
        lambda **kwargs: pytest.fail("stop_quest should not run before human confirmation"),
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="stop_loss",
        requires_human_confirmation=True,
        controller_actions=[
            {
                "action_type": "stop_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Controller requires human confirmation before stopping the quest.",
        source="test-source",
        recorded_at="2026-04-05T06:05:00+00:00",
    )

    assert result["dispatch_status"] == "pending_human_confirmation"
    assert result["executed_controller_action"] is None
    assert result["controller_confirmation_summary_ref"] == {
        "summary_id": "controller-confirmation::001-risk::study-decision::001-risk::quest-001::stop_loss::2026-04-05T06:05:00+00:00",
        "artifact_path": str(
            (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").resolve()
        ),
    }
    assert result["human_confirmation_request"] == {
        "category": "controller_decision_confirmation",
        "summary": "Controller requires human confirmation before stopping the quest.",
        "runtime_blockers": [
            {
                "decision": "blocked",
                "reason": "startup_boundary_not_ready_for_resume",
                "record_id": runtime_escalation_ref["record_id"],
                "summary_ref": runtime_escalation_ref["summary_ref"],
            }
        ],
        "publication_blockers": [
            {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Primary claim is ready to continue on the same line.",
                "gap_summaries": ["External validation can still improve robustness."],
            }
        ],
        "current_required_action": "human_confirmation_required",
        "controller_actions": [
            {
                "action_type": "stop_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "question_for_user": "Approve controller action `stop_runtime` for study `001-risk`?",
    }
    artifact_path = Path(result["study_decision_ref"]["artifact_path"])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["requires_human_confirmation"] is True
    assert payload["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        }
    ]
    assert payload["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert payload["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert payload["family_human_gates"][0]["version"] == "family-human-gate.v1"
    assert payload["family_human_gates"][0]["status"] == "requested"
    assert payload["family_human_gates"][0]["gate_kind"] == "controller_human_confirmation"
    assert payload["family_human_gates"][0]["decision_options"] == ["approve", "request_changes", "reject"]
    confirmation_payload = json.loads(
        (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").read_text(encoding="utf-8")
    )
    assert confirmation_payload["status"] == "pending"
    assert confirmation_payload["question_for_user"] == "请确认是否允许 MAS 停止当前研究运行。"
    assert confirmation_payload["next_action_if_approved"] == "停止当前研究运行"


def test_study_outer_loop_tick_rejects_human_gate_for_autonomous_scientific_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "publishability_gate_blocked",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: pytest.fail("ordinary scientific decisions must stay autonomous"),
    )

    with pytest.raises(ValueError, match="major direction pivots"):
        module.study_outer_loop_tick(
            profile=profile,
            study_id="001-risk",
            charter_ref=charter_ref,
            publication_eval_ref=publication_eval_ref,
            decision_type="continue_same_line",
            requires_human_confirmation=True,
            controller_actions=[
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            reason="MAS should autonomously decide whether to continue the current evidence repair line.",
            source="test-source",
            recorded_at="2026-04-05T06:06:00+00:00",
        )

    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").exists()


def test_study_outer_loop_tick_dispatches_explicit_stopped_relaunch_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "quest_status": "stopped",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: (
            seen.setdefault("ensure_kwargs", kwargs),
            {
                "decision": "relaunch_stopped",
                "reason": "quest_stopped_explicit_relaunch_requested",
                "quest_status": "active",
            },
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "ensure_study_runtime_relaunch_stopped",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Controller explicitly approved relaunch for a stopped quest.",
        source="test-source",
        recorded_at="2026-04-05T06:10:00+00:00",
    )

    assert seen["ensure_kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "force": False,
        "source": "test-source",
        "allow_stopped_relaunch": True,
    }
    assert result["executed_controller_action"]["action_type"] == "ensure_study_runtime_relaunch_stopped"
    assert result["executed_controller_action"]["result"] == {
        "decision": "relaunch_stopped",
        "reason": "quest_stopped_explicit_relaunch_requested",
        "quest_status": "active",
    }


def test_build_runtime_watch_outer_loop_tick_request_materializes_bounded_analysis(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "mixed",
                "primary_claim_status": "partial",
                "summary": "Primary line is stable and a bounded robustness analysis should run next.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "evidence",
                    "severity": "important",
                    "summary": "Robustness check is still missing.",
                    "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-000",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "Controller can review the current evidence posture.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                },
                {
                    "action_id": "action-001",
                    "action_type": "bounded_analysis",
                    "priority": "now",
                    "reason": "Run the bounded robustness analysis before the next publication gate pass.",
                    "route_target": "analysis-campaign",
                    "route_key_question": "What is the narrowest supplementary analysis still required before the paper line can continue?",
                    "route_rationale": "The current line is clear enough to continue after one bounded supplementary analysis pass.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "bounded_analysis"
    assert request["route_target"] == "analysis-campaign"
    assert request["route_key_question"] == "What is the narrowest supplementary analysis still required before the paper line can continue?"
    assert request["route_rationale"] == "The current line is clear enough to continue after one bounded supplementary analysis pass."
    assert request["requires_human_confirmation"] is False
    assert request["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime_relaunch_stopped",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


@pytest.mark.parametrize(
    ("status_reason", "expected_action_type"),
    [
        ("publication_quality_gap", "ensure_study_runtime"),
        ("quest_stopped_requires_explicit_rerun", "ensure_study_runtime_relaunch_stopped"),
    ],
)
def test_build_runtime_watch_outer_loop_tick_request_materializes_route_back_same_line(
    tmp_path: Path,
    status_reason: str,
    expected_action_type: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "partial",
                "summary": "The direction and claim boundary are stable, but ordinary paper quality gaps remain.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "important",
                    "summary": "The paper needs a same-line route-back to repair reporting quality.",
                    "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Route back to the same core route; direction and claim boundary are unchanged.",
                    "route_target": "write",
                    "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
                    "route_rationale": "The publication gate is clear and the current paper line can continue through same-line manuscript work.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "reason": status_reason,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "route_back_same_line"
    assert request["requires_human_confirmation"] is False
    assert request["controller_actions"] == [
        {
            "action_type": expected_action_type,
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_build_runtime_watch_outer_loop_tick_request_falls_back_to_quest_runtime_escalation_ref(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "partial",
                "summary": "The same-line paper route can continue.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "important",
                    "summary": "The paper needs same-line reporting repair.",
                    "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Route back to the same paper line.",
                    "route_target": "write",
                    "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
                    "route_rationale": "The publication gate is clear and the current paper line can continue through same-line manuscript work.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "reason": "publication_quality_gap",
        },
    )

    assert request is not None
    assert request["decision_type"] == "route_back_same_line"
    assert request["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_build_runtime_watch_outer_loop_tick_request_autoparks_ready_submission_milestone(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is ready and only bundle-stage cleanup remains.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "optional",
                    "summary": "Only optional submission-bundle cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical question is already publication-ready.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Clinical framing is stable.",
                    "reviewer_revision_advice": "Only minor bundle cleanup remains.",
                    "reviewer_next_round_focus": "Keep the clinician-facing framing consistent across surfaces.",
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence chain is already closed.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Evidence posture is stable.",
                    "reviewer_revision_advice": "Only refresh delivery surfaces if needed.",
                    "reviewer_next_round_focus": "Keep evidence references synchronized across package surfaces.",
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Contribution boundary is already explicit.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Novelty framing is fixed.",
                    "reviewer_revision_advice": "Do not expand the claim boundary.",
                    "reviewer_next_round_focus": "Keep contribution wording aligned with the frozen charter.",
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "The human-facing current package is ready for review.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "The review package is synchronized.",
                    "reviewer_revision_advice": "Only keep bundle surfaces aligned.",
                    "reviewer_next_round_focus": "Double-check package surface consistency before submission.",
                },
            },
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only finalize-level bundle cleanup remains on the current paper line.",
                    "route_target": "finalize",
                    "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
                    "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-05T06:00:00+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
                "summary": "Only finalize-level submission hardening remains.",
            },
            "quality_review_loop": {
                "policy_id": "medical_publication_critique_v1",
                "loop_id": "quality-review-loop::001-risk::2026-04-05T06:00:00+00:00",
                "closure_state": "bundle_only_remaining",
                "lane_id": "submission_hardening",
                "current_phase": "bundle_hardening",
                "current_phase_label": "投稿包收口",
                "recommended_next_phase": "finalize",
                "recommended_next_phase_label": "定稿与投稿收尾",
                "active_plan_id": "quality-plan::001-risk::v1",
                "active_plan_execution_status": "planned",
                "blocking_issue_count": 1,
                "blocking_issues": ["Only finalize-level cleanup remains."],
                "next_review_focus": ["What is the narrowest finalize or submission-bundle step still required on the current paper line?"],
                "re_review_ready": False,
                "summary": "Core scientific quality is closed; only finalize-level bundle cleanup remains.",
                "recommended_next_action": "Return to finalize only if the runtime is explicitly resumed later.",
            },
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "run-001",
            "reason": "quest_already_running",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "finalize"
    assert request["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_build_runtime_watch_outer_loop_tick_request_autoparks_without_runtime_escalation_ref(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is ready and only bundle-stage cleanup remains.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "optional",
                    "summary": "Only optional submission-bundle cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical question is already publication-ready.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Clinical framing is stable.",
                    "reviewer_revision_advice": "Only minor bundle cleanup remains.",
                    "reviewer_next_round_focus": "Keep the clinician-facing framing consistent across surfaces.",
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence chain is already closed.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Evidence posture is stable.",
                    "reviewer_revision_advice": "Only refresh delivery surfaces if needed.",
                    "reviewer_next_round_focus": "Keep evidence references synchronized across package surfaces.",
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Contribution boundary is already explicit.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Novelty framing is fixed.",
                    "reviewer_revision_advice": "Do not expand the claim boundary.",
                    "reviewer_next_round_focus": "Keep contribution wording aligned with the frozen charter.",
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "The human-facing current package is ready for review.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "The review package is synchronized.",
                    "reviewer_revision_advice": "Only keep bundle surfaces aligned.",
                    "reviewer_next_round_focus": "Double-check package surface consistency before submission.",
                },
            },
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only finalize-level bundle cleanup remains on the current paper line.",
                    "route_target": "finalize",
                    "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
                    "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-05T06:00:00+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
                "summary": "Only finalize-level submission hardening remains.",
            },
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "run-001",
            "reason": "quest_already_running",
        },
    )

    assert request is not None
    assert request["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_build_runtime_watch_outer_loop_tick_request_prefers_quality_review_loop_re_review(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "partial",
                "summary": "Publication eval itself still reflects the pre-re-review state.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "important",
                    "summary": "A previous reporting gap existed.",
                    "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Older publication eval would still route back to write.",
                    "route_target": "write",
                    "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
                    "route_rationale": "This is the stale pre-re-review route.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-05T06:00:00+00:00",
            "overall_verdict": "promising",
            "primary_claim_status": "partial",
            "stop_loss_pressure": "none",
            "verdict_summary": "Revision is complete and MAS should re-review.",
            "requires_controller_decision": True,
            "quality_review_loop": {
                "policy_id": "publication-critique.v1",
                "loop_id": "quality-review-loop::001-risk::2026-04-05T06:00:00+00:00",
                "closure_state": "quality_repair_required",
                "lane_id": "general_quality_repair",
                "current_phase": "re_review_required",
                "current_phase_label": "等待复评",
                "recommended_next_phase": "re_review",
                "recommended_next_phase_label": "发起复评",
                "active_plan_id": "quality-plan::001-risk::v1",
                "active_plan_execution_status": "completed",
                "blocking_issue_count": 1,
                "blocking_issues": ["外部验证结果与主结论是否真正闭环"],
                "next_review_focus": ["外部验证结果与主结论是否真正闭环"],
                "re_review_ready": True,
                "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                "recommended_next_action": "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。",
            },
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "review"
    assert request["route_key_question"] == "外部验证结果与主结论是否真正闭环"
    assert request["route_rationale"] == "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。"
    assert request["reason"] == "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。"
    assert request["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime_relaunch_stopped",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_study_outer_loop_tick_dispatches_pause_runtime_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router.managed_runtime_transport,
        "pause_quest",
        lambda **kwargs: (
            seen.setdefault("pause_kwargs", kwargs),
            {"ok": True, "quest_id": "quest-001", "status": "paused", "snapshot": {"status": "paused"}},
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "pause_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Pause the current runtime before further controller review.",
        source="test-source",
        recorded_at="2026-04-05T06:10:00+00:00",
    )

    assert seen["pause_kwargs"] == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert module.study_runtime_router.managed_runtime_transport is module.study_runtime_router.med_deepscientist_transport
    assert result["dispatch_status"] == "executed"
    assert result["executed_controller_action"]["action_type"] == "pause_runtime"
    assert result["executed_controller_action"]["result"]["status"] == "paused"


def test_study_outer_loop_tick_dispatches_stop_runtime_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router.managed_runtime_transport,
        "stop_quest",
        lambda **kwargs: (
            seen.setdefault("stop_kwargs", kwargs),
            {"ok": True, "quest_id": "quest-001", "status": "stopped", "snapshot": {"status": "stopped"}},
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="stop_loss",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "stop_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Stop the current runtime under the formal stop contract.",
        source="test-source",
        recorded_at="2026-04-05T06:12:00+00:00",
    )

    assert seen["stop_kwargs"] == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert module.study_runtime_router.managed_runtime_transport is module.study_runtime_router.med_deepscientist_transport
    assert result["dispatch_status"] == "executed"
    assert result["executed_controller_action"]["action_type"] == "stop_runtime"
    assert result["executed_controller_action"]["result"]["status"] == "stopped"


def test_study_outer_loop_tick_materializes_runtime_escalation_ref_before_stop_runtime(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        {
            "recorded_at": "2026-04-05T06:10:00+00:00",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "decision": "noop",
            "reason": "quest_already_running",
            "execution": {
                "quest_id": "quest-001",
                "runtime_backend": "med_deepscientist",
                "entry_mode": "full_research",
                "auto_entry": "on_managed_research_intent",
            },
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router.managed_runtime_transport,
        "stop_quest",
        lambda **kwargs: (
            seen.setdefault("stop_kwargs", kwargs),
            {"ok": True, "quest_id": "quest-001", "status": "stopped", "snapshot": {"status": "stopped"}},
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "stop_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Human-review milestone reached; stop the live runtime and wait for explicit resume.",
        source="runtime_watch_outer_loop_wakeup",
        recorded_at="2026-04-05T06:12:00+00:00",
    )

    assert result["dispatch_status"] == "executed"
    assert result["executed_controller_action"]["action_type"] == "stop_runtime"
    runtime_escalation_ref = result["runtime_escalation_ref"]
    assert runtime_escalation_ref["record_id"] == (
        "runtime-escalation::001-risk::quest-001::quest_already_running::2026-04-05T06:12:00+00:00"
    )
    assert Path(runtime_escalation_ref["artifact_path"]).exists()
    assert seen["stop_kwargs"] == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "quest-001",
        "source": "runtime_watch_outer_loop_wakeup",
    }
