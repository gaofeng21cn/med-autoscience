from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from med_autoscience.agent_tool_arsenal import FORBIDDEN_DOMAIN_AUTHORITY
from med_autoscience.runtime_control.owner_callable_registry import (
    owner_callable_for_action,
    paper_work_unit_lifecycle_for_action,
)


CONTRACT_ID = "mas_authority_kernel_inventory.v1"
CONTRACT_REF = "contracts/authority_kernel_inventory.json"
SCHEMA_VERSION = 1
OWNER = "MedAutoScience"
INVENTORY_STATE = "inventory_landed_physical_thinning_pending"
GENERIC_RUNTIME_OWNER_NAMES = frozenset(
    {
        "OPL",
        "Temporal",
        "one-person-lab",
        "generic_runtime",
        "stage_run_kernel",
        "queue_and_attempt_ledger",
        "state_index_kernel",
        "lifecycle_plane",
        "workbench_shell",
    }
)
REQUIRED_ITEM_FIELDS = (
    "item_id",
    "category",
    "owner",
    "surface_ref",
    "active_caller_refs",
    "allowed_writes",
    "forbidden_authority",
    "output_refs",
    "cannot_lift_to_opl_reason",
)


@dataclass(frozen=True)
class AuthorityKernelItem:
    item_id: str
    category: str
    owner: str
    surface_ref: str
    active_caller_refs: tuple[str, ...]
    allowed_writes: tuple[str, ...]
    forbidden_authority: tuple[str, ...]
    output_refs: tuple[str, ...]
    cannot_lift_to_opl_reason: str
    forbidden_writes: tuple[str, ...] = ()
    retirement_gate: str | None = None
    upcollect_target: str | None = None
    notes: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        return {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in payload.items()
            if value not in (None, (), [])
        }


def build_authority_kernel_inventory() -> dict[str, Any]:
    items = tuple(_inventory_items())
    gaps = _inventory_gaps(items)
    return {
        "surface_kind": "mas_authority_kernel_inventory",
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "owner": OWNER,
        "state": INVENTORY_STATE,
        "contract_ref": CONTRACT_REF,
        "ordinary_planning_root": "current_owner_delta",
        "source_of_truth_refs": [
            "docs/runtime/designs/mas_opl_agent_os_target_operating_architecture.md",
            "docs/active/mas-ideal-state-gap-plan.md",
            "src/med_autoscience/runtime_control/owner_callable_registry.py",
            "src/med_autoscience/agent_tool_arsenal.py",
            "contracts/foundry-agent-os-domain-kernel-manifest.json",
            "contracts/mas-paper-study-stage-pack.json",
        ],
        "required_item_fields": list(REQUIRED_ITEM_FIELDS),
        "forbidden_domain_authority": list(FORBIDDEN_DOMAIN_AUTHORITY),
        "generic_runtime_owner_names": sorted(GENERIC_RUNTIME_OWNER_NAMES),
        "items": [item.to_payload() for item in items],
        "counts": {
            "item_count": len(items),
            "category_count": len({item.category for item in items}),
            "owner_callable_backed_count": sum(
                1
                for item in items
                if any(ref.startswith("owner_callable:") for ref in item.active_caller_refs)
            ),
            "upcollect_target_count": sum(1 for item in items if item.upcollect_target),
            "retirement_gate_count": sum(1 for item in items if item.retirement_gate),
            "gap_count": len(gaps),
        },
        "gaps": gaps,
        "non_claims": {
            "authority_fully_retired": False,
            "physical_thinning_complete": False,
            "production_ready": False,
            "paper_line_progress": False,
            "publication_ready": False,
            "artifact_mutation_authorized": False,
        },
    }


