from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study


QUALITY_DIMENSIONS = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "medical_journal_prose_quality",
    "human_review_readiness",
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _quality_assessment(statuses: dict[str, str]) -> dict[str, Any]:
    return {
        dimension: {
            "status": statuses[dimension],
            "summary": f"{dimension} {statuses[dimension]}",
            "evidence_refs": [f"paper/evidence_ledger.json#{dimension}"],
        }
        for dimension in QUALITY_DIMENSIONS
    }


def _write_dm002_like_surfaces(study_root: Path, quest_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::002::latest",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "policy_id": "publication_gate_projection_v1",
                "source_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
                "ai_reviewer_required": True,
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "publication gate blocked",
            },
            "quality_assessment": _quality_assessment(
                {
                    "clinical_significance": "ready",
                    "evidence_strength": "blocked",
                    "novelty_positioning": "partial",
                    "medical_journal_prose_quality": "partial",
                    "human_review_readiness": "blocked",
                }
            ),
            "gaps": [{"gap_id": "reviewer-first", "gap_type": "evidence", "severity": "must_fix"}],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "decision_type": "bounded_analysis",
            "route_target": "write",
            "reason": "publication_gate_specificity_required",
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "health_status": "recovering",
            "latest_recorded_at": "2026-05-04T07:21:34+00:00",
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "health_status": "recovering",
            "active_run_id": "run-dm002",
        },
    )
    _write_json(
        quest_root / ".ds" / "runs" / "run-dm002" / "telemetry.json",
        {
            "run_id": "run-dm002",
            "tool_call_count": 3,
            "unique_command_count": 2,
            "read_tool_call_count": 1,
        },
    )
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        {
            "schema_version": 1,
            "items": [
                {
                    "item_id": "anchor-guideline",
                    "claim": "External validation should report calibration and discrimination.",
                    "guideline_ref": "guideline:TRIPOD+AI",
                    "source_ref": "paper/evidence_ledger.json#anchor-guideline",
                },
                {
                    "item_id": "anchor-pmid",
                    "claim": "Diabetes mortality prediction needs population transportability review.",
                    "pmid": "12345678",
                    "source_ref": "paper/evidence_ledger.json#anchor-pmid",
                },
            ],
            "claims": [{"claim_id": "claim-transportability", "evidence_refs": ["anchor-guideline", "anchor-pmid"]}],
        },
    )


def test_open_auto_research_soak_read_only_reports_missing_sources_without_writing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.open_auto_research_soak")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")

    result = module.run_open_auto_research_soak(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        study_root=None,
        allow_controller_writes=False,
    )

    assert result["surface"] == "open_auto_research_soak"
    assert result["study_id"] == "002-dm-china-us-mortality-attribution"
    assert result["verdict"]["status"] == "blocked"
    assert result["verdict"]["mode"] == "read_only_audit"
    assert result["authority"]["can_authorize_publication_quality"] is False
    assert result["authority"]["can_authorize_submission"] is False
    assert result["capability_results"]["open_auto_research_projection"]["status"] == "blocked"
    assert not (study_root / "artifacts" / "runtime" / "open_auto_research_soak" / "latest.json").exists()
    assert not (study_root / "artifacts" / "runtime" / "open_auto_research_projection" / "latest.json").exists()


