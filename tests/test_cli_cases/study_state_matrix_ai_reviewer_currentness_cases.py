from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_directory_current_package_delivery(study_root: Path) -> None:
    package_root = study_root / "manuscript" / "current_package"
    (package_root / "figures").mkdir(parents=True, exist_ok=True)
    (package_root / "tables").mkdir(parents=True, exist_ok=True)
    for relative_path in (
        "manuscript.docx",
        "paper.pdf",
        "references.bib",
        "figures/Figure1.png",
        "tables/Table1.md",
    ):
        (package_root / relative_path).write_text("placeholder\n", encoding="utf-8")
    (package_root / "SUBMISSION_TODO.md").write_text(
        "# Submission TODO\n\nPending items:\n- Authors: pending\n- Ethics: pending\n- Funding: pending\n",
        encoding="utf-8",
    )
    _write_json(
        package_root / "audit" / "submission_manifest.json",
        {
            "schema_version": 1,
            "figures": [{"figure_id": "Figure1"}],
            "tables": [{"table_id": "Table1"}],
            "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
        },
    )
    _write_json(
        study_root / "manuscript" / "delivery_manifest.json",
        {
            "schema_version": 1,
            "stage": "submission_minimal",
            "source_signature": "sig-current",
            "evaluated_source_signature": "sig-current",
            "authority_source_signature": "sig-current",
            "surface_roles": {
                "human_facing_current_package_root": str(package_root.resolve()),
                "human_facing_current_package_zip": str((study_root / "manuscript" / "current_package.zip").resolve()),
            },
        },
    )


def test_study_state_matrix_routes_ai_reviewer_ready_without_currentness_back_to_review(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "002-dm"
    package_root = study_root / "manuscript" / "current_package"
    package_root.mkdir(parents=True)
    (package_root / "manuscript.docx").write_text("delivered package\n", encoding="utf-8")
    (study_root / "manuscript" / "current_package.zip").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "manuscript" / "current_package.zip").write_text("zip\n", encoding="utf-8")
    (study_root / "study.yaml").write_text("study_id: 002-dm\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::002-dm::quest-002::2026-05-15T19:20:58+00:00",
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-15T19:20:58+00:00",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer_recheck",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
            },
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "ready",
                    "summary": "AI reviewer marked prose ready, but the reviewer OS trace lacks currentness.",
                    "evidence_refs": [
                        str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")
                    ],
                }
            },
            "reviewer_operating_system": {
                "contract_id": "medical_publication_ai_reviewer_os_v1",
                "input_bundle": {
                    "manuscript": str(study_root / "paper" / "draft.md"),
                    "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                    "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
                    "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
                    "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                    "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
                    "medical_prose_review": str(
                        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
                    ),
                    "publication_gate_projection": str(
                        study_root / "artifacts" / "publication_eval" / "latest.json"
                    ),
                },
                "rubric_scores": {
                    dimension: {
                        "status": "ready",
                        "rationale": "Old reviewer trace did not include currentness checks.",
                        "evidence_refs": [str(study_root / "paper" / "draft.md")],
                    }
                    for dimension in (
                        "clinical_significance",
                        "evidence_strength",
                        "novelty_positioning",
                        "medical_journal_prose_quality",
                        "human_review_readiness",
                    )
                },
                "decision_matrix": [
                    {
                        "dimension": "medical_journal_prose_quality",
                        "status": "ready",
                        "rationale": "Old reviewer trace did not include currentness checks.",
                    }
                ],
                "provenance_checks": {
                    "assessment_owner": "ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                    "mechanical_projection_used_as_quality_authority": False,
                },
                "route_back_decision": {
                    "recommended_action": "continue_same_line",
                    "rationale": "Old reviewer trace did not include currentness checks.",
                },
            },
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "002-dm",
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "quest_waiting_for_submission_metadata",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    transition = json.loads(captured.out)["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "ai_reviewer_re_eval"
    assert transition["route_target"] == "review"
    assert transition["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert transition["controller_action"] == "return_to_ai_reviewer_workflow"
    assert transition["owner"] == "ai_reviewer"


def test_study_state_matrix_underdefined_ai_reviewer_preempts_delivered_directory_package_handoff(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "002-dm"
    _write_directory_current_package_delivery(study_root)
    (study_root / "study.yaml").write_text("study_id: 002-dm\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::002-dm::quest-002::2026-05-18T03:45:29+00:00",
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-18T03:45:29+00:00",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer_recheck",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
            },
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "Medical prose review remains unresolved after clean migration.",
                    "evidence_refs": [str(study_root / "paper" / "draft.md")],
                }
            },
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "002-dm",
            "study_root": str(study_root),
            "quest_status": "running",
            "active_run_id": "run-live",
            "runtime_liveness_status": "live",
            "reason": "quest_already_running",
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    study = json.loads(captured.out)["studies"][0]
    transition = study["domain_transition"]

    assert exit_code == 0
    assert study["delivered_package"]["observed"] is True
    assert transition["decision_type"] == "ai_reviewer_re_eval"
    assert transition["route_target"] == "review"
    assert transition["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert transition["controller_action"] == "return_to_ai_reviewer_workflow"
    assert transition["owner"] == "ai_reviewer"
