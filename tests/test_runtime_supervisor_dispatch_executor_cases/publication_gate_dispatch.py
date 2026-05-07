from __future__ import annotations

import importlib
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_runs_publication_gate_owner_surface(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
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
        module.study_runtime_router,
        "study_runtime_status",
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

    monkeypatch.setattr(module.publication_gate, "build_gate_state", fake_build_gate_state)
    monkeypatch.setattr(module.publication_gate, "build_gate_report", fake_build_gate_report)
    monkeypatch.setattr(module.publication_gate, "write_gate_files", fake_write_gate_files)
    monkeypatch.setattr(module.publication_gate, "_materialize_publication_eval_latest", fake_materialize_publication_eval_latest)

    result = module.execute_default_executor_dispatches(
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
