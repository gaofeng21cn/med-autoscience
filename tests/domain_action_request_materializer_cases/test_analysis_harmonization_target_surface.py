from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    source_fingerprint = f"truth-source::{study_id}::{owner_reason}"
    truth_epoch = f"truth-epoch::{study_id}"
    runtime_health_epoch = f"runtime-health::{study_id}::{owner_reason}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": source_fingerprint,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": owner_reason,
            "work_unit_fingerprint": source_fingerprint,
            "owner_route_currentness_basis": {
                "runtime_health_epoch": runtime_health_epoch,
                "truth_epoch": truth_epoch,
                "work_unit_fingerprint": source_fingerprint,
                "work_unit_id": owner_reason,
            },
        },
    }


def test_unit_harmonization_uses_body_free_precise_target_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    action_type = "unit_harmonized_external_validation_rerun"
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="analysis_harmonization_owner",
        owner_reason=action_type,
        allowed_actions=[action_type],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route, "meaningful_artifact_delta": False}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": action_type,
                    "authority": "observability_only",
                    "owner": "analysis_harmonization_owner",
                    "reason": "unit_harmonized_rerun_required",
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": action_type,
                        "authority": "observability_only",
                        "request_owner": "analysis_harmonization_owner",
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

    task = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    target_surface = task["required_output_target_surface"]
    assert target_surface == dispatch["prompt_contract"]["required_output_target_surface"]
    assert target_surface == dispatch["required_output_target_surface"]
    assert target_surface["surface"] == "analysis_harmonization_owner_target_surface"
    assert target_surface["body_free"] is True
    assert target_surface["work_unit"] == action_type
    assert target_surface["accepted_outputs"] == [
        "unit_harmonized_external_validation_rerun_evidence",
        "feature_order_and_coefficient_provenance",
        "calibration_or_recalibration_evidence",
        "claim_evidence_map_update_ref",
        "stable_typed_blocker:unit_harmonized_rerun_required",
    ]
    assert target_surface["output_refs"] == {
        "owner_result": "artifacts/controller/analysis_harmonization/latest.json",
        "rerun_evidence": (
            "artifacts/controller/analysis_harmonization/"
            "unit_harmonized_external_validation_rerun.json"
        ),
        "claim_evidence_map": "paper/claim_evidence_map.json",
        "request_packet": "artifacts/supervision/requests/analysis_harmonization/latest.json",
    }
    assert target_surface["publication_ready_authorized"] is False
    assert target_surface["current_package_write_allowed"] is False
    assert target_surface["paper_body_write_allowed"] is False
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "analysis_harmonization"
        / "latest.json"
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["required_output_target_surface"] == target_surface
    assert task["handoff_packet"]["required_output_target_surface"] == target_surface
