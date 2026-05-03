from __future__ import annotations

import re

from med_autoscience import display_registry
from med_autoscience import figure_renderer_contract
from med_autoscience.policies.medical_reporting_contract import display_story_role_for_requirement_key

from med_autoscience.policies.medical_manuscript_draft_quality import (
    ANALYSIS_PLANE_JARGON_PATTERN_SPECS,
    FORBIDDEN_PATTERN_SPECS,
    METHOD_LABEL_PATTERN_SPECS,
    MEDICAL_JOURNAL_PROSE_PATTERN_SPECS,
    PUBLICATION_SURFACE_RESIDUE_PATTERN_SPECS,
    RESULTS_NARRATION_PATTERN_SPECS,
    build_work_report_residue_clause,
)

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
CLAIM_EVIDENCE_MAP_BASENAME = "claim_evidence_map.json"
EVIDENCE_LEDGER_BASENAME = "evidence_ledger.json"
REVIEW_LEDGER_BASENAME = "review_ledger.json"
MEDICAL_MANUSCRIPT_BLUEPRINT_BASENAME = "medical_manuscript_blueprint.json"
MEDICAL_PROSE_REVIEW_BASENAME = "medical_prose_review.json"
STATISTICAL_REVIEWER_AUDIT_BASENAME = "statistical_reviewer_audit.json"
PUBLIC_EVIDENCE_DECISIONS_KEY = "public_evidence_decisions"
PUBLIC_EVIDENCE_SURFACE_DECISIONS = frozenset(
    {
        "main_text_earned",
        "appendix_earned",
        "drop_from_manuscript",
    }
)
PUBLIC_EVIDENCE_EARNED_DECISIONS = frozenset(
    {
        "main_text_earned",
        "appendix_earned",
    }
)
_SETUP_STORY_ROLE_ALIASES = frozenset(
    {
        "study_setup",
        "study_population_and_design_anchor",
    }
)
INTRODUCTION_REQUIRED_PARAGRAPH_COUNT = 3
METHODS_REQUIRED_SUBSECTION_HEADINGS = (
    "Study design and cohort",
    "Variable definition and measurement",
    "Model building",
    "Validation framework",
)
RESULTS_MIN_SUBSECTION_COUNT = 2


def get_forbidden_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [(pattern_id, phrase, re.compile(pattern, flags=flags)) for pattern_id, phrase, pattern, flags in FORBIDDEN_PATTERN_SPECS]


def get_results_narration_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [
        (pattern_id, phrase, re.compile(pattern, flags=flags))
        for pattern_id, phrase, pattern, flags in RESULTS_NARRATION_PATTERN_SPECS
    ]


def get_analysis_plane_jargon_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [
        (pattern_id, phrase, re.compile(pattern, flags=flags))
        for pattern_id, phrase, pattern, flags in ANALYSIS_PLANE_JARGON_PATTERN_SPECS
    ]


def get_publication_surface_residue_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [
        (pattern_id, phrase, re.compile(pattern, flags=flags))
        for pattern_id, phrase, pattern, flags in PUBLICATION_SURFACE_RESIDUE_PATTERN_SPECS
    ]


def get_methodology_label_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [
        (pattern_id, phrase, re.compile(pattern, flags=flags))
        for pattern_id, phrase, pattern, flags in METHOD_LABEL_PATTERN_SPECS
    ]


def get_medical_journal_prose_patterns() -> list[tuple[str, str, re.Pattern[str]]]:
    return [
        (pattern_id, phrase, re.compile(pattern, flags=flags))
        for pattern_id, phrase, pattern, flags in MEDICAL_JOURNAL_PROSE_PATTERN_SPECS
    ]


def validate_medical_manuscript_blueprint(payload: object) -> list[str]:
    from med_autoscience.medical_manuscript_blueprint import validate_medical_manuscript_blueprint as _validator

    return _validator(payload)


def validate_medical_prose_review(payload: object) -> list[str]:
    from med_autoscience.medical_prose_review import validate_medical_prose_review as _validator

    return _validator(payload)


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


def _story_role_matches_expected(*, observed_story_role: str, expected_story_role: str) -> bool:
    if observed_story_role == expected_story_role:
        return True
    if expected_story_role == "study_setup" and observed_story_role in _SETUP_STORY_ROLE_ALIASES:
        return True
    return False


