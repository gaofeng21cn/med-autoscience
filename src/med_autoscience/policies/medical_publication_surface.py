from __future__ import annotations

import re

from med_autoscience import display_registry
from med_autoscience import figure_renderer_contract


FORBIDDEN_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    ("deployment-facing", "deployment-facing", r"\bdeployment-facing\b", re.IGNORECASE),
    ("baseline-comparable", "baseline-comparable", r"\bbaseline-comparable\b", re.IGNORECASE),
    ("locked study freeze", "locked study freeze", r"\blocked study freeze\b", re.IGNORECASE),
    ("locked cohort", "locked cohort", r"\blocked cohort\b", re.IGNORECASE),
    ("locked comparison", "locked comparison", r"\blocked comparison\b", re.IGNORECASE),
    ("locked validation", "locked validation", r"\blocked validation\b", re.IGNORECASE),
    ("locked probability", "locked probability", r"\blocked probability\b", re.IGNORECASE),
    ("contract", "contract", r"\bcontract\b", re.IGNORECASE),
    ("surface", "surface", r"\bsurface\b", re.IGNORECASE),
    ("frontier", "frontier", r"\bfrontier\b", re.IGNORECASE),
    ("mainline", "mainline", r"\bmainline\b", re.IGNORECASE),
    ("sidecar", "sidecar", r"\bsidecar\b", re.IGNORECASE),
    ("post-gate", "post-gate", r"\bpost-gate\b", re.IGNORECASE),
    ("Clinical Utility Model", "Clinical Utility Model", r"\bClinical Utility Model\b", 0),
    ("Preoperative Core Model", "Preoperative Core Model", r"\bPreoperative Core Model\b", 0),
    ("Pathology-Augmented Model", "Pathology-Augmented Model", r"\bPathology-Augmented Model\b", 0),
    ("Elastic-Net Benchmark", "Elastic-Net Benchmark", r"\bElastic-Net Benchmark\b", 0),
    ("Random-Forest Benchmark", "Random-Forest Benchmark", r"\bRandom-Forest Benchmark\b", 0),
    ("roc_auc", "roc_auc", r"\broc_auc\b", re.IGNORECASE),
    ("average_precision", "average_precision", r"\baverage_precision\b", re.IGNORECASE),
    ("brier_score", "brier_score", r"\bbrier_score\b", re.IGNORECASE),
    ("calibration_intercept", "calibration_intercept", r"\bcalibration_intercept\b", re.IGNORECASE),
    ("calibration_slope", "calibration_slope", r"\bcalibration_slope\b", re.IGNORECASE),
    ("open-source disclosure", "open-source:", r"\bopen-source:\s*https?://\S+", re.IGNORECASE),
    ("online service disclosure", "online service:", r"\bonline service:\s*https?://\S+", re.IGNORECASE),
    ("deepscientist", "deepscientist", r"\bdeepscientist\b", re.IGNORECASE),
    ("poster sources label", "Sources:", r"\bSources:", re.IGNORECASE),
    ("poster why-this-matters label", "Why this matters", r"\bWhy this matters\b", re.IGNORECASE),
    ("comparison framework", "comparison framework", r"\bcomparison framework\b", re.IGNORECASE),
    ("model surface", "model surface", r"\bmodel surfaces?\b", re.IGNORECASE),
    ("version label", "v2026-03-28", r"\bv\d{4}-\d{2}-\d{2}\b", re.IGNORECASE),
    ("internal model code", "A1", r"\b(?:A\d|B\d|M\d(?:_[A-Za-z0-9]+)?)\b", 0),
]

