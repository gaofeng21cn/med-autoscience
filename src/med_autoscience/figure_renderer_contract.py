from __future__ import annotations


FIGURE_SEMANTICS_EVIDENCE = "evidence"
FIGURE_SEMANTICS_ILLUSTRATION = "illustration"
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

    return errors


def normalize_renderer_contract(payload: object) -> dict[str, object]:
    errors = validate_renderer_contract(payload)
    if errors:
        raise ValueError("; ".join(errors))
    assert isinstance(payload, dict)
    return {
        "figure_semantics": _normalize_string(payload.get("figure_semantics")),
        "renderer_family": _normalize_string(payload.get("renderer_family")),
        "selection_rationale": str(payload.get("selection_rationale") or "").strip(),
        "fallback_on_failure": False,
        "failure_action": FAILURE_ACTION_BLOCK_AND_FIX_ENVIRONMENT,
    }
