from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path

from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_reviewer_os
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "route_epoch": f"truth-epoch::{study_id}",
        "source_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
    }


def test_materialize_domain_action_requests_keeps_current_prose_routeback_dispatch_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = "quest-dpcc"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "reason": "ai_reviewer_assessment_required",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": str(study_root / "paper" / "draft.md"),
                "manuscript_digest": "sha256:" + "b" * 64,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Repair medical manuscript prose against current evidence.",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::003::stale",
            "assessment_provenance": {"owner": "ai_reviewer"},
            "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                }
            ],
            "action_queue": [action],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "repeat_suppressed",
            "owner_route": route,
            "idempotency_key": route["idempotency_key"],
            "prompt_contract": {
                "do_not_repeat": True,
                "repeat_suppression_key": route["source_fingerprint"],
            },
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["repeat_suppressed"] is False
    assert dispatch["blocked_reason"] is None
    assert result["repeat_suppressed_count"] == 0


def test_materialize_ai_reviewer_dispatch_inherits_owner_reason_forbidden_surfaces(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    dispatch_contract = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.dispatch_contract"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    owner_forbidden_surfaces = [
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_manuscript",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route["owner_reason_contract"] = {
        "registered": True,
        "reason": "ai_reviewer_record_stale_after_current_manuscript",
        "owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "required_output": "artifacts/publication_eval/latest.json",
        "forbidden_surfaces": [
            "manuscript/**",
            "current_package/**",
            "paper/current_package/**",
            "manuscript/current_package/**",
            *owner_forbidden_surfaces,
        ],
        "priority_class": "ai_reviewer_currentness",
    }
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "ai_reviewer_record_stale_after_current_manuscript",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                        "owner_route": route,
                    },
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    prompt_forbidden_surfaces = set(dispatch["prompt_contract"]["forbidden_surfaces"])
    for surface in owner_forbidden_surfaces:
        assert surface in prompt_forbidden_surfaces
    assert dispatch_contract.prompt_contract_error(
        dispatch["prompt_contract"],
        forbidden_surfaces=module.FORBIDDEN_SURFACES,
    ) is None
    persisted = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "return_to_ai_reviewer_workflow.json"
        ).read_text(encoding="utf-8")
    )
    assert set(persisted["prompt_contract"]["forbidden_surfaces"]) == prompt_forbidden_surfaces


