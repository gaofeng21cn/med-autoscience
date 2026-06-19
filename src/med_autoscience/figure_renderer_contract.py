from __future__ import annotations

from med_autoscience import display_registry


FIGURE_SEMANTICS_EVIDENCE = "evidence"
FIGURE_SEMANTICS_ILLUSTRATION = "illustration"
FIGURE_SEMANTICS_SUBMISSION_COMPANION = "submission_companion"
RENDERER_FAMILY_PYTHON = "python"
RENDERER_FAMILY_R_GGPLOT2 = "r_ggplot2"
RENDERER_FAMILY_HTML_SVG = "html_svg"
FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT = "block_and_fix_environment"

_ALLOWED_RENDERERS_BY_SEMANTICS: dict[str, tuple[str, ...]] = {
    FIGURE_SEMANTICS_EVIDENCE: (
        RENDERER_FAMILY_R_GGPLOT2,
    ),
    FIGURE_SEMANTICS_ILLUSTRATION: (
        RENDERER_FAMILY_PYTHON,
        RENDERER_FAMILY_R_GGPLOT2,
        RENDERER_FAMILY_HTML_SVG,
    ),
    FIGURE_SEMANTICS_SUBMISSION_COMPANION: (
        RENDERER_FAMILY_PYTHON,
        RENDERER_FAMILY_R_GGPLOT2,
        RENDERER_FAMILY_HTML_SVG,
    ),
}


def _normalize_string(value: object) -> str:
    return str(value or "").strip().lower()


def _normalize_display_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_non_empty_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_normalize_display_string(item) for item in value if _normalize_display_string(item)]


