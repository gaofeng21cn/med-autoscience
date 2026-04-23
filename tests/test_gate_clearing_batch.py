from __future__ import annotations

import importlib
import json
import threading
import time
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_blocked_publication_eval(study_root: Path, *, quest_id: str) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_root.name}::{quest_id}::2026-04-21T12:42:39+00:00",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-21T12:42:39+00:00",
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
            "summary": "Return to bounded analysis before write continues.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "medical_publication_surface_blocked",
                "evidence_refs": [str(study_root / "paper")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::bounded_analysis::2026-04-21T12:42:39+00:00",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Run the narrowest bounded analysis first.",
                "route_target": "analysis-campaign",
                "route_key_question": "当前论文线继续前还差哪一个最窄的补充分析？",
                "route_rationale": "The publication gate remains blocked.",
                "evidence_refs": [str(study_root / "paper")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return payload


def _write_bundle_stage_publication_eval(study_root: Path, *, quest_id: str) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_root.name}::{quest_id}::2026-04-22T01:05:42+00:00",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-22T01:05:42+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "bundle-stage publishability repair",
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
            "summary": "Bundle-stage blockers are on the critical path.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "delivery",
                "severity": "must_fix",
                "summary": "submission_surface_qc_failure_present",
                "evidence_refs": [str(study_root / "paper")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::2026-04-22T01:05:42+00:00",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Bundle-stage blockers should route back to the controller.",
                "evidence_refs": [str(study_root / "paper")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return payload


def _write_submission_minimal_fingerprint_inputs(paper_root: Path) -> None:
    _write_text(paper_root / "build" / "compiled_manuscript.md", "# Results\n\nStable content.\n")
    _write_text(paper_root / "build" / "compiled_paper.pdf", "%PDF-1.4\n")
    _write_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown_path": "paper/build/compiled_manuscript.md",
            "output_pdf": "paper/build/compiled_paper.pdf",
        },
    )
    _write_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    _write_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "compiled_markdown_path": "paper/build/compiled_manuscript.md",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
            "pdf_path": "paper/build/compiled_paper.pdf",
        },
    )