def test_materialize_ai_reviewer_request_preserves_current_manuscript_record_refs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent story.\n", encoding="utf-8")
    review_manuscript_path.write_text("# Draft\n\nCurrent story.\n", encoding="utf-8")
    source_ref = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    stale_record_ref = study_root / "artifacts" / "publication_eval" / "latest.json"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_manuscript",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "reason": "ai_reviewer_record_stale_after_current_manuscript",
        "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "work_unit_fingerprint": "dm002-current-manuscript-record",
        "source_ref": str(source_ref.resolve()),
        "stale_record_ref": str(stale_record_ref.resolve()),
        "required_currentness_refs": [
            str(manuscript_path.resolve()),
            str(review_manuscript_path.resolve()),
        ],
        "record_only_surface": True,
        "publication_eval_latest_write_allowed": False,
        "controller_decision_write_allowed": False,
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}::{quest_id}",
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(stale_record_ref.resolve()),
                "required_currentness_refs": [
                    str(manuscript_path.resolve()),
                    str(review_manuscript_path.resolve()),
                ],
                "source_ref": str(source_ref.resolve()),
            },
            "source_workflow_ref": {
                "surface": "owner_route_reconcile",
                "route_back_target": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
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
                }
            },
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260524T010000Z_publication_eval_record.json",
        current_manuscript_routeback_record(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_path.read_text(encoding="utf-8"),
            study_id=study_id,
            quest_id=quest_id,
            eval_id="publication-eval::002::quest::2026-05-24T01:00:00+00:00::ai-reviewer",
            emitted_at="2026-05-24T01:00:00+00:00",
        ),
    )
    stale_response_record_ref = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260524T010000Z_publication_eval_record.json"
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "requests"
            / "ai_reviewer"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    dispatch = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "return_to_ai_reviewer_workflow.json"
        ).read_text(encoding="utf-8")
    )
    expected_refs = [str(manuscript_path.resolve()), str(review_manuscript_path.resolve())]
    assert result["request_tasks"][0]["dispatch_status"] == "applied"
    assert request["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert request["request_lifecycle"]["required_currentness_refs"] == expected_refs
    assert request["request_lifecycle"]["stale_record_ref"] == str(stale_response_record_ref.resolve())
    assert request["request_lifecycle"]["source_ref"] == str(source_ref.resolve())
    assert request["source_workflow_ref"]["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert dispatch["source_action"]["required_currentness_refs"] == expected_refs
    assert dispatch["source_action"]["stale_record_ref"] == str(stale_record_ref.resolve())
    assert dispatch["source_action"]["record_only_surface"] is True
    assert dispatch["source_action"]["publication_eval_latest_write_allowed"] is False
    assert dispatch["source_action"]["controller_decision_write_allowed"] is False


def test_materialize_domain_action_requests_refreshes_existing_ai_reviewer_request_to_latest_valid_record_without_new_queue_task(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript with numeric results and 95% CIs.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    os.utime(manuscript_path, (0, 0))
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    old_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260521T213722Z_publication_eval_record.json"
    )
    new_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260522T203041Z_publication_eval_record.json"
    )
    quality_assessment = {
        dimension: {"status": "blocked", "summary": f"{dimension} remains blocked."}
        for dimension in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "medical_journal_prose_quality",
            "human_review_readiness",
        )
    }
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}::{quest_id}",
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(old_record_path.resolve()),
                "required_currentness_refs": [str(manuscript_path.resolve())],
                "missing_currentness_refs": [str(manuscript_path.resolve())],
                "currentness_evidence": {
                    "surface_kind": "ai_reviewer_record_currentness_evidence",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                },
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
                    "review_ledger": {"path": str(study_root / "paper" / "review" / "review_ledger.json"), "present": True, "valid": True},
                    "study_charter": {"path": str(study_root / "artifacts" / "controller" / "study_charter.json"), "present": True, "valid": True},
                    "medical_manuscript_blueprint": {"path": str(study_root / "paper" / "medical_manuscript_blueprint.json"), "present": True, "valid": True},
                    "claim_evidence_map": {"path": str(study_root / "paper" / "claim_evidence_map.json"), "present": True, "valid": True},
                    "medical_prose_review": {"path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"), "present": True, "valid": True},
                    "publication_gate_projection": {"path": str(study_root / "artifacts" / "publication_eval" / "latest.json"), "present": True, "valid": True},
                }
            },
        },
    )
    _write_json(
        new_record_path,
        current_manuscript_routeback_record(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_text,
            study_id=study_id,
            quest_id=quest_id,
            eval_id="publication-eval::002::quest::2026-05-22T20:30:41+00:00::ai-reviewer",
            emitted_at="2026-05-22T20:30:41+00:00",
        )
        | {"quality_assessment": quality_assessment},
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id}],
            "action_queue": [],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    refreshed = json.loads(request_path.read_text(encoding="utf-8"))
    assert result["ai_reviewer_request_refresh_count"] == 1
    assert result["ai_reviewer_request_refreshes"][0]["refresh_status"] == "refreshed"
    assert result["ai_reviewer_request_refreshes"][0]["publication_eval_record_ref"] == str(new_record_path.resolve())
    assert refreshed["request_lifecycle"]["blocked_reason"] is None
    assert "stale_record_ref" not in refreshed["request_lifecycle"]
    assert "required_currentness_refs" not in refreshed["request_lifecycle"]
    assert "missing_currentness_refs" not in refreshed["request_lifecycle"]
    assert "currentness_evidence" not in refreshed["request_lifecycle"]
    assert refreshed["publication_eval_record_ref"] == str(new_record_path.resolve())
    assert refreshed["ai_reviewer_record"]["eval_id"] == "publication-eval::002::quest::2026-05-22T20:30:41+00:00::ai-reviewer"