def _normalize_figure_semantics_entries(payload: dict[object, object]) -> list[dict[object, object]] | None:
    figures = payload.get("figures")
    if isinstance(figures, list):
        return [item for item in figures if isinstance(item, dict)]
    if isinstance(figures, dict):
        entries: list[dict[object, object]] = []
        for figure_id, raw_entry in figures.items():
            if not isinstance(raw_entry, dict):
                continue
            entry = dict(raw_entry)
            if not str(entry.get("figure_id") or "").strip():
                entry["figure_id"] = str(figure_id)
            entries.append(entry)
        return entries
    return None


def _renderer_contract_value(renderer_contract: object, *field_names: str) -> str:
    if not isinstance(renderer_contract, dict):
        return ""
    for field_name in field_names:
        value = str(renderer_contract.get(field_name) or "").strip()
        if value:
            return value
    return ""


def _figure_semantics_list_is_valid(value: object) -> bool:
    return isinstance(value, list) and any(str(item or "").strip() for item in value)


def _figure_semantics_mapping_is_valid(value: object) -> bool:
    return isinstance(value, dict) and any(str(key or "").strip() and str(item or "").strip() for key, item in value.items())


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
    figures = _normalize_figure_semantics_entries(payload)
    if not figures:
        return ["figures must contain at least one figure entry"]
    legacy_required_fields = (
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
    keyed_required_fields = (
        "figure_id",
        "title",
        "research_question",
        "direct_message",
        "clinical_implication",
        "interpretation_boundary",
        "panel_level_messages",
        "glossary_terms",
        "threshold_or_stratification_caveats",
        "renderer_contract",
    )
    panel_fields = ("panel_id", "message")
    glossary_fields = ("term", "explanation")
    for index, figure in enumerate(figures):
        renderer_contract_payload = figure.get("renderer_contract")
        if not isinstance(renderer_contract_payload, dict):
            return [f"figures[{index}].renderer_contract must be an object"]
        has_keyed_shape = (
            "panel_level_messages" in figure
            or "glossary_terms" in figure
            or "threshold_or_stratification_caveats" in figure
            or "allowed_renderers" in renderer_contract_payload
            or "renderer" in renderer_contract_payload
        )
        required_fields = keyed_required_fields if has_keyed_shape else legacy_required_fields
        missing_fields = _missing_required_fields(figure, required_fields)
        if missing_fields:
            return [f"missing figures[{index}] fields: {', '.join(missing_fields)}"]
        if has_keyed_shape:
            if not _figure_semantics_list_is_valid(figure.get("panel_level_messages")):
                return [f"figures[{index}].panel_level_messages must contain at least one panel message"]
            if not _figure_semantics_mapping_is_valid(figure.get("glossary_terms")):
                return [f"figures[{index}].glossary_terms must contain at least one glossary term"]
            if not _figure_semantics_list_is_valid(figure.get("threshold_or_stratification_caveats")):
                return [
                    f"figures[{index}].threshold_or_stratification_caveats must contain at least one caveat"
                ]
            renderer_family = _renderer_contract_value(renderer_contract_payload, "renderer", "renderer_family")
            if not renderer_family:
                return [f"figures[{index}].renderer_contract renderer must be non-empty"]
            allowed_renderers = renderer_contract_payload.get("allowed_renderers")
            if isinstance(allowed_renderers, list):
                normalized_allowed_renderers = {
                    str(item or "").strip().lower() for item in allowed_renderers if str(item or "").strip()
                }
                if renderer_family.lower() not in normalized_allowed_renderers:
                    return [
                        f"figures[{index}].renderer_contract renderer `{renderer_family}` is not listed in allowed_renderers"
                    ]
            if renderer_contract_payload.get("fallback_on_failure") is not False:
                return [f"figures[{index}].renderer_contract fallback_on_failure must be false"]
            failure_action = str(renderer_contract_payload.get("failure_action") or "").strip()
            if failure_action != figure_renderer_contract.FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT:
                return [
                    f"figures[{index}].renderer_contract failure_action must be "
                    f"`{figure_renderer_contract.FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT}`"
                ]
        else:
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
            renderer_contract_errors = figure_renderer_contract.validate_renderer_contract(renderer_contract_payload)
            if renderer_contract_errors:
                return [f"figures[{index}].renderer_contract invalid: {'; '.join(renderer_contract_errors)}"]
        template_id = str(renderer_contract_payload.get("template_id") or "").strip()
        if template_id and display_registry.is_illustration_shell(template_id):
            shell_id = display_registry.get_illustration_shell_spec(template_id).shell_id
            expected_story_role = display_story_role_for_requirement_key(shell_id)
            if expected_story_role == "study_setup":
                observed_story_role = str(figure.get("story_role") or "").strip()
                if not _story_role_matches_expected(
                    observed_story_role=observed_story_role,
                    expected_story_role=expected_story_role,
                ):
                    return [
                        f"figures[{index}].story_role "
                        f"`{observed_story_role}` does not match canonical story role "
                        f"`{expected_story_role}` for illustration shell `{shell_id}`"
                    ]
    return []


def validate_claim_evidence_map(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        return ["claims must contain at least one claim entry"]
    required_fields = (
        "claim_id",
        "statement",
        "status",
        "paper_role",
        "display_bindings",
        "sections",
        "evidence_items",
    )
    evidence_item_fields = ("item_id", "support_level", "source_paths")
    for index, claim in enumerate(claims):
        missing_fields = _missing_required_fields(claim, required_fields)
        if missing_fields:
            return [f"missing claims[{index}] fields: {', '.join(missing_fields)}"]
        evidence_items = claim.get("evidence_items")
        if not isinstance(evidence_items, list) or not evidence_items:
            return [f"claims[{index}].evidence_items must contain at least one evidence item"]
        for evidence_index, evidence_item in enumerate(evidence_items):
            missing_evidence_fields = _missing_required_fields(evidence_item, evidence_item_fields)
            if missing_evidence_fields:
                return [
                    f"missing claims[{index}].evidence_items[{evidence_index}] fields: {', '.join(missing_evidence_fields)}"
                ]
    return []


def validate_evidence_ledger(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        return ["claims must contain at least one claim entry"]
    required_fields = (
        "claim_id",
        "statement",
        "status",
        "submission_scope",
        "evidence",
        "gaps",
        "recommended_actions",
    )
    evidence_fields = ("evidence_id", "kind", "source_paths", "support_level", "summary")
    gap_fields = ("gap_id", "description", "submission_impact")
    recommended_action_fields = ("action_id", "priority", "description")
    for index, claim in enumerate(claims):
        missing_fields = _missing_required_fields(claim, required_fields)
        if missing_fields:
            return [f"missing claims[{index}] fields: {', '.join(missing_fields)}"]
        evidence_items = claim.get("evidence")
        if not isinstance(evidence_items, list) or not evidence_items:
            return [f"claims[{index}].evidence must contain at least one evidence entry"]
        for evidence_index, evidence_item in enumerate(evidence_items):
            missing_evidence_fields = _missing_required_fields(evidence_item, evidence_fields)
            if missing_evidence_fields:
                return [
                    f"missing claims[{index}].evidence[{evidence_index}] fields: {', '.join(missing_evidence_fields)}"
                ]
        gaps = claim.get("gaps")
        if not isinstance(gaps, list) or not gaps:
            return [f"claims[{index}].gaps must contain at least one gap entry"]
        for gap_index, gap in enumerate(gaps):
            missing_gap_fields = _missing_required_fields(gap, gap_fields)
            if missing_gap_fields:
                return [
                    f"missing claims[{index}].gaps[{gap_index}] fields: {', '.join(missing_gap_fields)}"
                ]
        recommended_actions = claim.get("recommended_actions")
        if not isinstance(recommended_actions, list) or not recommended_actions:
            return [f"claims[{index}].recommended_actions must contain at least one action entry"]
        for action_index, action in enumerate(recommended_actions):
            missing_action_fields = _missing_required_fields(action, recommended_action_fields)
            if missing_action_fields:
                return [
                    f"missing claims[{index}].recommended_actions[{action_index}] fields: "
                    f"{', '.join(missing_action_fields)}"
                ]
    return []


def validate_review_ledger(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    schema_version = payload.get("schema_version")
    if schema_version != 1:
        return ["schema_version must be 1"]
    concerns = payload.get("concerns")
    if not isinstance(concerns, list) or not concerns:
        return ["concerns must contain at least one reviewer concern"]
    required_fields = (
        "concern_id",
        "reviewer_id",
        "summary",
        "severity",
        "status",
        "owner_action",
        "revision_links",
    )
    allowed_severity = {"critical", "major", "minor", "editorial"}
    allowed_status = {"open", "in_progress", "resolved", "deferred"}
    revision_link_fields = ("revision_id", "revision_log_path")
    for index, concern in enumerate(concerns):
        missing_fields = _missing_required_fields(concern, required_fields)
        if missing_fields:
            return [f"missing concerns[{index}] fields: {', '.join(missing_fields)}"]
        severity = str(concern.get("severity") or "").strip()
        if severity not in allowed_severity:
            return [
                f"concerns[{index}].severity `{severity}` must be one of {', '.join(sorted(allowed_severity))}"
            ]
        status = str(concern.get("status") or "").strip()
        if status not in allowed_status:
            return [f"concerns[{index}].status `{status}` must be one of {', '.join(sorted(allowed_status))}"]
        revision_links = concern.get("revision_links")
        if not isinstance(revision_links, list) or not revision_links:
            return [f"concerns[{index}].revision_links must contain at least one revision link"]
        for revision_index, revision_link in enumerate(revision_links):
            missing_revision_fields = _missing_required_fields(revision_link, revision_link_fields)
            if missing_revision_fields:
                return [
                    "missing concerns"
                    f"[{index}].revision_links[{revision_index}] fields: {', '.join(missing_revision_fields)}"
                ]
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


def validate_public_evidence_decisions(payload: object) -> list[str]:
    if not isinstance(payload, list) or not payload:
        return ["public_evidence_decisions must contain at least one decision entry"]
    required_fields = (
        "entry_id",
        "dataset_ids",
        "analysis_ids",
        "paper_surface_decision",
        "decision_rationale",
    )
    earned_fields = (
        "result_statement",
        "linked_display_items",
        "linked_sections",
        "interpretation_boundary",
    )
    for index, item in enumerate(payload):
        missing_fields = _missing_required_fields(item, required_fields)
        if missing_fields:
            return [f"missing public_evidence_decisions[{index}] fields: {', '.join(missing_fields)}"]
        decision = str(item.get("paper_surface_decision") or "").strip()
        if decision not in PUBLIC_EVIDENCE_SURFACE_DECISIONS:
            return [
                "public_evidence_decisions"
                f"[{index}].paper_surface_decision `{decision}` must be one of "
                + ", ".join(sorted(PUBLIC_EVIDENCE_SURFACE_DECISIONS))
            ]
        if decision in PUBLIC_EVIDENCE_EARNED_DECISIONS:
            missing_earned_fields = _missing_required_fields(item, earned_fields)
            if missing_earned_fields:
                return [
                    f"missing public_evidence_decisions[{index}] earned fields: {', '.join(missing_earned_fields)}"
                ]
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
    prose_structure_clause = ""
    if "introduction_structure_missing_or_incomplete" in (report.get("blockers") or []):
        prose_structure_clause += (
            " Rewrite the Introduction into a formal three-paragraph medical structure: clinical background and follow-up context, "
            "current study landscape with concrete gaps, and the present study objective plus design."
        )
    if "methods_section_structure_missing_or_incomplete" in (report.get("blockers") or []):
        prose_structure_clause += (
            " Rewrite the manuscript Methods prose so it includes the exact reviewer-facing subsections "
            f"`{METHODS_REQUIRED_SUBSECTION_HEADINGS[0]}`, `{METHODS_REQUIRED_SUBSECTION_HEADINGS[1]}`, "
            f"`{METHODS_REQUIRED_SUBSECTION_HEADINGS[2]}`, and `{METHODS_REQUIRED_SUBSECTION_HEADINGS[3]}`."
        )
    results_clause = ""
    if "results_narrative_map_missing_or_incomplete" in (report.get("blockers") or []):
        results_clause = (
            f" Also create or complete `paper/{RESULTS_NARRATIVE_MAP_BASENAME}` so each results subsection is organized around "
            "a research question, a direct answer, key quantitative findings, supporting display items, clinical meaning, and "
            "claim boundary."
        )
    if "results_section_structure_missing_or_incomplete" in (report.get("blockers") or []):
        prose_structure_clause += (
            f" Rewrite the Results prose into at least {RESULTS_MIN_SUBSECTION_COUNT} reviewer-facing subsections with explicit headings "
            "instead of a single undifferentiated block."
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
    evidence_ledger_clause = ""
    if "evidence_ledger_missing_or_incomplete" in (report.get("blockers") or []):
        evidence_ledger_clause = (
            f" Also create or complete `paper/{EVIDENCE_LEDGER_BASENAME}` so each submission-facing claim records a "
            "claim identifier, statement, claim status, submission scope, direct evidence entries with source paths and support level, "
            "explicit gaps, and reviewer-facing recommended actions."
        )
    derived_analysis_clause = ""
    if "derived_analysis_manifest_missing_or_incomplete" in (report.get("blockers") or []):
        derived_analysis_clause = (
            f" Also create or complete `paper/{DERIVED_ANALYSIS_MANIFEST_BASENAME}` so every derived or secondary analysis records "
            "its purpose, source data, derivation procedure, resampling design, refit policy, missing-data handling, "
            "correlation/collinearity assessment, and interpretation boundary."
        )
    public_evidence_clause = ""
    if "public_evidence_decisions_missing_or_incomplete" in (report.get("blockers") or []):
        public_evidence_clause = (
            f" Also add a top-level `paper/{DERIVED_ANALYSIS_MANIFEST_BASENAME}` field named "
            f"`{PUBLIC_EVIDENCE_DECISIONS_KEY}` so every retained public dataset is explicitly marked as "
            "`main_text_earned`, `appendix_earned`, or `drop_from_manuscript`, with a decision rationale. "
            "Any earned public route must also declare the result statement, linked display items, linked manuscript "
            "sections, and interpretation boundary."
        )
    public_surface_clause = ""
    if "paper_facing_public_data_without_earned_evidence" in (report.get("blockers") or []):
        public_surface_clause = (
            " Remove public-dataset mentions from the title, abstract, main text, figure catalog, and table catalog "
            "unless those datasets have already earned a manuscript-facing role through an explicit public-evidence decision."
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
    prose_evidence_clause = ""
    if int(report.get("medical_prose_reviewer_evidence_hit_count") or 0):
        prose_evidence_clause = (
            " Mechanical prose hits, including figure/table-led Results sentences or question-form prose, are evidence "
            "snippets for the AI prose reviewer; they do not independently authorize a subjective style blocker."
        )
    medical_prose_clause = ""
    if "medical_journal_prose_style_not_met" in (report.get("blockers") or []):
        medical_prose_clause = (
            " Rewrite the manuscript voice to neutral general-medical-journal prose: open from the clinical problem, "
            "move through the evidence gap to the study objective, make clinical findings rather than figures or tables "
            "the grammatical subject of Results sentences, avoid unsupported no-difference or best/novel claims, and write "
            "the Discussion as principal finding, relation to prior work, clinical interpretation, limitations, and conservative conclusion."
        )
    report_residue_clause = build_work_report_residue_clause(report.get("top_hits"))
    return (
        "Hard control message from Codex orchestration layer: stop the current manuscript continuation now. "
        f"The current manuscript-facing surface still violates the `{PUBLICATION_PROFILE}` contract and may not continue "
        "into more literature expansion, proofing, or finalize until these issues are fixed. "
        f"Controller blockers: {blockers}. "
        f"Concrete examples: {example_text}. "
        "Required next route: first rewrite manuscript-facing prose in `paper/draft.md` and `paper/build/review_manuscript.md`, "
        "then rewrite figure/table titles and captions in the catalogs so they no longer use engineering terms such as "
        "`deployment-facing`, `baseline-comparable`, `locked cohort`, `paper-facing`, `limitation-aware`, "
        "`supportive endpoint`, `frozen analysis outputs`, `contract`, metric IDs such as "
        "`roc_auc`, `average_precision`, `brier_score`, `calibration_intercept`, `calibration_slope`, "
        "or tool/service references such as `deepscientist`, service URLs, or editing recommendations. "
        "Do not advertise tooling in figure captions. Do not reopen accepted figures unless in-figure visible text itself still "
        "contains a forbidden manuscript term."
        f"{ama_clause}{methods_clause}{prose_structure_clause}{results_clause}{figure_semantics_clause}{evidence_ledger_clause}{derived_analysis_clause}{public_evidence_clause}{public_surface_clause}{reproducibility_clause}{missing_data_policy_clause}{endpoint_clause}{method_label_clause}{prose_evidence_clause}{medical_prose_clause}{report_residue_clause} "
        "After those corrections, resume reviewer-style proofing or finalize."
    )