AMA_CSL_BASENAME = "american-medical-association.csl"
BLOCKED_RECOMMENDED_ACTION = "stop_current_run_and_rewrite_medical_surface"
CLEAR_RECOMMENDED_ACTION = "continue_current_write_route"
PUBLICATION_PROFILE = "general_medical_journal"
METHODS_IMPLEMENTATION_MANIFEST_BASENAME = "methods_implementation_manifest.json"
RESULTS_NARRATIVE_MAP_BASENAME = "results_narrative_map.json"
FIGURE_SEMANTICS_MANIFEST_BASENAME = "figure_semantics_manifest.json"
DERIVED_ANALYSIS_MANIFEST_BASENAME = "derived_analysis_manifest.json"
REPRODUCIBILITY_SUPPLEMENT_BASENAME = "manuscript_safe_reproducibility_supplement.json"
ENDPOINT_PROVENANCE_NOTE_BASENAME = "endpoint_provenance_note.md"
RESULTS_NARRATION_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    ("figure shows", "Figure 1 shows", r"\bFigure\s+\d+[A-Za-z]?\s+shows\b", re.IGNORECASE),
    ("figure illustrates", "Figure 1 illustrates", r"\bFigure\s+\d+[A-Za-z]?\s+illustrates\b", re.IGNORECASE),
    ("figure demonstrates", "Figure 1 demonstrates", r"\bFigure\s+\d+[A-Za-z]?\s+demonstrates\b", re.IGNORECASE),
    ("table shows", "Table 1 shows", r"\bTable\s+\d+[A-Za-z]?\s+shows\b", re.IGNORECASE),
    ("table summarizes", "Table 1 summarizes", r"\bTable\s+\d+[A-Za-z]?\s+summarizes\b", re.IGNORECASE),
    ("table presents", "Table 1 presents", r"\bTable\s+\d+[A-Za-z]?\s+presents\b", re.IGNORECASE),
]
METHOD_LABEL_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    ("knowledge-guided", "knowledge-guided", r"\bknowledge-guided\b", re.IGNORECASE),
    ("causal", "causal", r"\bcausal\b", re.IGNORECASE),
    ("mechanistic", "mechanistic", r"\bmechanistic\b", re.IGNORECASE),
    ("calibration-first", "calibration-first", r"\bcalibration-first\b", re.IGNORECASE),
]


def get_forbidden_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [(pattern_id, phrase, re.compile(pattern, flags=flags)) for pattern_id, phrase, pattern, flags in FORBIDDEN_PATTERN_SPECS]


def get_results_narration_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [
        (pattern_id, phrase, re.compile(pattern, flags=flags))
        for pattern_id, phrase, pattern, flags in RESULTS_NARRATION_PATTERN_SPECS
    ]


def get_methodology_label_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [
        (pattern_id, phrase, re.compile(pattern, flags=flags))
        for pattern_id, phrase, pattern, flags in METHOD_LABEL_PATTERN_SPECS
    ]


def ama_defaults_regex() -> re.Pattern[str]:
    return re.compile(
        rf"^\s*csl:\s*(?:\.\./)?(?:latex/)?{re.escape(AMA_CSL_BASENAME)}\s*$",
        flags=re.MULTILINE,
    )


def _missing_required_fields(item: object, fields: tuple[str, ...]) -> list[str]:
    if not isinstance(item, dict):
        return list(fields)
    missing: list[str] = []
    for field in fields:
        value = item.get(field)
        if isinstance(value, list):
            if not value:
                missing.append(field)
        elif not str(value or "").strip():
            missing.append(field)
    return missing


