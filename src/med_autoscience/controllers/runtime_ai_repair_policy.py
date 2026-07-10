from __future__ import annotations

from typing import Any


SCHEMA_VERSION = 1


def owner_callable_policy() -> dict[str, Any]:
    return {
        "surface_kind": "mas_owner_callable_execution_requirement",
        "schema_version": SCHEMA_VERSION,
        "execution_authorization_owner": "one-person-lab",
        "required_input": "trusted_opl_execution_authorization",
        "domain_owner": "MedAutoScience",
        "mas_selects_executor": False,
        "mas_selects_model": False,
        "mas_runs_generic_executor": False,
        "mas_may_validate_domain_preconditions": True,
    }


def two_layer_ai_repair_policy_payload() -> dict[str, Any]:
    return {
        "surface": "mas_domain_repair_handoff_policy",
        "schema_version": SCHEMA_VERSION,
        "owner_callable_requirement": owner_callable_policy(),
        "domain_repair_boundary": {
            "mas_may_emit_domain_action_ref": True,
            "mas_may_emit_human_gate": True,
            "mas_may_emit_typed_blocker": True,
            "mas_may_authorize_provider_attempt": False,
            "mas_may_run_generic_scheduler": False,
            "mas_may_define_repo_write_policy": False,
        },
        "guardrails": {
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    }


__all__ = ["owner_callable_policy", "two_layer_ai_repair_policy_payload"]
