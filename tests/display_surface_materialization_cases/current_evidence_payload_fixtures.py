from __future__ import annotations


def _make_generalizability_subgroup_composite_panel_display(display_id: str = "Figure17") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "generalizability_subgroup_composite_panel",
        "title": "Generalizability and subgroup discrimination composite for external validation",
        "caption": (
            "Bounded composite lock for overall external generalizability and prespecified subgroup discrimination "
            "stability."
        ),
        "metric_family": "discrimination",
        "primary_label": "Locked model",
        "comparator_label": "Derivation cohort",
        "overview_panel_title": "External cohort discrimination overview",
        "overview_x_label": "AUROC",
        "overview_rows": [
            {
                "cohort_id": "external_a",
                "cohort_label": "External A",
                "support_count": 184,
                "event_count": 29,
                "metric_value": 0.82,
                "comparator_metric_value": 0.79,
            },
            {
                "cohort_id": "external_b",
                "cohort_label": "External B",
                "support_count": 163,
                "event_count": 21,
                "metric_value": 0.78,
                "comparator_metric_value": 0.79,
            },
            {
                "cohort_id": "temporal",
                "cohort_label": "Temporal",
                "support_count": 142,
                "event_count": 18,
                "metric_value": 0.80,
                "comparator_metric_value": 0.79,
            },
        ],
        "subgroup_panel_title": "Prespecified subgroup discrimination stability",
        "subgroup_x_label": "AUROC",
        "subgroup_reference_value": 0.80,
        "subgroup_rows": [
            {
                "subgroup_id": "age_ge_65",
                "subgroup_label": "Age >=65 years",
                "group_n": 201,
                "estimate": 0.82,
                "lower": 0.78,
                "upper": 0.86,
            },
            {
                "subgroup_id": "female",
                "subgroup_label": "Female",
                "group_n": 173,
                "estimate": 0.79,
                "lower": 0.75,
                "upper": 0.83,
            },
            {
                "subgroup_id": "high_risk",
                "subgroup_label": "High-risk surgery",
                "group_n": 96,
                "estimate": 0.84,
                "lower": 0.79,
                "upper": 0.89,
            },
        ],
    }


__all__ = ["_make_generalizability_subgroup_composite_panel_display"]