def _validate_evidence_display_to_claim_fields(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []
    required_string_fields = (
        ("core_claim", "core_claim must be non-empty for evidence figure renderer contracts"),
        ("panel_role", "panel_role must be non-empty for evidence figure renderer contracts"),
    )
    for field_name, error_message in required_string_fields:
        if not _normalize_display_string(payload.get(field_name)):
            errors.append(error_message)

    required_list_fields = (
        ("evidence_chain", "evidence_chain must contain at least one reference for evidence figure renderer contracts"),
        (
            "source_data_refs",
            "source_data_refs must contain at least one reference for evidence figure renderer contracts",
        ),
        ("statistics_refs", "statistics_refs must contain at least one reference for evidence figure renderer contracts"),
        ("qa_risks", "qa_risks must contain at least one risk for evidence figure renderer contracts"),
    )
    for field_name, error_message in required_list_fields:
        if not _normalize_non_empty_string_list(payload.get(field_name)):
            errors.append(error_message)

    export_contract = payload.get("export_contract")
    if not isinstance(export_contract, dict) or not export_contract:
        errors.append("export_contract must be a non-empty object for evidence figure renderer contracts")
    return errors


def _semantics_allowed_families(figure_semantics: str) -> tuple[tuple[str, ...], list[str]]:
    if not figure_semantics:
        return (), ["figure_semantics must be non-empty"]
    try:
        return allowed_renderer_families(figure_semantics), []
    except ValueError as exc:
        return (), [str(exc)]


def _validate_renderer_family(
    *,
    renderer_family: str,
    figure_semantics: str,
    allowed_families: tuple[str, ...],
) -> list[str]:
    supported_families = {
        RENDERER_FAMILY_PYTHON,
        RENDERER_FAMILY_R_GGPLOT2,
        RENDERER_FAMILY_HTML_SVG,
    }
    if not renderer_family:
        return ["renderer_family must be non-empty"]
    if renderer_family not in supported_families:
        supported = ", ".join(sorted(supported_families))
        return [f"Unsupported renderer_family `{renderer_family}`; expected one of: {supported}"]
    if figure_semantics and allowed_families and renderer_family not in allowed_families:
        allowed = ", ".join(allowed_families)
        return [
            f"renderer_family `{renderer_family}` is not allowed for figure_semantics `{figure_semantics}`; "
            f"allowed: {allowed}"
        ]
    return []


def _validate_required_text_fields(payload: dict[str, object]) -> list[str]:
    required_fields = (
        ("selection_rationale", "selection_rationale must be non-empty"),
        ("template_id", "template_id must be non-empty"),
        ("layout_qc_profile", "layout_qc_profile must be non-empty"),
    )
    return [
        error_message
        for field_name, error_message in required_fields
        if not _normalize_display_string(payload.get(field_name))
    ]


def _required_exports(payload: dict[str, object]) -> tuple[tuple[str, ...], list[str]]:
    required_exports_raw = payload.get("required_exports")
    if isinstance(required_exports_raw, list):
        normalized_exports = tuple(_normalize_string(item) for item in required_exports_raw if _normalize_string(item))
        if normalized_exports:
            return normalized_exports, []
    return (), ["required_exports must contain at least one export format"]


def _validate_failure_policy(payload: dict[str, object]) -> list[str]:
    fallback_on_failure = payload.get("fallback_on_failure")
    if not isinstance(fallback_on_failure, bool):
        return ["fallback_on_failure must be a boolean"]
    if fallback_on_failure:
        return ["fallback_on_failure must be false"]

    failure_action = _normalize_string(payload.get("failure_action"))
    if not failure_action:
        return ["failure_action must be non-empty"]
    if failure_action != FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT:
        return [f"failure_action must be `{FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT}`"]
    return []


def _registered_spec_errors(
    *,
    template_id: str,
    renderer_family: str,
    layout_qc_profile: str,
    required_exports: tuple[str, ...],
    registered_renderer_family: str,
    registered_layout_qc_profile: str,
    registered_required_exports: tuple[str, ...],
    layout_qc_label: str,
) -> list[str]:
    errors: list[str] = []
    if renderer_family and renderer_family != registered_renderer_family:
        errors.append(
            f"renderer_family `{renderer_family}` does not match registered renderer_family "
            f"`{registered_renderer_family}` for template_id `{template_id}`"
        )
    if layout_qc_profile and layout_qc_profile != registered_layout_qc_profile:
        errors.append(
            f"layout_qc_profile `{layout_qc_profile}` does not match registered {layout_qc_label} "
            f"`{registered_layout_qc_profile}` for template_id `{template_id}`"
        )
    if required_exports:
        missing_exports = [item for item in registered_required_exports if item not in required_exports]
        if missing_exports:
            errors.append(
                f"required_exports missing registered export formats for template_id `{template_id}`: "
                f"{', '.join(missing_exports)}"
            )
    return errors


def _validate_registered_evidence_template(
    *,
    template_id: str,
    renderer_family: str,
    layout_qc_profile: str,
    required_exports: tuple[str, ...],
) -> list[str]:
    if not display_registry.is_evidence_figure_template(template_id):
        return [f"template_id `{template_id}` is not a registered evidence figure template"]
    spec = display_registry.get_evidence_figure_spec(template_id)
    return _registered_spec_errors(
        template_id=template_id,
        renderer_family=renderer_family,
        layout_qc_profile=layout_qc_profile,
        required_exports=required_exports,
        registered_renderer_family=spec.renderer_family,
        registered_layout_qc_profile=spec.layout_qc_profile,
        registered_required_exports=spec.required_exports,
        layout_qc_label="layout_qc_profile",
    )


def _validate_registered_illustration_shell(
    *,
    template_id: str,
    renderer_family: str,
    layout_qc_profile: str,
    required_exports: tuple[str, ...],
) -> list[str]:
    if not display_registry.is_illustration_shell(template_id):
        return [f"template_id `{template_id}` is not a registered illustration shell"]
    spec = display_registry.get_illustration_shell_spec(template_id)
    return _registered_spec_errors(
        template_id=template_id,
        renderer_family=renderer_family,
        layout_qc_profile=layout_qc_profile,
        required_exports=required_exports,
        registered_renderer_family=spec.renderer_family,
        registered_layout_qc_profile=spec.shell_qc_profile,
        registered_required_exports=spec.required_exports,
        layout_qc_label="shell_qc_profile",
    )


def _validate_registered_template(
    *,
    figure_semantics: str,
    template_id: str,
    renderer_family: str,
    layout_qc_profile: str,
    required_exports: tuple[str, ...],
) -> list[str]:
    if figure_semantics == FIGURE_SEMANTICS_EVIDENCE and template_id:
        return _validate_registered_evidence_template(
            template_id=template_id,
            renderer_family=renderer_family,
            layout_qc_profile=layout_qc_profile,
            required_exports=required_exports,
        )
    if _uses_illustration_shell_contract(figure_semantics) and template_id:
        return _validate_registered_illustration_shell(
            template_id=template_id,
            renderer_family=renderer_family,
            layout_qc_profile=layout_qc_profile,
            required_exports=required_exports,
        )
    return []


def allowed_renderer_families(figure_semantics: str) -> tuple[str, ...]:
    normalized = _normalize_string(figure_semantics)
    if normalized not in _ALLOWED_RENDERERS_BY_SEMANTICS:
        supported = ", ".join(sorted(_ALLOWED_RENDERERS_BY_SEMANTICS))
        raise ValueError(f"Unsupported figure_semantics `{figure_semantics}`; expected one of: {supported}")
    return _ALLOWED_RENDERERS_BY_SEMANTICS[normalized]


def _uses_illustration_shell_contract(figure_semantics: str) -> bool:
    normalized = _normalize_string(figure_semantics)
    return normalized in {
        FIGURE_SEMANTICS_ILLUSTRATION,
        FIGURE_SEMANTICS_SUBMISSION_COMPANION,
    }


def validate_renderer_contract(payload: object, *, label: str = "renderer_contract") -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be a JSON object"]

    errors: list[str] = []
    figure_semantics = _normalize_string(payload.get("figure_semantics"))
    allowed_families, semantics_errors = _semantics_allowed_families(figure_semantics)
    errors.extend(semantics_errors)

    renderer_family = _normalize_string(payload.get("renderer_family"))
    errors.extend(
        _validate_renderer_family(
            renderer_family=renderer_family,
            figure_semantics=figure_semantics,
            allowed_families=allowed_families,
        )
    )

    errors.extend(_validate_required_text_fields(payload))
    required_exports, export_errors = _required_exports(payload)
    errors.extend(export_errors)
    errors.extend(_validate_failure_policy(payload))

    if figure_semantics == FIGURE_SEMANTICS_EVIDENCE:
        errors.extend(_validate_evidence_display_to_claim_fields(payload))

    errors.extend(
        _validate_registered_template(
            figure_semantics=figure_semantics,
            template_id=_normalize_display_string(payload.get("template_id")),
            renderer_family=renderer_family,
            layout_qc_profile=_normalize_display_string(payload.get("layout_qc_profile")),
            required_exports=required_exports,
        )
    )

    return errors


def normalize_renderer_contract(payload: object) -> dict[str, object]:
    errors = validate_renderer_contract(payload)
    if errors:
        raise ValueError("; ".join(errors))
    assert isinstance(payload, dict)
    normalized = {
        "figure_semantics": _normalize_string(payload.get("figure_semantics")),
        "renderer_family": _normalize_string(payload.get("renderer_family")),
        "template_id": str(payload.get("template_id") or "").strip(),
        "selection_rationale": str(payload.get("selection_rationale") or "").strip(),
        "layout_qc_profile": str(payload.get("layout_qc_profile") or "").strip(),
        "required_exports": [
            _normalize_string(item)
            for item in list(payload.get("required_exports") or [])
            if _normalize_string(item)
        ],
        "fallback_on_failure": False,
        "failure_action": FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT,
    }
    if normalized["figure_semantics"] == FIGURE_SEMANTICS_EVIDENCE:
        normalized.update(
            {
                "core_claim": _normalize_display_string(payload.get("core_claim")),
                "evidence_chain": _normalize_non_empty_string_list(payload.get("evidence_chain")),
                "panel_role": _normalize_display_string(payload.get("panel_role")),
                "source_data_refs": _normalize_non_empty_string_list(payload.get("source_data_refs")),
                "statistics_refs": _normalize_non_empty_string_list(payload.get("statistics_refs")),
                "export_contract": dict(payload.get("export_contract") or {}),
                "qa_risks": _normalize_non_empty_string_list(payload.get("qa_risks")),
            }
        )
    return normalized
