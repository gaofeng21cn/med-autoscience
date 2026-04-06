from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceFigureSpec:
    template_id: str
    display_name: str
    evidence_class: str
    renderer_family: str
    input_schema_id: str
    layout_qc_profile: str
    required_exports: tuple[str, ...]
    allowed_paper_roles: tuple[str, ...] = ("main_text", "supplementary")


@dataclass(frozen=True)
class IllustrationShellSpec:
    shell_id: str
    display_name: str
    renderer_family: str
    input_schema_id: str
    shell_qc_profile: str
    required_exports: tuple[str, ...]
    allowed_paper_roles: tuple[str, ...] = ("main_text",)


@dataclass(frozen=True)
class TableShellSpec:
    shell_id: str
    display_name: str
    input_schema_id: str
    table_qc_profile: str
    required_exports: tuple[str, ...]
    allowed_paper_roles: tuple[str, ...] = ("main_text", "supplementary")


_EVIDENCE_FIGURE_SPECS: tuple[EvidenceFigureSpec, ...] = (
    EvidenceFigureSpec(
        template_id="roc_curve_binary",
        display_name="ROC Curve (Binary Outcome)",
        evidence_class="prediction_performance",
        renderer_family="r_ggplot2",
        input_schema_id="binary_prediction_curve_inputs_v1",
        layout_qc_profile="publication_evidence_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="pr_curve_binary",
        display_name="Precision-Recall Curve (Binary Outcome)",
        evidence_class="prediction_performance",
        renderer_family="r_ggplot2",
        input_schema_id="binary_prediction_curve_inputs_v1",
        layout_qc_profile="publication_evidence_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="calibration_curve_binary",
        display_name="Calibration Curve (Binary Outcome)",
        evidence_class="prediction_performance",
        renderer_family="r_ggplot2",
        input_schema_id="binary_prediction_curve_inputs_v1",
        layout_qc_profile="publication_evidence_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="decision_curve_binary",
        display_name="Decision Curve (Binary Outcome)",
        evidence_class="clinical_utility",
        renderer_family="r_ggplot2",
        input_schema_id="binary_prediction_curve_inputs_v1",
        layout_qc_profile="publication_evidence_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="risk_layering_monotonic_bars",
        display_name="Monotonic Risk Layering Bars",
        evidence_class="time_to_event",
        renderer_family="python",
        input_schema_id="risk_layering_monotonic_inputs_v1",
        layout_qc_profile="publication_risk_layering_bars",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="binary_calibration_decision_curve_panel",
        display_name="Binary Calibration and Decision Curve Panel",
        evidence_class="clinical_utility",
        renderer_family="python",
        input_schema_id="binary_calibration_decision_curve_panel_inputs_v1",
        layout_qc_profile="publication_binary_calibration_decision_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="model_complexity_audit_panel",
        display_name="Model Complexity Audit Panel",
        evidence_class="model_audit",
        renderer_family="python",
        input_schema_id="model_complexity_audit_panel_inputs_v1",
        layout_qc_profile="publication_model_complexity_audit",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="time_dependent_roc_horizon",
        display_name="Time-Dependent ROC (Horizon)",
        evidence_class="time_to_event",
        renderer_family="r_ggplot2",
        input_schema_id="binary_prediction_curve_inputs_v1",
        layout_qc_profile="publication_evidence_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="kaplan_meier_grouped",
        display_name="Kaplan-Meier Curve (Grouped)",
        evidence_class="time_to_event",
        renderer_family="r_ggplot2",
        input_schema_id="time_to_event_grouped_inputs_v1",
        layout_qc_profile="publication_survival_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="cumulative_incidence_grouped",
        display_name="Cumulative Incidence Curve (Grouped)",
        evidence_class="time_to_event",
        renderer_family="r_ggplot2",
        input_schema_id="time_to_event_grouped_inputs_v1",
        layout_qc_profile="publication_survival_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="umap_scatter_grouped",
        display_name="UMAP Scatter (Grouped)",
        evidence_class="data_geometry",
        renderer_family="r_ggplot2",
        input_schema_id="embedding_grouped_inputs_v1",
        layout_qc_profile="publication_embedding_scatter",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="pca_scatter_grouped",
        display_name="PCA Scatter (Grouped)",
        evidence_class="data_geometry",
        renderer_family="r_ggplot2",
        input_schema_id="embedding_grouped_inputs_v1",
        layout_qc_profile="publication_embedding_scatter",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="tsne_scatter_grouped",
        display_name="t-SNE Scatter (Grouped)",
        evidence_class="data_geometry",
        renderer_family="r_ggplot2",
        input_schema_id="embedding_grouped_inputs_v1",
        layout_qc_profile="publication_embedding_scatter",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="heatmap_group_comparison",
        display_name="Heatmap (Group Comparison)",
        evidence_class="matrix_pattern",
        renderer_family="r_ggplot2",
        input_schema_id="heatmap_group_comparison_inputs_v1",
        layout_qc_profile="publication_heatmap",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="correlation_heatmap",
        display_name="Correlation Heatmap",
        evidence_class="matrix_pattern",
        renderer_family="r_ggplot2",
        input_schema_id="correlation_heatmap_inputs_v1",
        layout_qc_profile="publication_heatmap",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="clustered_heatmap",
        display_name="Clustered Heatmap (Precomputed Ordering)",
        evidence_class="matrix_pattern",
        renderer_family="r_ggplot2",
        input_schema_id="clustered_heatmap_inputs_v1",
        layout_qc_profile="publication_heatmap",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="forest_effect_main",
        display_name="Forest Plot (Main Effects)",
        evidence_class="effect_estimate",
        renderer_family="r_ggplot2",
        input_schema_id="forest_effect_inputs_v1",
        layout_qc_profile="publication_forest_plot",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="subgroup_forest",
        display_name="Forest Plot (Subgroup Effects)",
        evidence_class="effect_estimate",
        renderer_family="r_ggplot2",
        input_schema_id="forest_effect_inputs_v1",
        layout_qc_profile="publication_forest_plot",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="shap_summary_beeswarm",
        display_name="SHAP Summary Beeswarm",
        evidence_class="model_explanation",
        renderer_family="python",
        input_schema_id="shap_summary_inputs_v1",
        layout_qc_profile="publication_shap_summary",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="time_to_event_discrimination_calibration_panel",
        display_name="Validation Discrimination and Grouped Calibration (Time-to-Event)",
        evidence_class="time_to_event",
        renderer_family="python",
        input_schema_id="time_to_event_discrimination_calibration_inputs_v1",
        layout_qc_profile="publication_evidence_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="time_to_event_risk_group_summary",
        display_name="Risk-Group Summary (Time-to-Event)",
        evidence_class="time_to_event",
        renderer_family="python",
        input_schema_id="time_to_event_grouped_inputs_v1",
        layout_qc_profile="publication_survival_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="time_to_event_decision_curve",
        display_name="Decision Curve (Time-to-Event Horizon)",
        evidence_class="clinical_utility",
        renderer_family="python",
        input_schema_id="time_to_event_decision_curve_inputs_v1",
        layout_qc_profile="publication_decision_curve",
        required_exports=("png", "pdf"),
    ),
    EvidenceFigureSpec(
        template_id="multicenter_generalizability_overview",
        display_name="Multicenter Generalizability Overview",
        evidence_class="generalizability",
        renderer_family="python",
        input_schema_id="multicenter_generalizability_inputs_v1",
        layout_qc_profile="publication_multicenter_overview",
        required_exports=("png", "pdf"),
    ),
)

