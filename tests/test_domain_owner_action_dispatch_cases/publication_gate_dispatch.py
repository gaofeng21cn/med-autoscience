from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_runs_publication_gate_owner_surface(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_gate_specificity_required.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_build_gate_state(quest_root_arg) -> dict[str, object]:
        called["quest_root"] = quest_root_arg
        return {"quest_root": quest_root_arg}

    def fake_build_gate_report(state) -> dict[str, object]:
        called["state"] = state
        return {
            "generated_at": "2026-05-05T00:00:00+00:00",
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        }

    def fake_write_gate_files(quest_root_arg, report) -> tuple[Path, Path]:
        called["write_quest_root"] = quest_root_arg
        called["report"] = report
        json_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        md_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.md"
        _write_json(json_path, report)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text("# gate\n", encoding="utf-8")
        return json_path, md_path

    def fake_materialize_publication_eval_latest(**kwargs) -> dict[str, str]:
        called["materialize_kwargs"] = kwargs
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "surface": "publication_eval",
                "recommended_actions": [
                    {
                        "action_type": "return_to_controller",
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "primary_claim",
                                "source_path": "paper/claim_evidence_map.json",
                                "blocking_reason": "claim_evidence_consistency_failed",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": "paper/figures/figure_catalog.json",
                                "blocking_reason": "figure_semantics_manifest_missing_or_incomplete",
                            },
                            {
                                "target_kind": "table",
                                "target_id": "submission_manifest",
                                "source_path": "paper/submission_minimal/submission_manifest.json",
                                "blocking_reason": "submission_hardening_incomplete",
                            },
                            {
                                "target_kind": "metric",
                                "target_id": "main_result_metrics",
                                "source_path": "artifacts/results/main_result.json",
                                "blocking_reason": "derived_analysis_manifest_missing_or_incomplete",
                            },
                            {
                                "target_kind": "source_path",
                                "target_id": "gate_report",
                                "source_path": "artifacts/reports/publishability_gate/latest.json",
                                "blocking_reason": "publication_gate_blocked",
                            },
                        ],
                    }
                ],
            },
        )
        return {"artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")}

    monkeypatch.setattr(module.action_execution.publication_gate, "build_gate_state", fake_build_gate_state)
    monkeypatch.setattr(module.action_execution.publication_gate, "build_gate_report", fake_build_gate_report)
    monkeypatch.setattr(module.action_execution.publication_gate, "write_gate_files", fake_write_gate_files)
    monkeypatch.setattr(
        module.action_execution.publication_gate,
        "_materialize_publication_eval_latest",
        fake_materialize_publication_eval_latest,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_gate_specificity_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_callable_surface"] == "publication_gate.write_gate_files+_materialize_publication_eval_latest"
    assert called["quest_root"] == quest_root
    assert called["write_quest_root"] == quest_root
    assert called["materialize_kwargs"]["report"]["latest_gate_path"].endswith("latest.json")
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").is_file()


def test_execute_dispatch_runs_publication_gate_owner_when_terminal_stall_handoff_current(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "004-dpcc-longitudinal-care-inertia-intensification-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    route = _owner_route(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
    )
    route.update(
        {
            "truth_epoch": "truth-event-anchor-missing",
            "route_epoch": "truth-event-anchor-missing",
            "source_fingerprint": "truth-snapshot::anchor-missing",
            "work_unit_fingerprint": "truth-snapshot::anchor-missing",
            "idempotency_key": "owner-route::publication-gate-anchor-missing",
        }
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::anchor-missing",
        "stall_reasons": ["same_fingerprint_loop", "runtime_recovery_retry_budget_exhausted"],
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_gate_specificity_required.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "publication_gate_specificity_required",
                    "execution_status": "blocked",
                    "blocked_reason": "paper_progress_stall_terminal",
                    "owner_route": route,
                    "prompt_contract": dispatch["prompt_contract"],
                    "repeat_suppression_key": "truth-snapshot::anchor-missing",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_build_gate_state(quest_root_arg) -> dict[str, object]:
        called["quest_root"] = quest_root_arg
        return {"quest_root": quest_root_arg}

    def fake_build_gate_report(state) -> dict[str, object]:
        called["state"] = state
        return {
            "generated_at": "2026-05-17T00:00:00+00:00",
            "status": "blocked",
            "blockers": ["missing_publication_anchor"],
        }

    def fake_write_gate_files(quest_root_arg, report) -> tuple[Path, Path]:
        json_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        md_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.md"
        _write_json(json_path, report)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text("# gate\n", encoding="utf-8")
        return json_path, md_path

    def fake_materialize_publication_eval_latest(**kwargs) -> dict[str, str]:
        called["materialize_kwargs"] = kwargs
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "surface": "publication_eval",
                "recommended_actions": [
                    {
                        "action_type": "return_to_controller",
                        "specificity_targets": [
                            {
                                "target_kind": "source_path",
                                "target_id": "publishability_gate",
                                "source_path": "artifacts/reports/publishability_gate/latest.json",
                                "blocking_reason": "missing_publication_anchor",
                            }
                        ],
                    }
                ],
            },
        )
        return {"artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")}

    monkeypatch.setattr(module.action_execution.publication_gate, "build_gate_state", fake_build_gate_state)
    monkeypatch.setattr(module.action_execution.publication_gate, "build_gate_report", fake_build_gate_report)
    monkeypatch.setattr(module.action_execution.publication_gate, "write_gate_files", fake_write_gate_files)
    monkeypatch.setattr(
        module.action_execution.publication_gate,
        "_materialize_publication_eval_latest",
        fake_materialize_publication_eval_latest,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_gate_specificity_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["repeat_suppressed_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["repeat_suppression"]["repeat_suppressed"] is False
    assert execution["action_class"] == "controller_apply"
    assert execution["will_start_llm"] is False
    assert execution["owner_callable_surface"] == "publication_gate.write_gate_files+_materialize_publication_eval_latest"
    assert called["quest_root"] == quest_root
