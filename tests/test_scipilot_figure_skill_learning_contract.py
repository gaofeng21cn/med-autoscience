from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCIPILOT_ADOPTION_CONTRACT = REPO_ROOT / "contracts/scipilot_figure_skill_learning_adoption.json"


def _load_contract() -> dict[str, object]:
    parsed = json.loads(SCIPILOT_ADOPTION_CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict)
    return parsed


def _adoptions_by_pattern(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    adoptions = payload["adoptions"]
    assert isinstance(adoptions, list)
    result: dict[str, dict[str, object]] = {}
    for adoption in adoptions:
        assert isinstance(adoption, dict)
        pattern_id = adoption["pattern_id"]
        assert isinstance(pattern_id, str)
        result[pattern_id] = adoption
    return result


def test_scipilot_figure_skill_learning_lands_as_non_authority_refs() -> None:
    payload = _load_contract()
    source = payload["source"]
    assert isinstance(source, dict)

    assert payload["contract_id"] == "scipilot_figure_skill_learning_adoption.v1"
    assert source["repository"] == "https://github.com/Haojae/scipilot-figure-skill"
    assert source["observed_head"] == "43098ddb9e6a6d142218540c114f9ed38922fc42"
    assert {
        "data_question_first_plot_selection",
        "small_n_and_misleading_chart_warning_floor",
        "programmatic_qc_then_ai_visual_review_split",
    } <= set(payload["learned_patterns"])
    assert {
        "publication_readiness_authority",
        "visual_audit_replacement",
        "default_renderer_runtime_dependency",
    } <= set(payload["global_forbidden_authority"])


def test_scipilot_plot_selection_and_visual_qa_patterns_are_consumable_but_nonblocking() -> None:
    payload = _load_contract()
    adoptions = _adoptions_by_pattern(payload)

    plot_selection = adoptions["data_question_first_plot_selection"]
    assert plot_selection["classification"] == "adopt"
    assert plot_selection["landing_status"] == "owner_surface_landed"
    assert "src/med_autoscience.display_pack_agent_parts.figure_contract.compile_display_figure_intent" in (
        plot_selection["consumable_surfaces"]
    )
    assert "unrelated owner dispatch must continue" in plot_selection["progress_policy"]

    qa_split = adoptions["programmatic_qc_then_ai_visual_review_split"]
    assert qa_split["classification"] == "adapt"
    assert "src/med_autoscience.publication_figure_quality_contract.load_figure_workflow_packet" in (
        qa_split["consumable_surfaces"]
    )
    assert "do not replace the visual-audit receipt" in qa_split["progress_policy"]


def test_scipilot_runtime_import_is_rejected() -> None:
    payload = _load_contract()
    rejected = _adoptions_by_pattern(payload)["scipilot_python_runtime_and_scripts"]

    assert rejected["classification"] == "reject"
    assert rejected["landing_status"] == "rejected_by_boundary"
    assert {
        "matplotlib_seaborn_plotly_as_default_mas_evidence_renderer",
        "scipilot_scripts_as_mas_tools",
        "scipilot_checklist_as_publication_authority",
        "external_skill_runner_as_provider",
    } <= set(rejected["rejected_surfaces"])
