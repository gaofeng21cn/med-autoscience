from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

FEATURE_ORDER = ("Age", "Sex", "Smoke", "HbA1c", "hdl_mmol_l", "SBP", "DBP")
HDL_MG_DL_TO_MMOL_L = 0.02586
COX_PENALIZER = 0.1
HORIZON_YEARS = 5.0
BOOTSTRAP_REPLICATES = 200
BOOTSTRAP_RANDOM_SEED = 20260521
CALIBRATION_GROUP_COUNT = 10


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
    nhanes_unit_risk = _predicted_risk(cph=cph, frame=nhanes_unit, feature_order=FEATURE_ORDER)
    nhanes_unit_observed = _observed_at_horizon(frame=nhanes_unit, horizon_years=HORIZON_YEARS)
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
        "uncertainty": _bootstrap_uncertainty(
            np=np,
            frame=nhanes_unit,
            risk=nhanes_unit_risk,
            observed=nhanes_unit_observed,
            feature_order=FEATURE_ORDER,
            horizon_years=HORIZON_YEARS,
        ),
        "calibration": _calibration_summary(np=np, risk=nhanes_unit_risk, observed=nhanes_unit_observed),
        "grouped_calibration": _grouped_calibration(
            np=np,
            risk=nhanes_unit_risk,
            observed=nhanes_unit_observed,
            groups=CALIBRATION_GROUP_COUNT,
        ),
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
    risk = _predicted_risk(cph=cph, frame=frame, feature_order=feature_order)
    observed = _observed_at_horizon(frame=frame, horizon_years=horizon_years)
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


def _predicted_risk(*, cph: Any, frame: Any, feature_order: tuple[str, ...]) -> Any:
    predictions = cph.predict_survival_function(frame[list(feature_order)], times=[HORIZON_YEARS]).T.iloc[:, 0]
    return 1.0 - predictions


def _observed_at_horizon(*, frame: Any, horizon_years: float) -> Any:
    return ((frame["os_event"] == 1) & (frame["os_time"] <= horizon_years)).astype(float)


def _bootstrap_uncertainty(
    *,
    np: Any,
    frame: Any,
    risk: Any,
    observed: Any,
    feature_order: tuple[str, ...],
    horizon_years: float,
) -> dict[str, Any]:
    rng = np.random.default_rng(BOOTSTRAP_RANDOM_SEED)
    risk_values = np.asarray(risk.to_numpy(), dtype=float)
    observed_values = np.asarray(observed.to_numpy(), dtype=float)
    duration_values = np.asarray(frame["os_time"].to_numpy(), dtype=float)
    event_values = np.asarray(frame["os_event"].to_numpy(), dtype=float)
    metric_samples: dict[str, list[float]] = {
        "c_index": [],
        "mean_predicted_5y_risk": [],
        "observed_5y_rate": [],
        "observed_expected_ratio": [],
        "brier_5y": [],
    }
    n = len(risk_values)
    if n == 0:
        return {
            "method": "nonparametric_bootstrap_fixed_model_external_validation",
            "replicates": 0,
            "random_seed": BOOTSTRAP_RANDOM_SEED,
            "horizon_years": horizon_years,
            "cohort": "unit_harmonized_nhanes",
            "metrics_95ci": {},
        }
    for _ in range(BOOTSTRAP_REPLICATES):
        indices = rng.integers(0, n, size=n)
        sampled_risk = risk_values[indices]
        sampled_observed = observed_values[indices]
        sampled_duration = duration_values[indices]
        sampled_event = event_values[indices]
        metrics = _metric_values(
            np=np,
            risk=sampled_risk,
            observed=sampled_observed,
            duration=sampled_duration,
            event=sampled_event,
        )
        for key, value in metrics.items():
            if value is not None:
                metric_samples[key].append(value)
    point = _metric_values(
        np=np,
        risk=risk_values,
        observed=observed_values,
        duration=duration_values,
        event=event_values,
    )
    return {
        "method": "nonparametric_bootstrap_fixed_model_external_validation",
        "replicates": BOOTSTRAP_REPLICATES,
        "random_seed": BOOTSTRAP_RANDOM_SEED,
        "horizon_years": horizon_years,
        "cohort": "unit_harmonized_nhanes",
        "metrics_95ci": {
            key: _percentile_interval(np=np, values=values, estimate=point.get(key))
            for key, values in metric_samples.items()
            if values
        },
        "feature_order": list(feature_order),
    }


def _metric_values(*, np: Any, risk: Any, observed: Any, duration: Any, event: Any) -> dict[str, float | None]:
    mean_risk = float(np.mean(risk)) if len(risk) else math.nan
    observed_rate = float(np.mean(observed)) if len(observed) else math.nan
    return {
        "c_index": _concordance_index(duration=duration, event=event, risk=risk),
        "mean_predicted_5y_risk": _finite_float(mean_risk),
        "observed_5y_rate": _finite_float(observed_rate),
        "observed_expected_ratio": _finite_float(observed_rate / mean_risk if mean_risk else math.nan),
        "brier_5y": _finite_float(float(np.mean((risk - observed) ** 2)) if len(risk) else math.nan),
    }


def _concordance_index(*, duration: Any, event: Any, risk: Any) -> float | None:
    try:
        from lifelines.utils import concordance_index
    except ImportError:
        return None
    try:
        return _finite_float(float(concordance_index(duration, -risk, event)))
    except (ArithmeticError, ValueError, ZeroDivisionError):
        return None


