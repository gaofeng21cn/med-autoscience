from __future__ import annotations

import importlib

import pytest


def test_mas_runtime_backend_module_is_physically_retired() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.runtime_backend")


def test_opl_runtime_contract_is_refs_only_without_provider_callables() -> None:
    module = importlib.import_module("med_autoscience.opl_runtime_contract")

    contract = module.opl_runtime_default_operation_contract()

    assert contract["runtime_owner"] == "one-person-lab"
    assert contract["runtime_substrate"] == "opl_hosted_stage_runtime"
    assert contract["runtime_ref"] == "opl_hosted_stage_runtime"
    assert contract["runtime_backend_is_generic_owner"] is False
    assert contract["mas_runtime_backend_registry_retired"] is True
    assert contract["provider_attempt_owner"] == "one-person-lab"
    assert contract["provider_completion_is_domain_completion"] is False
    assert contract["default_autonomous_runtime"]["mas_daemon_scheduler_attempt_loop_allowed"] is False
    assert contract["domain_progression_requires"] == [
        "mas_owner_receipt",
        "mas_typed_blocker",
        "ai_reviewer_backed_verdict",
        "publication_gate_receipt",
    ]


def test_provider_admission_blocker_does_not_create_mas_provider_backend() -> None:
    module = importlib.import_module("med_autoscience.opl_runtime_contract")

    blocker = module.provider_admission_required_blocker(operation="create_quest", quest_id="quest-001")

    assert blocker["ok"] is False
    assert blocker["status"] == "provider_admission_required"
    assert blocker["runtime_owner"] == "one-person-lab"
    assert blocker["domain_owner"] == "med-autoscience"
    assert blocker["provider_completion_is_domain_completion"] is False
    assert blocker["typed_blocker"]["blocker_type"] == "opl_provider_admission_required"
    assert blocker["typed_blocker"]["reason"] == "mas_private_runtime_backend_retired"


def test_retired_runtime_transport_modules_do_not_resurrect() -> None:
    for module_name in (
        "med_autoscience.runtime_transport.opl_provider_backed_stage_runtime",
        "med_autoscience.runtime_transport.med_deepscientist",
        "med_autoscience.runtime_transport.mas_runtime_core",
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)


def test_runtime_contract_rejects_non_opl_runtime_ref() -> None:
    module = importlib.import_module("med_autoscience.opl_runtime_contract")

    with pytest.raises(ValueError, match="OPL owns runtime hydration"):
        module.engine_id_for_runtime_ref("mas_runtime_core")