def _inventory_items() -> tuple[AuthorityKernelItem, ...]:
    return (
        _owner_callable_item(
            item_id="owner_receipt_signer.publication_handoff_owner_gate",
            category="owner_receipt_signer",
            action_type="publication_handoff_owner_gate",
            cannot_lift_to_opl_reason=(
                "The terminal publication handoff receipt signs MAS publication-route "
                "owner judgment; OPL may transport StageRun refs but cannot sign the "
                "domain owner answer."
            ),
            upcollect_target="OPL StageRun transports receipt refs only",
            notes=(
                "Does not claim publication-ready or submission-ready by inventory presence.",
            ),
        ),
        _owner_callable_item(
            item_id="typed_blocker_materializer.medical_paper_readiness_surface",
            category="typed_blocker_materializer",
            action_type="complete_medical_paper_readiness_surface",
            cannot_lift_to_opl_reason=(
                "The blocker names missing medical-paper readiness refs and route-back "
                "conditions; OPL can carry the blocker ref but cannot decide the MAS "
                "domain shortcut being avoided."
            ),
            upcollect_target="OPL StageRun carries typed blocker refs only",
        ),
        _stage_pack_item(
            item_id="source_readiness.stage_pack_source_readiness_receipt",
            category="source_readiness",
            surface_ref="contracts/mas-paper-study-stage-pack.json#/stages/2/stable_artifact_roles/2",
            active_caller_refs=(
                "agent/knowledge/source_readiness_and_artifact_authority.md",
                "agent/quality_gates/artifact_source_authority_gate.md",
                "src/med_autoscience/controllers/mas_stage_semantic_receipts.py::validate_mas_stage_semantic_receipt",
            ),
            allowed_writes=(
                "artifacts/stage_outputs/03-data_asset_and_cohort_build/source_readiness_receipt.json",
                "typed blocker:source_readiness_blocker",
            ),
            output_refs=(
                "source_readiness_receipt_refs",
                "source_boundary_refs",
                "typed_blocker_refs",
            ),
            cannot_lift_to_opl_reason=(
                "Source readiness depends on current study claim, cohort, provenance, "
                "source limitations, and medical route impact; generic runtime may only "
                "index the receipt refs."
            ),
            upcollect_target="OPL State Index stores source readiness refs only",
        ),
        _owner_callable_item(
            item_id="publication_quality_gate.ai_reviewer_publication_eval",
            category="publication_quality_gate",
            action_type="return_to_ai_reviewer_workflow",
            cannot_lift_to_opl_reason=(
                "Publication quality requires an independent AI reviewer/auditor record "
                "against current manuscript and evidence refs; provider completion or "
                "generated projection cannot become the verdict."
            ),
            upcollect_target="OPL transports reviewer invocation and eval refs only",
        ),
        _stage_pack_item(
            item_id="artifact_mutation_authorization.artifact_package_authority_receipt",
            category="artifact_mutation_authorization",
            surface_ref="contracts/mas-paper-study-stage-pack.json#/stages/5/stable_artifact_roles/2",
            active_caller_refs=(
                "agent/knowledge/source_readiness_and_artifact_authority.md",
                "agent/quality_gates/artifact_source_authority_gate.md",
                "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
            ),
            allowed_writes=(
                "artifacts/stage_outputs/06-manuscript_authoring/artifact_package_authority_receipt.json",
                "typed blocker:artifact_mutation_blocker",
            ),
            output_refs=(
                "artifact_package_authority_receipt_refs",
                "artifact_package_refs",
                "typed_blocker_refs",
            ),
            cannot_lift_to_opl_reason=(
                "Artifact mutation authorization is tied to canonical manuscript/source "
                "refs, rebuild proof, package freshness, and MAS owner receipt; lifecycle "
                "or cleanup plans cannot authorize mutation."
            ),
            upcollect_target="OPL Lifecycle Plane handles locator, restore, retention, and cleanup transport",
        ),
        _stage_pack_item(
            item_id="memory_accept_reject.publication_route_memory_writeback",
            category="memory_accept_reject",
            surface_ref="contracts/mas-paper-study-stage-pack.json#/stages/4/stable_artifact_roles/2",
            active_caller_refs=(
                "agent/knowledge/publication_route_memory.md",
                "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_writeback.py",
                "src/med_autoscience/controllers/study_transition_receipt_consumption_parts/owner_receipts.py::publication_route_memory_writeback_receipt_consumption",
            ),
            allowed_writes=(
                "artifacts/stage_outputs/05-evidence_synthesis/memory_accept_reject_receipts.json",
                "publication_route_memory/writeback_receipts/*.json",
                "typed blocker:publication_route_memory_writeback_blocker",
            ),
            output_refs=(
                "memory_accept_reject_receipt_refs",
                "publication_route_memory_writeback_receipt_refs",
                "typed_blocker_refs",
            ),
            cannot_lift_to_opl_reason=(
                "Memory accept/reject is a MAS reviewer or route-authority decision over "
                "publication-route memory body and router receipts; OPL can expose "
                "locators and receipt metadata only."
            ),
            upcollect_target="OPL memory locator/index reads receipt metadata only",
        ),
        _owner_callable_item(
            item_id="no_forbidden_write_proof.external_learning_sidecar",
            category="no_forbidden_write_proof",
            action_type="run_external_learning_sidecar",
            cannot_lift_to_opl_reason=(
                "The sidecar is refs-only and nonblocking, but MAS owns the forbidden "
                "authority envelope proving advisory output did not become study truth, "
                "quality verdict, artifact authority, or memory authority."
            ),
            upcollect_target="OPL Capability Registry invokes advisory workers fail-open",
        ),
        _capability_item(),
        _diagnostic_probe_item(),
    )