_ILLUSTRATION_SHELL_SPECS: tuple[IllustrationShellSpec, ...] = (
    IllustrationShellSpec(
        shell_id="cohort_flow_figure",
        display_name="Cohort Flow Figure",
        renderer_family="python",
        input_schema_id="cohort_flow_shell_inputs_v1",
        shell_qc_profile="publication_illustration_flow",
        required_exports=("png", "svg"),
    ),
    IllustrationShellSpec(
        shell_id="submission_graphical_abstract",
        display_name="Submission Graphical Abstract",
        renderer_family="python",
        input_schema_id="submission_graphical_abstract_inputs_v1",
        shell_qc_profile="submission_graphical_abstract",
        required_exports=("png", "svg"),
        allowed_paper_roles=("submission_companion",),
    ),
)

_TABLE_SHELL_SPECS: tuple[TableShellSpec, ...] = (
    TableShellSpec(
        shell_id="table1_baseline_characteristics",
        display_name="Table 1 Baseline Characteristics",
        input_schema_id="baseline_characteristics_schema_v1",
        table_qc_profile="publication_table_baseline",
        required_exports=("csv", "md"),
    ),
    TableShellSpec(
        shell_id="table2_time_to_event_performance_summary",
        display_name="Table 2 Time-to-Event Performance Summary",
        input_schema_id="time_to_event_performance_summary_v1",
        table_qc_profile="publication_table_performance",
        required_exports=("md",),
    ),
    TableShellSpec(
        shell_id="table3_clinical_interpretation_summary",
        display_name="Table 3 Clinical Interpretation Summary",
        input_schema_id="clinical_interpretation_summary_v1",
        table_qc_profile="publication_table_interpretation",
        required_exports=("md",),
    ),
    TableShellSpec(
        shell_id="performance_summary_table_generic",
        display_name="Performance Summary Table (Generic)",
        input_schema_id="performance_summary_table_generic_v1",
        table_qc_profile="publication_table_performance",
        required_exports=("csv", "md"),
    ),
    TableShellSpec(
        shell_id="grouped_risk_event_summary_table",
        display_name="Grouped Risk Event Summary Table",
        input_schema_id="grouped_risk_event_summary_table_v1",
        table_qc_profile="publication_table_interpretation",
        required_exports=("csv", "md"),
    ),
)

