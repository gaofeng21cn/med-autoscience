from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_action_request_materializer_cases.shared import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def test_current_default_dispatch_for_execution_marks_paper_recovery_callable_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    fingerprint = "sha256:paper-recovery-ready-for-execution"
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [],
            "action_queue": [],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
            },
            "authority_snapshot": {
                "allowed_controller_actions": [
                    "record_user_decision",
                    "direct_study_execution",
                    "direct_paper_line_write",
                ],
            },
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    observe_payload = module.current_owner_callable_adapters(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=False,
    )
    execution_payload = module.current_owner_callable_adapters(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=True,
    )

    assert observe_payload["domain_progress_transition_requests"][0]["dispatch_status"] == "dry_run"
    assert execution_payload["domain_progress_transition_requests"][0]["dispatch_status"] == (
        "transition_request_pending"
    )
    for payload in (observe_payload, execution_payload):
        assert payload["canonical_transition_request_surface"] == "domain_progress_transition_requests"
        assert payload["domain_progress_transition_request_count"] == 1
        assert "owner_callable_adapters" not in payload
        assert "owner_callable_adapter_count" not in payload
        diagnostics = payload["legacy_owner_callable_adapter_diagnostics"]
        assert diagnostics["diagnostic_only"] is True
        assert diagnostics["legacy_payload_scope"] == "identity_refs_only"
        assert diagnostics["legacy_dispatch_body_omitted"] is True
        assert diagnostics["legacy_dispatches"] == diagnostics["legacy_dispatch_refs"]
        assert "opl_domain_progress_transition_request" not in diagnostics["legacy_dispatches"][0]
        assert "owner_route" not in diagnostics["legacy_dispatches"][0]
        assert "source_action" not in diagnostics["legacy_dispatches"][0]


def test_materialize_dry_run_reports_paper_recovery_callable_as_would_be_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    fingerprint = "sha256:paper-recovery-successor-ready"
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [],
            "action_queue": [],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "current_owner_route_missing",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
            },
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "one-person-lab",
                    "obligation": {
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                        "blocker_type": "current_owner_route_missing",
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "decision_id": "supervisor-decision::materialize_recovery_action::dm003",
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "gate_clearing_batch",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_gate_clearing_batch",
                        "owner": "gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
                        "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                    },
                },
            },
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=True,
    )

    assert result["dry_run"] is True
    assert result["dispatch_ready_for_execution_preview"] is False
    assert result["dispatch_ready_for_execution_preview_requested"] is True
    assert result["dispatch_ready_for_execution_preview_blocked_reason"] == (
        "opl_execution_authorization_required"
    )
    assert result["written_files"] == []
    assert result["domain_progress_transition_request_count"] == 1
    assert result["ready_domain_progress_transition_request_count"] == 0
    assert result["transition_request_pending_domain_progress_transition_request_count"] == 1
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    assert dispatch["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert dispatch["opl_transition_runtime_required_for_durable_carrier"] is True
    assert dispatch["dispatch_ready_for_execution_authority"] is False
    assert dispatch["mas_dispatch_authority"] is False
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_kind"] == (
        "DomainProgressTransitionRuntime"
    )
    assert dispatch["work_unit_id"] == "publication_gate_replay"
    assert dispatch["work_unit_fingerprint"] == fingerprint