def validate_methods_implementation_manifest(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    required_top_level = (
        "study_design",
        "model_registry",
        "software_stack",
        "statistical_analysis",
        "causal_boundary",
    )
    missing_top_level = [key for key in required_top_level if key not in payload]
    if missing_top_level:
        return [f"missing top-level keys: {', '.join(missing_top_level)}"]

    study_design = payload.get("study_design")
    if not isinstance(study_design, dict):
        return ["study_design must be an object"]
    study_design_fields = (
        "center",
        "time_window",
        "study_design",
        "ethics",
        "inclusion_criteria",
        "exclusion_criteria",
        "cohort_definition",
        "endpoint_definition",
        "variable_definitions",
        "split_strategy",
        "missing_data_strategy",
        "missing_data_policy_id",
        "case_mix_summary",
        "applicability_boundary",
    )
    missing_study_design_fields = [field for field in study_design_fields if not str(study_design.get(field) or "").strip()]
    if missing_study_design_fields:
        return [f"missing study_design fields: {', '.join(missing_study_design_fields)}"]

    model_registry = payload.get("model_registry")
    if not isinstance(model_registry, list) or not model_registry:
        return ["model_registry must contain at least one model"]
    model_fields = (
        "model_id",
        "manuscript_name",
        "role",
        "family",
        "origin",
        "inputs",
        "input_scope",
        "feature_construction",
        "predictor_selection_strategy",
        "target",
        "fit_procedure",
        "selection_rationale",
        "comparison_rationale",
        "claim_boundary",
    )
    for index, model in enumerate(model_registry):
        missing_model_fields = _missing_required_fields(model, model_fields)
        if missing_model_fields:
            return [f"missing model_registry[{index}] fields: {', '.join(missing_model_fields)}"]

    software_stack = payload.get("software_stack")
    if not isinstance(software_stack, list) or not software_stack:
        return ["software_stack must contain at least one package"]
    for item in software_stack:
        if not isinstance(item, dict):
            return ["software_stack entries must be objects"]
        if not str(item.get("package") or "").strip() or not str(item.get("version") or "").strip():
            return ["each software_stack entry must include package and version"]

    statistical_analysis = payload.get("statistical_analysis")
    if not isinstance(statistical_analysis, dict):
        return ["statistical_analysis must be an object"]
    if not statistical_analysis.get("primary_metrics") or not str(statistical_analysis.get("subgroup_strategy") or "").strip():
        return ["statistical_analysis must include primary_metrics and subgroup_strategy"]

    causal_boundary = payload.get("causal_boundary")
    if not isinstance(causal_boundary, dict):
        return ["causal_boundary must be an object"]
    causal_fields = ("claim_level", "allowed_language", "not_allowed")
    missing_causal_fields = [field for field in causal_fields if not str(causal_boundary.get(field) or "").strip()]
    if missing_causal_fields:
        return [f"missing causal_boundary fields: {', '.join(missing_causal_fields)}"]

    method_labels = payload.get("method_labels")
    if method_labels is not None:
        if not isinstance(method_labels, list):
            return ["method_labels must be a list when present"]
        for item in method_labels:
            if not isinstance(item, dict):
                return ["method_labels entries must be objects"]
            label_fields = ("label", "operational_definition", "implementation_anchor")
            missing_label_fields = [field for field in label_fields if not str(item.get(field) or "").strip()]
            if missing_label_fields:
                return [f"missing method_labels fields: {', '.join(missing_label_fields)}"]

    return []


def validate_results_narrative_map(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        return ["sections must contain at least one results section"]
    required_fields = (
        "section_id",
        "section_title",
        "research_question",
        "direct_answer",
        "supporting_display_items",
        "key_quantitative_findings",
        "clinical_meaning",
        "boundary",
    )
    for index, section in enumerate(sections):
        missing_fields = _missing_required_fields(section, required_fields)
        if missing_fields:
            return [f"missing sections[{index}] fields: {', '.join(missing_fields)}"]
    return []


def validate_figure_semantics_manifest(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    figures = payload.get("figures")
    if not isinstance(figures, list) or not figures:
        return ["figures must contain at least one figure entry"]
    required_fields = (
        "figure_id",
        "story_role",
        "research_question",
        "direct_message",
        "clinical_implication",
        "interpretation_boundary",
        "panel_messages",
        "legend_glossary",
        "threshold_semantics",
        "stratification_basis",
        "recommendation_boundary",
        "renderer_contract",
    )
    panel_fields = ("panel_id", "message")
    glossary_fields = ("term", "explanation")
    for index, figure in enumerate(figures):
        missing_fields = _missing_required_fields(figure, required_fields)
        if missing_fields:
            return [f"missing figures[{index}] fields: {', '.join(missing_fields)}"]
        panel_messages = figure.get("panel_messages")
        if not isinstance(panel_messages, list) or not panel_messages:
            return [f"figures[{index}].panel_messages must contain at least one panel message"]
        for panel_index, panel in enumerate(panel_messages):
            missing_panel_fields = _missing_required_fields(panel, panel_fields)
            if missing_panel_fields:
                return [
                    f"missing figures[{index}].panel_messages[{panel_index}] fields: {', '.join(missing_panel_fields)}"
                ]
        legend_glossary = figure.get("legend_glossary")
        if not isinstance(legend_glossary, list) or not legend_glossary:
            return [f"figures[{index}].legend_glossary must contain at least one glossary entry"]
        for glossary_index, glossary in enumerate(legend_glossary):
            missing_glossary_fields = _missing_required_fields(glossary, glossary_fields)
            if missing_glossary_fields:
                return [
                    f"missing figures[{index}].legend_glossary[{glossary_index}] fields: {', '.join(missing_glossary_fields)}"
                ]
        renderer_contract_payload = figure.get("renderer_contract")
        if not isinstance(renderer_contract_payload, dict):
            return [f"figures[{index}].renderer_contract must be an object"]
        renderer_contract_errors = figure_renderer_contract.validate_renderer_contract(renderer_contract_payload)
        if renderer_contract_errors:
            return [f"figures[{index}].renderer_contract invalid: {'; '.join(renderer_contract_errors)}"]
    return []


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _path_suffixes(paths: list[str]) -> set[str]:
    suffixes: set[str] = set()
    for path in paths:
        match = re.search(r"\.([A-Za-z0-9]+)$", path)
        if match:
            suffixes.add(match.group(1).lower())
    return suffixes


def validate_figure_catalog(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    figures = payload.get("figures")
    if not isinstance(figures, list):
        return ["figures must be a list"]
    for index, figure in enumerate(figures):
        if not isinstance(figure, dict):
            return [f"figures[{index}] must be an object"]
        required_fields = (
            "figure_id",
            "template_id",
            "renderer_family",
            "paper_role",
            "input_schema_id",
            "qc_profile",
            "qc_result",
        )
        missing_fields = _missing_required_fields(figure, required_fields)
        if missing_fields:
            return [f"missing figures[{index}] fields: {', '.join(missing_fields)}"]
        qc_result = figure.get("qc_result")
        if not isinstance(qc_result, dict) or not str(qc_result.get("status") or "").strip():
            return [f"figures[{index}].qc_result must be an object with non-empty status"]

        template_id = str(figure.get("template_id") or "").strip()
        renderer_family = str(figure.get("renderer_family") or "").strip()
        input_schema_id = str(figure.get("input_schema_id") or "").strip()
        qc_profile = str(figure.get("qc_profile") or "").strip()
        paper_role = str(figure.get("paper_role") or "").strip()
        export_paths = _normalize_string_list(figure.get("export_paths"))
        if not export_paths:
            export_paths = _normalize_string_list(figure.get("planned_exports"))
        if not export_paths:
            return [f"figures[{index}] must include export_paths or planned_exports"]

        if display_registry.is_evidence_figure_template(template_id):
            spec = display_registry.get_evidence_figure_spec(template_id)
            expected_qc_profile = spec.layout_qc_profile
        elif display_registry.is_illustration_shell(template_id):
            spec = display_registry.get_illustration_shell_spec(template_id)
            expected_qc_profile = spec.shell_qc_profile
        else:
            return [f"figures[{index}].template_id `{template_id}` is not registered"]

        required_qc_fields = ("status", "checked_at", "engine_id", "qc_profile", "layout_sidecar_path")
        missing_qc_fields = _missing_required_fields(qc_result, required_qc_fields)
        if missing_qc_fields:
            return [f"figures[{index}].qc_result missing fields: {', '.join(missing_qc_fields)}"]
        qc_status = str(qc_result.get("status") or "").strip()
        if qc_status not in {"pass", "fail"}:
            return [f"figures[{index}].qc_result.status `{qc_status}` must be `pass` or `fail`"]
        raw_audit_classes = qc_result.get("audit_classes", [])
        if not isinstance(raw_audit_classes, list):
            return [f"figures[{index}].qc_result.audit_classes must be a list"]
        audit_classes = _normalize_string_list(raw_audit_classes)
        if qc_status == "fail":
            return [f"figures[{index}].qc_result.status `fail` blocks publication with audit classes {audit_classes}"]
        qc_result_profile = str(qc_result.get("qc_profile") or "").strip()
        if qc_result_profile != expected_qc_profile:
            return [
                f"figures[{index}].qc_result.qc_profile `{qc_result_profile}` does not match registered qc profile `{expected_qc_profile}`"
            ]

        if renderer_family != spec.renderer_family:
            return [
                f"figures[{index}].renderer_family `{renderer_family}` does not match registered renderer `{spec.renderer_family}`"
            ]
        if input_schema_id != spec.input_schema_id:
            return [
                f"figures[{index}].input_schema_id `{input_schema_id}` does not match registered schema `{spec.input_schema_id}`"
            ]
        if qc_profile != expected_qc_profile:
            return [
                f"figures[{index}].qc_profile `{qc_profile}` does not match registered qc profile `{expected_qc_profile}`"
            ]
        if paper_role not in spec.allowed_paper_roles:
            return [f"figures[{index}].paper_role `{paper_role}` is not allowed for template_id `{template_id}`"]
        missing_export_formats = sorted(set(spec.required_exports) - _path_suffixes(export_paths))
        if missing_export_formats:
            return [
                f"figures[{index}].export_paths missing required export formats for template_id `{template_id}`: "
                f"{', '.join(missing_export_formats)}"
            ]
    return []


def validate_table_catalog(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    tables = payload.get("tables")
    if not isinstance(tables, list):
        return ["tables must be a list"]
    for index, table in enumerate(tables):
        if not isinstance(table, dict):
            return [f"tables[{index}] must be an object"]
        required_fields = (
            "table_id",
            "table_shell_id",
            "paper_role",
            "input_schema_id",
            "qc_profile",
            "qc_result",
        )
        missing_fields = _missing_required_fields(table, required_fields)
        if missing_fields:
            return [f"missing tables[{index}] fields: {', '.join(missing_fields)}"]
        qc_result = table.get("qc_result")
        if not isinstance(qc_result, dict) or not str(qc_result.get("status") or "").strip():
            return [f"tables[{index}].qc_result must be an object with non-empty status"]

        shell_id = str(table.get("table_shell_id") or "").strip()
        paper_role = str(table.get("paper_role") or "").strip()
        input_schema_id = str(table.get("input_schema_id") or "").strip()
        qc_profile = str(table.get("qc_profile") or "").strip()
        asset_paths = _normalize_string_list(table.get("asset_paths"))
        if not asset_paths:
            path_value = str(table.get("path") or "").strip()
            if path_value:
                asset_paths = [path_value]
        if not asset_paths:
            return [f"tables[{index}] must include asset_paths or path"]

        if not display_registry.is_table_shell(shell_id):
            return [f"tables[{index}].table_shell_id `{shell_id}` is not registered"]
        spec = display_registry.get_table_shell_spec(shell_id)
        if paper_role not in spec.allowed_paper_roles:
            return [f"tables[{index}].paper_role `{paper_role}` is not allowed for table_shell_id `{shell_id}`"]
        if input_schema_id != spec.input_schema_id:
            return [
                f"tables[{index}].input_schema_id `{input_schema_id}` does not match registered schema `{spec.input_schema_id}`"
            ]
        if qc_profile != spec.table_qc_profile:
            return [
                f"tables[{index}].qc_profile `{qc_profile}` does not match registered qc profile `{spec.table_qc_profile}`"
            ]
        missing_export_formats = sorted(set(spec.required_exports) - _path_suffixes(asset_paths))
        if missing_export_formats:
            return [
                f"tables[{index}].asset_paths missing required export formats for table_shell_id `{shell_id}`: "
                f"{', '.join(missing_export_formats)}"
            ]
    return []


def validate_derived_analysis_manifest(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    analyses = payload.get("analyses")
    if not isinstance(analyses, list) or not analyses:
        return ["analyses must contain at least one derived analysis entry"]
    required_fields = (
        "analysis_id",
        "linked_display_items",
        "purpose",
        "data_source",
        "derivation_procedure",
        "resampling_design",
        "refit_policy",
        "missing_data_handling",
        "missing_data_policy_id",
        "correlation_or_collinearity_assessment",
        "interpretation_boundary",
    )
    for index, analysis in enumerate(analyses):
        missing_fields = _missing_required_fields(analysis, required_fields)
        if missing_fields:
            return [f"missing analyses[{index}] fields: {', '.join(missing_fields)}"]
    return []


def validate_reproducibility_supplement(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    required_top_level = (
        "software_versions",
        "random_seed_policy",
        "key_hyperparameters",
        "missing_data_strategy",
        "missing_data_policy_id",
        "metric_definitions",
    )
    missing = [key for key in required_top_level if key not in payload]
    if missing:
        return [f"missing top-level keys: {', '.join(missing)}"]
    software_versions = payload.get("software_versions")
    if not isinstance(software_versions, list) or not software_versions:
        return ["software_versions must contain at least one package"]
    metric_definitions = payload.get("metric_definitions")
    if not isinstance(metric_definitions, list) or not metric_definitions:
        return ["metric_definitions must contain at least one metric definition"]
    if not str(payload.get("random_seed_policy") or "").strip():
        return ["random_seed_policy must be non-empty"]
    if not str(payload.get("missing_data_strategy") or "").strip():
        return ["missing_data_strategy must be non-empty"]
    if not str(payload.get("missing_data_policy_id") or "").strip():
        return ["missing_data_policy_id must be non-empty"]
    key_hyperparameters = payload.get("key_hyperparameters")
    if not isinstance(key_hyperparameters, list) or not key_hyperparameters:
        return ["key_hyperparameters must contain at least one model entry"]
    return []


def parse_endpoint_provenance_note(text: str) -> dict[str, str]:
    payload: dict[str, str] = {}
    pattern = re.compile(r"^\s*-\s*(?P<key>[A-Za-z_]+)\s*:\s*(?P<value>.+?)\s*$")
    for raw_line in text.splitlines():
        match = pattern.match(raw_line)
        if match:
            payload[match.group("key")] = match.group("value").strip()
    return payload


def validate_endpoint_provenance_note(text: str) -> list[str]:
    payload = parse_endpoint_provenance_note(text)
    required_fields = ("endpoint_name", "provenance_caveat", "manuscript_required_statement")
    missing = [field for field in required_fields if not str(payload.get(field) or "").strip()]
    if missing:
        return [f"missing endpoint provenance note fields: {', '.join(missing)}"]
    return []


def extract_defined_method_labels(payload: object) -> dict[str, dict[str, str]]:
    if not isinstance(payload, dict):
        return {}
    labels = payload.get("method_labels")
    if not isinstance(labels, list):
        return {}
    normalized: dict[str, dict[str, str]] = {}
    for item in labels:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip().lower()
        if not label:
            continue
        normalized[label] = {
            "operational_definition": str(item.get("operational_definition") or "").strip(),
            "implementation_anchor": str(item.get("implementation_anchor") or "").strip(),
        }
    return normalized


def build_intervention_message(report: dict[str, object]) -> str:
    examples = report.get("top_hits") or []
    example_text = "; ".join(
        f"{str(hit['path']).split('/')[-1]}::{hit['location']} -> `{hit['phrase']}`" for hit in examples[:6]
    ) or "none"
    blockers = ", ".join(report.get("blockers") or []) or "none"
    ama_clause = ""
    if "ama_pdf_defaults_missing" in (report.get("blockers") or []):
        ama_clause = (
            " Also wire AMA into the current PDF compile defaults by using "
            f"`{AMA_CSL_BASENAME}` from `paper/latex/`, then recompile `paper.pdf` and refresh "
            "`submission_minimal` from the same medical publication surface."
        )
    methods_clause = ""
    if "methods_implementation_manifest_missing_or_incomplete" in (report.get("blockers") or []):
        methods_clause = (
            f" Also create or complete `paper/{METHODS_IMPLEMENTATION_MANIFEST_BASENAME}` so it explicitly records cohort "
            "definition, endpoint definition, split strategy, missing-data strategy, a shared missing-data policy identifier, "
            "case mix, applicability boundary, model registry with input scope, feature construction, predictor-selection strategy, "
            "comparison rationale, software package and version, statistical analysis plan, and causal-language boundary."
        )
    results_clause = ""
    if "results_narrative_map_missing_or_incomplete" in (report.get("blockers") or []):
        results_clause = (
            f" Also create or complete `paper/{RESULTS_NARRATIVE_MAP_BASENAME}` so each results subsection is organized around "
            "a research question, a direct answer, key quantitative findings, supporting display items, clinical meaning, and "
            "claim boundary."
        )
    figure_semantics_clause = ""
    if "figure_semantics_manifest_missing_or_incomplete" in (report.get("blockers") or []):
        figure_semantics_clause = (
            f" Also create or complete `paper/{FIGURE_SEMANTICS_MANIFEST_BASENAME}` so every main-text figure records its "
            "research question, direct message, clinical implication, interpretation boundary, panel-level messages, glossary terms, "
            "threshold or stratification caveats, and a locked renderer contract. Evidence figures may use only "
            "`python` or `r_ggplot2`; illustration figures may use `python`, `r_ggplot2`, or `html_svg`. "
            "Do not allow fallback-on-failure; the only permitted failure action is `block_and_fix_environment`."
        )
    derived_analysis_clause = ""
    if "derived_analysis_manifest_missing_or_incomplete" in (report.get("blockers") or []):
        derived_analysis_clause = (
            f" Also create or complete `paper/{DERIVED_ANALYSIS_MANIFEST_BASENAME}` so every derived or secondary analysis records "
            "its purpose, source data, derivation procedure, resampling design, refit policy, missing-data handling, "
            "correlation/collinearity assessment, and interpretation boundary."
        )
    reproducibility_clause = ""
    if "manuscript_safe_reproducibility_supplement_missing_or_incomplete" in (report.get("blockers") or []):
        reproducibility_clause = (
            f" Also create or complete `paper/{REPRODUCIBILITY_SUPPLEMENT_BASENAME}` with manuscript-safe package versions, random seed policy, "
            "key hyperparameters, missing-data strategy, a shared missing-data policy identifier, and metric definitions."
        )
    missing_data_policy_clause = ""
    if "missing_data_policy_inconsistent" in (report.get("blockers") or []):
        missing_data_policy_clause = (
            " Also align missing-data documentation so `study_design.missing_data_policy_id`, every derived-analysis "
            "`missing_data_policy_id`, and the reproducibility supplement `missing_data_policy_id` point to the same manuscript-safe policy."
        )
    endpoint_clause = ""
    if "endpoint_provenance_note_missing_or_unapplied" in (report.get("blockers") or []):
        endpoint_clause = (
            f" Also create or complete `paper/{ENDPOINT_PROVENANCE_NOTE_BASENAME}` and make sure its manuscript-required statement appears on the manuscript-facing surface."
        )
    method_label_clause = ""
    if "undefined_methodology_labels_present" in (report.get("blockers") or []):
        method_label_clause = (
            " Any label such as `knowledge-guided`, `causal`, `mechanistic`, or `calibration-first` must carry a manuscript-checkable operational definition; otherwise rewrite it into a more conservative factual description."
        )
    narration_clause = ""
    if "figure_table_led_results_narration_present" in (report.get("blockers") or []):
        narration_clause = (
            " Rewrite the Results section so it no longer reads as `Figure/Table X shows ...`; each subsection should answer "
            "the medical question first, then cite figures or tables as support."
        )
    return (
        "Hard control message from Codex orchestration layer: stop the current manuscript continuation now. "
        f"The current manuscript-facing surface still violates the `{PUBLICATION_PROFILE}` contract and may not continue "
        "into more literature expansion, proofing, or finalize until these issues are fixed. "
        f"Controller blockers: {blockers}. "
        f"Concrete examples: {example_text}. "
        "Required next route: first rewrite manuscript-facing prose in `paper/draft.md` and `paper/build/review_manuscript.md`, "
        "then rewrite figure/table titles and captions in the catalogs so they no longer use engineering terms such as "
        "`deployment-facing`, `baseline-comparable`, `locked cohort`, `contract`, metric IDs such as "
        "`roc_auc`, `average_precision`, `brier_score`, `calibration_intercept`, `calibration_slope`, "
        "or tool/service references such as `deepscientist`, service URLs, or editing recommendations. "
        "Do not advertise tooling in figure captions. Do not reopen accepted figures unless in-figure visible text itself still "
        "contains a forbidden manuscript term."
        f"{ama_clause}{methods_clause}{results_clause}{figure_semantics_clause}{derived_analysis_clause}{reproducibility_clause}{missing_data_policy_clause}{endpoint_clause}{method_label_clause}{narration_clause} "
        "After those corrections, resume reviewer-style proofing or finalize."
    )
