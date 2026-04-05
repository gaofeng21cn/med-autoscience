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
        RENDERER_FAMILY_PYTHON,
        RENDERER_FAMILY_R_GGPLOT2,
    ),
    FIGURE_SEMANTICS_ILLUSTRATION: (
        RENDERER_FAMILY_PYTHON,
        RENDERER_FAMILY_R_GGPLOT2,
        RENDERER_FAMILY_HTML_SVG,
    ),
    FIGURE_SEMANTICS_SUBMISSION_COMPANION: (
        RENDERER_FAMILY_PYTHON,
    ),
}


def _normalize_string(value: object) -> str:
    return str(value or "").strip().lower()


def allowed_renderer_families(figure_semantics: str) -> tuple[str, ...]:
    normalized = _normalize_string(figure_semantics)
    if normalized not in _ALLOWED_RENDERERS_BY_SEMANTICS:
        supported = ", ".join(sorted(_ALLOWED_RENDERERS_BY_SEMANTICS))
        raise ValueError(f"Unsupported figure_semantics `{figure_semantics}`; expected one of: {supported}")
    return _ALLOWED_RENDERERS_BY_SEMANTICS[normalized]


def validate_renderer_contract(payload: object, *, label: str = "renderer_contract") -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be a JSON object"]

    errors: list[str] = []
    figure_semantics = _normalize_string(payload.get("figure_semantics"))
    if not figure_semantics:
        errors.append("figure_semantics must be non-empty")
    else:
        try:
            allowed_families = allowed_renderer_families(figure_semantics)
        except ValueError as exc:
            errors.append(str(exc))
            allowed_families = ()

    renderer_family = _normalize_string(payload.get("renderer_family"))
    supported_families = {
        RENDERER_FAMILY_PYTHON,
        RENDERER_FAMILY_R_GGPLOT2,
        RENDERER_FAMILY_HTML_SVG,
    }
    if not renderer_family:
        errors.append("renderer_family must be non-empty")
    elif renderer_family not in supported_families:
        supported = ", ".join(sorted(supported_families))
        errors.append(f"Unsupported renderer_family `{renderer_family}`; expected one of: {supported}")
    elif figure_semantics and allowed_families and renderer_family not in allowed_families:
        allowed = ", ".join(allowed_families)
        errors.append(
            f"renderer_family `{renderer_family}` is not allowed for figure_semantics `{figure_semantics}`; "
            f"allowed: {allowed}"
        )

    selection_rationale = str(payload.get("selection_rationale") or "").strip()
    if not selection_rationale:
        errors.append("selection_rationale must be non-empty")

    template_id = str(payload.get("template_id") or "").strip()
    if not template_id:
        errors.append("template_id must be non-empty")

    layout_qc_profile = str(payload.get("layout_qc_profile") or "").strip()
    if not layout_qc_profile:
        errors.append("layout_qc_profile must be non-empty")

    required_exports_raw = payload.get("required_exports")
    required_exports: tuple[str, ...] = ()
    if isinstance(required_exports_raw, list):
        normalized_exports = tuple(_normalize_string(item) for item in required_exports_raw if _normalize_string(item))
        if normalized_exports:
            required_exports = normalized_exports
    if not required_exports:
        errors.append("required_exports must contain at least one export format")

    fallback_on_failure = payload.get("fallback_on_failure")
    if not isinstance(fallback_on_failure, bool):
        errors.append("fallback_on_failure must be a boolean")
    elif fallback_on_failure:
        errors.append("fallback_on_failure must be false")

    failure_action = _normalize_string(payload.get("failure_action"))
    if not failure_action:
        errors.append("failure_action must be non-empty")
    elif failure_action != FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT:
        errors.append(f"failure_action must be `{FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT}`")

    if figure_semantics == FIGURE_SEMANTICS_EVIDENCE and template_id:
        if not display_registry.is_evidence_figure_template(template_id):
            errors.append(f"template_id `{template_id}` is not a registered evidence figure template")
        else:
            spec = display_registry.get_evidence_figure_spec(template_id)
            if renderer_family and renderer_family != spec.renderer_family:
                errors.append(
                    f"renderer_family `{renderer_family}` does not match registered renderer_family `{spec.renderer_family}` "
                    f"for template_id `{template_id}`"
                )
            if layout_qc_profile and layout_qc_profile != spec.layout_qc_profile:
                errors.append(
                    f"layout_qc_profile `{layout_qc_profile}` does not match registered layout_qc_profile "
                    f"`{spec.layout_qc_profile}` for template_id `{template_id}`"
                )
            if required_exports:
                missing_exports = [item for item in spec.required_exports if item not in required_exports]
                if missing_exports:
                    errors.append(
                        f"required_exports missing registered export formats for template_id `{template_id}`: "
                        f"{', '.join(missing_exports)}"
                    )
    if figure_semantics in {FIGURE_SEMANTICS_ILLUSTRATION, FIGURE_SEMANTICS_SUBMISSION_COMPANION} and template_id:
        if figure_semantics == FIGURE_SEMANTICS_SUBMISSION_COMPANION and not display_registry.is_submission_companion_shell(template_id):
            errors.append(f"template_id `{template_id}` is not a registered submission companion shell")
        elif not display_registry.is_illustration_shell(template_id):
            errors.append(f"template_id `{template_id}` is not a registered illustration shell")
        else:
            spec = display_registry.get_illustration_shell_spec(template_id)
            if renderer_family and renderer_family != spec.renderer_family:
                errors.append(
                    f"renderer_family `{renderer_family}` does not match registered renderer_family `{spec.renderer_family}` "
                    f"for template_id `{template_id}`"
                )
            if layout_qc_profile and layout_qc_profile != spec.shell_qc_profile:
                errors.append(
                    f"layout_qc_profile `{layout_qc_profile}` does not match registered shell_qc_profile "
                    f"`{spec.shell_qc_profile}` for template_id `{template_id}`"
                )
            if required_exports:
                missing_exports = [item for item in spec.required_exports if item not in required_exports]
                if missing_exports:
                    errors.append(
                        f"required_exports missing registered export formats for template_id `{template_id}`: "
                        f"{', '.join(missing_exports)}"
                    )

    return errors


def normalize_renderer_contract(payload: object) -> dict[str, object]:
    errors = validate_renderer_contract(payload)
    if errors:
        raise ValueError("; ".join(errors))
    assert isinstance(payload, dict)
    return {
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
