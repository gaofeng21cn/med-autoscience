from __future__ import annotations

import json
from pathlib import Path

from med_autoscience import cli
from med_autoscience.display_pack_agent import (
    display_pack_capability_discover,
    display_pack_figure_plan,
    display_pack_orchestrate,
    display_pack_preflight,
    display_pack_render,
)
from med_autoscience.publication_display_contract import seed_publication_display_contracts_if_missing


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_roc_payload(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_data_digest": "payload-digest",
                "title": "Primary ROC",
                "x_label": "1 - Specificity",
                "y_label": "Sensitivity",
                "series": [
                    {"label": "Model", "x": [0.0, 0.2, 1.0], "y": [0.0, 0.8, 1.0]},
                    {"label": "Comparator", "x": [0.0, 0.4, 1.0], "y": [0.0, 0.7, 1.0]},
                ],
                "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _styled_paper_root(tmp_path: Path) -> Path:
    paper_root = tmp_path / "paper"
    seed_publication_display_contracts_if_missing(paper_root=paper_root)
    return paper_root


def test_display_pack_capability_discover_exposes_agent_actions_and_inventory() -> None:
    payload = display_pack_capability_discover(repo_root=REPO_ROOT)

    assert payload["surface_kind"] == "display_pack_agent_capability"
    assert payload["status"] == "available"
    assert payload["inventory"]["template_count"] >= 90
    assert payload["inventory"]["kind_counts"]["evidence_figure"] >= 80
    assert payload["inventory"]["renderer_family_counts"]["r_ggplot2"] >= 50
    assert {item["command"] for item in payload["callable_actions"]} == {
        "display-pack-capability-discover",
        "display-pack-orchestrate",
        "display-pack-figure-plan",
        "display-pack-preflight",
        "display-pack-render",
    }
    assert payload["authority_boundary"]["can_mutate_data_or_statistics"] is False
    assert payload["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert payload["expected_receipt_refs"]["figure_render_receipt"] == "paper/figure_render_receipt.json"


def test_display_pack_figure_plan_prefers_r_ggplot2_template_for_agent_request() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={
            "figure_kind": "evidence_figure",
            "audit_family": "Prediction Performance",
            "preferred_renderer_family": "r_ggplot2",
            "query": "roc",
        },
        max_recommendations=3,
    )

    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["status"] == "display_plan_ready"
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["recommended_template"]["renderer_family"] == "r_ggplot2"
    assert payload["recommended_template"]["adaptation_required"] is False
    assert payload["next_callable"] == "display-pack-preflight"


def test_display_pack_figure_plan_uses_close_template_as_adaptable_baseline() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={
            "figure_kind": "evidence_figure",
            "audit_family": "Custom Mortality Discrimination",
            "paper_family": "custom_journal_family",
            "preferred_renderer_family": "r_ggplot2",
            "input_schema_ref": "schemas/custom_roc_payload.schema.json",
            "query": "roc",
        },
        max_recommendations=3,
    )

    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["status"] == "display_plan_ready"
    assert payload["agent_manual_template_selection_required"] is False
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["recommended_template"]["renderer_family"] == "r_ggplot2"
    assert payload["recommended_template"]["template_fit_policy"] == (
        "adaptable_baseline_not_exact_contract"
    )
    assert payload["recommended_template"]["adaptation_required"] is True
    assert {
        hint["code"]
        for hint in payload["recommended_template"]["adaptation_hints"]
    } >= {
        "audit_family_adaptation_required",
        "paper_family_adaptation_required",
        "input_schema_adaptation_required",
    }
    assert set(payload["recommended_template"]["adaptation_boundary"]["allowed_layers"]) >= {
        "layout",
        "labels_and_caption",
        "style_tokens",
    }
    assert "data_values" in payload["recommended_template"]["adaptation_boundary"]["forbidden_layers"]
    assert "statistical_estimates" in payload["recommended_template"]["adaptation_boundary"]["forbidden_layers"]
    assert set(payload["minimum_fit_floor"]["hard_constraints"]) >= {
        "figure_kind_compatible",
        "explicit_template_id_match_when_requested",
    }
    assert payload["publication_readiness_verdict"] is False


def test_display_pack_figure_plan_explicit_template_id_remains_hard_selection() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={
            "figure_kind": "evidence_figure",
            "template_id": "not-a-real-template",
            "query": "roc",
        },
    )

    assert payload["status"] == "blocked"
    assert payload["recommended_template"] is None
    assert payload["typed_blocker"]["blocked_reason"] == "display_template_not_found"
    assert payload["typed_blocker"]["requested_template_id"] == "not-a-real-template"
    assert payload["agent_manual_template_selection_required"] is False


