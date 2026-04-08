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
    assert latest_payload == payload


def test_study_outer_loop_tick_fails_closed_without_runtime_escalation_ref(monkeypatch, tmp_path: Path) -> None:
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
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
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
        module.study_runtime_router.med_deepscientist_transport,
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
    artifact_path = Path(result["study_decision_ref"]["artifact_path"])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["requires_human_confirmation"] is True
    assert payload["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
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
        module.study_runtime_router.med_deepscientist_transport,
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
        module.study_runtime_router.med_deepscientist_transport,
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
    assert result["dispatch_status"] == "executed"
    assert result["executed_controller_action"]["action_type"] == "stop_runtime"
    assert result["executed_controller_action"]["result"]["status"] == "stopped"
