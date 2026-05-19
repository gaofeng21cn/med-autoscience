from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study, write_text


def _write_transport_inputs(study_root: Path) -> None:
    transport_root = study_root / "analysis" / "clean_room_execution" / "20_transportability"
    rows = "\n".join(
        [
            "Age,Sex,Smoke,HbA1c,HDL,SBP,DBP,os_event,os_time",
            "45,1,0,7.1,1.1,120,75,0,5.0",
            "58,0,1,8.2,1.3,135,80,1,3.2",
            "66,1,1,9.1,1.0,148,86,1,2.4",
            "52,0,0,6.8,1.4,126,78,0,5.0",
        ]
    )
    write_text(transport_root / "china_transportability_input.csv", rows + "\n")
    nhanes_rows = "\n".join(
        [
            "Age,Sex,Smoke,HbA1c,HDL,SBP,DBP,os_event,os_time",
            "63,1,1,7.8,46,136,82,1,2.8",
            "71,0,0,8.4,52,142,84,0,5.0",
            "59,1,1,7.2,39,130,76,1,4.1",
            "68,0,0,6.9,57,138,80,0,5.0",
        ]
    )
    write_text(transport_root / "nhanes_transportability_input.csv", nhanes_rows + "\n")
    write_text(
        study_root / "analysis" / "clean_room_execution" / "00_harmonization" / "predictor_mapping_table.md",
        "| logical_name | nhanes_column |\n| --- | --- |\n| hdl_c | LBDHDD |\n",
    )
    write_text(
        transport_root / "model_spec_and_feature_list.md",
        "# Model spec\n\nClean rebuild is authorized because old transport model provenance was not recovered.\n",
    )


def _fake_rerun_evidence(*, study_root: Path, **_: object) -> dict[str, object]:
    evidence_path = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    return {
        "evidence_path": evidence_path,
        "evidence_payload": {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "schema_version": 1,
            "status": "completed",
            "model": {
                "model_family": "clean_rebuild_penalized_cox_ph",
                "penalizer": 0.1,
                "feature_order": ["Age", "Sex", "Smoke", "HbA1c", "hdl_mmol_l", "SBP", "DBP"],
            },
            "hdl_unit_handling": {
                "nhanes_raw_hdl_unit": "mg/dL",
                "nhanes_model_hdl_unit": "mmol/L",
                "mg_dl_to_mmol_l_factor": 0.02586,
            },
            "comparison": {
                "raw_scale_nhanes": {"c_index": 0.56, "mean_predicted_5y_risk": 0.001},
                "unit_harmonized_nhanes": {"c_index": 0.73, "mean_predicted_5y_risk": 0.023},
            },
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    }


def test_clean_rebuild_authorization_materializes_unit_harmonized_rerun_evidence(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.analysis_harmonization_owner")
    monkeypatch.setattr(module, "_materialize_unit_harmonized_rerun_evidence", _fake_rerun_evidence, raising=False)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_transport_inputs(study_root)

    dispatch = {
        "action_type": "unit_harmonized_external_validation_rerun",
        "action_id": "dispatch::dm002::unit-harmonized-rerun",
        "source_action": {
            "clean_reproducible_model_rebuild_authorized": True,
            "selected_route_option": "rebuild_reproducible_model_route",
        },
        "refs": {"dispatch_path": "artifacts/supervision/consumer/default_executor_dispatches/rerun.json"},
    }
    request = {
        "request_kind": "unit_harmonized_external_validation_rerun",
        "clean_reproducible_model_rebuild_authorized": True,
    }

    result = module.unit_harmonized_external_validation_rerun_or_typed_blocker(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
        request=request,
        apply=True,
    )

    owner_result = result["owner_result"]
    evidence_ref = Path(owner_result["rerun_evidence_ref"])
    assert owner_result["status"] == "completed"
    assert owner_result["blocked_reason"] is None
    assert owner_result["typed_blocker"] is None
    assert owner_result["unit_harmonized_rerun_completed"] is True
    assert owner_result["analysis_lane_status"] == "unit_harmonized_rerun_materialized"
    assert owner_result["clean_reproducible_model_rebuild_authorized"] is True
    assert owner_result["old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion"] is True
    assert owner_result["publication_eval_written"] is False
    assert owner_result["controller_decision_written"] is False
    assert owner_result["paper_package_mutation_allowed"] is False
    assert evidence_ref.is_file()
    evidence = json.loads(evidence_ref.read_text(encoding="utf-8"))
    assert evidence["surface"] == "unit_harmonized_external_validation_rerun_evidence"
    assert evidence["comparison"]["unit_harmonized_nhanes"]["c_index"] == 0.73
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()


def test_dispatch_can_complete_unit_harmonized_rerun_without_forbidden_writes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    executor = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    owner_module = importlib.import_module("med_autoscience.controllers.analysis_harmonization_owner")
    monkeypatch.setattr(owner_module, "_materialize_unit_harmonized_rerun_evidence", _fake_rerun_evidence, raising=False)
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_transport_inputs(study_root)
    route = _owner_route(
        study_id=study_id,
        action_type="unit_harmonized_external_validation_rerun",
        owner="analysis_harmonization_owner",
    )
    route.update(
        {
            "work_unit_fingerprint": "clean-rebuild::unit_harmonized_external_validation_rerun::decision",
            "source_fingerprint": "truth-snapshot::clean-rebuild-authorized",
            "idempotency_key": "owner-route::dm002::analysis-harmonization::clean-rebuild",
        }
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="unit_harmonized_external_validation_rerun",
        owner="analysis_harmonization_owner",
        required_output_surface=(
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        owner_route=route,
    )
    dispatch["source_action"] = {
        "action_type": "unit_harmonized_external_validation_rerun",
        "clean_reproducible_model_rebuild_authorized": True,
        "selected_route_option": "rebuild_reproducible_model_route",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )

    result = executor.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("unit_harmonized_external_validation_rerun",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    owner_result = execution["owner_result"]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert owner_result["status"] == "completed"
    assert owner_result["unit_harmonized_rerun_completed"] is True
    assert Path(owner_result["rerun_evidence_ref"]).is_file()
    assert owner_result["request_kind"] == "unit_harmonized_external_validation_rerun"
    assert owner_result["publication_eval_written"] is False
    assert owner_result["controller_decision_written"] is False
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
