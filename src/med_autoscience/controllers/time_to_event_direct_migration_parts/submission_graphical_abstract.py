from __future__ import annotations

from typing import Any

from med_autoscience import display_registry

from .shared import _extract_regex_group, _row_map_from_markdown_table


def _build_submission_graphical_abstract_payload(
    *,
    cohort_flow_payload: dict[str, Any],
    table2_header: list[str],
    table2_rows: list[list[str]],
) -> dict[str, Any]:
    def endpoint_count(endpoint: dict[str, Any]) -> int:
        raw_value = endpoint.get("n")
        if raw_value is None:
            raw_value = endpoint.get("event_n")
        return int(raw_value)

    steps = list(cohort_flow_payload.get("steps") or [])
    endpoint_inventory = list(cohort_flow_payload.get("endpoint_inventory") or [])
    if len(steps) < 3:
        raise ValueError("submission graphical abstract requires at least three cohort flow steps")

    analytic_cohort = steps[-3]
    derivation_split = steps[-2]
    validation_split = steps[-1]

    endpoint_by_label = {
        str(item.get("label") or "").strip().casefold(): item
        for item in endpoint_inventory
        if isinstance(item, dict) and str(item.get("label") or "").strip()
    }
    cvd_endpoint = next(
        (
            item
            for label, item in endpoint_by_label.items()
            if "cardiovascular" in label and "mortality" in label
        ),
        None,
    )
    all_cause_endpoint = next(
        (
            item
            for label, item in endpoint_by_label.items()
            if "all-cause" in label and "mortality" in label
        ),
        None,
    )
    if cvd_endpoint is None or all_cause_endpoint is None:
        raise ValueError("submission graphical abstract requires cardiovascular and all-cause endpoint inventory rows")

    table_rows = _row_map_from_markdown_table(header=table2_header, rows=table2_rows, label_column="Endpoint")
    primary_row = table_rows.get("Cardiovascular mortality")
    supportive_row = table_rows.get("All-cause mortality")
    if primary_row is None or supportive_row is None:
        raise ValueError("submission graphical abstract requires cardiovascular and all-cause rows in table2")

    primary_cindex_ridge, primary_cindex_lasso = _extract_regex_group(
        text=str(primary_row.get("C-index") or ""),
        pattern=r"Ridge\s+([0-9.]+).*?lasso\s+([0-9.]+)",
        label="primary C-index pair",
    )
    primary_high_risk_events, primary_observed_events, primary_dca_window = _extract_regex_group(
        text=str(primary_row.get("Stratification / utility") or ""),
        pattern=r"High-risk tertile:\s*([0-9]+)\s*/\s*([0-9]+)\s*events.*?positive DCA at\s*([0-9.\-%]+)\s*thresholds",
        label="primary stratification summary",
    )
    supportive_cindex = _extract_regex_group(
        text=str(supportive_row.get("C-index") or ""),
        pattern=r"Supportive Cox line\s+([0-9.]+)",
        label="supportive C-index",
    )[0]
    supportive_tertiles = _extract_regex_group(
        text=str(supportive_row.get("Stratification / utility") or ""),
        pattern=r"Observed 5-year risk across tertiles:\s*([0-9.]+%)\s*,\s*([0-9.]+%)\s*,\s*([0-9.]+%)",
        label="supportive tertile summary",
    )

    return {
        "schema_version": 1,
        "shell_id": display_registry.get_illustration_shell_spec("submission_graphical_abstract").shell_id,
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "paper_role": "submission_companion",
        "title": "Graphical abstract for internal cardiovascular mortality risk stratification",
        "caption": (
            "A submission-companion overview summarizes cohort assembly, the primary 5-year cardiovascular "
            "mortality result, the supportive all-cause endpoint, and the internal multicenter applicability "
            "boundary without adding new evidence."
        ),
        "panels": [
            {
                "panel_id": "cohort_split",
                "panel_label": "A",
                "title": "Cohort and split",
                "subtitle": "Chinese multicenter diabetes cohort",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "analytic_cohort",
                                "title": "Analytic cohort",
                                "value": f"{int(analytic_cohort['n']):,}",
                                "detail": "Formal modeling cohort after endpoint-completeness screening",
                                "accent_role": "neutral",
                            }
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "cvd_deaths",
                                "title": "Cardiovascular deaths",
                                "value": f"{endpoint_count(cvd_endpoint):,}",
                                "detail": "Primary endpoint",
                                "accent_role": "primary",
                            },
                            {
                                "card_id": "all_cause_deaths",
                                "title": "All-cause deaths",
                                "value": f"{endpoint_count(all_cause_endpoint):,}",
                                "detail": "Supportive endpoint",
                                "accent_role": "secondary",
                            },
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "derivation_split",
                                "title": "Derivation",
                                "value": f"{int(derivation_split['n']):,}",
                                "detail": str(derivation_split.get("detail") or ""),
                                "accent_role": "neutral",
                            },
                            {
                                "card_id": "validation_split",
                                "title": "Validation",
                                "value": f"{int(validation_split['n']):,}",
                                "detail": str(validation_split.get("detail") or ""),
                                "accent_role": "neutral",
                            },
                        ]
                    },
                ],
            },
            {
                "panel_id": "primary_endpoint",
                "panel_label": "B",
                "title": "Primary 5-year endpoint",
                "subtitle": "Cardiovascular mortality",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "ridge_cindex",
                                "title": "Ridge Cox validation C-index",
                                "value": primary_cindex_ridge,
                                "detail": f"Lasso comparator {primary_cindex_lasso}",
                                "accent_role": "primary",
                            },
                            {
                                "card_id": "lasso_cindex",
                                "title": "Lasso Cox",
                                "value": primary_cindex_lasso,
                                "detail": "Same frozen validation split",
                                "accent_role": "secondary",
                            },
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "high_risk_events",
                                "title": "Observed 5-year events in the high-risk tertile",
                                "value": f"{primary_high_risk_events} / {primary_observed_events}",
                                "detail": "Marked event concentration in the highest tertile",
                                "accent_role": "primary",
                            }
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "decision_curve_window",
                                "title": "Decision-curve net-benefit range",
                                "value": primary_dca_window,
                                "detail": "Clinically relevant low-threshold window",
                                "accent_role": "audit",
                            }
                        ]
                    },
                ],
            },
            {
                "panel_id": "supportive_context",
                "panel_label": "C",
                "title": "Supportive context",
                "subtitle": "All-cause endpoint and internal applicability",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "supportive_cindex",
                                "title": "Supportive all-cause Cox C-index",
                                "value": supportive_cindex,
                                "detail": f"Observed 5-year tertiles {' | '.join(supportive_tertiles)}",
                                "accent_role": "secondary",
                            }
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "internal_boundary",
                                "title": "Applicability boundary",
                                "value": "Internal validation only",
                                "detail": "Multicenter support inside the current cohort",
                                "accent_role": "contrast",
                            },
                            {
                                "card_id": "transportability_boundary",
                                "title": "Transportability boundary",
                                "value": "No external validation",
                                "detail": "Do not expand beyond the audited cohort",
                                "accent_role": "audit",
                            },
                        ]
                    },
                ],
            },
        ],
        "footer_pills": [
            {
                "pill_id": "internal_validation_only",
                "panel_id": "cohort_split",
                "label": "Internal validation only",
                "style_role": "neutral",
            },
            {
                "pill_id": "supportive_endpoint_only",
                "panel_id": "primary_endpoint",
                "label": "All-cause endpoint is supportive",
                "style_role": "secondary",
            },
            {
                "pill_id": "no_external_validation",
                "panel_id": "supportive_context",
                "label": "No external validation",
                "style_role": "audit",
            },
        ],
    }


__all__ = ["_build_submission_graphical_abstract_payload"]
