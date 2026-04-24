from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

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
def test_runtime_watch_outer_loop_prefers_active_task_intake_analysis_over_gate_clearing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
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
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-22T13:19:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-22T13:19:00+00:00",
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
                "submission_minimal_ref": str(
                    study_root / "paper" / "submission_minimal" / "submission_manifest.json"
                ),
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "Return to finalize to close submission-readiness gaps.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_submission_minimal_authority",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-finalize",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Return to finalize.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "Return to finalize.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "当前稿件不能按已达投稿包里程碑直接收口；必须补做分层统计分析，"
            "并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        evidence_boundary=("统计扩展限于预设 subgroup / association analysis。",),
        first_cycle_outputs=("价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。",),
    )
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)

    def fail_batch_recommendation(**_: object) -> None:
        raise AssertionError("gate-clearing batch should not preempt active task-intake bounded analysis")

    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        fail_batch_recommendation,
    )
    monkeypatch.setattr(
        module.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        fail_batch_recommendation,
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "reason": "publication_quality_gap",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "bounded_analysis"
    assert request["route_target"] == "analysis-campaign"
    assert request["route_key_question"] == "价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。"
    assert request["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
def test_runtime_watch_outer_loop_routes_deterministic_closeout_before_stale_task_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
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
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-22T23:53:24+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-22T23:53:24+00:00",
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
                "paper_root_ref": str(quest_root / ".ds" / "worktrees" / "paper-run" / "paper"),
                "submission_minimal_ref": str(
                    quest_root / ".ds" / "worktrees" / "paper-run" / "paper" / "submission_minimal" / "submission_manifest.json"
                ),
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "Only deterministic submission closeout remains.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_submission_minimal_authority",
                    "evidence_refs": [str(publication_eval_path)],
                },
                {
                    "gap_id": "gap-002",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_study_delivery_mirror",
                    "evidence_refs": [str(publication_eval_path)],
                },
                {
                    "gap_id": "gap-003",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "submission_surface_qc_failure_present",
                    "evidence_refs": [str(publication_eval_path)],
                },
            ],
            "recommended_actions": [
                {
                    "action_id": "action-return",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "Clear deterministic submission closeout blockers.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "当前稿件不能按已达投稿包里程碑直接收口；必须补做分层统计分析，"
            "并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        evidence_boundary=("统计扩展限于预设 subgroup / association analysis。",),
        first_cycle_outputs=("价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。",),
    )
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "return_to_publishability_gate",
        "paper_line_open_supplementary_count": 0,
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_current": True,
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        module.publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": quest_root / ".ds" / "worktrees" / "paper-run" / "paper"})(),
    )
    monkeypatch.setattr(module.publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        lambda **_: {
            "action_id": "gate-closeout",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Run deterministic closeout batch.",
            "route_target": "finalize",
            "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
            "route_rationale": "Only submission package authority, mirror, and QC blockers remain.",
            "requires_controller_decision": True,
            "controller_action_type": "run_gate_clearing_batch",
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "reason": "publication_quality_gap",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "route_back_same_line"
    assert request["route_target"] == "finalize"
    assert request["controller_actions"] == [
        {
            "action_type": "run_gate_clearing_batch",
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
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
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
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
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
                "next_review_focus": ["当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"],
                "re_review_ready": False,
                "summary": "Core scientific quality is closed; only finalize-level bundle cleanup remains.",
                "recommended_next_action": "Return to finalize only if the runtime is explicitly resumed later.",
            },
        },
    )
    runtime_event_path = quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json"
    _write_json(
        runtime_event_path,
        {
            "schema_version": 1,
            "event_id": "quest-runtime::quest-001::runtime_state_observed::2026-04-05T05:59:00+00:00",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:59:00+00:00",
            "event_source": "quest_runtime_state",
            "event_kind": "runtime_state_observed",
            "summary_ref": "quest-runtime::quest-001::runtime_state_observed::2026-04-05T05:59:00+00:00",
            "status_snapshot": {
                "quest_status": "running",
                "display_status": "running",
                "active_run_id": "run-001",
                "runtime_liveness_status": "live",
                "worker_running": True,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_reason": "unchanged_finalize_state",
            },
            "outer_loop_input": {
                "quest_status": "running",
                "display_status": "running",
                "active_run_id": "run-001",
                "runtime_liveness_status": "live",
                "worker_running": True,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_reason": "unchanged_finalize_state",
            },
            "artifact_path": str(runtime_event_path),
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