def test_materialize_current_ai_reviewer_record_work_unit_routes_to_publication_owner_when_current(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    manuscript_text = "# Draft\n\nCurrent story with reproducible numeric results and 95% CIs.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    review_manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::002::quest::2026-05-26T08:00:00+00:00::ai-reviewer"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260526T080000Z_publication_eval_record.json"
    )
    record_payload = {
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-26T08:00:00+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [str(manuscript_path.resolve()), str(review_manuscript_path.resolve())],
        },
        "quality_assessment": {
            dimension: {"status": "ready", "summary": f"{dimension} current."}
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
                "limitation": "External-validation limitations remain explicit.",
                "impact_on_claim": "Claims stay restrained.",
                "required_future_analysis_data_or_design": "None for this replay.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_text,
            eval_id=eval_id,
        ),
    }
    _write_json(record_path, record_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "assessment_written", "blocked_reason": None},
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "surface": "quality_repair_execution_evidence",
            "schema_version": 1,
            "source_eval_id": eval_id,
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "manuscript_surface_hygiene": {
                "story_surface_delta_required": True,
                "story_surface_delta_present": True,
                "story_surface_delta_refs": [
                    str(manuscript_path.resolve()),
                    str(review_manuscript_path.resolve()),
                ],
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {"status": "current", "source_eval_id": eval_id},
    )
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="quest_waiting_opl_runtime_owner_route",
        allowed_actions=["run_quality_repair_batch"],
    )
    route.update(
        {
            "schema_version": 2,
            "runtime_health_epoch": "runtime-health-dm002-materialization",
            "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
            "source_refs": {
                "runtime_health_epoch": "runtime-health-dm002-materialization",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
                "source_eval_id": eval_id,
            },
        }
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "request_owner": "write",
                    "reason": "quest_waiting_opl_runtime_owner_route",
                    "next_work_unit": work_unit_id,
                    "controller_work_unit_id": work_unit_id,
                    "executable_work_unit": work_unit_id,
                    "required_output_surface": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 1
    assert result["default_executor_dispatch_count"] == 1
    request = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    assert request["action_type"] == "run_gate_clearing_batch"
    assert request["request_owner"] == "gate_clearing_batch"
    assert request["reason"] == "publication_owner_materialization_required"
    assert request["required_output_surface"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert dispatch["action_type"] == "run_gate_clearing_batch"
    assert dispatch["next_executable_owner"] == "gate_clearing_batch"
    assert dispatch["required_output_surface"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert dispatch["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert source_refs["work_unit_id"] == work_unit_id
    assert source_refs["materialized_work_unit_id"] == "publication_gate_replay"
    assert source_refs["materialized_from_action_type"] == "run_quality_repair_batch"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_publication_owner_bridge"
    assert source_refs["bridged_from_owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert source_refs["bridged_from_idempotency_key"] == route["idempotency_key"]
    assert dispatch["source_action"]["controller_work_unit_id"] == work_unit_id
    assert dispatch["source_action"]["materialization_decision"] == "publication_gate_replay"
    assert dispatch["source_action"]["reviewer_record_ref"] == str(record_path.resolve())
    assert dispatch["source_action"]["story_surface_delta_refs"] == [
        str(manuscript_path.resolve()),
        str(review_manuscript_path.resolve()),
    ]


def test_materialize_current_ai_reviewer_record_work_unit_routes_missing_currentness_to_ai_reviewer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent story changed after review.\n", encoding="utf-8")
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="quest_waiting_opl_runtime_owner_route",
        allowed_actions=["run_quality_repair_batch"],
    )
    route.update(
        {
            "schema_version": 2,
            "runtime_health_epoch": "runtime-health-dm002-materialization",
            "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
            "source_refs": {
                "runtime_health_epoch": "runtime-health-dm002-materialization",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
            },
        }
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "required_currentness_refs": [str(manuscript_path.resolve())],
            },
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "request_owner": "write",
                    "reason": "quest_waiting_opl_runtime_owner_route",
                    "next_work_unit": work_unit_id,
                    "controller_work_unit_id": work_unit_id,
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    assert request["action_type"] == "return_to_ai_reviewer_workflow"
    assert request["request_owner"] == "ai_reviewer"
    assert request["reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert dispatch["source_action"]["materialization_decision"] == "ai_reviewer_currentness_required"
    assert dispatch["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]


def test_dm002_20260529_current_positive_ai_reviewer_archive_replays_gate_without_record_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nDM002 current manuscript is ready for gate replay after AI review.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    evidence_ledger_path = study_root / "paper" / "evidence_ledger.json"
    claim_evidence_map_path = study_root / "paper" / "claim_evidence_map.json"
    review_ledger_path = study_root / "paper" / "review" / "review_ledger.json"
    _write_json(evidence_ledger_path, {"schema_version": 1, "items": [{"id": "dm002-current-evidence"}]})
    _write_json(claim_evidence_map_path, {"schema_version": 1, "claims": [{"claim_id": "dm002-current-claim"}]})
    _write_json(review_ledger_path, {"schema_version": 1, "items": []})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"schema_version": 1})
    _write_json(study_root / "paper" / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json", {"schema_version": 1})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::dm002::stale-latest::2026-05-28T21:00:00+00:00",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            },
        },
    )
    eval_id = "publication-eval::dm002::current-positive::2026-05-29T09:54:14Z"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260529T095414Z_publication_eval_record.json"
    )
    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-05-29T09:54:14Z",
    )
    for assessment in record_payload["quality_assessment"].values():
        assessment["status"] = "ready"
    reviewer_os = record_payload["reviewer_operating_system"]
    for score in reviewer_os["rubric_scores"].values():
        score["status"] = "ready"
    reviewer_os["currentness_checks"]["medical_prose_review"]["route_back_required"] = False
    reviewer_os["currentness_checks"]["medical_prose_review"].pop("route_target", None)
    reviewer_os["currentness_checks"]["evidence_ledger"] = {
        "status": "current",
        "source_ref": str(evidence_ledger_path.resolve()),
        "digest": _sha256_file(evidence_ledger_path),
    }
    reviewer_os["currentness_checks"]["claim_evidence_map"] = {
        "status": "current",
        "source_ref": str(claim_evidence_map_path.resolve()),
        "digest": _sha256_file(claim_evidence_map_path),
    }
    reviewer_os["route_back_decision"] = {
        "recommended_action": "publication_gate_replay",
        "route_target": "publication_eval",
        "rationale": "Current positive AI reviewer record is consumable by publication gate replay.",
    }
    record_payload["verdict"] = {
        "overall_verdict": "ready_for_publication_gate_replay",
        "primary_claim_status": "supported",
    }
    record_payload["recommended_actions"] = [
        {
            "action_id": "dm002-current-positive-gate-replay",
            "action_type": "publication_gate_replay",
            "priority": "now",
            "reason": "Replay publication gate against the current positive AI reviewer record.",
            "evidence_refs": [str(record_path.resolve())],
            "requires_controller_decision": True,
        }
    ]
    _write_json(record_path, record_payload)
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {"status": "current", "source_eval_id": eval_id},
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True}
                }
            },
        },
    )
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    work_unit_fingerprint = f"domain-transition::ai_reviewer_re_eval::{work_unit_id}"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-dm002-20260529T095414Z",
            "route_epoch": "truth-event-dm002-20260529T095414Z",
            "source_fingerprint": "truth-snapshot::dm002-20260529-current-positive",
            "runtime_health_epoch": "runtime-health-dm002-20260529T095414Z",
            "work_unit_fingerprint": work_unit_fingerprint,
            "idempotency_key": "owner-route::dm002::20260529-current-input-record-production",
            "source_refs": {
                "study_truth_epoch": "truth-event-dm002-20260529T095414Z",
                "runtime_health_epoch": "runtime-health-dm002-20260529T095414Z",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            },
        }
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner": "ai_reviewer",
                    "request_owner": "ai_reviewer",
                    "reason": "ai_reviewer_record_stale_after_current_inputs",
                    "next_work_unit": work_unit_id,
                    "controller_work_unit_id": work_unit_id,
                    "executable_work_unit": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    request = result["request_tasks"][0]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert request["action_type"] == "run_gate_clearing_batch"
    assert request["request_owner"] == "gate_clearing_batch"
    assert dispatch["action_type"] == "run_gate_clearing_batch"
    assert dispatch["source_action"]["materialization_decision"] == "publication_gate_replay"
    assert dispatch["source_action"]["reviewer_record_ref"] == str(record_path.resolve())
    assert dispatch["source_action"]["source_eval_id"] == eval_id
    assert source_refs["materialized_work_unit_id"] == "publication_gate_replay"
    assert source_refs["materialized_from_action_type"] == "return_to_ai_reviewer_workflow"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_publication_owner_bridge"
    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" not in {
        dispatch["action_type"],
        dispatch["source_action"]["next_work_unit"],
        dispatch["owner_route"]["source_refs"]["materialized_work_unit_id"],
    }
