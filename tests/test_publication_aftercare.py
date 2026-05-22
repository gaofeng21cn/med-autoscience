from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str = "ref-only fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _populate_ready_aftercare_refs(study_root: Path, quest_root: Path) -> None:
    aris_root = quest_root / "artifacts" / "algorithm_research" / "aris"
    for name in (
        "input_contract.json",
        "algorithm_scout_report.md",
        "innovation_hypotheses.md",
        "final_method_proposal.md",
        "experiment_plan.md",
        "experiment_results_summary.md",
        "review_loop_summary.md",
        "prior_limitations.md",
        "why_our_method_can_work.md",
        "claim_to_evidence_map.md",
    ):
        if name.endswith(".json"):
            _write_json(aris_root / name, {"ref": f"aris-ref:{name}"})
        else:
            _write_text(aris_root / name)
    _write_json(aris_root / "sidecar_manifest.json", {"provider": "aris", "status": "result_ready"})
    _write_json(
        study_root / "artifacts" / "submission_targets" / "latest.json",
        {
            "target_venue_ref": "journal:target-a",
            "target_whitelist_refs": ["journal:target-a", "journal:target-b"],
            "hard_ledger_ref": "resubmit-ledger:dm002/strict-text-only",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_aftercare" / "resubmit_route_hard_ledger.json",
        {"ref": "resubmit-ledger:dm002/strict-text-only"},
    )
    _write_json(
        study_root / "artifacts" / "analysis_queue" / "latest.json",
        {
            "queue_ref": "analysis-queue:dm002/reviewer-repair",
            "items": [
                {
                    "item_ref": "analysis-queue-item:hdl-harmonization",
                    "state": "ready",
                    "source_refs": ["review-ref:hdl-harmonization"],
                }
            ],
            "reviewer_refs": ["review-ref:hdl-harmonization"],
            "experiment_refs": ["experiment-ref:external-validation-rerun"],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer"},
            "review_refs": ["review-ref:publication-eval"],
            "source_refs": ["paper-ref:current-manuscript"],
        },
    )
    _write_json(
        study_root / "paper" / "review" / "review_ledger.json",
        {"review_refs": ["review-ref:ledger"]},
    )
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {"claim_refs": ["claim-ref:main"], "evidence_refs": ["evidence-ref:main"]},
    )
    _write_json(
        study_root / "paper" / "citation_audit.json",
        {"citation_audit_ref": "citation-audit:dm002/ready", "citation_refs": ["citation-ref:core"]},
    )
    _write_json(
        study_root / "paper" / "kill_argument_refs.json",
        {"kill_argument_refs": ["kill-argument:dm002/weak-causal-language"]},
    )
    _write_json(
        study_root / "paper" / "anonymity_check.json",
        {"anonymity_refs": ["anonymity-ref:double-blind-ready"]},
    )
    _write_json(
        study_root / "artifacts" / "paper_talk" / "latest.json",
        {"paper_talk_ref": "paper-talk:dm002/conference-brief", "talk_script_ref": "talk-script:dm002/v1"},
    )
    _write_json(
        study_root / "artifacts" / "slides_polish" / "latest.json",
        {"deck_ref": "slides-polish:dm002/v1"},
    )
    _write_json(
        study_root / "artifacts" / "overleaf" / "latest.json",
        {
            "overleaf_project_ref": "overleaf:project/dm002",
            "status_ref": "overleaf-status:dm002/refs-only-clean",
            "check_ref": "overleaf-check:dm002/no-token",
            "pull_ref": "overleaf-pull:dm002/refs-only",
        },
    )


