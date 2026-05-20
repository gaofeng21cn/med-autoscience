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


def test_source_provenance_owner_records_candidate_search_without_accepting_result_summary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    summary_path = (
        study_root
        / "experiments"
        / "analysis"
        / "clinical_transportability_attribution_analysis"
        / "RESULT.json"
    )
    _write_json(
        summary_path,
        {
            "schema_version": 1,
            "analysis_id": "clinical_transportability_attribution_analysis",
            "metric_rows": [{"metric": "c_index", "value": 0.5647}],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="recover_transport_model_provenance",
            owner="source_provenance_owner",
            required_output_surface=(
                "canonical transport model provenance bundle or "
                "typed blocker:transport_model_provenance_recovery_required"
            ),
            owner_route=_owner_route(
                study_id=study_id,
                action_type="recover_transport_model_provenance",
                owner="source_provenance_owner",
            ),
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_result = result["executions"][0]["owner_result"]
    assert owner_result["status"] == "blocked"
    assert owner_result["transport_model_provenance_recovered"] is False
    assert owner_result["canonical_transport_model_provenance_bundle_ref"] is None
    assert owner_result["provenance_search"]["searched"] is True
    assert owner_result["provenance_search"]["candidate_count"] == 1
    assert owner_result["provenance_search"]["accepted_bundle_ref"] is None
    assert owner_result["provenance_search"]["candidates"][0]["path"] == str(summary_path)
    assert owner_result["provenance_search"]["candidates"][0]["accepted"] is False
    assert "canonical_transport_model_provenance_bundle_missing" in owner_result["typed_blocker"][
        "blocking_reasons"
    ]
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_source_provenance_owner_records_binary_candidates_without_crashing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    binary_path = study_root / "analysis" / "models" / "transport_cox_model.pkl"
    binary_path.parent.mkdir(parents=True, exist_ok=True)
    binary_path.write_bytes(b"\x80\x04\x95binary-model-candidate")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="recover_transport_model_provenance",
            owner="source_provenance_owner",
            required_output_surface=(
                "canonical transport model provenance bundle or "
                "typed blocker:transport_model_provenance_recovery_required"
            ),
            owner_route=_owner_route(
                study_id=study_id,
                action_type="recover_transport_model_provenance",
                owner="source_provenance_owner",
            ),
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_result = result["executions"][0]["owner_result"]
    assert owner_result["status"] == "blocked"
    assert owner_result["transport_model_provenance_recovered"] is False
    assert owner_result["canonical_transport_model_provenance_bundle_ref"] is None
    assert owner_result["provenance_search"]["candidate_count"] == 1
    assert owner_result["provenance_search"]["candidates"][0]["path"] == str(binary_path)
    assert owner_result["provenance_search"]["candidates"][0]["candidate_kind"] == "non_json_or_non_object_candidate"
    assert owner_result["provenance_search"]["candidates"][0]["accepted"] is False
    assert owner_result["provenance_search"]["result_summary_acceptance_allowed"] is False
    assert owner_result["provenance_search"]["substitute_refit_allowed"] is False
    assert "canonical_transport_model_provenance_bundle_missing" in owner_result["typed_blocker"][
        "blocking_reasons"
    ]
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_source_provenance_owner_uses_bounded_search_for_deep_legacy_archive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    legacy_root = profile.workspace_root / "runtime" / "archives" / "legacy_mds"
    deep_bundle_path = (
        legacy_root
        / "snapshot"
        / "runtime"
        / "quest"
        / "generated"
        / "nested"
        / "paper"
        / "analysis"
        / "models"
        / "transport_model_provenance_bundle.json"
    )
    _write_json(
        deep_bundle_path,
        {
            "surface": "canonical_transport_model_provenance_bundle",
            "schema_version": 1,
            "model_type": "penalized_cox_ph",
            "coefficients": {"age": 0.04},
            "feature_order": ["age"],
            "feature_coding": {"age": {"type": "continuous"}},
            "baseline_survival_at_5_years": 0.98,
            "penalty": {"type": "ridge", "lambda": 0.01},
            "standardization": {"center": {"age": 50.0}, "scale": {"age": 10.0}},
            "original_result_artifact": "legacy/RESULT.json",
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="recover_transport_model_provenance",
            owner="source_provenance_owner",
            required_output_surface=(
                "canonical transport model provenance bundle or "
                "typed blocker:transport_model_provenance_recovery_required"
            ),
            owner_route=_owner_route(
                study_id=study_id,
                action_type="recover_transport_model_provenance",
                owner="source_provenance_owner",
            ),
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_result = result["executions"][0]["owner_result"]
    search = owner_result["provenance_search"]
    legacy_summary = next(
        summary for summary in search["root_scan_summaries"] if summary["root_kind"] == "legacy_archive"
    )
    assert owner_result["status"] == "blocked"
    assert owner_result["transport_model_provenance_recovered"] is False
    assert owner_result["canonical_transport_model_provenance_bundle_ref"] is None
    assert search["searched"] is True
    assert search["bounded_search"] is True
    assert str(deep_bundle_path) not in {candidate["path"] for candidate in search["candidates"]}
    assert legacy_summary["bounded"] is True
    assert legacy_summary["max_depth"] < len(deep_bundle_path.relative_to(legacy_root).parts) - 1
    assert "canonical_transport_model_provenance_bundle_missing" in owner_result["typed_blocker"][
        "blocking_reasons"
    ]
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_source_provenance_owner_accepts_complete_canonical_transport_model_bundle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    bundle_path = (
        study_root
        / "artifacts"
        / "model_provenance"
        / "transport_model_provenance_bundle.json"
    )
    _write_json(
        bundle_path,
        {
            "surface": "canonical_transport_model_provenance_bundle",
            "schema_version": 1,
            "model_type": "penalized_cox_ph",
            "coefficients": {
                "age": 0.04,
                "sex_male": 0.2,
                "smoking_current": 0.3,
                "hba1c": 0.08,
                "hdl_c": -0.15,
                "sbp": 0.01,
                "dbp": 0.01,
            },
            "feature_order": ["age", "sex_male", "smoking_current", "hba1c", "hdl_c", "sbp", "dbp"],
            "feature_coding": {
                "sex_male": {"source": "sex", "reference": "female"},
                "smoking_current": {"source": "smoking", "reference": "not_current"},
            },
            "baseline_survival_at_5_years": 0.98,
            "penalty": {"type": "ridge", "lambda": 0.01, "selection": "cross_validation"},
            "standardization": {
                "center": {"age": 50.0},
                "scale": {"age": 10.0},
                "unit_conversions": {"hdl_c": "mmol/L"},
            },
            "original_result_artifact": "paper/analysis_groups/clinical_transportability_attribution_analysis/RESULT.json",
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="recover_transport_model_provenance",
            owner="source_provenance_owner",
            required_output_surface=(
                "canonical transport model provenance bundle or "
                "typed blocker:transport_model_provenance_recovery_required"
            ),
            owner_route=_owner_route(
                study_id=study_id,
                action_type="recover_transport_model_provenance",
                owner="source_provenance_owner",
            ),
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_result = result["executions"][0]["owner_result"]
    assert owner_result["status"] == "completed"
    assert owner_result["blocked_reason"] is None
    assert owner_result["typed_blocker"] is None
    assert owner_result["transport_model_provenance_recovered"] is True
    assert owner_result["canonical_transport_model_provenance_bundle_ref"] == str(bundle_path)
    assert owner_result["next_owner"] == "analysis_harmonization_owner"
    assert owner_result["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert owner_result["provenance_search"]["accepted_bundle_ref"] == str(bundle_path)
    assert owner_result["provenance_assessment"]["status"] == "completed"
    assert owner_result["publication_eval_written"] is False
    assert owner_result["controller_decision_written"] is False
    assert not (study_root / "paper").exists()
