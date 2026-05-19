from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

FEATURE_ORDER = ("Age", "Sex", "Smoke", "HbA1c", "hdl_mmol_l", "SBP", "DBP")
HDL_MG_DL_TO_MMOL_L = 0.02586
COX_PENALIZER = 0.1
HORIZON_YEARS = 5.0


def materialize_unit_harmonized_rerun_evidence(
    *,
    study_root: Path,
    study_id: str,
    generated_at: str,
    input_summary: Mapping[str, Any],
) -> dict[str, Any]:
    pd, np, CoxPHFitter = _analysis_dependencies()
    transport_root = study_root / "analysis" / "clean_room_execution" / "20_transportability"
    china_path = transport_root / "china_transportability_input.csv"
    nhanes_path = transport_root / "nhanes_transportability_input.csv"
    china = _prepared_frame(pd.read_csv(china_path), hdl_unit="mmol_l")
    nhanes_raw = _prepared_frame(pd.read_csv(nhanes_path), hdl_unit="raw")
    nhanes_unit = _prepared_frame(pd.read_csv(nhanes_path), hdl_unit="mg_dl_to_mmol_l")

    model_columns = [*FEATURE_ORDER, "os_time", "os_event"]
    cph = CoxPHFitter(penalizer=COX_PENALIZER)
    cph.fit(china[model_columns], duration_col="os_time", event_col="os_event")

    china_metrics = _metrics(
        np=np,
        cph=cph,
        frame=china,
        feature_order=FEATURE_ORDER,
        horizon_years=HORIZON_YEARS,
    )
    nhanes_raw_metrics = _metrics(
        np=np,
        cph=cph,
        frame=nhanes_raw,
        feature_order=FEATURE_ORDER,
        horizon_years=HORIZON_YEARS,
    )
    nhanes_unit_metrics = _metrics(
        np=np,
        cph=cph,
        frame=nhanes_unit,
        feature_order=FEATURE_ORDER,
        horizon_years=HORIZON_YEARS,
    )
    evidence_path = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    coefficients = {
        str(index): _finite_float(value)
        for index, value in cph.params_.to_dict().items()
    }
    evidence_payload = {
        "surface": "unit_harmonized_external_validation_rerun_evidence",
        "schema_version": 1,
        "generated_at": generated_at,
        "study_id": study_id,
        "owner": "analysis_harmonization_owner",
        "work_unit": "unit_harmonized_external_validation_rerun",
        "status": "completed",
        "model": {
            "model_family": "clean_rebuild_penalized_cox_ph",
            "penalizer": COX_PENALIZER,
            "horizon_years": HORIZON_YEARS,
            "duration_col": "os_time",
            "event_col": "os_event",
            "feature_order": list(FEATURE_ORDER),
            "coefficients": coefficients,
            "baseline_survival_at_5y": _baseline_survival_at(cph, HORIZON_YEARS),
            "software": {
                "python_packages": {
                    "pandas": getattr(pd, "__version__", None),
                    "numpy": getattr(np, "__version__", None),
                    "lifelines": _lifelines_version(CoxPHFitter),
                }
            },
        },
        "hdl_unit_handling": {
            "china_input_hdl_unit": "mmol/L",
            "nhanes_raw_hdl_unit": "mg/dL",
            "nhanes_model_hdl_unit": "mmol/L",
            "mg_dl_to_mmol_l_factor": HDL_MG_DL_TO_MMOL_L,
            "raw_mapping_was_not_medical_evidence": True,
        },
        "cohorts": {
            "china": _cohort_summary(china),
            "nhanes": _cohort_summary(nhanes_unit),
        },
        "comparison": {
            "china_development": china_metrics,
            "raw_scale_nhanes": nhanes_raw_metrics,
            "unit_harmonized_nhanes": nhanes_unit_metrics,
            "unit_harmonization_delta": {
                "nhanes_c_index_delta": _finite_float(
                    nhanes_unit_metrics.get("c_index") - nhanes_raw_metrics.get("c_index")
                ),
                "nhanes_mean_predicted_5y_risk_delta": _finite_float(
                    nhanes_unit_metrics.get("mean_predicted_5y_risk")
                    - nhanes_raw_metrics.get("mean_predicted_5y_risk")
                ),
            },
        },
        "input_summary": dict(input_summary),
        "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        "medical_claim_authoring_allowed": False,
        "publication_eval_written": False,
        "controller_decision_written": False,
        "paper_package_mutation_allowed": False,
        "current_package_write_allowed": False,
    }
    return {"evidence_path": evidence_path, "evidence_payload": evidence_payload}


