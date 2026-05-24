from __future__ import annotations

from copy import deepcopy
from typing import Any


FORBIDDEN_RUNTIME_PATCH_REFS = [
    "src/med_autoscience/controllers/runtime_control/owner_route.py",
    "src/med_autoscience/controllers/domain_action_request_materializer.py",
    "src/med_autoscience/controllers/domain_owner_action_dispatch.py",
]

ALLOWED_PATCH_REFS = [
    "tests/test_unique_control_plane_canary_registry.py",
    "contracts/unique_control_plane_canary_registry.json",
    "docs/active/unique_control_plane_canary_registry.md",
    "src/med_autoscience/controllers/unique_control_plane_canary_registry.py",
]


def _canary(
    *,
    category: str,
    slug: str,
    target_studies: list[str],
    mas_fixture_refs: list[str],
    opl_transport_fixture_refs: list[str],
    owner_route_regression_refs: list[str],
    no_forbidden_write_proof_refs: list[str],
) -> dict[str, Any]:
    canary_id = f"opl-unique-control-plane-canary:{slug}"
    work_order_ref = f"work-order:opl/unique-control-plane-canary/{slug}"
    suite_ref = f"agent-lab-suite:opl/unique-control-plane-canary/{slug}"
    return {
        "canary_id": canary_id,
        "category": category,
        "target_studies": target_studies,
        "semantic_role": "standard_agent_purity_regression_guard",
        "failure_class": f"{category}_standard_agent_purity_canary",
        "migration_boundary": {
            "canonical_control_plane_owner": "OPL",
            "mas_role": "domain_truth_quality_and_owner_receipt_authority",
            "registry_must_not_recreate_duplicate_mas_runtime": True,
        },
        "mas_fixture_refs": mas_fixture_refs,
        "opl_transport_fixture_refs": opl_transport_fixture_refs,
        "owner_route_regression_refs": owner_route_regression_refs,
        "no_forbidden_write_proof_refs": no_forbidden_write_proof_refs,
        "work_order_refs": [work_order_ref],
        "agent_lab_regression_loop": {
            "output_mode": "executable_regression_work_order",
            "executable": True,
            "suite_ref": suite_ref,
            "work_order_ref": work_order_ref,
            "developer_patch_work_order": {
                "work_order_id": f"oma_developer_patch_work_order_opl_ucp_canary_{slug.replace('-', '_')}",
                "owner_agent": "opl-meta-agent",
                "role": "developer_direct_repo_patch",
                "can_modify_mas_repo": True,
                "can_write_study_truth": False,
                "can_authorize_quality_verdict": False,
                "executable": True,
                "canary_id": canary_id,
                "category": category,
                "allowed_patch_refs": ALLOWED_PATCH_REFS,
                "forbidden_patch_refs": FORBIDDEN_RUNTIME_PATCH_REFS,
                "target_test_refs": owner_route_regression_refs
                + ["tests/test_unique_control_plane_canary_registry.py"],
                "mas_fixture_refs": mas_fixture_refs,
                "opl_transport_fixture_refs": opl_transport_fixture_refs,
                "no_forbidden_write_proof_refs": no_forbidden_write_proof_refs,
                "verification_command_refs": [
                    "scripts/run-pytest-clean.sh tests/test_unique_control_plane_canary_registry.py -q",
                    f"opl agent-lab run --suite {suite_ref} --json",
                ],
            },
        },
    }


