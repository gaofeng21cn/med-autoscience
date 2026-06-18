from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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

    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
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
