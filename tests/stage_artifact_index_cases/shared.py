from __future__ import annotations

import json
from pathlib import Path

PAPER_STUDY_STAGE_PACK_REF = "contracts/mas-paper-study-stage-pack.json"
EXPECTED_PAPER_STUDY_STAGE_IDS = (
    "01-study_intake",
    "02-protocol_and_analysis_plan",
    "03-data_asset_and_cohort_build",
    "04-analysis_execution",
    "05-evidence_synthesis",
    "06-manuscript_authoring",
    "07-independent_review_and_revision",
    "08-publication_package_handoff",
)
EXPECTED_AUTHORITY_FUNCTIONS = (
    "study_truth",
    "source_readiness",
    "reviewer_quality",
    "publication_gate",
    "artifact_package_authority",
    "memory_accept_reject",
    "typed_blocker",
    "medical_owner_receipt",
)
EXPECTED_LEGACY_ROUTE_IDS = (
    "scout",
    "idea",
    "baseline",
    "experiment",
    "analysis-campaign",
    "write",
    "review",
    "finalize",
    "decision",
    "journal-resolution",
)

STUDY_INTAKE_REFS = [
    "artifacts/stage_outputs/01-study_intake/study_truth_snapshot.json",
    "artifacts/stage_outputs/01-study_intake/source_readiness_assessment.json",
    "artifacts/stage_outputs/01-study_intake/study_intake_owner_receipt.json",
]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path, text: str = "content\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_stage_native_contract(
    study_root: Path,
    *,
    stage_id: str,
    refs: list[str],
) -> None:
    base = study_root / "artifacts" / "stage_outputs" / stage_id
    write_json(
        base / "stage_manifest.json",
        {
            "surface_kind": "stage_manifest",
            "schema_version": 1,
            "stage_id": stage_id,
            "artifact_refs": refs,
        },
    )
    write_json(
        base / "receipts/owner_receipt.json",
        {
            "surface_kind": "mas_stage_owner_receipt",
            "schema_version": 1,
            "stage_id": stage_id,
            "owner": stage_id,
            "receipt_kind": "stage_artifact_delta",
            "artifact_refs": refs,
        },
    )


def write_opl_physical_stage_attempt(
    state_root: Path,
    *,
    study_id: str,
    stage_id: str,
    attempt_id: str,
    output_ref: str,
) -> dict[str, str]:
    deliverable_root = (
        state_root
        / "runtime-state"
        / "domains"
        / "med-autoscience"
        / "deliverables"
        / "mas-paper-study"
        / study_id
        / "paper-study"
    )
    stage_root = deliverable_root / "stages" / stage_id
    attempt_root = stage_root / "attempts" / attempt_id
    for child in ("inputs", "outputs", "evidence", "receipts"):
        (attempt_root / child).mkdir(parents=True, exist_ok=True)
    write_json(
        deliverable_root / "deliverable.json",
        {
            "surface_kind": "opl_stage_artifact_deliverable",
            "domain_id": "med-autoscience",
            "program_id": "mas-paper-study",
            "topic_id": study_id,
            "deliverable_id": "paper-study",
        },
    )
    write_json(
        deliverable_root / "current.json",
        {
            "surface_kind": "opl_stage_artifact_runtime_current",
            "locator": {
                "domain_id": "med-autoscience",
                "program_id": "mas-paper-study",
                "topic_id": study_id,
                "deliverable_id": "paper-study",
            },
            "current_stage": {
                "stage_id": stage_id,
                "status": "success",
                "latest_attempt_id": attempt_id,
            },
        },
    )
    write_json(
        stage_root / "stage.json",
        {
            "surface_kind": "opl_stage_artifact_stage",
            "stage_id": stage_id,
        },
    )
    (stage_root / "latest").write_text(f"{attempt_id}\n", encoding="utf-8")
    write_json(
        attempt_root / "attempt.json",
        {
            "surface_kind": "opl_stage_artifact_attempt",
            "stage_id": stage_id,
            "attempt_id": attempt_id,
        },
    )
    (attempt_root / "outputs" / output_ref).write_text("artifact\n", encoding="utf-8")
    write_json(
        attempt_root / "receipts" / "owner-receipt.json",
        {
            "receipt_ref": f"mas-owner-receipt:{stage_id}:{attempt_id}",
        },
    )
    write_json(
        attempt_root / "manifest.json",
        {
            "surface_kind": "opl_stage_artifact_manifest",
            "manifest_version": "stage-artifact-manifest.v1",
            "stage_id": stage_id,
            "attempt_id": attempt_id,
            "terminal_status": "success",
            "required_outputs": [output_ref],
            "present_outputs": [output_ref],
            "output_hashes": [
                {
                    "path": output_ref,
                    "sha256": "0" * 64,
                    "kind": "output",
                }
            ],
            "evidence_hashes": [],
            "receipt_hashes": [
                {
                    "path": "owner-receipt.json",
                    "sha256": "1" * 64,
                    "kind": "receipt",
                }
            ],
            "owner_receipt_refs": [f"mas-owner-receipt:{stage_id}:{attempt_id}"],
            "typed_blocker_refs": [],
            "decision_receipt_refs": [f"mas-domain-decision:{stage_id}:{attempt_id}"],
            "restore_refs": [f"restore-index:{stage_id}:{attempt_id}"],
            "retention_refs": [f"retention-ledger:{stage_id}:{attempt_id}"],
        },
    )
    lineage_root = deliverable_root / "lineage"
    lineage_root.mkdir(parents=True, exist_ok=True)
    (lineage_root / "events.jsonl").write_text(
        json.dumps(
            {
                "surface_kind": "opl_stage_artifact_lineage_event",
                "event_kind": "attempt_committed",
                "stage_id": stage_id,
                "attempt_id": attempt_id,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    write_json(
        lineage_root / "graph.json",
        {
            "surface_kind": "opl_stage_artifact_lineage_graph",
            "nodes": [{"stage_id": stage_id, "attempt_id": attempt_id}],
        },
    )
    return {
        "deliverable_root": str(deliverable_root),
        "stage_root": str(stage_root),
        "attempt_root": str(attempt_root),
        "manifest_ref": str(attempt_root / "manifest.json"),
        "receipt_ref": str(attempt_root / "receipts" / "owner-receipt.json"),
        "current_pointer_ref": str(deliverable_root / "current.json"),
        "latest_pointer_ref": str(stage_root / "latest"),
    }