REGISTRY: dict[str, Any] = {
    "surface_kind": "opl_unique_control_plane_canary_registry",
    "schema_version": 1,
    "registry_id": "opl-unique-control-plane-canary-registry-dm002-dm003-v1",
    "owner": "MedAutoScience",
    "updated_at": "2026-05-23",
    "target_studies": ["DM002", "DM003"],
    "migration_semantics": {
        "program": "standard_agent_purity_guard",
        "canonical_control_plane_owner": "OPL",
        "domain_owner": "MedAutoScience",
        "duplicate_mas_runtime_claimed": False,
    },
    "canaries": [
        _canary(
            category="currentness",
            slug="dm002-currentness",
            target_studies=["DM002"],
            mas_fixture_refs=[
                "tests/test_ai_reviewer_publication_eval_workflow.py",
                "tests/fixtures/dm002_ai_first_observation.py",
            ],
            opl_transport_fixture_refs=[
                "opl:agent-lab/transport/currentness-basis",
                "contracts/agent_lab_handoff.json",
            ],
            owner_route_regression_refs=[
                "tests/test_paper_progress_state.py",
                "regression-suite:mas/owner-route/currentness",
            ],
            no_forbidden_write_proof_refs=[
                "tests/test_unique_control_plane_canary_registry.py",
                "no-forbidden-write:mas/dm002/currentness",
            ],
        ),
        _canary(
            category="stale_dispatch",
            slug="dm002-stale-dispatch",
            target_studies=["DM002"],
            mas_fixture_refs=[
                "tests/test_paper_repair_executor.py",
                "tests/test_quality_repair_batch_cases/medical_prose_write_repair.py",
            ],
            opl_transport_fixture_refs=[
                "opl:agent-lab/transport/default-executor-dispatch",
                "contracts/generated_surface_handoff.json",
            ],
            owner_route_regression_refs=[
                "tests/test_domain_owner_action_dispatch_cases/quality_repair_owner_route_cases.py",
                "regression-suite:mas/owner-route/stale-dispatch",
            ],
            no_forbidden_write_proof_refs=[
                "tests/test_unique_control_plane_canary_registry.py",
                "no-forbidden-write:mas/dm002/stale-dispatch",
            ],
        ),
        _canary(
            category="provider_terminal_sync",
            slug="dm003-provider-terminal-sync",
            target_studies=["DM003"],
            mas_fixture_refs=[
                "tests/test_real_paper_autonomy_soak_inventory_cases/test_canary_body_free_packets.py",
                "tests/product_entry_cases/action_catalog_parity_cases/provider_cases.py",
            ],
            opl_transport_fixture_refs=[
                "opl:agent-lab/transport/provider-terminal-sync",
                "opl:temporal-provider/typed-closeout",
            ],
            owner_route_regression_refs=[
                "tests/test_opl_agent_lab_longline_migration.py",
                "regression-suite:mas/provider-terminal-sync",
            ],
            no_forbidden_write_proof_refs=[
                "tests/test_real_paper_autonomy_soak_inventory_cases/test_canary_body_free_packets.py",
                "no-forbidden-write:mas/dm003/provider-terminal-sync",
            ],
        ),
        _canary(
            category="owner_precedence",
            slug="dm003-owner-precedence",
            target_studies=["DM003"],
            mas_fixture_refs=[
                "tests/test_study_outer_loop_cases/quality_repair_priority_cases.py",
                "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_live_work_unit_autonomy_repair.py",
            ],
            opl_transport_fixture_refs=[
                "opl:agent-lab/transport/owner-route-precedence",
                "contracts/owner_receipt_contract.json",
            ],
            owner_route_regression_refs=[
                "tests/test_gate_clearing_batch_cases/quality_repair_route_context.py",
                "regression-suite:mas/owner-route/owner-precedence",
            ],
            no_forbidden_write_proof_refs=[
                "tests/test_unique_control_plane_canary_registry.py",
                "no-forbidden-write:mas/dm003/owner-precedence",
            ],
        ),
        _canary(
            category="paper_delta_missing",
            slug="dm002-dm003-paper-delta-missing",
            target_studies=["DM002", "DM003"],
            mas_fixture_refs=[
                "tests/test_paper_repair_execution_evidence.py",
                "tests/test_paper_repair_execution_evidence_cases/story_surface_delta_cases.py",
            ],
            opl_transport_fixture_refs=[
                "opl:agent-lab/transport/typed-closeout-paper-delta",
                "opl:agent-lab/work-order/artifact-delta-ref",
            ],
            owner_route_regression_refs=[
                "tests/test_paper_work_unit_lifecycle_contract.py",
                "regression-suite:mas/work-unit/paper-delta-adoption",
            ],
            no_forbidden_write_proof_refs=[
                "tests/test_unique_control_plane_canary_registry.py",
                "no-forbidden-write:mas/paper-delta-missing",
            ],
        ),
        _canary(
            category="quality_authority_stale",
            slug="dm002-dm003-quality-authority-stale",
            target_studies=["DM002", "DM003"],
            mas_fixture_refs=[
                "tests/test_agent_lab_medical_manuscript_quality.py",
                "tests/test_ai_reviewer_publication_eval_workflow.py",
            ],
            opl_transport_fixture_refs=[
                "opl:agent-lab/transport/quality-authority-stale",
                "contracts/agent_lab_handoff.json",
            ],
            owner_route_regression_refs=[
                "tests/test_gate_clearing_batch_cases/submission_authority_sync.py",
                "regression-suite:mas/quality-authority/currentness",
            ],
            no_forbidden_write_proof_refs=[
                "tests/test_unique_control_plane_canary_registry.py",
                "no-forbidden-write:mas/quality-authority-stale",
            ],
        ),
    ],
    "coverage_proof": {
        "covers_mas_fixture_refs": True,
        "covers_opl_transport_fixture_refs": True,
        "covers_owner_route_regression_refs": True,
        "covers_no_forbidden_write_proof_refs": True,
        "required_ref_groups": [
            "mas_fixture_refs",
            "opl_transport_fixture_refs",
            "owner_route_regression_refs",
            "no_forbidden_write_proof_refs",
        ],
        "contract_refs": ["contracts/unique_control_plane_canary_registry.json"],
    },
}


def build_unique_control_plane_canary_registry() -> dict[str, Any]:
    return deepcopy(REGISTRY)


__all__ = ["build_unique_control_plane_canary_registry"]