def _owner_callable_item(
    *,
    item_id: str,
    category: str,
    action_type: str,
    cannot_lift_to_opl_reason: str,
    upcollect_target: str,
    notes: tuple[str, ...] = (),
) -> AuthorityKernelItem:
    callable_payload = owner_callable_for_action(action_type)
    if callable_payload is None:
        raise ValueError(f"Missing owner callable for action_type={action_type}")
    lifecycle = paper_work_unit_lifecycle_for_action(action_type) or {}
    allowed_writes = tuple(_list_text(lifecycle.get("allowed_writes")))
    forbidden_writes = tuple(_list_text(lifecycle.get("forbidden_writes")))
    output_refs = tuple(
        _list_text(lifecycle.get("required_output_refs") or callable_payload.get("required_outputs"))
    )
    return AuthorityKernelItem(
        item_id=item_id,
        category=category,
        owner=_required_text(callable_payload.get("owner"), "owner"),
        surface_ref=(
            "src/med_autoscience/runtime_control/owner_callable_registry.py::"
            f"{action_type}"
        ),
        active_caller_refs=(
            f"owner_callable:{action_type}",
            _required_text(callable_payload.get("callable_surface"), "callable_surface"),
        ),
        allowed_writes=allowed_writes,
        forbidden_writes=forbidden_writes,
        forbidden_authority=tuple(FORBIDDEN_DOMAIN_AUTHORITY),
        output_refs=output_refs,
        cannot_lift_to_opl_reason=cannot_lift_to_opl_reason,
        upcollect_target=upcollect_target,
        notes=notes,
    )


def _stage_pack_item(
    *,
    item_id: str,
    category: str,
    surface_ref: str,
    active_caller_refs: tuple[str, ...],
    allowed_writes: tuple[str, ...],
    output_refs: tuple[str, ...],
    cannot_lift_to_opl_reason: str,
    upcollect_target: str,
) -> AuthorityKernelItem:
    return AuthorityKernelItem(
        item_id=item_id,
        category=category,
        owner=OWNER,
        surface_ref=surface_ref,
        active_caller_refs=active_caller_refs,
        allowed_writes=allowed_writes,
        forbidden_authority=tuple(FORBIDDEN_DOMAIN_AUTHORITY),
        output_refs=output_refs,
        cannot_lift_to_opl_reason=cannot_lift_to_opl_reason,
        upcollect_target=upcollect_target,
    )


def _capability_item() -> AuthorityKernelItem:
    return AuthorityKernelItem(
        item_id="refs_only_helper.scientific_capability_registry",
        category="refs_only_helper",
        owner=OWNER,
        surface_ref="src/med_autoscience/scientific_capability_registry.py::build_scientific_capability_registry",
        active_caller_refs=(
            "contracts/agent_tool_arsenal.json#/tool_cards/scientific_capability_registry",
            "src/med_autoscience/agent_tool_arsenal.py::build_agent_tool_arsenal_index",
            "src/med_autoscience/mcp_server.py::agent_tool_arsenal",
        ),
        allowed_writes=(
            "artifacts/advisory/external_learning_sidecar/latest.json",
            "artifacts/stage_outputs/<stage>/advisory/light_external_pattern_refs.json",
            "artifacts/runtime/evo_scientist_sidecar/latest.json",
            "display_pack_agent refs-only plan outputs",
        ),
        forbidden_authority=tuple(FORBIDDEN_DOMAIN_AUTHORITY),
        output_refs=(
            "refs-only advisory candidates",
            "reviewer briefing refs",
            "repair hint refs",
            "display_pack_agent_figure_plan",
        ),
        cannot_lift_to_opl_reason=(
            "The helper itself is refs-only and can be hosted by OPL, but MAS must keep "
            "the domain boundary that prevents capability output from becoming quality, "
            "publication, artifact, memory, or study truth authority."
        ),
        upcollect_target="OPL Capability Registry / Tool Arsenal runtime consumption",
    )


