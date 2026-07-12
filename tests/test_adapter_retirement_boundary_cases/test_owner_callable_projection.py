from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"


def test_legacy_owner_callable_body_is_diagnostic_only() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.owner_callable_adapter_projection"
    )
    payload = {
        "owner_callable_adapters": [
            {
                "study_id": "study-1",
                "action_type": "run_quality_repair_batch",
                "dispatch_status": "ready",
                "dispatch_authority": "legacy_dispatch",
                "source_action": {
                    "work_unit_id": "legacy-work",
                    "work_unit_fingerprint": "legacy-fingerprint",
                },
                "owner_route": {"next_owner": "write"},
                "prompt_contract": {"action_type": "run_quality_repair_batch"},
                "opl_ai_route_context": {"surface_kind": "retired"},
            }
        ]
    }

    assert projection.owner_callable_adapters(payload) == []
    assert projection.ai_route_contexts(payload) == []
    projected = projection.with_owner_callable_adapter_projection(payload)
    assert projected["canonical_ai_route_context_surface"] == "ai_route_contexts"
    assert projected["ai_route_context_count"] == 0
    assert "owner_callable_adapters" not in projected
    refs = projected["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatch_refs"]
    assert refs == [
        {
            "diagnostic_ref_only": True,
            "payload_body_omitted": True,
            "study_id": "study-1",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy-work",
            "work_unit_fingerprint": "legacy-fingerprint",
            "dispatch_status": "ready",
            "dispatch_authority": "legacy_dispatch",
        }
    ]


def test_ai_route_context_is_canonical_and_non_authoritative() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.owner_callable_adapter_projection"
    )
    payload = {
        "ai_route_contexts": [
            {
                "study_id": "study-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "ai_route_context": {
                    "surface_kind": "mas_ai_route_context",
                    "route_selection_owner": "codex_cli",
                },
            }
        ]
    }

    contexts = projection.ai_route_contexts(payload)
    assert len(contexts) == 1
    assert contexts[0]["surface"] == "mas_ai_route_context_projection"
    assert contexts[0]["provider_admission_pending"] is False
    assert contexts[0]["provider_admission_requires_opl_runtime_result"] is False
    assert contexts[0]["mas_dispatch_authority"] is False
    assert contexts[0]["mas_creates_opl_event"] is False
    assert contexts[0]["mas_creates_opl_outbox"] is False
    assert contexts[0]["mas_creates_opl_stage_run"] is False
    projected = projection.with_owner_callable_adapter_projection(payload)
    assert projected["ai_route_context_count"] == 1
    assert projected["canonical_ai_route_context_surface"] == "ai_route_contexts"


def test_owner_action_execution_payloads_do_not_recommend_retired_private_cli_aliases() -> None:
    action_execution_root = SRC_ROOT / "controllers" / "stage_outcome_authority" / "action_execution"
    forbidden_tokens = ("domain-action-request-materialize", "stage-outcome-authority")
    violations = [
        str(path.relative_to(REPO_ROOT))
        for path in sorted(action_execution_root.rglob("*.py"))
        if any(token in path.read_text(encoding="utf-8") for token in forbidden_tokens)
    ]
    assert violations == []


def test_domain_owner_controller_refresh_public_wrapper_is_retired() -> None:
    dispatch_module = importlib.import_module("med_autoscience.controllers.stage_outcome_authority")
    assert not hasattr(dispatch_module, "refresh_controller_decisions_for_current_publication_eval")
    assert "refresh_controller_decisions_for_current_publication_eval" not in getattr(
        dispatch_module, "__all__", ()
    )
    assert importlib.util.find_spec("med_autoscience.cli_public_surface") is None