_EVIDENCE_BY_TEMPLATE = {item.template_id: item for item in _EVIDENCE_FIGURE_SPECS}
_ILLUSTRATION_BY_SHELL = {item.shell_id: item for item in _ILLUSTRATION_SHELL_SPECS}
_TABLE_BY_SHELL = {item.shell_id: item for item in _TABLE_SHELL_SPECS}


def list_evidence_figure_specs() -> tuple[EvidenceFigureSpec, ...]:
    return _EVIDENCE_FIGURE_SPECS


def list_illustration_shell_specs() -> tuple[IllustrationShellSpec, ...]:
    return _ILLUSTRATION_SHELL_SPECS


def list_table_shell_specs() -> tuple[TableShellSpec, ...]:
    return _TABLE_SHELL_SPECS


def get_evidence_figure_spec(template_id: str) -> EvidenceFigureSpec:
    normalized = str(template_id or "").strip()
    try:
        return _EVIDENCE_BY_TEMPLATE[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown evidence figure template `{template_id}`") from exc


def get_illustration_shell_spec(shell_id: str) -> IllustrationShellSpec:
    normalized = str(shell_id or "").strip()
    try:
        return _ILLUSTRATION_BY_SHELL[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown illustration shell `{shell_id}`") from exc


def get_table_shell_spec(shell_id: str) -> TableShellSpec:
    normalized = str(shell_id or "").strip()
    try:
        return _TABLE_BY_SHELL[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown table shell `{shell_id}`") from exc


def is_evidence_figure_template(template_id: str) -> bool:
    return str(template_id or "").strip() in _EVIDENCE_BY_TEMPLATE


def is_illustration_shell(shell_id: str) -> bool:
    return str(shell_id or "").strip() in _ILLUSTRATION_BY_SHELL


def is_table_shell(shell_id: str) -> bool:
    return str(shell_id or "").strip() in _TABLE_BY_SHELL
