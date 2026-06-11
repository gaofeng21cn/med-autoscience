from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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
