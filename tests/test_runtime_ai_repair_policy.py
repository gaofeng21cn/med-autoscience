from __future__ import annotations

import importlib


def test_runtime_ai_repair_policy_requires_opl_execution_authorization() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_ai_repair_policy")

    payload = module.two_layer_ai_repair_policy_payload()

    assert payload["surface"] == "mas_domain_repair_handoff_policy"
    assert payload["owner_callable_requirement"] == {
        "surface_kind": "mas_owner_callable_execution_requirement",
        "schema_version": 1,
        "execution_authorization_owner": "one-person-lab",
        "required_input": "trusted_opl_execution_authorization",
        "domain_owner": "MedAutoScience",
        "mas_selects_executor": False,
        "mas_selects_model": False,
        "mas_runs_generic_executor": False,
        "mas_may_validate_domain_preconditions": True,
    }
    assert payload["domain_repair_boundary"] == {
        "mas_may_emit_domain_action_ref": True,
        "mas_may_emit_human_gate": True,
        "mas_may_emit_typed_blocker": True,
        "mas_may_authorize_provider_attempt": False,
        "mas_may_run_generic_scheduler": False,
        "mas_may_define_repo_write_policy": False,
    }
    assert payload["guardrails"]["paper_package_mutation_allowed"] is False
    assert payload["guardrails"]["quality_gate_relaxation_allowed"] is False
