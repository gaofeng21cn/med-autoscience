from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


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
            "generated_at": "2026-05-18T03:25:04+00:00",
            "source_signature": "sig-current",
            "evaluated_source_signature": "sig-current",
            "authority_source_signature": "sig-current",
            "surface_roles": {
                "human_facing_current_package_root": str(package_root.resolve()),
                "human_facing_current_package_zip": str((study_root / "manuscript" / "current_package.zip").resolve()),
            },
        },
    )


def test_build_runtime_watch_outer_loop_tick_request_stops_live_delivered_package_before_ai_reviewer_redrive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm")
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    _write_directory_current_package_delivery(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::002-dm::quest-002::2026-05-18T03:45:29+00:00",
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-18T03:45:29+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::002-dm::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer_recheck",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [
                    str(study_root / "paper"),
                    str(study_root / "manuscript" / "current_package"),
                ],
                "ai_reviewer_required": False,
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "A human-facing package has been generated for review.",
                "stop_loss_pressure": "none",
            },
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical question is reviewable.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "The clinical framing is stable enough for package handoff.",
                    "reviewer_revision_advice": "Do not infer submission readiness from package handoff.",
                    "reviewer_next_round_focus": "Review only after explicit user wakeup.",
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence surface is sufficient for handoff.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "The current package is a review milestone.",
                    "reviewer_revision_advice": "Keep evidence authority separate from the handoff.",
                    "reviewer_next_round_focus": "Re-open only after explicit revision intake.",
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Contribution boundary is stable.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "The package has a stable study framing.",
                    "reviewer_revision_advice": "Do not expand claims during parking.",
                    "reviewer_next_round_focus": "Reassess positioning only on user wakeup.",
                },
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "Medical journal prose quality still requires AI reviewer closure.",
                    "evidence_refs": [str(study_root / "paper" / "draft.md")],
                    "reviewer_reason": "Prose closure is not being claimed by the package handoff.",
                    "reviewer_revision_advice": "Wait for explicit user feedback before re-opening the line.",
                    "reviewer_next_round_focus": "Methods completeness and result specificity.",
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "The package is ready for user-side review as a milestone.",
                    "evidence_refs": [str(study_root / "manuscript" / "current_package")],
                    "reviewer_reason": "The handoff is human-facing, not quality-authority-facing.",
                    "reviewer_revision_advice": "Wait for explicit user wakeup.",
                    "reviewer_next_round_focus": "User feedback intake.",
                },
            },
            "gaps": [
                {
                    "gap_id": "user-package-review-handoff",
                    "gap_type": "delivery",
                    "severity": "optional",
                    "summary": "The delivered package awaits explicit user feedback.",
                    "evidence_refs": [str(study_root / "manuscript" / "current_package")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::ai-reviewer-prose-review",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Without delivery handoff parking this would redrive AI reviewer prose review.",
                    "route_target": "review",
                    "route_key_question": "Should AI reviewer re-review prose now?",
                    "route_rationale": "This action must not reopen a delivered package without explicit user wakeup.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                    "next_work_unit": {
                        "unit_id": "ai_reviewer_medical_prose_quality_review",
                        "lane": "review",
                        "summary": "Re-run AI reviewer manuscript-quality review.",
                    },
                }
            ],
        },
    )
    gate_report = {
        "generated_at": "2026-05-18T03:45:29+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "medical_publication_surface_status": "clear",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        _runtime_watch_tick_request_module().publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        lambda **_: pytest.fail("delivered package handoff must not run gate-clearing redrive"),
    )
    monkeypatch.setattr(
        module.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        lambda **_: pytest.fail("delivered package handoff must not run quality-repair redrive"),
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-live",
            "reason": "quest_already_running",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "human_gate"
    assert request["next_work_unit"]["unit_id"] == "package_review_handoff"
    assert request["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