def test_submission_minimal_fingerprint_payload_ignores_materialized_submission_source_from_compile_report(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    submission_minimal_tests = importlib.import_module("tests.test_submission_minimal")
    paper_root = submission_minimal_tests.make_materialized_submission_source_workspace(tmp_path)
    profile = make_profile(tmp_path)

    payload = module._submission_minimal_fingerprint_payload(
        paper_root=paper_root,
        gate_report={
            "status": "blocked",
            "blockers": ["stale_submission_minimal_authority"],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
        profile=profile,
    )

    assert payload["compiled_markdown"]["path"] == str((paper_root / "draft.md").resolve())


def test_build_gate_clearing_batch_recommended_action_promotes_blocked_bounded_analysis(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    mapping_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "analysis-analysis-c7574291-freeze-scientific-anchor-and-gate-map"
        / "experiments"
        / "analysis"
        / "analysis-c7574291"
        / "freeze-scientific-anchor-and-gate-map"
        / "outputs"
        / "scientific_anchor_mapping.json"
    )
    _write_json(
        mapping_path,
        {
            "proposed_scientific_followup_questions": ["Q1"],
            "proposed_explanation_targets": ["T1"],
            "clinician_facing_interpretation_target": "Clinician-facing interpretation target.",
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "missing_medical_story_contract",
            "table_catalog_missing_or_incomplete",
        ],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert action["gate_clearing_batch_mapping_path"] == str(mapping_path)
    assert "scientific-anchor fields can be frozen" in action["gate_clearing_batch_reason"]

def test_build_gate_clearing_batch_recommended_action_promotes_bundle_stage_return_to_finalize(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Let MAS re-evaluate the finalize-stage blockers before the same paper line resumes.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    gate_report = {
        "status": "blocked",
        "blockers": [
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "complete_bundle_stage",
        "controller_stage_note": "Only finalize or submission-bundle repairs remain on the current paper line.",
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_named_blockers": [],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-004",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["action_type"] == "route_back_same_line"
    assert action["route_target"] == "finalize"
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert "finalize/submission bundle blockers are deterministic same-line repair candidates" in action[
        "gate_clearing_batch_reason"
    ]


def test_run_gate_clearing_batch_executes_parallel_units_then_replays_gate(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-001" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "stale_study_delivery_mirror",
                "medical_publication_surface_blocked",
                "claim_evidence_consistency_failed",
            ],
            "medical_publication_surface_status": "blocked",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (
            paper_root / "scientific_anchor_mapping.json",
            {
                "proposed_scientific_followup_questions": ["Q1"],
                "proposed_explanation_targets": ["T1"],
                "clinician_facing_interpretation_target": "Clinician target.",
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_freeze_scientific_anchor_fields",
        lambda **_: {"status": "updated", "scientific_followup_question_count": 1},
    )
    monkeypatch.setattr(
        module,
        "_repair_paper_live_paths",
        lambda **_: {"ok": True, "status": "updated", "repaired_files": ["paper/claim_evidence_map.json"]},
    )
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda **_: {"status": "materialized", "tables_materialized": ["T1"]},
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    replay_kwargs: dict[str, Any] = {}

    def fake_run_controller(**kwargs: Any) -> dict[str, Any]:
        replay_kwargs.update(kwargs)
        return {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["claim_evidence_consistency_failed"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        }

    monkeypatch.setattr(module.publication_gate, "run_controller", fake_run_controller)

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "freeze_scientific_anchor_fields",
        "repair_paper_live_paths",
        "materialize_display_surface",
    ]
    assert result["gate_replay"]["status"] == "blocked"
    assert replay_kwargs["enqueue_intervention"] is False
    record = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert record["source_eval_id"] == publication_eval_payload["eval_id"]
    assert record["unit_results"][0]["unit_id"] == "freeze_scientific_anchor_fields"


def test_run_gate_clearing_batch_waits_for_live_path_repair_before_display_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-001" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_blocked_publication_eval(study_root, quest_id="quest-001")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "medical_publication_surface_blocked",
            ],
            "medical_publication_surface_status": "blocked",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (
            paper_root / "scientific_anchor_mapping.json",
            {
                "proposed_scientific_followup_questions": ["Q1"],
                "proposed_explanation_targets": ["T1"],
            },
        ),
    )
    freeze_started = threading.Event()
    repair_started = threading.Event()
    repair_done = threading.Event()
    overlap_seen: dict[str, bool] = {"value": False}

    def fake_freeze(**_: Any) -> dict[str, Any]:
        freeze_started.set()
        assert repair_started.wait(1), "freeze_scientific_anchor_fields should overlap with live-path repair"
        overlap_seen["value"] = not repair_done.is_set()
        return {"status": "updated"}

    def fake_repair(**_: Any) -> dict[str, Any]:
        repair_started.set()
        assert freeze_started.wait(1), "repair_paper_live_paths should overlap with anchor freeze"
        time.sleep(0.15)
        repair_done.set()
        return {"status": "updated"}

    def fake_materialize(**_: Any) -> dict[str, Any]:
        assert repair_done.is_set(), "display refresh must wait for live-path repair"
        return {"status": "materialized"}

    monkeypatch.setattr(module, "_freeze_scientific_anchor_fields", fake_freeze)
    monkeypatch.setattr(module, "_repair_paper_live_paths", fake_repair)
    monkeypatch.setattr(module, "_materialize_display_surface", fake_materialize)
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["medical_publication_surface_blocked"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    result_by_unit = {item["unit_id"]: item for item in result["unit_results"]}
    assert overlap_seen["value"] is True
    assert result_by_unit["freeze_scientific_anchor_fields"]["status"] == "updated"
    assert result_by_unit["repair_paper_live_paths"]["status"] == "updated"
    assert result_by_unit["materialize_display_surface"]["status"] == "materialized"

def test_run_gate_clearing_batch_executes_bundle_stage_submission_refresh_then_replays_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "submission_surface_qc_failure_present",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["submission_surface_qc_failure_present"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == ["create_submission_minimal_package"]
    assert result["gate_replay"]["status"] == "blocked"
    assert result["gate_blockers"] == ["submission_surface_qc_failure_present"]


def test_run_gate_clearing_batch_refreshes_stale_submission_minimal_authority_without_bundle_stage_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["stale_submission_minimal_authority"],
            "current_required_action": "continue_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == ["create_submission_minimal_package"]
    assert result["gate_replay"]["status"] == "clear"
    assert result["gate_blockers"] == ["stale_submission_minimal_authority"]


def test_run_gate_clearing_batch_executes_bundle_stage_workspace_refresh_before_submission_replay(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    (paper_root / "build").mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "generate_display_exports.py").write_text("print('ok')\n", encoding="utf-8")
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "submission_surface_qc_failure_present",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module,
        "_run_workspace_display_repair_script",
        lambda **_: {"status": "updated", "script_path": str(paper_root / "build" / "generate_display_exports.py")},
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["submission_surface_qc_failure_present"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "workspace_display_repair_script",
        "create_submission_minimal_package",
    ]
    assert result["gate_replay"]["status"] == "blocked"
    assert result["gate_blockers"] == ["submission_surface_qc_failure_present"]


def test_run_gate_clearing_batch_syncs_stale_submission_delivery_after_bundle_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "stale_study_delivery_mirror",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "stale_source_changed",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        lambda **_: {"status": "synced", "current_package_root": "studies/004-invasive-architecture/manuscript/current_package"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "create_submission_minimal_package",
        "sync_submission_minimal_delivery",
    ]
    assert result["unit_results"][1]["status"] == "synced"
    assert result["gate_replay"]["status"] == "clear"


def test_run_gate_clearing_batch_reuses_embedded_submission_delivery_sync_after_bundle_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "stale_study_delivery_mirror",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "stale_source_changed",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {
            "output_root": "paper/submission_minimal",
            "status": "ready",
            "delivery_sync": {
                "status": "synced",
                "current_package_root": "studies/004-invasive-architecture/manuscript/current_package",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("embedded delivery_sync should be reused instead of re-running study_delivery_sync")
        ),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert [item["unit_id"] for item in result["unit_results"]] == [
        "create_submission_minimal_package",
        "sync_submission_minimal_delivery",
    ]
    assert result["unit_results"][1]["status"] == "synced"
    assert result["unit_results"][1]["result"]["current_package_root"] == (
        "studies/004-invasive-architecture/manuscript/current_package"
    )


def test_run_gate_clearing_batch_executes_delivery_refresh_fast_lane_for_stale_projection_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "stale_study_delivery_mirror",
            ],
            "current_required_action": "continue_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "stale_projection_missing",
            "study_delivery_stale_reason": "delivery_projection_missing",
            "study_delivery_missing_source_paths": [],
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    sync_calls: list[tuple[str, str, bool]] = []

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "status": "synced",
            "current_package_root": str(study_root / "manuscript" / "current_package"),
            "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        }

    monkeypatch.setattr(
        module.study_delivery_sync,
        "can_sync_study_delivery",
        lambda *, paper_root: True,
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        fake_sync,
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **_: (_ for _ in ()).throw(AssertionError("projection-missing should use sync_study_delivery")),
    )
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("stale projection fast lane should not rebuild submission_minimal")
        ),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert [item["unit_id"] for item in result["unit_results"]] == ["sync_submission_minimal_delivery"]
    assert result["unit_results"][0]["status"] == "synced"
    assert result["gate_replay"]["status"] == "clear"
    assert result["gate_blockers"] == ["stale_study_delivery_mirror"]


def test_run_gate_clearing_batch_skips_repair_units_when_unit_fingerprints_match_latest_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "materialize_display_surface", "status": "materialized"},
                {"unit_id": "sync_submission_minimal_delivery", "status": "synced"},
            ],
            "unit_fingerprints": {
                "materialize_display_surface": "display-fp",
                "sync_submission_minimal_delivery": "delivery-fp",
            },
            "gate_replay": {
                "status": "blocked",
                "blockers": ["stale_study_delivery_mirror", "medical_publication_surface_blocked"],
            },
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["stale_study_delivery_mirror", "medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "study_delivery_status": "stale_projection_missing",
            "study_delivery_stale_reason": "delivery_projection_missing",
            "study_delivery_missing_source_paths": [],
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module,
        "_repair_unit_fingerprint",
        lambda *, unit_id, **kwargs: {
            "materialize_display_surface": "display-fp",
            "sync_submission_minimal_delivery": "delivery-fp",
        }.get(unit_id),
    )
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda **_: (_ for _ in ()).throw(AssertionError("matching display fingerprint should skip heavy refresh")),
    )
    monkeypatch.setattr(
        module,
        "_repair_paper_live_paths",
        lambda **_: {"ok": True, "status": "updated", "repaired_files": ["paper/live-paths.json"]},
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "can_sync_study_delivery",
        lambda *, paper_root: True,
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        lambda **_: (_ for _ in ()).throw(AssertionError("matching delivery fingerprint should skip sync")),
    )
    replay_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **kwargs: (
            replay_calls.append(kwargs),
            {
                "status": "blocked",
                "allow_write": False,
                "blockers": ["stale_study_delivery_mirror"],
                "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            },
        )[1],
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert replay_calls == [
        {
            "quest_root": quest_root,
            "apply": True,
            "source": "test-source",
            "enqueue_intervention": False,
        }
    ]
    assert result["ok"] is True
    result_by_unit = {item["unit_id"]: item for item in result["unit_results"]}
    assert set(result_by_unit) == {
        "repair_paper_live_paths",
        "materialize_display_surface",
        "sync_submission_minimal_delivery",
    }
    assert result_by_unit["materialize_display_surface"]["status"] == "skipped_matching_unit_fingerprint"
    assert result_by_unit["sync_submission_minimal_delivery"]["status"] == "skipped_matching_unit_fingerprint"
    assert result_by_unit["materialize_display_surface"]["fingerprint"] == "display-fp"
    assert result_by_unit["sync_submission_minimal_delivery"]["fingerprint"] == "delivery-fp"
    saved = json.loads(latest_record_path.read_text(encoding="utf-8"))
    assert saved["source_eval_id"] == publication_eval_payload["eval_id"]
    assert saved["unit_fingerprints"] == {
        "materialize_display_surface": "display-fp",
        "sync_submission_minimal_delivery": "delivery-fp",
    }


def test_run_gate_clearing_batch_skips_submission_refresh_only_when_inputs_match_and_previous_run_succeeded(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_submission_minimal_fingerprint_inputs(paper_root)
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    matching_gate_report = {
        "status": "blocked",
        "blockers": ["stale_study_delivery_mirror"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
    }
    matching_fingerprint = module._repair_unit_fingerprint(
        unit_id="create_submission_minimal_package",
        paper_root=paper_root,
        gate_report=matching_gate_report,
        profile=profile,
    )
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
            ],
            "unit_fingerprints": {
                "create_submission_minimal_package": matching_fingerprint,
            },
        },
    )
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(matching_gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("matching submission fingerprint plus previous success should skip heavy rebuild")
        ),
    )
    sync_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda *, paper_root, profile: (
            sync_calls.append(paper_root),
            {"status": "synced", "current_package_root": "studies/004-invasive-architecture/manuscript/current_package"},
        )[1],
    )
    replay_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **kwargs: (
            replay_calls.append(kwargs),
            {
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            },
        )[1],
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    result_by_unit = {item["unit_id"]: item for item in result["unit_results"]}
    assert result_by_unit["create_submission_minimal_package"]["status"] == "skipped_matching_unit_fingerprint"
    assert result_by_unit["create_submission_minimal_package"]["fingerprint"] == matching_fingerprint
    assert result_by_unit["create_submission_minimal_package"]["last_success_status"] == "ok"
    assert result_by_unit["sync_submission_minimal_delivery"]["status"] == "synced"
    assert sync_calls == [paper_root]
    assert replay_calls == [
        {
            "quest_root": quest_root,
            "apply": True,
            "source": "test-source",
            "enqueue_intervention": False,
        }
    ]


def test_run_gate_clearing_batch_reruns_submission_refresh_when_previous_matching_run_failed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_submission_minimal_fingerprint_inputs(paper_root)
    gate_report = {
        "status": "blocked",
        "blockers": ["submission_surface_qc_failure_present"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
    }
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    matching_fingerprint = module._repair_unit_fingerprint(
        unit_id="create_submission_minimal_package",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "failed"},
            ],
            "unit_fingerprints": {
                "create_submission_minimal_package": matching_fingerprint,
            },
        },
    )
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    rebuild_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda *, paper_root, profile: (rebuild_calls.append(paper_root), {"status": "ready"})[1],
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["submission_surface_qc_failure_present"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert rebuild_calls == [paper_root]
    assert result["unit_results"][0]["unit_id"] == "create_submission_minimal_package"
    assert result["unit_results"][0]["status"] == "ready"


def test_run_gate_clearing_batch_reruns_submission_refresh_when_quality_inputs_change(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_submission_minimal_fingerprint_inputs(paper_root)
    gate_report = {
        "status": "blocked",
        "blockers": ["submission_surface_qc_failure_present"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
    }
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    previous_fingerprint = module._repair_unit_fingerprint(
        unit_id="create_submission_minimal_package",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
            ],
            "unit_fingerprints": {
                "create_submission_minimal_package": previous_fingerprint,
            },
        },
    )
    _write_text(paper_root / "build" / "compiled_manuscript.md", "# Results\n\nUpdated content changes the submission package.\n")
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    rebuild_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda *, paper_root, profile: (rebuild_calls.append(paper_root), {"status": "ready"})[1],
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["submission_surface_qc_failure_present"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert rebuild_calls == [paper_root]
    assert result["unit_results"][0]["unit_id"] == "create_submission_minimal_package"
    assert result["unit_results"][0]["status"] == "ready"


def test_study_outer_loop_executes_gate_clearing_batch_controller_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    runtime_protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

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
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "publication_quality_gap",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-21T12:42:39+00:00",
                "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_resolve_runtime_escalation_record",
        lambda **_: (
            runtime_protocol.RuntimeEscalationRecordRef(
                record_id="runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-21T12:42:39+00:00",
                artifact_path=str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            ),
            None,
        ),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("batch_kwargs", kwargs),
            {"ok": True, "status": "executed"},
        )[1],
    )

    result = module.study_outer_loop_tick(
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
        decision_type="bounded_analysis",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Gate-clearing batch should run before resuming the same study line.",
        source="test-source",
        recorded_at="2026-04-21T12:45:00+00:00",
    )

    assert seen["batch_kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert result["executed_controller_action"]["action_type"] == "run_gate_clearing_batch"
    assert result["executed_controller_action"]["result"] == {"ok": True, "status": "executed"}
