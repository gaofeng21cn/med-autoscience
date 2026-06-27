from __future__ import annotations

import importlib
import json
from pathlib import Path


SCHOLARSKILLS_MODULE_IDS = [
    "opl.scholarskills.display",
    "opl.scholarskills.tables",
    "opl.scholarskills.stats",
    "opl.scholarskills.omics",
    "opl.scholarskills.lit",
    "opl.scholarskills.write",
    "opl.scholarskills.review",
    "opl.scholarskills.submit",
    "opl.scholarskills.data",
    "opl.scholarskills.intake",
]

SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE = {
    "opl.scholarskills.display": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "artifact_manifest_ref",
        "visual_audit_or_gallery_preview_ref",
    ],
    "opl.scholarskills.tables": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "table_manifest_ref",
        "table_qc_ref",
    ],
    "opl.scholarskills.stats": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "analysis_manifest_ref",
        "reproducibility_check_ref",
    ],
    "opl.scholarskills.omics": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "omics_pipeline_manifest_ref",
        "feature_matrix_qc_ref",
    ],
    "opl.scholarskills.lit": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "evidence_map_ref",
        "citation_manifest_ref",
    ],
    "opl.scholarskills.write": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "draft_section_manifest_ref",
        "source_trace_ref",
    ],
    "opl.scholarskills.review": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "reviewer_report_ref",
        "route_back_ref",
    ],
    "opl.scholarskills.submit": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "package_manifest_ref",
        "submission_checklist_ref",
    ],
    "opl.scholarskills.data": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "data_manifest_ref",
        "lineage_readiness_ref",
    ],
    "opl.scholarskills.intake": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "source_snapshot_ref",
        "adoption_contract_ref",
    ],
}


def _write_tables_materialized_package(
    package_root: Path,
    *,
    manifest_overrides: dict[str, object] | None = None,
    receipt_overrides: dict[str, object] | None = None,
) -> dict[str, Path]:
    package_root.mkdir(parents=True)
    receipt_path = package_root / "execution_receipt_candidate.json"
    manifest_path = package_root / "manifest.json"
    artifact_manifest_path = package_root / "artifacts" / "table_manifest.json"
    artifact_manifest_path.parent.mkdir()
    artifact_manifest_path.write_text('{"items":[]}', encoding="utf-8")
    authority_flags = {
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_current_package": False,
        "can_write_paper_or_package": False,
        "can_write_study_truth": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
    }
    receipt = {
        "surface_kind": "opl_scholarskills_execution_receipt_candidate",
        "module_id": "opl.scholarskills.tables",
        "execution_receipt_ref": "opl-vault:receipts/tables/receipt.json",
        "artifact_manifest_path": str(artifact_manifest_path),
        "candidate_artifacts": [
            {
                "kind": "table_manifest",
                "ref": "opl-vault:tables/table_manifest.json",
                "sha256": "sha256:table-manifest",
                "readiness_notes": ["candidate table package ready for MAS owner review"],
                "missing_inputs": [],
            }
        ],
        "candidate_artifact_bodies": {
            "table_summary": {
                "body": {"rows": 2, "columns": ["metric", "value"]},
                "readiness_notes": ["body carried only as candidate artifact evidence"],
                "missing_inputs": ["owner_acceptance_ref"],
            }
        },
        "execution_receipt_refs": {
            "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
            "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
            "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
            "table_qc_ref": "opl-vault:tables/qc.json",
        },
        "written_files": [
            "opl-vault:tables/table_manifest.json",
            "opl-vault:tables/qc.json",
        ],
        "sha256": "sha256:receipt",
        "authority_flags": dict(authority_flags),
    }
    if receipt_overrides:
        receipt.update(receipt_overrides)
    manifest = {
        "surface_kind": "opl_scholarskills_materialized_package_manifest",
        "module_id": "opl.scholarskills.tables",
        "execution_receipt_candidate_path": receipt_path.name,
        "artifact_manifest_path": str(artifact_manifest_path),
        "written_files": [str(artifact_manifest_path)],
        "sha256": "sha256:manifest",
        "authority_flags": dict(authority_flags),
    }
    if manifest_overrides:
        manifest.update(manifest_overrides)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return {
        "artifact_manifest_path": artifact_manifest_path,
        "manifest_path": manifest_path,
        "receipt_path": receipt_path,
    }


def _structured_payload(result: dict[str, object]) -> dict[str, object]:
    structured = result["structuredContent"]
    assert isinstance(structured, dict)
    assert structured["surface_kind"] == "mas_tool_result_envelope"
    payload = structured["structured_payload"]
    assert isinstance(payload, dict)
    return payload
