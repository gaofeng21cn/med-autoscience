from __future__ import annotations

import json
from pathlib import Path

from med_autoscience import cli
from med_autoscience.display_pack_agent import display_pack_render
from tests.test_display_pack_agent import (
    REPO_ROOT,
    _styled_paper_root,
    _write_prepared_dependency_environment,
)


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


def test_display_pack_render_returns_agent_receipt_around_scaffold_render(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    _write_prepared_dependency_environment(paper_root)
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
    assert payload["dependency_environment"]["status"] == "prepared"
    assert payload["publication_readiness_verdict"] is False
    assert payload["render_result"]["figures"][0]["template_id"] == (
        "fenggaolab.org.medical-display-core::roc_curve_binary"
    )
    assert (paper_root / "build" / "display_pack_publication_manifest.json").is_file()
    assert (paper_root / "build" / "display_pack_lock.json").is_file()
    assert (paper_root / "figure_visual_audit_receipt.json").is_file()
    assert (paper_root / "figure_render_receipt.json").is_file()
    assert payload["receipt_refs"]["figure_render_receipt"] == "paper/figure_render_receipt.json"
    assert payload["receipt_refs"]["dependency_environment_receipt"] == (
        "paper/build/dependency_environment_receipt.json"
    )
    assert payload["receipt_refs"]["figure_workflow_packet"] == "paper/figure_workflow_packet.json"
    figure_receipt = json.loads((paper_root / "figure_render_receipt.json").read_text(encoding="utf-8"))
    assert figure_receipt["dependency_environment"]["receipt_ref"] == (
        "paper/build/dependency_environment_receipt.json"
    )
    assert figure_receipt["figures"][0]["dependency_environment"]["run_context_fingerprint"] == (
        "sha256:test-display-env-run-context"
    )
    assert figure_receipt["authority_boundary"][
        "dependency_environment_can_authorize_publication_readiness"
    ] is False
    manifest = json.loads((paper_root / "build" / "display_pack_publication_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dependency_environment"]["run_context_ref"] == "paper/build/dependency_run_context.json"
    assert manifest["authority_boundary"]["renderer_code_must_not_install_packages"] is True
    assert (paper_root / "figure_workflow_packet.json").is_file()
    workflow_packet = json.loads((paper_root / "figure_workflow_packet.json").read_text(encoding="utf-8"))
    assert workflow_packet["workflow_status"] == "audit_clear"
    assert workflow_packet["figures"][0]["render_inspect_revise"]["visual_audit_final_status"] == "clear"
    assert payload["render_result"]["figure_workflow_packet"]["workflow_status"] == "audit_clear"


def test_display_pack_render_fail_closes_missing_dependency_environment(tmp_path: Path) -> None:
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
        },
    )

    assert payload["surface_kind"] == "display_pack_agent_render_receipt"
    assert payload["status"] == "blocked"
    assert payload["dependency_environment"]["status"] == "missing_prepared_receipt"
    assert payload["typed_blocker"]["code"] == "dependency_environment_not_prepared"
    assert payload["typed_blocker"]["repair_owner"] == "OPL Framework"
    assert payload["publication_readiness_verdict"] is False
    assert not (paper_root / "figure_render_receipt.json").exists()


def test_display_pack_render_fail_closes_cohort_flow_missing_ggconsort_capable_receipt(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    payload_path = tmp_path / "cohort-flow-payload.json"
    payload_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "shell_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
                "display_id": "cohort_flow_figure",
                "title": "Participant flow",
                "layout_mode": "participant_flow",
                "steps": [{"step_id": "screened", "label": "Screened", "n": 100}],
                "exclusions": [],
                "endpoint_inventory": [],
                "design_panels": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = display_pack_render(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        figure_request={
            "template_id": "cohort_flow_figure",
            "data_payload_file": str(payload_path),
            "figure_id": "F1",
        },
    )

    requirement = payload["dependency_environment"]["dependency_requirements"][0]

    assert payload["surface_kind"] == "display_pack_agent_render_receipt"
    assert payload["status"] == "blocked"
    assert payload["dependency_environment"]["status"] == "missing_prepared_receipt"
    assert requirement["profile_id"] == "r_ggplot2_ggconsort_reporting_flow_v1"
    assert requirement["render_contract"]["checked_in_renderer_uses_ggconsort"] is True
    assert payload["typed_blocker"]["code"] == "dependency_environment_not_prepared"
    assert payload["typed_blocker"]["repair_owner"] == "OPL Framework"
    assert not (paper_root / "figure_render_receipt.json").exists()


def test_display_pack_render_blocks_raw_input_when_direct_template_id_is_summary_only(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    payload_path = tmp_path / "roc-payload.json"
    _write_roc_payload(payload_path)

    payload = display_pack_render(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        figure_request={
            "template_id": "roc_curve_binary",
            "data_payload_file": str(payload_path),
            "analysis_input_state": "labels_and_scores",
        },
    )

    assert payload["surface_kind"] == "display_pack_agent_render_receipt"
    assert payload["status"] == "blocked"
    assert payload["typed_blocker"]["blocked_reason"] == "analysis_summary_required_before_display_render"
    assert payload["typed_blocker"]["route_hint"] == (
        "materialize_validated_analysis_summary_before_display_render"
    )
    assert payload["next_callable"] == "display-pack-repair"


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
