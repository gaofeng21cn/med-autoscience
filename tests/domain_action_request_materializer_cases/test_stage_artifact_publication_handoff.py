from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_materialize_domain_action_requests_dispatches_stage_artifact_publication_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "truth_epoch": "truth-epoch-dm002-terminal-handoff",
        "runtime_health_epoch": "runtime-health-epoch-dm002-terminal-handoff",
        "work_unit_fingerprint": "stage-artifact-index::08-publication_package_handoff::publication_handoff_owner_gate",
        "failure_signature": "publication_handoff_owner_gate",
        "trace_id": "owner-route-trace::dm002::publication-handoff",
        "route_epoch": "truth-epoch-dm002-terminal-handoff",
        "source_fingerprint": "truth-source-dm002-terminal-handoff",
        "current_owner": "mas_controller",
        "next_owner": "publication_gate_owner",
        "owner_reason": "publication_handoff_owner_gate",
        "active_run_id": None,
        "allowed_actions": ["publication_handoff_owner_gate"],
        "blocked_actions": [],
        "source_refs": {
            "work_unit_id": "publication_handoff_owner_gate",
            "work_unit_fingerprint": (
                "stage-artifact-index::08-publication_package_handoff::"
                "publication_handoff_owner_gate"
            ),
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-epoch-dm002-terminal-handoff",
                "runtime_health_epoch": "runtime-health-epoch-dm002-terminal-handoff",
                "work_unit_id": "publication_handoff_owner_gate",
                "work_unit_fingerprint": (
                    "stage-artifact-index::08-publication_package_handoff::"
                    "publication_handoff_owner_gate"
                ),
            },
        },
        "idempotency_key": "owner-route::dm002::publication-handoff-owner-gate",
    }
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "owner_route": owner_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": "quest-dm002",
                            "action_type": "publication_handoff_owner_gate",
                            "authority": "observability_only",
                            "owner": "publication_gate_owner",
                            "request_owner": "publication_gate_owner",
                            "recommended_owner": "publication_gate_owner",
                            "reason": "publication_handoff_owner_gate",
                            "required_output_surface": (
                                "artifacts/stage_outputs/08-publication_package_handoff/"
                                "handoff_owner_receipt.json or "
                                "artifacts/stage_outputs/08-publication_package_handoff/"
                                "receipts/typed_blocker.json"
                            ),
                            "work_unit_id": "publication_handoff_owner_gate",
                            "work_unit_fingerprint": (
                                "stage-artifact-index::08-publication_package_handoff::"
                                "publication_handoff_owner_gate"
                            ),
                            "owner_route": owner_route,
                            "handoff_packet": {
                                "action_type": "publication_handoff_owner_gate",
                                "request_owner": "publication_gate_owner",
                                "recommended_owner": "publication_gate_owner",
                                "owner_route": owner_route,
                                "idempotency_key": owner_route["idempotency_key"],
                            },
                        }
                    ],
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

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "publication_handoff_owner_gate"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["next_executable_owner"] == "publication_gate_owner"
    assert dispatch["owner_route"]["next_owner"] == "publication_gate_owner"
    assert dispatch["owner_route"]["allowed_actions"] == ["publication_handoff_owner_gate"]
    assert dispatch["prompt_contract"]["request_packet_ref"] == (
        "artifacts/supervision/requests/publication_handoff_owner_gate/latest.json"
    )
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "publication_handoff_owner_gate"
        / "latest.json"
    )
    persisted_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_handoff_owner_gate.json"
    )
    assert request_path.is_file()
    assert persisted_dispatch_path.is_file()
