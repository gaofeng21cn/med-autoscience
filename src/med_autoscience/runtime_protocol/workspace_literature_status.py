from __future__ import annotations

from pathlib import Path


WORKSPACE_LITERATURE_SCHEMA_VERSION = 2
OPL_CONNECT_OWNER_REF = "one-person-lab:src/modules/connect/opl-connect-scientific.ts"
OPL_SOURCE_INTAKE_OWNER_REF = (
    "one-person-lab:src/modules/workspace/workspace-source-material.ts"
)
OPL_SOURCE_INGEST_COMMAND = "opl workspace source ingest"


def workspace_literature_status(*, workspace_root: Path) -> dict[str, object]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    return {
        "schema_version": WORKSPACE_LITERATURE_SCHEMA_VERSION,
        "surface_kind": "mas_literature_source_refs",
        "status": "opl_managed",
        "workspace_root": str(resolved_workspace_root),
        "workspace_literature_exists": False,
        "workspace_literature_root": None,
        "registry_path": None,
        "references_bib_path": None,
        "coverage_report_path": None,
        "record_count": 0,
        "references_bib_entry_count": 0,
        "coverage": {
            "status": "opl_connect_or_workspace_receipt_required",
            "high_priority_missing": [],
        },
        "opl_owner_refs": {
            "scientific_connector": OPL_CONNECT_OWNER_REF,
            "source_intake": OPL_SOURCE_INTAKE_OWNER_REF,
            "source_ingest_command": OPL_SOURCE_INGEST_COMMAND,
        },
        "authority_boundary": {
            "transport_owner": "one-person-lab",
            "domain_semantics_owner": "MedAutoScience",
            "mas_writes_generic_source_registry": False,
            "mas_materializes_workspace_bibtex": False,
            "mas_materializes_workspace_coverage": False,
        },
    }


__all__ = ["WORKSPACE_LITERATURE_SCHEMA_VERSION", "workspace_literature_status"]