def test_display_pack_orchestrate_compiles_current_owner_delta_into_render_next_step(tmp_path: Path) -> None:
    paper_root = _styled_paper_root(tmp_path)
    payload = display_pack_orchestrate(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        current_owner_delta={
            "action_type": "artifact_display_surface_materialization_required",
            "owner": "publication_display",
            "work_unit_id": "figure-roc",
            "work_unit_fingerprint": "sha256:display",
            "display_intent": "Generate a primary ROC figure for prediction performance.",
        },
        claim_ref="claim:primary-model-discrimination",
        data_ref="data:analysis/roc_payload.json",
        paper_target="jama",
        check_runtime_dependencies=False,
    )

    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["status"] == "ready_to_render"
    assert payload["figure_intent"]["planning_root"] == "current_owner_delta"
    assert payload["figure_request"]["claim_ref"] == "claim:primary-model-discrimination"
    assert payload["figure_request"]["data_ref"] == "data:analysis/roc_payload.json"
    assert payload["figure_request"]["audit_family"] == "Prediction Performance"
    assert payload["figure_request"]["preferred_renderer_family"] == "r_ggplot2"
    assert payload["plan"]["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["preflight"]["status"] == "ready"
    assert payload["quality_floor"]["checks"]["template_selected"] is True
    assert payload["agent_manual_template_selection_required"] is False
    assert payload["publication_readiness_verdict"] is False
    assert payload["next_callable"] == "display-pack-render"


def test_display_pack_orchestrate_routes_missing_claim_and_data_refs() -> None:
    payload = display_pack_orchestrate(
        repo_root=REPO_ROOT,
        intent="Need a ROC figure for prediction performance.",
        check_runtime_dependencies=False,
    )

    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["status"] == "needs_repair"
    assert payload["next_callable"] == "display-pack-repair"
    assert {item["code"] for item in payload["typed_repair_routes"]} >= {
        "claim_ref_missing",
        "data_ref_missing",
    }


def test_display_pack_preflight_reports_missing_paper_style_profile(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    paper_root.mkdir()

    payload = display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        template_id="roc_curve_binary",
        check_runtime_dependencies=False,
    )

    assert payload["surface_kind"] == "display_pack_agent_preflight"
    assert payload["status"] == "blocked"
    assert payload["style_profile"]["status"] == "missing"
    assert {item["code"] for item in payload["blocking_findings"]} >= {
        "publication_style_profile_missing",
    }


def test_display_pack_render_returns_agent_receipt_around_scaffold_render(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    payload_path = tmp_path / "roc-payload.json"
    _write_roc_payload(payload_path)

    payload = display_pack_render(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        figure_request={
            "figure_kind": "evidence_figure",
            "audit_family": "Prediction Performance",
            "preferred_renderer_family": "r_ggplot2",
            "query": "roc",
            "data_payload_file": str(payload_path),
            "figure_id": "F1",
            "claim_ref": "claim:primary",
            "cohort_ref": "cohort:demo",
            "endpoint_ref": "endpoint:mortality",
            "risk_horizon": "5y",
        },
    )

    assert payload["surface_kind"] == "display_pack_agent_render_receipt"
    assert payload["status"] == "publication_manifested"
    assert payload["publication_readiness_verdict"] is False
    assert payload["render_result"]["figures"][0]["template_id"] == (
        "fenggaolab.org.medical-display-core::roc_curve_binary"
    )
    assert (paper_root / "build" / "display_pack_publication_manifest.json").is_file()
    assert (paper_root / "build" / "display_pack_lock.json").is_file()
    assert (paper_root / "figure_visual_audit_receipt.json").is_file()
    assert (paper_root / "figure_render_receipt.json").is_file()
    assert payload["receipt_refs"]["figure_render_receipt"] == "paper/figure_render_receipt.json"


def test_cli_display_pack_agent_plan_loads_figure_request_json(capsys) -> None:
    exit_code = cli.main(
        [
            "publication",
            "display-pack-agent-plan",
            "--repo-root",
            str(REPO_ROOT),
            "--figure-request-json",
            json.dumps(
                {
                    "figure_kind": "evidence_figure",
                    "audit_family": "Prediction Performance",
                    "preferred_renderer_family": "r_ggplot2",
                    "query": "roc",
                }
            ),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"


def test_cli_display_pack_agent_orchestrate_accepts_current_owner_delta_json(capsys, tmp_path: Path) -> None:
    paper_root = _styled_paper_root(tmp_path)
    exit_code = cli.main(
        [
            "publication",
            "display-pack-agent-orchestrate",
            "--repo-root",
            str(REPO_ROOT),
            "--paper-root",
            str(paper_root),
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "display_pack_orchestrate",
                    "display_intent": "Create ROC figure for model discrimination.",
                }
            ),
            "--claim-ref",
            "claim:roc",
            "--data-ref",
            "data:roc",
            "--skip-runtime-dependency-check",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["status"] == "ready_to_render"
    assert payload["plan"]["recommended_template"]["template_id"] == "roc_curve_binary"
