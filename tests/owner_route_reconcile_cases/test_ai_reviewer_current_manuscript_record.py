from __future__ import annotations

import importlib
import json
import hashlib
from pathlib import Path

from tests.reviewer_os_fixture_helpers import (
    current_manuscript_routeback_reviewer_os,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_current_ai_reviewer_response_record_drives_write_route_without_latest_mutation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    canonical_inputs = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.canonical_inputs"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript with updated 95% CIs.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    old_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::old::2026-05-22T20:30:41+00:00::ai-reviewer",
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-22T20:30:41+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:old",
                    "manuscript_ref": str(manuscript_path),
                    "manuscript_digest": "sha256:old",
                    "route_back_required": True,
                    "route_target": "write",
                }
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": "old-write-route",
                "next_work_unit": {
                    "unit_id": "old_publication_hardening",
                    "lane": "write",
                    "summary": "Old write route.",
                },
            }
        ],
    }
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(latest_path, old_eval)
    current_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260524T175827Z_publication_eval_record.json"
    )
    current_eval_id = "publication-eval::dm002::new::2026-05-24T17:58:27+00:00::ai-reviewer"
    current_record = {
        "schema_version": 1,
        "eval_id": current_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-24T17:58:27+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            dimension: {"status": "blocked", "summary": f"{dimension} requires hardening."}
            for dimension in (
                "clinical_significance",
                "evidence_strength",
                "novelty_positioning",
                "medical_journal_prose_quality",
                "human_review_readiness",
            )
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "External validation remains observational.",
                "impact_on_claim": "Use restrained validation wording.",
                "required_future_analysis_data_or_design": "Independent implementation validation.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_text,
            eval_id=current_eval_id,
        ),
        "recommended_actions": [
            {
                "action_id": "route-back-same-line-current-publication-hardening-dm002-20260524T175827Z",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "route_key_question": "Can the current manuscript be hardened without adding claims?",
                "route_rationale": "Current AI reviewer response routes same-line manuscript repair to write.",
                "work_unit_fingerprint": (
                    "dm002_current_ai_reviewer_publication_eval_live_draft_"
                    "2dcd51592c6a_20260524T175827Z"
                ),
                "next_work_unit": {
                    "unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                    "lane": "write",
                    "summary": "Harden the current manuscript against the current AI reviewer record.",
                },
            }
        ],
    }
    _write_json(current_record_path, current_record)
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": old_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-current-record",
            "source_signature": "truth-source-dm002-current-record",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(latest_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }
    selected_publication_eval = canonical_inputs.publication_eval_payload(status_payload, progress_payload)
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, selected_publication_eval),
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["present"] is True
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["next_work_unit"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert action["work_unit_fingerprint"].endswith("20260524T175827Z")
    assert action["controller_route"]["publication_eval_id"] == current_record["eval_id"]
    assert action["controller_route"]["publication_eval_ref"]["artifact_path"] == str(current_record_path.resolve())
    assert study["owner_route"]["source_refs"]["source_eval_id"] == current_record["eval_id"]
    assert study["owner_route"]["source_refs"]["publication_eval_path"] == str(current_record_path.resolve())
    assert study["owner_route"]["next_owner"] == "write"


def test_current_manuscript_stale_ai_reviewer_request_supersedes_write_route(
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
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent manuscript with updated 95% CIs.\n", encoding="utf-8")
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260521T213722Z_publication_eval_record.json"
    )
    eval_id = "publication-eval::dm002::old-write-route-back"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "verdict": {"overall_verdict": "blocked", "primary_claim_status": "partial"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "recommended_actions": [
            {
                "action_id": "return-to-write",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_same_line_publication_paper_repair"
                ),
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript body against current AI reviewer prose findings.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(stale_record_path),
                "required_currentness_refs": [str(manuscript_path)],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "review_ledger": {
                        "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_manuscript_blueprint": {
                        "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                        "present": True,
                        "valid": True,
                    },
                    "claim_evidence_map": {
                        "path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_prose_review": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                        "present": True,
                        "valid": True,
                    },
                    "publication_gate_projection": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        "present": True,
                        "valid": True,
                    },
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-stale-current-manuscript-review",
            "source_signature": "truth-source-dm002-stale-current-manuscript-review",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
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
    assert [action["action_type"] for action in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert action["required_currentness_refs"] == [str(manuscript_path)]
    assert action["stale_record_ref"] == str(stale_record_path)
    assert study["next_owner"] == "ai_reviewer"
    assert study["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    request = json.loads(
        (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert request["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert request["request_lifecycle"]["required_currentness_refs"] == [str(manuscript_path)]


def test_quality_repair_digest_mismatch_routes_to_current_manuscript_ai_reviewer_record(
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
    eval_id = "publication-eval::dm002::stale-manuscript-digest"
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request-current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(stale_reviewer_story),
                    "route_back_required": True,
                    "route_target": "write",
                }
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
        "reviewer_manuscript_ref": str(manuscript_path.resolve()),
        "reviewer_manuscript_digest": _sha256_text(stale_reviewer_story),
        "story_surface_digests": [
            {"path": str(manuscript_path.resolve()), "present": True, "digest": _sha256_text(live_story)},
            {"path": str(review_manuscript_path.resolve()), "present": True, "digest": _sha256_text(live_story)},
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
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": [
                    "canonical_artifact_delta_missing",
                    "manuscript_story_surface_delta_missing",
                ],
                "canonical_artifact_delta": {"status": "blocked", "meaningful_artifact_delta": False},
            },
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
            "truth_epoch": "truth-epoch-dm002-digest-mismatch",
            "source_signature": "truth-source-dm002-digest-mismatch",
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
    assert [action["action_type"] for action in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert action["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert action["required_output_surface"] == "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    assert action["record_only_surface"] is True
    assert action["publication_eval_latest_write_allowed"] is False
    assert action["controller_decision_write_allowed"] is False
    assert action["required_currentness_refs"] == [str(manuscript_path.resolve()), str(review_manuscript_path.resolve())]
    assert action["stale_record_ref"] == str(latest_eval_path.resolve())
    assert action["source_ref"] == str(quality_batch_path.resolve())
    assert study["next_owner"] == "ai_reviewer"
    assert study["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    request = json.loads(
        (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert request["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert request["request_lifecycle"]["required_currentness_refs"] == [
        str(manuscript_path.resolve()),
        str(review_manuscript_path.resolve()),
    ]
    assert request["request_lifecycle"]["stale_record_ref"] == str(latest_eval_path.resolve())
    assert request["request_lifecycle"]["source_ref"] == str(quality_batch_path.resolve())


def test_record_production_domain_transition_supersedes_stale_story_surface_blocker(
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
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent manuscript with updated 95% CIs.\n", encoding="utf-8")
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260521T213722Z_publication_eval_record.json"
    )
    eval_id = "publication-eval::dm002::2026-05-21T21:37:22+00:00"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "medical_journal_prose_quality": {"status": "blocked"},
        },
        "recommended_actions": [
            {
                "action_id": "return-to-write",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "dm002_same_line_publication_paper_repair_20260521",
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript body against stale AI reviewer prose findings.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "blocked",
            "source_eval_id": eval_id,
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "next_owner": "write",
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "created_at": "2026-05-21T20:00:00+00:00",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(stale_record_path),
                "required_currentness_refs": [str(manuscript_path)],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "review_ledger": {
                        "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_manuscript_blueprint": {
                        "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                        "present": True,
                        "valid": True,
                    },
                    "claim_evidence_map": {
                        "path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_prose_review": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                        "present": True,
                        "valid": True,
                    },
                    "publication_gate_projection": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        "present": True,
                        "valid": True,
                    },
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
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
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "lane": "review",
                "summary": "Produce a current AI reviewer publication-eval record before dispatching the publication-eval workflow.",
            },
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-current-record-production",
            "source_signature": "truth-source-dm002-current-record-production",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_opl_runtime_owner_handoff_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
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
    assert [action["action_type"] for action in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert action["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert action["required_output_surface"] == "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    assert action["required_currentness_refs"] == [str(manuscript_path)]
    assert action["stale_record_ref"] == str(stale_record_path)
    assert study["next_owner"] == "ai_reviewer"
    assert study["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]


def test_record_production_domain_transition_survives_opl_admission_wait(
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
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent manuscript with updated intervals.\n", encoding="utf-8")
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260522T223001Z_publication_eval_record.json"
    )
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::stale-record",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "recommended_actions": [
            {
                "action_id": "return-to-write",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": "stale-write-route",
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Old write route that must not outrank current AI reviewer record production.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(stale_record_path),
                "required_currentness_refs": [str(manuscript_path)],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "review_ledger": {
                        "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_manuscript_blueprint": {
                        "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                        "present": True,
                        "valid": True,
                    },
                    "claim_evidence_map": {
                        "path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_prose_review": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                        "present": True,
                        "valid": True,
                    },
                    "publication_gate_projection": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        "present": True,
                        "valid": True,
                    },
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
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
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "lane": "review",
                "summary": "Produce a current AI reviewer publication-eval record before dispatching the publication-eval workflow.",
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-event-dm002-admission",
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-dm002-admission",
            "source_signature": "truth-snapshot-dm002-admission",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_runtime_escalated",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
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
    assert [action["action_type"] for action in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert action["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert action["record_only_surface"] is True
    assert study["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["owner_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert study["owner_route"]["owner_reason_contract"]["registered"] is True
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert study["owner_route"]["owner_route_attempt_protocol"]["dispatchable"] is True