def _percentile_interval(*, np: Any, values: list[float], estimate: float | None) -> dict[str, float | None]:
    if not values:
        return {"estimate": estimate, "lower": None, "upper": None}
    return {
        "estimate": estimate,
        "lower": _finite_float(float(np.percentile(values, 2.5))),
        "upper": _finite_float(float(np.percentile(values, 97.5))),
    }


def _calibration_summary(*, np: Any, risk: Any, observed: Any) -> dict[str, Any]:
    risk_values = np.asarray(risk.to_numpy(), dtype=float)
    observed_values = np.asarray(observed.to_numpy(), dtype=float)
    clipped = np.clip(risk_values, 1e-6, 1.0 - 1e-6)
    logit_risk = np.log(clipped / (1.0 - clipped))
    intercept_model = _logistic_fit(np=np, design=np.ones((len(logit_risk), 1)), outcome=observed_values, offset=logit_risk)
    slope_model = _logistic_fit(
        np=np,
        design=np.column_stack([np.ones(len(logit_risk)), logit_risk]),
        outcome=observed_values,
        offset=None,
    )
    return {
        "method": "horizon_logistic_calibration_fixed_predictions",
        "horizon_years": HORIZON_YEARS,
        "cohort": "unit_harmonized_nhanes",
        "calibration_intercept": _coefficient_summary(intercept_model, index=0),
        "calibration_slope": _coefficient_summary(slope_model, index=1),
    }


def _logistic_fit(*, np: Any, design: Any, outcome: Any, offset: Any | None) -> dict[str, Any]:
    if len(outcome) == 0:
        return {"coef": [], "se": [], "converged": False}
    coef = np.zeros(design.shape[1], dtype=float)
    offset_values = np.zeros(len(outcome), dtype=float) if offset is None else np.asarray(offset, dtype=float)
    converged = False
    for _ in range(50):
        eta = np.clip(offset_values + design @ coef, -35.0, 35.0)
        mu = 1.0 / (1.0 + np.exp(-eta))
        weights = np.clip(mu * (1.0 - mu), 1e-9, None)
        gradient = design.T @ (outcome - mu)
        hessian = design.T @ (weights[:, None] * design)
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            break
        coef = coef + step
        if float(np.max(np.abs(step))) < 1e-8:
            converged = True
            break
    try:
        covariance = np.linalg.inv(hessian)
        se = np.sqrt(np.diag(covariance))
    except (np.linalg.LinAlgError, UnboundLocalError, ValueError):
        se = np.full(design.shape[1], np.nan)
    return {
        "coef": [_finite_float(value) for value in coef],
        "se": [_finite_float(value) for value in se],
        "converged": converged,
    }


def _coefficient_summary(model: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    coefficients = model.get("coef") if isinstance(model.get("coef"), list) else []
    standard_errors = model.get("se") if isinstance(model.get("se"), list) else []
    estimate = coefficients[index] if len(coefficients) > index else None
    se = standard_errors[index] if len(standard_errors) > index else None
    lower = _finite_float(estimate - 1.96 * se) if estimate is not None and se is not None else None
    upper = _finite_float(estimate + 1.96 * se) if estimate is not None and se is not None else None
    return {
        "estimate": estimate,
        "se": se,
        "ci_95": {"lower": lower, "upper": upper},
        "converged": bool(model.get("converged")),
    }


def _grouped_calibration(*, np: Any, risk: Any, observed: Any, groups: int) -> dict[str, Any]:
    risk_values = np.asarray(risk.to_numpy(), dtype=float)
    observed_values = np.asarray(observed.to_numpy(), dtype=float)
    if len(risk_values) == 0:
        return {"method": "risk_quantile_groups", "group_count": 0, "groups": []}
    order = np.argsort(risk_values)
    bins = np.array_split(order, min(groups, len(order)))
    group_payloads = []
    for index, indices in enumerate(bins, start=1):
        group_risk = risk_values[indices]
        group_observed = observed_values[indices]
        n = int(len(indices))
        observed_rate = float(np.mean(group_observed)) if n else math.nan
        group_payloads.append(
            {
                "group": index,
                "n": n,
                "risk_min": _finite_float(float(np.min(group_risk)) if n else math.nan),
                "risk_max": _finite_float(float(np.max(group_risk)) if n else math.nan),
                "mean_predicted_5y_risk": _finite_float(float(np.mean(group_risk)) if n else math.nan),
                "observed_5y_rate": _finite_float(observed_rate),
                "observed_5y_events": int(np.sum(group_observed)),
                "observed_5y_rate_ci_95": _wilson_interval(events=int(np.sum(group_observed)), n=n),
            }
        )
    return {
        "method": "risk_quantile_groups_with_wilson_intervals",
        "group_count": len(group_payloads),
        "horizon_years": HORIZON_YEARS,
        "cohort": "unit_harmonized_nhanes",
        "groups": group_payloads,
    }


def _wilson_interval(*, events: int, n: int) -> dict[str, float | None]:
    if n <= 0:
        return {"lower": None, "upper": None}
    z = 1.96
    p = events / n
    denominator = 1.0 + z**2 / n
    center = (p + z**2 / (2.0 * n)) / denominator
    half_width = z * math.sqrt((p * (1.0 - p) + z**2 / (4.0 * n)) / n) / denominator
    return {
        "lower": _finite_float(max(0.0, center - half_width)),
        "upper": _finite_float(min(1.0, center + half_width)),
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
