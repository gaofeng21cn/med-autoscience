from __future__ import annotations

from typing import Any

from .provider_readiness import DOMAIN_OWNER, OPL_OWNER, TARGET_DOMAIN_ID


def build_opl_lifecycle_inventory_surface() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_lifecycle_inventory",
        "version": "mas-opl-lifecycle-inventory.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "classification_policy": "framework_generic_moves_to_opl_refs_only_mas_domain_specific_remains_mas_truth",
        "framework_generic": [
            _inventory_item(
                "provider_stage_attempt",
                "OPL provider attempt ledger, retry, dead-letter, signal, and query metadata.",
                "move_to_opl_provider",
                owner=OPL_OWNER,
                mas_exports_refs_only=True,
            ),
            _inventory_item(
                "runtime_lifecycle_sidecar_index",
                (
                    "MAS domain sidecar/reference adapter over lifecycle refs; OPL owns the generic "
                    "persistence/lifecycle replacement contract."
                ),
                "lift_to_opl_framework",
                owner=OPL_OWNER,
                mas_exports_refs_only=True,
            ),
            _inventory_item(
                "artifact_locator_and_retention_projection",
                "Artifact root locator, freshness index, retention policy, cache cleanup receipt, and restore proof refs.",
                "lift_to_opl_framework",
                owner=OPL_OWNER,
                mas_exports_refs_only=True,
            ),
            _inventory_item(
                "operator_projection_cache",
                "Read-only workbench or runtime projection cache built from MAS source refs.",
                "move_to_opl_provider",
                owner=OPL_OWNER,
                mas_exports_refs_only=True,
            ),
        ],
        "mas_domain_specific": [
            _inventory_item(
                "study_truth_and_runtime_health",
                "StudyTruth, RuntimeHealth, study macro state, runtime_watch, and study_runtime_status authority.",
                "retain_in_mas",
                owner=DOMAIN_OWNER,
            ),
            _inventory_item(
                "publication_quality_and_ai_reviewer",
                "publication_eval/latest.json, AI reviewer workflow, publication gate, and quality verdicts.",
                "retain_in_mas",
                owner=DOMAIN_OWNER,
            ),
            _inventory_item(
                "paper_package_and_artifact_authority",
                "canonical manuscript, evidence/review ledgers, submission_minimal, current package, and artifact gate.",
                "retain_in_mas",
                owner=DOMAIN_OWNER,
            ),
            _inventory_item(
                "owner_route_and_domain_dispatch_receipts",
                "MAS owner-route reconcile, guarded domain dispatch receipts, gate replay, and stop-loss/human gate.",
                "retain_in_mas",
                owner=DOMAIN_OWNER,
            ),
        ],
    }

def _inventory_item(
    item_id: str,
    summary: str,
    target_class: str,
    *,
    owner: str,
    mas_exports_refs_only: bool = False,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "summary": summary,
        "target_class": target_class,
        "owner": owner,
        "mas_exports_refs_only": mas_exports_refs_only,
        "domain_truth_allowed": owner == DOMAIN_OWNER,
    }
