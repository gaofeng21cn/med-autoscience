from __future__ import annotations

import importlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"


def test_owner_callable_projection_does_not_accept_legacy_dispatch_alias() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    assert projection.owner_callable_adapters(
        {
            "owner_callable_adapters": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        }
    ) == []
    assert projection.adapter_count(
        {
            "owner_callable_adapters": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        }
    ) == 1
    assert projection.adapter_status_count(
        {
            "owner_callable_adapters": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        },
        "ready",
    ) == 1
    assert projection.adapter_count(
        {
            "owner_callable_adapter_count": 7,
            "ready_owner_callable_adapter_count": 6,
        }
    ) == 0
    assert projection.adapter_status_count(
        {
            "owner_callable_adapter_count": 7,
            "ready_owner_callable_adapter_count": 6,
        },
        "ready",
    ) == 0
    assert projection.legacy_owner_callable_adapter_count(
        {
            "legacy_owner_callable_adapter_diagnostics": {
                "legacy_dispatch_count": 2,
                "legacy_dispatch_refs": [
                    {"dispatch_status": "ready"},
                    {"dispatch_status": "blocked"},
                ],
            }
        }
    ) == 2
    assert projection.domain_progress_transition_requests(
        {
            "owner_callable_adapters": [
                {
                    "dispatch_status": "ready",
                    "action_type": "legacy_dispatch",
                    "opl_domain_progress_transition_request": {
                        "surface_kind": "mas_domain_progress_transition_request",
                    },
                },
            ],
        }
    ) == []
    assert projection.transition_request_count(
        {
            "owner_callable_adapters": [
                {
                    "dispatch_status": "transition_request_pending",
                    "action_type": "legacy_dispatch",
                    "opl_domain_progress_transition_request": {
                        "surface_kind": "mas_domain_progress_transition_request",
                    },
                },
            ],
        }
    ) == 0


def test_transition_request_counts_are_canonical_not_legacy_adapter_counts() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    payload = {
        "owner_callable_adapters": [
            {
                "study_id": "study-1",
                "dispatch_status": "ready",
                "action_type": "legacy_ready",
                "dispatch_authority": "ai_reviewer_record_production_handoff",
                "source_action": {
                    "work_unit_id": "legacy-body-work",
                    "work_unit_fingerprint": "legacy-body-fingerprint",
                },
            },
        ],
        "domain_progress_transition_requests": [
            {
                "study_id": "study-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
            },
            {
                "study_id": "study-1",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "gate-work",
                "work_unit_fingerprint": "fingerprint-2",
                "dispatch_status": "blocked",
            },
        ],
    }

    assert projection.owner_callable_adapters(payload) == []
    assert projection.legacy_owner_callable_adapter_count(payload) == 1
    assert projection.legacy_owner_callable_adapter_status_count(payload, "ready") == 1
    assert projection.adapter_count(payload) == projection.legacy_owner_callable_adapter_count(payload)
    assert projection.adapter_status_count(
        payload,
        "ready",
    ) == projection.legacy_owner_callable_adapter_status_count(payload, "ready")
    assert projection.transition_request_count(payload) == 2
    assert projection.transition_request_status_count(payload, "transition_request_pending") == 1
    assert projection.transition_request_status_count(payload, "blocked") == 1
    diagnostics = projection.legacy_owner_callable_adapter_diagnostics(payload)
    assert diagnostics["surface"] == "legacy_owner_callable_adapter_diagnostics"
    assert diagnostics["canonical_transition_request_surface"] == "domain_progress_transition_requests"
    assert diagnostics["diagnostic_only"] is True
    assert diagnostics["counts_authority"] is False
    assert diagnostics["readiness_authority"] is False
    assert diagnostics["can_create_success_outcome"] is False
    assert diagnostics["body_authority"] is False
    assert diagnostics["body_projection"] is False
    assert diagnostics["legacy_payload_scope"] == "identity_refs_only"
    assert diagnostics["legacy_dispatch_count"] == 1
    assert diagnostics["legacy_ready_count"] == 1
    assert diagnostics["legacy_blocked_count"] == 0
    assert diagnostics["legacy_transition_request_pending_count"] == 0
    assert diagnostics["legacy_dispatches"] == [
        {
            "diagnostic_ref_only": True,
            "payload_body_omitted": True,
            "study_id": "study-1",
            "action_type": "legacy_ready",
            "work_unit_id": "legacy-body-work",
            "work_unit_fingerprint": "legacy-body-fingerprint",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
        }
    ]
    assert diagnostics["legacy_dispatch_refs"] == diagnostics["legacy_dispatches"]
    assert diagnostics["legacy_dispatch_body_omitted"] is True
    assert "source_action" not in diagnostics["legacy_dispatches"][0]
    assert "owner_route" not in diagnostics["legacy_dispatches"][0]
    assert "prompt_contract" not in diagnostics["legacy_dispatches"][0]


