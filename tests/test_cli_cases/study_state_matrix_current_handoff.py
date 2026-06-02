from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_study_state_matrix_projects_current_handoff_over_stale_transition_table_case(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    state_matrix = importlib.import_module("med_autoscience.controllers.study_state_matrix")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    stale_transition = {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "owner": "write",
        "controller_action": "request_opl_stage_attempt",
        "next_work_unit": {
            "unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
            "lane": "write",
        },
        "typed_blocker": None,
        "guard_boundary": {
            "runner_boundary": "mas_domain_read_model_only",
            "can_write_domain_truth": False,
            "can_execute_generic_state_machine": False,
        },
        "source_refs": ["artifacts/publication_eval/latest.json"],
        "completion_receipt_consumption": {
            "status": "consumed",
            "receipt_kind": "ai_reviewer_publication_eval",
            "receipt_ref": "artifacts/publication_eval/latest.json",
            "work_unit_id": "quality_dimension_novelty_positioning::ai_reviewer_recheck",
            "work_unit_fingerprint": "sha256:old-reviewer-work",
        },
    }

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "running_provider_attempt": False,
                "execution_state_kind": "executable_owner_action",
                "next_owner": "analysis_harmonization_owner",
                "controller_action": "unit_harmonized_external_validation_rerun",
                "next_work_unit": "unit_harmonized_external_validation_rerun",
                "dispatch_consumption": {"consumption_status": "unconsumed"},
                "next_forced_delta": {
                    "target_surface_specificity": "explicit_owner_route_target",
                    "target_surface": {
                        "ref_kind": "route_obligation",
                        "route_target": "analysis_harmonization_owner",
                        "surface_ref": (
                            "unit-harmonized external-validation rerun evidence or typed "
                            "blocker:unit_harmonized_rerun_required"
                        ),
                    },
                },
            },
        },
    )
    monkeypatch.setattr(
        state_matrix.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: dict(stale_transition),
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    study = payload["studies"][0]
    row = payload["domain_transition_table"]["rows"][0]
    case = payload["domain_transition_table"]["family_transition_matrix_cases"][0]
    accounting_study = payload["progress_first_tick_accounting"]["studies"][0]

    assert exit_code == 0
    assert study["monitoring"]["next_owner"] == "analysis_harmonization_owner"
    assert study["domain_transition"]["decision_type"] == "current_owner_handoff"
    assert study["domain_transition"]["owner"] == "analysis_harmonization_owner"
    assert study["domain_transition"]["controller_action"] == "unit_harmonized_external_validation_rerun"
    assert study["domain_transition"]["next_work_unit"]["unit_id"] == "unit_harmonized_external_validation_rerun"
    assert row["owner"] == "analysis_harmonization_owner"
    assert row["controller_action"] == "unit_harmonized_external_validation_rerun"
    assert row["next_work_unit"]["unit_id"] == "unit_harmonized_external_validation_rerun"
    assert row["guard_boundary"]["required_owner_surface"].startswith("unit-harmonized external-validation")
    assert case["expected"]["owner"] == "analysis_harmonization_owner"
    assert case["expected"]["controller_action"] == "unit_harmonized_external_validation_rerun"
    assert case["expected"]["next_work_unit_id"] == "unit_harmonized_external_validation_rerun"
    assert accounting_study["monitoring_status"] == "stalled_unconsumed_action"
    assert accounting_study["next_owner"] == "analysis_harmonization_owner"
