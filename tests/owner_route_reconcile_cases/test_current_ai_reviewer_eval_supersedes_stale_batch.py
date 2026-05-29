from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_current_ai_reviewer_eval_supersedes_stale_quality_batch_digest_mismatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    live_story = "# Draft\n\nCurrent external validation manuscript with updated intervals.\n"
    stale_reviewer_story = "# Draft\n\nPrior external validation manuscript.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(live_story, encoding="utf-8")
    review_manuscript_path.write_text(live_story, encoding="utf-8")
    live_digest = _sha256_text(live_story)
    current_story_refs = [
        str(manuscript_path.resolve()),
        str(review_manuscript_path.resolve()),
    ]
    eval_id = "publication-eval::dm002::current-manuscript-routeback"
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "source_refs": current_story_refs,
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:current-request",
                    "manuscript_ref": current_story_refs[0],
                    "manuscript_digest": live_digest,
                    "route_back_required": True,
                    "route_target": "write",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": current_story_refs[0],
                    "manuscript_digest": live_digest,
                },
            }
        },
        "recommended_actions": [
            {
                "action_id": "return-to-write",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "dm002-display-table-package-repair",
                "next_work_unit": {
                    "unit_id": "dm002_same_line_display_table_package_repair",
                    "lane": "write",
                    "summary": "Repair display, table, and package-facing manuscript surfaces.",
                },
            }
        ],
    }
    _write_json(latest_eval_path, publication_eval)
    mismatch_blocker = {
        "blocked_reason": "quality_repair_batch_current_manuscript_digest_mismatch",
        "source_eval_id": eval_id,
        "reviewer_manuscript_ref": current_story_refs[0],
        "reviewer_manuscript_digest": _sha256_text(stale_reviewer_story),
        "story_surface_digests": [
            {"path": current_story_refs[0], "present": True, "digest": live_digest},
            {"path": current_story_refs[1], "present": True, "digest": live_digest},
        ],
    }
    quality_batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    _write_json(
        quality_batch_path,
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "source_eval_artifact_path": str(latest_eval_path.resolve()),
            "status": "blocked",
            "ok": False,
            "blocked_reason": "quality_repair_batch_current_manuscript_digest_mismatch",
            "typed_blocker": "quality_repair_batch_current_manuscript_digest_mismatch",
            "next_owner": "write",
            "gate_clearing_batch": {
                "source_work_unit_fingerprint": "dm002-display-table-package-repair",
                "unit_results": [
                    {
                        "unit_id": "dm002_same_line_display_table_package_repair",
                        "status": "blocked",
                        "result": {
                            "status": "blocked",
                            "work_unit_id": "dm002_same_line_display_table_package_repair",
                            "blocked_reason": "quality_repair_batch_current_manuscript_digest_mismatch",
                            "currentness_blocker": mismatch_blocker,
                        },
                    }
                ],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-current-eval",
            "source_signature": "truth-source-dm002-current-eval",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(latest_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["next_work_unit"] == "dm002_same_line_display_table_package_repair"
    assert action["controller_route"]["authorization_basis"] == "ai_reviewer_current_write_routeback"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]


def test_current_ai_reviewer_write_routeback_uses_blocking_work_unit_when_next_work_unit_absent(
    tmp_path: Path,
) -> None:
    current_truth_owner = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.current_truth_owner"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent DM003 manuscript.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::003-dpcc::current-manuscript-record::20260529T120533Z"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": "003-dpcc",
        "quest_id": "003-dpcc",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(manuscript_path.resolve())],
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:" + "a" * 64,
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                    "route_back_required": True,
                    "route_target": "write",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
                "source_eval": {"status": "current", "eval_id": eval_id},
                "current_package_freshness": {
                    "status": "downstream_pending",
                    "source_eval_id": eval_id,
                },
            }
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::003-dpcc::route-current-manuscript-to-write-repair",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Route the current manuscript back to MAS write owner.",
                "requires_controller_decision": True,
                "route_target": "write",
                "route_key_question": "Can MAS write owner finish current manuscript prose/reporting repair?",
                "route_rationale": "The record-only AI reviewer verdict cannot authorize submission readiness.",
                "work_unit_fingerprint": "stage-attempt::sat-current::medical_prose_write_repair",
                "blocking_work_units": [
                    {
                        "unit_id": "medical_prose_write_repair",
                        "lane": "write",
                        "summary": "Refresh durable prose review and repair remaining display-led Results wording.",
                    }
                ],
            }
        ],
    }

    route = current_truth_owner.current_ai_reviewer_write_routeback_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    )

    assert route is not None
    assert route["controller_actions"] == ["run_quality_repair_batch"]
    assert route["route_target"] == "write"
    assert route["work_unit_id"] == "medical_prose_write_repair"
    assert route["next_work_unit"] == {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
        "summary": "Refresh durable prose review and repair remaining display-led Results wording.",
    }
    assert route["authorization_basis"] == "ai_reviewer_current_write_routeback"


def test_current_ai_reviewer_write_routeback_preempts_stale_current_inputs_record_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent DPCC manuscript.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::003-dpcc::current-manuscript-record::20260529T120533Z"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(manuscript_path.resolve())],
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:" + "a" * 64,
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                    "route_back_required": True,
                    "route_target": "write",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
                "source_eval": {"status": "current", "eval_id": eval_id},
            }
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::003-dpcc::route-current-manuscript-to-write-repair",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": "stage-attempt::sat-current::medical_prose_write_repair",
                "blocking_work_units": [
                    {
                        "unit_id": "medical_prose_write_repair",
                        "lane": "write",
                        "summary": "Repair the current manuscript prose and reporting surfaces.",
                    }
                ],
            }
        ],
    }
    _write_json(publication_eval_path, publication_eval)
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "lane": "review",
                "summary": "Produce a current AI reviewer publication-eval record against current inputs.",
            },
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "continue_supervising_runtime",
            "attempt_state": "idle",
            "retry_budget_remaining": 2,
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-current-write-route",
            "source_signature": "truth-source-dm003-current-write-route",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(publication_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
        "ai_reviewer_request_lifecycle": {
            "surface": "ai_reviewer_request_lifecycle",
            "state": "requested",
            "request_owner": "ai_reviewer",
            "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            "required_currentness_refs": [str(manuscript_path.resolve())],
        },
    }
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["controller_work_unit_id"] == "medical_prose_write_repair"
    assert action["controller_route"]["authorization_basis"] == "ai_reviewer_current_write_routeback"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
