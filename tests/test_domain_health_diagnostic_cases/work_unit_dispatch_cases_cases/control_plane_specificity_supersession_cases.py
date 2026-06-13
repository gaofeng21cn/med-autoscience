from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared
from tests.test_domain_health_diagnostic_cases.work_unit_dispatch_cases_cases.control_plane_dispatch_shared import (
    _authority_snapshot,
)

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_control_plane_blocked_request_supersedes_stale_specificity_decision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    specificity_work_unit = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    specificity_publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        work_unit_fingerprint="publication-blockers::vague",
        next_work_unit=specificity_work_unit,
    )
    specificity_tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": specificity_publication_eval_ref,
        "decision_type": "return_to_controller",
        "route_target": "controller",
        "route_key_question": "gate_needs_specificity: Which exact claim is blocking the publication gate?",
        "route_rationale": "Publication gate needs concrete blocker targets before dispatch.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_gate_specificity",
                "payload_ref": str(
                    (study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()
                ),
            }
        ],
        "reason": "Publication gate needs concrete blocker targets before dispatch.",
        "work_unit_fingerprint": "publication-blockers::vague",
        "next_work_unit": specificity_work_unit,
    }
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
    }

    monkeypatch.setattr(
        module.study_outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda **_: specificity_tick_request,
    )
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    stale_decision = json.loads(
        (study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8")
    )
    assert stale_decision["next_work_unit"]["unit_id"] == "gate_needs_specificity"

    actionable_work_unit = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence blockers.",
    }
    actionable_publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="bounded_analysis",
        work_unit_fingerprint="publication-blockers::specific",
        next_work_unit=actionable_work_unit,
    )
    actionable_tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": actionable_publication_eval_ref,
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": "Run bounded claim-evidence repair.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_opl_stage_attempt",
                "payload_ref": str(
                    (study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()
                ),
            }
        ],
        "reason": "Run bounded claim-evidence repair.",
        "work_unit_fingerprint": "publication-blockers::specific",
        "next_work_unit": actionable_work_unit,
        "blocking_work_units": [actionable_work_unit],
    }
    blocked_status_payload = {
        **status_payload,
        "authority_snapshot": _authority_snapshot(
            state="blocked",
            blocking_reasons=["execution_owner_guard.supervisor_only"],
        ),
    }
    dispatch_calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        dispatch_calls.append(str(kwargs.get("source") or ""))
        return {"dispatch_status": "executed"}

    monkeypatch.setattr(
        module.study_outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda **_: actionable_tick_request,
    )
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: blocked_status_payload)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    current_decision = json.loads(
        (study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8")
    )
    wakeup_latest = json.loads(
        (
            study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
        ).read_text(encoding="utf-8")
    )

    assert dispatch_calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["outcome"] == "control_plane_dispatch_blocked"
    assert wakeup_latest["controller_decision"]["dispatch_status"] == "recorded_non_dispatching"
    assert current_decision["decision_type"] == "bounded_analysis"
    assert current_decision["work_unit_fingerprint"] == "publication-blockers::specific"
    assert current_decision["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