def _analysis_dependencies() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        import pandas as pd
        from lifelines import CoxPHFitter
    except ImportError as exc:
        raise RuntimeError(f"analysis_dependency_missing:{exc.name}") from exc
    return pd, np, CoxPHFitter


def _prepared_frame(frame: Any, *, hdl_unit: str) -> Any:
    result = frame.copy()
    if hdl_unit == "mmol_l":
        result["hdl_mmol_l"] = result["HDL"]
    elif hdl_unit == "mg_dl_to_mmol_l":
        result["hdl_mmol_l"] = result["HDL"] * HDL_MG_DL_TO_MMOL_L
    elif hdl_unit == "raw":
        result["hdl_mmol_l"] = result["HDL"]
    else:
        raise ValueError(f"Unsupported HDL unit preparation: {hdl_unit}")
    required = [*FEATURE_ORDER, "os_time", "os_event"]
    return result[required].dropna()


def _metrics(*, np: Any, cph: Any, frame: Any, feature_order: tuple[str, ...], horizon_years: float) -> dict[str, Any]:
    predictions = cph.predict_survival_function(frame[list(feature_order)], times=[horizon_years]).T.iloc[:, 0]
    risk = 1.0 - predictions
    observed = ((frame["os_event"] == 1) & (frame["os_time"] <= horizon_years)).astype(float)
    c_index = float(cph.score(frame[[*feature_order, "os_time", "os_event"]], scoring_method="concordance_index"))
    mean_risk = float(risk.mean())
    observed_rate = float(observed.mean())
    return {
        "n": int(len(frame)),
        "events": int(frame["os_event"].sum()),
        "events_within_horizon": int(observed.sum()),
        "c_index": _finite_float(c_index),
        "mean_predicted_5y_risk": _finite_float(mean_risk),
        "observed_5y_rate": _finite_float(observed_rate),
        "predicted_minus_observed_5y_risk": _finite_float(mean_risk - observed_rate),
        "observed_expected_ratio": _finite_float(observed_rate / mean_risk if mean_risk else math.nan),
        "brier_5y": _finite_float(float(np.mean((risk.to_numpy() - observed.to_numpy()) ** 2))),
        "predicted_5y_risk_summary": _series_summary(risk),
    }


def _cohort_summary(frame: Any) -> dict[str, Any]:
    return {
        "n": int(len(frame)),
        "events": int(frame["os_event"].sum()),
        "hdl_mmol_l": _series_summary(frame["hdl_mmol_l"]),
        "age": _series_summary(frame["Age"]),
        "hba1c": _series_summary(frame["HbA1c"]),
        "sbp": _series_summary(frame["SBP"]),
        "dbp": _series_summary(frame["DBP"]),
    }


def _series_summary(series: Any) -> dict[str, Any]:
    return {
        "min": _finite_float(float(series.min())),
        "q1": _finite_float(float(series.quantile(0.25))),
        "median": _finite_float(float(series.quantile(0.5))),
        "mean": _finite_float(float(series.mean())),
        "q3": _finite_float(float(series.quantile(0.75))),
        "max": _finite_float(float(series.max())),
    }


def _baseline_survival_at(cph: Any, horizon_years: float) -> float | None:
    survival = cph.baseline_survival_
    if survival.empty:
        return None
    index = survival.index.to_series()
    nearest = (index - horizon_years).abs().idxmin()
    return _finite_float(float(survival.loc[nearest].iloc[0]))


def _lifelines_version(CoxPHFitter: Any) -> str | None:
    module_name = getattr(CoxPHFitter, "__module__", "")
    root_module = module_name.split(".", 1)[0]
    if not root_module:
        return None
    try:
        module = __import__(root_module)
    except ImportError:
        return None
    return getattr(module, "__version__", None)


def _finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
