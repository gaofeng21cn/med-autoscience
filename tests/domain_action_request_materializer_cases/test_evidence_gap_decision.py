from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_action_request_materializer_cases.shared import owner_route, write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def test_materializer_evidence_gap_prompt_defaults_do_not_block_without_gap() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.evidence_gap_decision"
    )
    projection = {"study_id": "DM003", "quest_id": "quest-dm003"}

    fields = module.prompt_fields(projection, mapping=lambda value: value if isinstance(value, dict) else {})

    assert module.blocked_reason(projection, mapping=lambda value: value if isinstance(value, dict) else {}) is None
    assert fields["evidence_gap_decisions"] == []
    assert fields["evidence_gap_typed_blocker_count"] == 0
    assert fields["current_action_can_continue"] is True
    assert fields["evidence_gap_decision_summary"]["total_count"] == 0


def _scan_with_action(tmp_path: Path, *, evidence_gap_inputs: list[dict[str, object]]) -> tuple[object, str]:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = "quest-dm003"
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="medical_prose_write_repair",
        allowed_actions=["run_quality_repair_batch"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_quality_repair_batch",
        "authority": "mas_owner_surface",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": "medical_prose_write_repair",
        "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": route["work_unit_fingerprint"],
        "action_fingerprint": route["work_unit_fingerprint"],
        "owner_route": route,
        "evidence_gap_inputs": evidence_gap_inputs,
    }
    write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "domain_action_request_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": route,
                    "action_queue": [action],
                }
            ],
            "action_queue": [action],
        },
    )
    return profile, study_id


def test_materializer_hard_evidence_gap_blocks_current_dispatch(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile, study_id = _scan_with_action(
        tmp_path,
        evidence_gap_inputs=[
            {
                "surface_kind": "opl_stage_run_currentness",
                "missing_ref_family": "StageRun currentness provider authorization",
                "confidence": "high",
            }
        ],
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "blocked"
    assert dispatch["blocked_reason"] == "evidence_gap_authority_gate_required"
    assert dispatch["evidence_gap_decision_summary"]["hard_gate_count"] == 1
    assert dispatch["evidence_gap_typed_blocker_count"] == 1
    assert dispatch["current_action_can_continue"] is False
    assert "paper_progress" in dispatch["forbidden_claims"]
    assert result["legacy_request_task_diagnostics"]["legacy_request_task_refs"][0][
        "evidence_gap_typed_blocker_count"
    ] == 1


def test_materializer_soft_gap_continues_and_records_ledger(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile, study_id = _scan_with_action(
        tmp_path,
        evidence_gap_inputs=[
            {
                "surface_kind": "reviewer_polish",
                "missing_ref_family": "reviewer structure non-hard concern",
            }
        ],
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "dry_run"
    assert dispatch.get("blocked_reason") is None
    assert dispatch["evidence_gap_decision_summary"]["soft_gap_count"] == 1
    assert dispatch["evidence_gap_typed_blocker_count"] == 0
    assert dispatch["evidence_gap_decision_summary"]["hard_gate_count"] == 0
    assert dispatch["soft_gap_ledger"][0]["gap_class"] == "soft_quality_gap"
    assert "paper_progress" in dispatch["forbidden_claims"]


def test_materializer_evidence_tail_continues_but_withholds_readiness_claims(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile, study_id = _scan_with_action(
        tmp_path,
        evidence_gap_inputs=[
            {
                "surface_kind": "live_runtime_tail",
                "missing_ref_family": "production soak direct-hosted parity live readiness tail",
            }
        ],
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "dry_run"
    assert dispatch.get("blocked_reason") is None
    assert dispatch["evidence_gap_decision_summary"]["evidence_tail_count"] == 1
    assert dispatch["evidence_gap_typed_blocker_count"] == 0
    assert dispatch["current_action_can_continue"] is True
    assert dispatch["evidence_tail_ledger"][0]["gap_class"] == "evidence_tail"
    assert "live_runtime_ready" in dispatch["forbidden_claims"]
