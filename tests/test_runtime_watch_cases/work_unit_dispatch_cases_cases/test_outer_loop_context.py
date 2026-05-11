from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_outer_loop_tick_request_carries_publication_work_unit_context(tmp_path: Path) -> None:
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    _write_publication_eval(
        study_root,
        quest_root,
        action_type="bounded_analysis",
        work_unit_fingerprint="publication-blockers::same",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
        },
    )

    request = outer_loop.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="blocked",
                reason="study_completion_publishability_gate_blocked",
            ),
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
        },
    )

    assert request is not None
    assert request["work_unit_fingerprint"] == "publication-blockers::same"
    assert request["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert request["blocking_work_units"][0]["unit_id"] == "analysis_claim_evidence_repair"


def test_outer_loop_tick_request_carries_gate_specificity_controller_request(tmp_path: Path) -> None:
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        reason="Publication gate needs concrete blocker targets before dispatch.",
        work_unit_fingerprint="publication-blockers::vague",
        next_work_unit={
            "unit_id": "gate_needs_specificity",
            "lane": "controller",
            "summary": "Ask the publication gate to identify concrete blocker targets.",
        },
    )

    request = outer_loop.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="blocked",
                reason="study_completion_publishability_gate_blocked",
            ),
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
        },
    )

    assert request is not None
    assert request["decision_type"] == "return_to_controller"
    assert request["route_target"] == "controller"
    assert request["controller_actions"] == [
        {
            "action_type": "request_gate_specificity",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    assert request["work_unit_fingerprint"] == "publication-blockers::vague"
    assert request["next_work_unit"]["unit_id"] == "gate_needs_specificity"


def test_outer_loop_tick_request_carries_gate_specificity_targets(tmp_path: Path) -> None:
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    targets = [
        {
            "target_kind": "claim",
            "target_id": "primary_claim",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "Primary claim needs a concrete evidence anchor.",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_2",
            "source_path": str(study_root / "paper" / "figures" / "figure_2.png"),
            "blocking_reason": "Figure 2 needs a concrete blocker reference.",
        },
        {
            "target_kind": "table",
            "target_id": "table_1",
            "source_path": str(study_root / "paper" / "tables" / "table_1.csv"),
            "blocking_reason": "Table 1 needs denominator provenance.",
        },
        {
            "target_kind": "metric",
            "target_id": "c_statistic",
            "source_path": str(study_root / "artifacts" / "results" / "model_performance.json"),
            "blocking_reason": "Metric needs a result source path.",
        },
        {
            "target_kind": "source_path",
            "target_id": "external_validation_dataset",
            "source_path": str(study_root / "artifacts" / "results" / "external_validation.json"),
            "blocking_reason": "External validation source path is missing.",
        },
    ]
    _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        reason="Publication gate named concrete blocker targets.",
        work_unit_fingerprint="publication-blockers::specific",
        next_work_unit={
            "unit_id": "gate_needs_specificity",
            "lane": "controller",
            "summary": "Concrete gate specificity targets are now available.",
        },
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))
    publication_eval["recommended_actions"][0]["specificity_targets"] = targets
    dump_json(publication_eval_path, publication_eval)

    request = outer_loop.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="blocked",
                reason="study_completion_publishability_gate_blocked",
            ),
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
        },
    )

    assert request is not None
    assert request["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert request["specificity_targets"] == targets
    assert request["controller_actions"] == [
        {
            "action_type": "request_gate_specificity",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_outer_loop_tick_request_backfills_targets_when_batch_action_promotes_specificity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    targets = [
        {
            "target_kind": "claim",
            "target_id": "primary_claim",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "Primary claim needs a concrete evidence anchor.",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_2",
            "source_path": str(study_root / "paper" / "figures" / "figure_2.png"),
            "blocking_reason": "Figure 2 needs a concrete blocker reference.",
        },
        {
            "target_kind": "table",
            "target_id": "table_1",
            "source_path": str(study_root / "paper" / "tables" / "table_1.csv"),
            "blocking_reason": "Table 1 needs denominator provenance.",
        },
        {
            "target_kind": "metric",
            "target_id": "c_statistic",
            "source_path": str(study_root / "artifacts" / "results" / "model_performance.json"),
            "blocking_reason": "Metric needs a result source path.",
        },
        {
            "target_kind": "source_path",
            "target_id": "external_validation_dataset",
            "source_path": str(study_root / "artifacts" / "results" / "external_validation.json"),
            "blocking_reason": "External validation source path is missing.",
        },
    ]
    _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        reason="Publication gate named concrete blocker targets.",
        work_unit_fingerprint="publication-blockers::specific",
        next_work_unit={
            "unit_id": "gate_needs_specificity",
            "lane": "controller",
            "summary": "Concrete gate specificity targets are now available.",
        },
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))
    publication_eval["verdict"]["overall_verdict"] = "blocked"
    publication_eval["recommended_actions"][0]["specificity_targets"] = targets
    dump_json(publication_eval_path, publication_eval)
    generic_work_unit = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
        "controller_work_unit_executable": False,
        "non_executable_reason": "gate_needs_specificity_without_targets",
        "required_target_kinds": [
            "claim",
            "display",
            "evidence_source",
            "citation",
            "metric",
            "package_artifact",
            "authorization_provenance",
        ],
    }

    monkeypatch.setattr(outer_loop.gate_clearing_batch, "resolve_profile_for_study_root", lambda _: profile)
    monkeypatch.setattr(
        outer_loop.publication_gate_controller,
        "build_gate_state",
        lambda _: {"status": "blocked"},
    )
    monkeypatch.setattr(
        outer_loop.publication_gate_controller,
        "build_gate_report",
        lambda _: {"status": "blocked", "blockers": ["claim_evidence_consistency_failed"]},
    )
    monkeypatch.setattr(outer_loop, "recommended_task_intake_action", lambda **_: None)
    monkeypatch.setattr(
        outer_loop.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        lambda **_: {
            "action_id": "quality-repair-batch::001-risk::latest",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Run one controller-owned quality repair batch.",
            "route_target": "review",
            "route_key_question": "Which deterministic quality repair is still blocking the gate?",
            "route_rationale": "Run deterministic quality repair units before replaying the gate.",
            "requires_controller_decision": True,
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_fingerprint": "publication-blockers::specific",
            "blocking_work_units": [generic_work_unit],
            "next_work_unit": generic_work_unit,
        },
    )

    request = outer_loop.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="blocked",
                reason="study_completion_publishability_gate_blocked",
            ),
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
        },
    )

    assert request is not None
    assert request["decision_type"] == "route_back_same_line"
    assert request["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert request["specificity_targets"] == targets
    assert "non_executable_reason" not in request["next_work_unit"]
    assert request["controller_actions"] == [
        {
            "action_type": "run_quality_repair_batch",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_matching_controller_decision_requires_same_work_unit_context(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_parts.managed_wakeup")
    study_root = tmp_path / "studies" / "001-risk"
    charter_ref = {
        "charter_id": "charter::001-risk::v1",
        "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
    }
    publication_eval_ref = {
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
        "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
    }
    controller_actions = [
        {
            "action_type": "ensure_study_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    next_work_unit = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence blockers.",
    }
    base_payload = {
        "schema_version": 1,
        "decision_id": "study-decision::001-risk::quest-001::bounded_analysis::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "decision_type": "bounded_analysis",
        "charter_ref": charter_ref,
        "runtime_escalation_ref": {
            "record_id": "runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T05:55:00+00:00",
            "artifact_path": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
            "summary_ref": "/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json",
        },
        "publication_eval_ref": publication_eval_ref,
        "requires_human_confirmation": False,
        "controller_actions": controller_actions,
        "reason": "Run deterministic gate repair.",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": (
            "Publication gate selected controller-owned work unit `analysis_claim_evidence_repair`."
        ),
    }
    tick_request = {
        "decision_type": "bounded_analysis",
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "requires_human_confirmation": False,
        "controller_actions": controller_actions,
        "reason": "Run deterministic gate repair.",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": (
            "Publication gate selected controller-owned work unit `analysis_claim_evidence_repair`."
        ),
        "source_route_key_question": "Broad reviewer revision checklist.",
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": next_work_unit,
        "blocking_work_units": [next_work_unit],
    }
    latest_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    dump_json(latest_path, base_payload)

    assert module._controller_decision_latest_matches_outer_loop_request(
        study_root=study_root,
        status_payload={},
        tick_request=tick_request,
    ) is False

    dump_json(
        latest_path,
        {
            **base_payload,
            "source_route_key_question": "Broad reviewer revision checklist.",
            "work_unit_fingerprint": "publication-blockers::same",
            "next_work_unit": next_work_unit,
            "blocking_work_units": [next_work_unit],
        },
    )

    assert module._controller_decision_latest_matches_outer_loop_request(
        study_root=study_root,
        status_payload={},
        tick_request=tick_request,
    ) is True