def test_publication_aftercare_plan_projects_aris_analysis_queue_and_reviewer_refresh_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_aftercare")
    study_root = tmp_path / "workspace" / "studies" / "DM002"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "q-DM002"
    _populate_ready_aftercare_refs(study_root, quest_root)

    result = module.build_publication_aftercare_plan(study_root=study_root, quest_root=quest_root)

    assert result["surface_kind"] == "mas_publication_aftercare_plan"
    assert result["refs_only"] is True
    assert result["body_included"] is False
    assert result["analysis_queue_entry"]["status"] == "ready"
    assert result["analysis_queue_entry"]["recommended_task_kind"] == (
        "publication_aftercare/analysis-queue-progress"
    )
    assert any("algorithm_research/aris/final_method_proposal.md" in ref for ref in result["analysis_queue_entry"]["research_pipeline_refs"])
    assert any("review_loop_summary.md" in ref for ref in result["analysis_queue_entry"]["auto_review_loop_refs"])
    assert "analysis-queue:dm002/reviewer-repair" in result["analysis_queue_entry"]["experiment_queue_refs"]
    assert result["reviewer_refresh_entry"]["status"] == "ready"
    assert result["reviewer_refresh_entry"]["reviewer_refresh_policy"]["separate_invocation_required"] is True
    assert result["reviewer_refresh_entry"]["recommended_task_kind"] == "publication_aftercare/reviewer-refresh"
    assert result["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert result["owner_route_task_policy"]["quality_gate_bypass_allowed"] is False
    assert result["owner_route_task_policy"]["direct_publication_eval_write_allowed"] is False
    assert "not projected" not in json.dumps(result, ensure_ascii=False)


def test_resubmit_route_hard_ledger_talk_slides_overleaf_and_readiness_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_aftercare")
    study_root = tmp_path / "workspace" / "studies" / "DM002"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "q-DM002"
    _populate_ready_aftercare_refs(study_root, quest_root)

    result = module.build_publication_aftercare_plan(study_root=study_root, quest_root=quest_root)

    hard_ledger = result["resubmission_plan"]["hard_ledger"]
    assert hard_ledger["text_only"] is True
    assert hard_ledger["no_new_experiment"] is True
    assert hard_ledger["no_bib_edits"] is True
    assert hard_ledger["no_overwrite"] is True
    assert hard_ledger["target_whitelisted"] is True
    assert result["resubmission_plan"]["target_whitelist_refs"] == ["journal:target-a", "journal:target-b"]
    assert result["resubmit_hard_ledger_refs"]
    assert result["paper_talk_refs"] == ["paper-talk:dm002/conference-brief"]
    assert result["slides_polish_refs"] == [
        str(study_root / "artifacts" / "slides_polish" / "latest.json"),
        "slides-polish:dm002/v1",
    ]
    assert result["overleaf_sync_plan"]["refs_only_maturity"]["project_ref_ready"] is True
    assert result["overleaf_sync_plan"]["refs_only_maturity"]["token_storage_clean"] is True
    assert result["aftercare_readiness_inputs"]["citation_audit_refs"]
    assert result["aftercare_readiness_inputs"]["kill_argument_refs"] == [
        str(study_root / "paper" / "kill_argument_refs.json"),
        "kill-argument:dm002/weak-causal-language",
    ]
    assert result["talk_package_plan"]["refs_only_maturity"]["paper_talk_ready"] is True
    assert result["talk_package_plan"]["refs_only_maturity"]["slides_polish_ready"] is True
    assert result["status"] == "ready"


def test_aftercare_blocks_non_whitelisted_target_and_token_bearing_overleaf_ref(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_aftercare")
    study_root = tmp_path / "workspace" / "studies" / "DM002"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "q-DM002"
    _populate_ready_aftercare_refs(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "submission_targets" / "latest.json",
        {"target_venue_ref": "journal:not-allowed", "target_whitelist_refs": ["journal:target-a"]},
    )
    _write_json(
        study_root / "artifacts" / "overleaf" / "latest.json",
        {
            "overleaf_project_ref": "overleaf:project/dm002",
            "status_ref": "overleaf-status:dm002/refs-only-clean",
            "access_token": "must-not-be-stored",
        },
    )

    result = module.build_publication_aftercare_plan(study_root=study_root, quest_root=quest_root)

    assert result["status"] == "blocked"
    assert "blocker:mas/DM002/publication-aftercare/target-not-whitelisted" in result["blockers"]
    assert "blocker:mas/DM002/publication-aftercare/overleaf-token-key-present" in result["blockers"]
    assert result["overleaf_sync_plan"]["token_storage_status"] == "blocked_token_key_present"


def test_publication_aftercare_forbidden_writes_are_read_only_contract_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_aftercare")
    study_root = tmp_path / "workspace" / "studies" / "DM002"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "q-DM002"
    _populate_ready_aftercare_refs(study_root, quest_root)
    before = {
        relative: (study_root / relative).exists()
        for relative in (
            "artifacts/controller_decisions/latest.json",
            "paper/submission_minimal",
            "manuscript/current_package",
            "manuscript/current_package.zip",
            "submission_package",
            "current_package",
            "current_package.zip",
        )
    }
    publication_eval_before = (study_root / "artifacts" / "publication_eval" / "latest.json").read_text(
        encoding="utf-8"
    )

    result = module.build_publication_aftercare_plan(study_root=study_root, quest_root=quest_root)

    assert result["forbidden_writes"] == [
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
        "paper/submission_minimal/",
        "manuscript/current_package/",
        "manuscript/current_package.zip",
        "submission_package/",
        "current_package/",
        "current_package.zip",
    ]
    assert result["can_push_submission"] is False
    assert result["can_authorize_submission_action"] is False
    assert result["authority_boundary"]["can_modify_current_package"] is False
    assert result["authority_boundary"]["can_modify_submission_package"] is False
    assert result["authority_boundary"]["forbidden_writes"] == result["forbidden_writes"]
    assert {
        relative: (study_root / relative).exists()
        for relative in before
    } == before
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").read_text(
        encoding="utf-8"
    ) == publication_eval_before


def test_publication_aftercare_pending_tasks_are_runtime_owner_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_aftercare")
    study_root = tmp_path / "workspace" / "studies" / "DM002"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "q-DM002"
    _populate_ready_aftercare_refs(study_root, quest_root)
    projection = module.build_publication_aftercare_plan(study_root=study_root, quest_root=quest_root)

    tasks = module.build_publication_aftercare_pending_tasks(
        profile_name="nfpitnet",
        profile_ref=tmp_path / "profile.local.toml",
        study_id="DM002",
        projection=projection,
    )

    assert [task["task_kind"] for task in tasks] == [
        "publication_aftercare/analysis-queue-progress",
        "publication_aftercare/reviewer-refresh",
    ]
    assert all(task["dispatch_owner"] == "med-autoscience" for task in tasks)
    assert all(task["payload"]["authority_boundary"] == "mas_owner_route_task_ref_only" for task in tasks)
    assert all(task["source_fingerprint"] for task in tasks)
    assert all(ref["body_included"] is False for task in tasks for ref in task["source_refs"])
    for task in tasks:
        evidence_payload = task["domain_dispatch_evidence_record_payload"]
        assert evidence_payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
        assert evidence_payload["domain_id"] == "medautoscience"
        assert evidence_payload["task_kind"] == task["task_kind"]
        assert evidence_payload["study_id"] == "DM002"
        assert evidence_payload["source_fingerprint"] == task["source_fingerprint"]
        assert evidence_payload["profile_name"] == "nfpitnet"
        assert {
            key: evidence_payload["record_payload"][key]
            for key in ("domain_id", "task_kind", "study_id", "source_fingerprint", "profile_name")
        } == {
            "domain_id": "medautoscience",
            "task_kind": task["task_kind"],
            "study_id": "DM002",
            "source_fingerprint": task["source_fingerprint"],
            "profile_name": "nfpitnet",
        }
        assert evidence_payload["body_included"] is False
        assert evidence_payload["domain_ready_claimed"] is False
        assert evidence_payload["publication_ready_claimed"] is False
        assert evidence_payload["record_payload"]["typed_blocker_refs"]
        assert evidence_payload["record_payload"]["evidence_refs"]
        assert evidence_payload["record_payload"]["no_regression_refs"]
        assert {
            packet["role"] for packet in evidence_payload["body_free_evidence_packets"]
        } == {"stable_typed_blocker_ref", "no_forbidden_write_proof_ref"}
