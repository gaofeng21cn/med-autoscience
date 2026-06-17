from __future__ import annotations

import json
import importlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"
ADAPTER_ROOT = SRC_ROOT / "adapters" / "deepscientist"
RUNTIME_TRANSPORT_ROOT = SRC_ROOT / "runtime_transport"


def test_production_code_does_not_import_deepscientist_adapters() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path.is_relative_to(ADAPTER_ROOT):
            continue
        text = path.read_text(encoding="utf-8")
        if "med_autoscience.adapters.deepscientist" not in text and "adapters.deepscientist" not in text:
            continue
        violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_legacy_deepscientist_adapter_modules_are_removed() -> None:
    assert not (ADAPTER_ROOT / "__init__.py").exists()
    assert not (ADAPTER_ROOT / "daemon_api.py").exists()
    assert not (ADAPTER_ROOT / "mailbox.py").exists()
    assert not (ADAPTER_ROOT / "runtime.py").exists()
    assert not (ADAPTER_ROOT / "paper_bundle.py").exists()


def test_legacy_manual_finishing_projection_field_is_not_resurrected() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "legacy_current_stage" in text:
            violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_mas_private_runtime_transport_modules_are_physically_retired() -> None:
    assert not RUNTIME_TRANSPORT_ROOT.exists()


def test_production_code_does_not_import_retired_mas_runtime_transport_modules() -> None:
    forbidden_tokens = (
        "med_autoscience.runtime_transport.mas_runtime_core",
        "from med_autoscience.runtime_transport import mas_runtime_core",
        "from med_autoscience.runtime_transport import mas_runtime_core_",
        "med_autoscience.runtime_transport import mas_runtime_core",
    )
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path.is_relative_to(RUNTIME_TRANSPORT_ROOT):
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_retired_runtime_supervisor_dispatch_executor_test_helper_is_removed() -> None:
    assert not (REPO_ROOT / "tests" / "runtime_supervisor_dispatch_executor_helpers.py").exists()


def test_runtime_like_surfaces_have_machine_readable_opl_migration_inventory() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

    assert inventory["surface_kind"] == "mas_runtime_surface_retirement_inventory"
    assert inventory["version"] == "mas-runtime-surface-retirement-inventory.v1"
    assert inventory["authority_boundary"] == {
        "opl_owns": [
            "queue",
            "attempt",
            "retry",
            "dead_letter",
            "provider_liveness",
            "generic_stage_state",
        ],
        "mas_owns": [
            "domain_truth",
            "ai_reviewer",
            "publication_gate",
            "artifact_authority",
            "owner_receipt",
            "typed_blocker",
        ],
    }
    assert inventory["compatibility_alias_policy"] == {
        "new_alias_allowed": False,
        "active_adapter_can_claim_mas_owner": False,
    }

    surfaces = {item["surface_id"]: item for item in inventory["surfaces"]}
    assert set(surfaces) >= {
        "runtime_transport_core_bridge",
        "runtime_turn_runner_closeout_adapter",
        "worker_lease_residency_projection",
        "domain_authority_refs_index",
        "default_executor_dispatch_request",
        "domain_action_request_materializer_local_carrier_persistence_api",
    }
    for surface in surfaces.values():
        assert surface["generic_runtime_owner"] == "one-person-lab"
        assert surface["mas_owner_claim_allowed"] is False
        assert surface["compatibility_alias_allowed"] is False
        if surface["surface_id"] in {
            "runtime_transport_core_bridge",
            "runtime_turn_runner_closeout_adapter",
            "worker_lease_residency_projection",
            "domain_action_request_materializer_local_carrier_persistence_api",
        }:
            assert surface["active_caller_migrated"] is True
            assert surface["current_disposition"] == "physically_retired"
        assert "mas_owned_generic_runtime" in surface["forbidden_claims"]

    carrier_persistence = surfaces["domain_action_request_materializer_local_carrier_persistence_api"]
    assert carrier_persistence["retained_mas_role"] == "none_physically_retired_no_alias"
    assert carrier_persistence["replacement_surface"] == (
        "owner_callable_adapters plus OPL DomainProgressTransitionRuntime durable carrier"
    )
    assert set(carrier_persistence["retired_symbols"]) == {
        "persist_default_executor_dispatches",
        "persist_request_packets",
        "persist_consumer_payload",
        "request_packet_for_persistence",
        "medical_paper_readiness_packet_for_persistence",
        "source_workflow_ref_for_ai_reviewer_request",
    }
    assert "mas_local_dispatch_carrier_persistence" in carrier_persistence["forbidden_claims"]
    assert "mas_local_request_packet_persistence" in carrier_persistence["forbidden_claims"]


def test_materializer_local_carrier_persistence_api_is_physically_retired() -> None:
    persistence = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.persistence"
    )

    for symbol in (
        "persist_default_executor_dispatches",
        "persist_request_packets",
        "persist_consumer_payload",
        "request_packet_for_persistence",
        "medical_paper_readiness_packet_for_persistence",
        "source_workflow_ref_for_ai_reviewer_request",
    ):
        assert not hasattr(persistence, symbol), symbol

    assert hasattr(persistence, "read_json_object")
    assert hasattr(persistence, "write_json")