def test_open_auto_research_soak_materializes_allowed_read_models_and_guard_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.open_auto_research_soak")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")
    quest_root = profile.runtime_root / "002-dm-china-us-mortality-attribution"
    _write_dm002_like_surfaces(study_root, quest_root)

    forbidden_paths = [
        study_root / "artifacts" / "publication_eval" / "latest.json",
        study_root / "artifacts" / "controller_decisions" / "latest.json",
    ]
    before = {str(path): path.read_text(encoding="utf-8") for path in forbidden_paths}

    result = module.run_open_auto_research_soak(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        study_root=None,
        allow_controller_writes=True,
        runtime_status_payload={
            "study_id": "002-dm-china-us-mortality-attribution",
            "study_root": str(study_root),
            "quest_root": str(quest_root),
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "active_run_id": "run-dm002",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "runtime_recovery_lifecycle": {"state": "recovering"},
            "runtime_liveness_audit": {"status": "none"},
        },
    )

    assert result["verdict"]["status"] == "blocked"
    assert result["verdict"]["mode"] == "controller_authorized_soak"
    assert result["live_runtime_context"]["current_stage"] == "managed_runtime_recovering"
    assert result["live_runtime_context"]["paper_stage"] == "publishability_gate_blocked"
    assert result["capability_results"]["open_auto_research_projection"]["counts"] == {
        "ready": 3,
        "blocked": 0,
        "needs_review": 1,
        "total": 4,
    }
    assert result["capability_results"]["open_auto_research_projection"]["status"] == "needs_review"
    assert result["authority_guard_results"]["forbidden_surface_unchanged"] is True
    assert result["authority_guard_results"]["authorized_writes_only"] is True
    assert result["authority_guard_results"]["forbidden_surface_hashes"]["changed"] == []
    assert result["entry_projection_results"]["study_progress"]["open_auto_research_status"] == "needs_review"
    assert result["entry_projection_results"]["mcp_compact"]["open_auto_research_status"] == "needs_review"
    assert "ai_reviewer_required" in result["remaining_gaps"]
    assert "publication_gate_blocked" in result["remaining_gaps"]
    assert "runtime_recovering" in result["remaining_gaps"]

    for path, content in before.items():
        assert Path(path).read_text(encoding="utf-8") == content
    assert (study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json").exists()
    assert (study_root / "artifacts" / "eval_hygiene" / "quality_regression_projection" / "latest.json").exists()
    assert (study_root / "artifacts" / "runtime" / "action_observation_trajectory" / "latest.json").exists()
    assert (study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json").exists()
    assert (study_root / "artifacts" / "runtime" / "open_auto_research_soak" / "latest.json").exists()
    assert not (study_root / "artifacts" / "runtime" / "open_auto_research_projection" / "latest.json").exists()


def test_open_auto_research_soak_literature_graph_accepts_reporting_contract_guideline(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.open_auto_research_soak")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")
    quest_root = profile.runtime_root / "002-dm-china-us-mortality-attribution"
    _write_dm002_like_surfaces(study_root, quest_root)
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        {
            "schema_version": 1,
            "items": [
                {
                    "item_id": "source-only-evidence",
                    "claim": "The paper follows a transportability validation framing.",
                    "source_ref": "paper/evidence_ledger.json#source-only-evidence",
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "medical_story_contract.json",
        {
            "schema_version": 1,
            "reporting_guideline_family": "TRIPOD",
            "clinical_question": "Can the model transport across China and US diabetes cohorts?",
        },
    )

    result = module.run_open_auto_research_soak(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        study_root=None,
        allow_controller_writes=True,
        runtime_status_payload={
            "study_id": "002-dm-china-us-mortality-attribution",
            "study_root": str(study_root),
            "quest_root": str(quest_root),
            "quest_status": "active",
            "active_run_id": "run-dm002",
        },
    )

    literature = result["capability_results"]["open_auto_research_projection"]["capabilities"][
        "literature_evidence_graph"
    ]
    assert literature["status"] == "ready"
    assert literature["coverage"]["guideline_count"] == 1


def test_open_auto_research_soak_cli_group_alias_accepts_allow_controller_writes(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "dm-cvd"',
                f'workspace_root = "{profile.workspace_root}"',
                f'runtime_root = "{profile.runtime_root}"',
                f'studies_root = "{profile.studies_root}"',
                f'portfolio_root = "{profile.portfolio_root}"',
                f'med_deepscientist_runtime_root = "{profile.med_deepscientist_runtime_root}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")
    _write_dm002_like_surfaces(study_root, profile.runtime_root / "002-dm-china-us-mortality-attribution")

    exit_code = cli.main(
        [
            "study",
            "open-auto-research-soak",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--format",
            "json",
            "--allow-controller-writes",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["surface"] == "open_auto_research_soak"
    assert output["study_id"] == "002-dm-china-us-mortality-attribution"
    assert output["verdict"]["mode"] == "controller_authorized_soak"