def test_owner_callable_projection_requires_canonical_transition_request_surface() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    legacy_payload = {
        "owner_callable_adapters": [
            {
                "study_id": "study-1",
                "quest_id": "quest-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
                "target_runtime_owner": "one-person-lab",
                "refs": {
                    "dispatch_path": (
                        "artifacts/supervision/consumer/owner_callable_adapters/"
                        "run_quality_repair_batch.json"
                    )
                },
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                    "study_id": "study-1",
                    "quest_id": "quest-1",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "repair-work",
                    "work_unit_fingerprint": "fingerprint-1",
                },
            }
        ]
    }

    assert projection.domain_progress_transition_requests(legacy_payload) == []
    assert projection.owner_callable_adapters(legacy_payload) == []
    assert projection.legacy_owner_callable_adapter_count(legacy_payload) == 1
    assert projection.with_owner_callable_adapter_projection(legacy_payload)[
        "domain_progress_transition_request_count"
    ] == 0
    legacy_projected = projection.with_owner_callable_adapter_projection(legacy_payload)
    assert "owner_callable_adapter_list_diagnostic_only" not in legacy_projected
    assert "owner_callable_adapter_count" not in legacy_projected
    assert "owner_callable_adapters" in legacy_payload
    assert "owner_callable_adapters" not in legacy_projected
    assert legacy_projected["legacy_owner_callable_adapter_diagnostics"]["diagnostic_only"] is True
    assert legacy_projected["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatch_count"] == 1
    assert legacy_projected["canonical_transition_request_surface"] == (
        "domain_progress_transition_requests"
    )

    canonical_payload = {
        "domain_progress_transition_requests": [
            {
                "study_id": "study-1",
                "quest_id": "quest-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
                "target_runtime_owner": "one-person-lab",
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                    "study_id": "study-1",
                    "quest_id": "quest-1",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "repair-work",
                    "work_unit_fingerprint": "fingerprint-1",
                },
            }
        ]
    }

    requests = projection.domain_progress_transition_requests(canonical_payload)

    assert len(requests) == 1
    assert requests[0]["surface"] == "mas_domain_progress_transition_request_projection"
    assert requests[0]["study_id"] == "study-1"
    assert requests[0]["action_type"] == "run_quality_repair_batch"
    assert requests[0]["work_unit_fingerprint"] == "fingerprint-1"
    assert requests[0]["mas_dispatch_authority"] is False
    assert requests[0]["mas_creates_owner_callable_carrier"] is False
    assert requests[0]["mas_creates_opl_outbox"] is False
    assert requests[0]["provider_admission_pending"] is False
    assert requests[0]["provider_admission_requires_opl_runtime_result"] is True
    projected = projection.with_owner_callable_adapter_projection(canonical_payload)
    assert projected["domain_progress_transition_request_count"] == 1
    assert "owner_callable_adapter_list_diagnostic_only" not in projected
    assert "owner_callable_adapter_count" not in projected
    assert "owner_callable_adapters" not in projected


def test_public_owner_callable_adapter_reader_is_not_active_carrier() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    payload = {
        "owner_callable_adapters": [
            {
                "study_id": "study-1",
                "action_type": "run_quality_repair_batch",
                "dispatch_status": "ready",
                "dispatch_authority": "ai_reviewer_record_production_handoff",
                "source_action": {
                    "work_unit_id": "legacy-work",
                    "work_unit_fingerprint": "legacy-fingerprint",
                },
                "owner_route": {"next_owner": "write"},
                "prompt_contract": {"action_type": "run_quality_repair_batch"},
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                },
            }
        ]
    }

    assert projection.owner_callable_adapters(payload) == []
    assert projection.adapter_count(payload) == 1
    assert projection.adapter_status_count(payload, "ready") == 1
    refs = projection.legacy_owner_callable_adapter_refs(payload)
    assert refs == [
        {
            "diagnostic_ref_only": True,
            "payload_body_omitted": True,
            "study_id": "study-1",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy-work",
            "work_unit_fingerprint": "legacy-fingerprint",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
        }
    ]
    assert "owner_route" not in refs[0]
    assert "prompt_contract" not in refs[0]
    assert "source_action" not in refs[0]
    assert "opl_domain_progress_transition_request" not in refs[0]


def test_owner_action_execution_payloads_do_not_recommend_retired_private_cli_aliases() -> None:
    action_execution_root = (
        SRC_ROOT
        / "controllers"
        / "stage_outcome_authority"
        / "action_execution"
    )
    forbidden_tokens = (
        "domain-action-request-materialize",
        "stage-outcome-authority",
    )
    violations: list[str] = []
    for path in sorted(action_execution_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_domain_owner_controller_refresh_public_wrapper_is_retired() -> None:
    dispatch_module = importlib.import_module("med_autoscience.controllers.stage_outcome_authority")

    assert not hasattr(dispatch_module, "refresh_controller_decisions_for_current_publication_eval")
    assert "refresh_controller_decisions_for_current_publication_eval" not in getattr(
        dispatch_module,
        "__all__",
        (),
    )
    assert importlib.util.find_spec("med_autoscience.cli_public_surface") is None


def test_retired_domain_owner_refresh_controller_command_is_not_active_cli_surface() -> None:
    retired_command = "domain-owner-action-refresh-controller-decisions"
    allowed_refs = {
        "tests/test_adapter_retirement_boundary.py",
        "tests/test_adapter_retirement_boundary_cases/owner_callable_projection.py",
        "tests/test_cli_cases/domain_action_request_materializer_command.py",
    }
    violations: list[str] = []
    for root in (SRC_ROOT, REPO_ROOT / "tests"):
        for path in sorted(root.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            if retired_command not in text:
                continue
            relative_path = str(path.relative_to(REPO_ROOT))
            if relative_path not in allowed_refs:
                violations.append(relative_path)

    assert violations == []


def test_current_controller_decision_refresh_does_not_emit_legacy_domain_owner_action_surface() -> None:
    source = (
        SRC_ROOT
        / "controllers"
        / "stage_outcome_authority"
        / "controller_refresh.py"
    ).read_text(encoding="utf-8")

    assert "domain_owner_action_controller_decision_refresh" not in source
    assert 'SURFACE = "current_controller_decision_refresh"' in source



__all__ = [name for name in globals() if name.startswith("test_")]
