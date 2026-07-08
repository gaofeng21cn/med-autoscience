from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile

def test_terminal_provider_attempt_closeout_projection_reads_completed_accepted_attempt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    fingerprint = "publication-blockers::0915410f804b3697"
    commands: list[tuple[str, ...]] = []

    def _attempt() -> dict:
        return {
            "stage_attempt_id": "sat-terminal",
            "idempotency_key": idempotency_key,
            "domain_id": "medautoscience",
            "stage_id": "stage_outcome/opl-handoff",
            "status": "completed",
            "task_id": "frt-terminal",
            "updated_at": "2026-06-20T02:28:40Z",
            "closeout_receipt_status": "accepted_typed_closeout",
            "closeout_refs": [
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json",
                f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json",
            ],
            "provider_run": {
                "provider_status": "completed",
                "workflow_id": "wf-terminal",
                "completed_at": "2026-06-20T02:28:40Z",
            },
            "route_impact": {
                "next_owner": "medautoscience",
                "domain_ready_verdict": "domain_gate_pending",
            },
            "workspace_locator": {
                "workspace_root": str(profile.workspace_root),
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "route_identity_key": idempotency_key,
                "attempt_idempotency_key": idempotency_key,
                "dispatch_ref": f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapters/run_quality_repair_batch.json",
                "stage_packet_ref": f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapters/immutable/run_quality_repair_batch/packet.json",
            },
        }

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "attempt", "list", "--json"):
            return {"family_runtime_stage_attempts": {"attempts": [_attempt()]}}
        if args == ("family-runtime", "attempt", "inspect", "sat-terminal", "--json"):
            return {"family_runtime_stage_attempt": {"attempt": _attempt()}}
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        preferred_actions=[
            {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "attempt_idempotency_key": idempotency_key,
            }
        ],
    )

    assert result is not None
    assert result["source"] == "opl_family_runtime_attempt_inspect"
    assert result["stage_attempt_id"] == "sat-terminal"
    assert result["status"] == "completed"
    assert result["closeout_receipt_status"] == "accepted_typed_closeout"
    assert result["attempt_idempotency_key"] == idempotency_key
    assert result["route_impact"]["domain_ready_verdict"] == "domain_gate_pending"
    assert result["authority_boundary"]["provider_completion_is_domain_completion"] is False
    assert commands == [
        ("family-runtime", "attempt", "list", "--json"),
        ("family-runtime", "attempt", "inspect", "sat-terminal", "--json"),
    ]


def test_terminal_provider_attempt_closeout_inspects_compact_attempt_before_preferred_match(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    fingerprint = "publication-blockers::0915410f804b3697"
    commands: list[tuple[str, ...]] = []

    compact_attempt = {
        "stage_attempt_id": "sat-compact-terminal",
        "domain_id": "medautoscience",
        "stage_id": "stage_outcome/opl-handoff",
        "study_id": study_id,
        "status": "completed",
        "task_id": "frt-compact-terminal",
        "updated_at": "2026-06-20T02:28:40Z",
    }
    inspected_attempt = {
        **compact_attempt,
        "closeout_receipt_status": "accepted_typed_closeout",
        "idempotency_key": "idem-opl-runtime-internal",
        "provider_run": {
            "provider_status": "completed",
            "workflow_id": "wf-terminal",
            "completed_at": "2026-06-20T02:28:40Z",
        },
        "route_impact": {
            "next_owner": "medautoscience",
            "domain_ready_verdict": "domain_gate_pending",
        },
        "workspace_locator": {
            "workspace_root": str(profile.workspace_root),
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": idempotency_key,
            "attempt_idempotency_key": idempotency_key,
            "dispatch_ref": f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapters/run_quality_repair_batch.json",
        },
    }

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "attempt", "list", "--json"):
            return {"family_runtime_stage_attempts": {"attempts": [compact_attempt]}}
        if args == ("family-runtime", "attempt", "inspect", "sat-compact-terminal", "--json"):
            return {"family_runtime_stage_attempt": {"attempt": inspected_attempt}}
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        max_inspect_count=1,
        preferred_actions=[
            {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "attempt_idempotency_key": idempotency_key,
            }
        ],
    )

    assert result is not None
    assert result["stage_attempt_id"] == "sat-compact-terminal"
    assert result["attempt_idempotency_key"] == idempotency_key
    assert result["work_unit_fingerprint"] == fingerprint
    assert commands == [
        ("family-runtime", "attempt", "list", "--json"),
        ("family-runtime", "attempt", "inspect", "sat-compact-terminal", "--json"),
    ]


def test_terminal_provider_attempt_closeout_prioritizes_preferred_attempt_within_budget(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    fingerprint = "publication-blockers::0915410f804b3697"
    commands: list[tuple[str, ...]] = []

    unrelated_attempt = {
        "stage_attempt_id": "sat-unrelated-terminal",
        "domain_id": "medautoscience",
        "stage_id": "stage_outcome/opl-handoff",
        "study_id": study_id,
        "status": "completed",
        "updated_at": "2026-06-20T03:00:00Z",
        "closeout_receipt_status": "accepted_typed_closeout",
        "workspace_locator": {
            "workspace_root": str(profile.workspace_root),
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
        },
    }
    preferred_attempt = {
        "stage_attempt_id": "sat-preferred-terminal",
        "domain_id": "medautoscience",
        "stage_id": "stage_outcome/opl-handoff",
        "study_id": study_id,
        "status": "completed",
        "updated_at": "2026-06-20T02:28:40Z",
        "closeout_receipt_status": "accepted_typed_closeout",
        "workspace_locator": {
            "workspace_root": str(profile.workspace_root),
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": idempotency_key,
            "attempt_idempotency_key": idempotency_key,
        },
    }

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict:
        commands.append(args)
        if args == ("family-runtime", "attempt", "list", "--json"):
            return {
                "family_runtime_stage_attempts": {
                    "attempts": [unrelated_attempt, preferred_attempt]
                }
            }
        if args == ("family-runtime", "attempt", "inspect", "sat-preferred-terminal", "--json"):
            return {"family_runtime_stage_attempt": {"attempt": preferred_attempt}}
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        max_inspect_count=1,
        preferred_actions=[
            {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "attempt_idempotency_key": idempotency_key,
            }
        ],
    )

    assert result is not None
    assert result["stage_attempt_id"] == "sat-preferred-terminal"
    assert result["attempt_idempotency_key"] == idempotency_key
    assert commands == [
        ("family-runtime", "attempt", "list", "--json"),
        ("family-runtime", "attempt", "inspect", "sat-preferred-terminal", "--json"),
    ]