def _diagnostic_probe_item() -> AuthorityKernelItem:
    return AuthorityKernelItem(
        item_id="diagnostic_probe.domain_health_diagnostic",
        category="diagnostic_probe",
        owner=OWNER,
        surface_ref="src/med_autoscience/controllers/domain_health_diagnostic.py",
        active_caller_refs=(
            "medautosci runtime domain-health-diagnostic --dry-run",
            "src/med_autoscience/mcp_server.py::domain_health_diagnostic",
            "docs/status.md#Accepted typed closeout currentness hardening",
        ),
        allowed_writes=(
            "artifacts/runtime/domain_health_diagnostic/*.json",
            "diagnostic projection refs",
            "typed blocker candidates",
        ),
        forbidden_authority=tuple(FORBIDDEN_DOMAIN_AUTHORITY),
        output_refs=(
            "domain_health_diagnostic_ref",
            "currentness_probe_ref",
            "route_back_evidence_ref",
            "typed_blocker_candidate_ref",
        ),
        cannot_lift_to_opl_reason=(
            "The probe can diagnose currentness and owner-route gaps but cannot be a "
            "generic runtime owner; MAS keeps the diagnostic boundary so probe output "
            "does not become owner answer, publication verdict, or paper progress."
        ),
        retirement_gate=(
            "Retire MAS-private diagnostic implementation only after OPL Route "
            "Reconciler consumes the same MAS owner receipt / typed blocker refs and "
            "focused parity tests prove no authority drift."
        ),
        upcollect_target="OPL Route Reconciler and Observability Plane",
    )


def _inventory_gaps(items: tuple[AuthorityKernelItem, ...]) -> list[dict[str, Any]]:
    categories = {item.category for item in items}
    required = {
        "owner_receipt_signer",
        "typed_blocker_materializer",
        "source_readiness",
        "publication_quality_gate",
        "artifact_mutation_authorization",
        "memory_accept_reject",
        "no_forbidden_write_proof",
        "refs_only_helper",
        "diagnostic_probe",
    }
    gaps: list[dict[str, Any]] = [
        {
            "gap_id": "missing_required_category",
            "missing_categories": sorted(required - categories),
        }
    ] if required - categories else []
    for item in items:
        missing_fields = [
            field
            for field in REQUIRED_ITEM_FIELDS
            if getattr(item, field) in (None, "", (), [])
        ]
        if missing_fields:
            gaps.append(
                {
                    "gap_id": "inventory_item_missing_required_fields",
                    "item_id": item.item_id,
                    "missing_fields": missing_fields,
                }
            )
        missing_forbidden = sorted(set(FORBIDDEN_DOMAIN_AUTHORITY) - set(item.forbidden_authority))
        if missing_forbidden:
            gaps.append(
                {
                    "gap_id": "inventory_item_missing_forbidden_authority",
                    "item_id": item.item_id,
                    "missing_forbidden_authority": missing_forbidden,
                }
            )
        if item.owner in GENERIC_RUNTIME_OWNER_NAMES:
            gaps.append(
                {
                    "gap_id": "generic_runtime_owner_listed_as_retained_authority",
                    "item_id": item.item_id,
                    "owner": item.owner,
                }
            )
    return gaps


def _list_text(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, Mapping):
        return [str(key) for key in value]
    try:
        return [str(item) for item in value or [] if str(item or "").strip()]
    except TypeError:
        return []


def _required_text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Missing required {field}")
    return text


__all__ = [
    "CONTRACT_ID",
    "CONTRACT_REF",
    "GENERIC_RUNTIME_OWNER_NAMES",
    "REQUIRED_ITEM_FIELDS",
    "build_authority_kernel_inventory",
]
