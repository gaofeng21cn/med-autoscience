from __future__ import annotations

import importlib

import pytest


def valid_contract(*, figure_semantics: str = "evidence", renderer_family: str = "python") -> dict[str, object]:
    if figure_semantics == "illustration":
        template_id = "cohort_flow_figure"
        layout_qc_profile = "publication_illustration_flow"
        required_exports = ["png", "svg"]
        renderer_family = "python"
    elif figure_semantics == "submission_companion":
        template_id = "submission_graphical_abstract"
        layout_qc_profile = "submission_graphical_abstract"
        required_exports = ["png", "svg"]
        renderer_family = "python"
    elif renderer_family == "python":
        template_id = "shap_summary_beeswarm"
        layout_qc_profile = "publication_shap_summary"
        required_exports = ["png", "pdf"]
    else:
        template_id = "roc_curve_binary"
        layout_qc_profile = "publication_evidence_curve"
        required_exports = ["png", "pdf"]
    return {
        "figure_semantics": figure_semantics,
        "renderer_family": renderer_family,
        "template_id": template_id,
        "selection_rationale": (
            "This figure stays on an audited programmatic renderer so the exported artifact remains coupled "
            "to the manuscript-safe analysis surface."
        ),
        "layout_qc_profile": layout_qc_profile,
        "required_exports": required_exports,
        "fallback_on_failure": False,
        "failure_action": "block_and_fix_environment",
    }


def test_allowed_renderer_families_follow_semantics_boundary() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    assert module.allowed_renderer_families("evidence") == ("python", "r_ggplot2")
    assert module.allowed_renderer_families("illustration") == ("python", "r_ggplot2", "html_svg")
    assert module.allowed_renderer_families("submission_companion") == ("python",)


def test_validate_renderer_contract_accepts_allowed_pairs() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    assert module.validate_renderer_contract(valid_contract(figure_semantics="evidence", renderer_family="python")) == []
    assert module.validate_renderer_contract(
        valid_contract(figure_semantics="evidence", renderer_family="r_ggplot2")
    ) == []
    assert module.validate_renderer_contract(
        valid_contract(figure_semantics="illustration", renderer_family="python")
    ) == []
    assert module.validate_renderer_contract(
        valid_contract(figure_semantics="submission_companion", renderer_family="python")
    ) == []


def test_validate_renderer_contract_rejects_html_svg_for_evidence() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    errors = module.validate_renderer_contract(valid_contract(figure_semantics="evidence", renderer_family="html_svg"))

    assert errors
    assert "renderer_family" in errors[0]
    assert "html_svg" in errors[0]
    assert "evidence" in errors[0]


def test_validate_renderer_contract_rejects_non_submission_shell_for_submission_companion_semantics() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    errors = module.validate_renderer_contract(
        {
            **valid_contract(figure_semantics="submission_companion", renderer_family="python"),
            "template_id": "cohort_flow_figure",
        }
    )

    assert errors
    assert "submission_graphical_abstract" in errors[0]


def test_validate_renderer_contract_rejects_failure_driven_fallbacks() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    errors = module.validate_renderer_contract(
        {
            **valid_contract(),
            "fallback_on_failure": True,
        }
    )

    assert errors == ["fallback_on_failure must be false"]


def test_validate_renderer_contract_requires_block_and_fix_environment_failure_action() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    errors = module.validate_renderer_contract(
        {
            **valid_contract(),
            "failure_action": "fallback_to_html_svg",
        }
    )

    assert errors == ["failure_action must be `block_and_fix_environment`"]


def test_validate_renderer_contract_requires_template_and_qc_fields() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    errors = module.validate_renderer_contract(
        {
            "figure_semantics": "evidence",
            "renderer_family": "r_ggplot2",
            "selection_rationale": "Publication-facing ROC figure stays on the audited R stack.",
            "fallback_on_failure": False,
            "failure_action": "block_and_fix_environment",
        }
    )

    assert "template_id must be non-empty" in errors
    assert "layout_qc_profile must be non-empty" in errors
    assert "required_exports must contain at least one export format" in errors


def test_normalize_renderer_contract_raises_for_invalid_combination() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    with pytest.raises(ValueError, match="html_svg"):
        module.normalize_renderer_contract(valid_contract(figure_semantics="evidence", renderer_family="html_svg"))
