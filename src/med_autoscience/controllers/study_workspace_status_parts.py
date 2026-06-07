from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


SURFACE_KIND = "study_workspace_status"
TARGET_STATE_REFERENCE_DOC = "docs/source/study_workspace_target_state.md"
STAGE_INDEX_SCHEMA = "mas.study_stage_index.v1"
WORKSPACE_INDEX_SCHEMA = "mas.workspace_index.v1"
WORKSPACE_STATUS_SCHEMA = "mas.workspace_status.v1"
WORKSPACE_MIGRATION_STAGE_ID = "00-workspace_target_state_migration"
MIGRATION_MANIFEST_ROOT_RELPATH = Path("_archive") / "migration_manifest"
MIGRATION_HISTORY_ROOT_RELPATH = MIGRATION_MANIFEST_ROOT_RELPATH / "history"
PAPER_CLEAN_ROOM_DESCRIPTOR_RELPATH = Path("artifacts") / "supervision" / "paper_clean_room_rebuild" / "latest.json"
STAGE_OUTPUTS_RELPATH = Path("artifacts") / "stage_outputs"
STAGE_REQUIRED_DIRS = (
    Path("inputs"),
    Path("outputs"),
    Path("role_artifacts"),
    Path("receipts"),
    Path("lineage"),
    Path("projection"),
)
USER_ENTRY_REFS = {
    "study_status": Path("STUDY_STATUS.md"),
    "study_config": Path("study.yaml"),
    "paper_metadata": Path("paper.yaml"),
    "current_stage": Path("control/current_stage.json"),
    "next_action": Path("control/next_action.json"),
    "stage_index": Path("control/stage_index.json"),
    "blockers": Path("control/blockers.json"),
    "current_package_status": Path("publication/current_package/STATUS.json"),
}
WORKSPACE_ENTRY_REFS = {
    "workspace_status": Path("WORKSPACE_STATUS.md"),
    "workspace_descriptor": Path("workspace.yaml"),
    "workspace_index": Path("workspace_index.json"),
    "reports_studies_index": Path("reports/studies_index.json"),
    "reports_latest_status": Path("reports/latest_status.json"),
}
PRODUCT_VIEW_DIRS = (
    Path("paper"),
    Path("analysis"),
    Path("evidence"),
    Path("publication"),
    Path("publication/current_package"),
)
CURRENT_PAPER_INPUTS = (
    (
        "current_manuscript",
        Path("paper/draft.md"),
        (
            Path("artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/draft.md"),
            Path("paper/draft.md"),
            Path("paper/build/review_manuscript.md"),
        ),
        True,
    ),
    (
        "evidence_ledger",
        Path("evidence/evidence_ledger.json"),
        (
            Path("artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/evidence_ledger.json"),
            Path(
                "artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/manuscript/audit/evidence_ledger.json"
            ),
            Path("evidence/evidence_ledger.json"),
            Path("paper/evidence_ledger.json"),
            Path("artifacts/evidence_ledger.json"),
        ),
        True,
    ),
    (
        "review_ledger",
        Path("paper/review/review_ledger.json"),
        (
            Path("artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/review/review_ledger.json"),
            Path("artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/manuscript/review/review_ledger.json"),
            Path("paper/review/review_ledger.json"),
            Path("artifacts/review_ledger.json"),
        ),
        True,
    ),
    (
        "claim_evidence_map",
        Path("paper/claim_evidence_map.json"),
        (
            Path("artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/claim_evidence_map.json"),
            Path("paper/claim_evidence_map.json"),
        ),
        False,
    ),
    (
        "medical_manuscript_blueprint",
        Path("paper/medical_manuscript_blueprint.json"),
        (
            Path(
                "artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/medical_manuscript_blueprint.json"
            ),
            Path("paper/medical_manuscript_blueprint.json"),
            Path("artifacts/publication_eval/medical_manuscript_blueprint.json"),
        ),
        False,
    ),
    (
        "figure_catalog",
        Path("paper/figures/figure_catalog.json"),
        (
            Path("artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/figures/figure_catalog.json"),
            Path("paper/figures/figure_catalog.json"),
        ),
        False,
    ),
    (
        "table_catalog",
        Path("paper/tables/table_catalog.json"),
        (
            Path("artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper/tables/table_catalog.json"),
            Path("paper/tables/table_catalog.json"),
        ),
        False,
    ),
)
AUTHORITY_BOUNDARY = {
    "paper_body_mutation_allowed": False,
    "publication_eval_write_allowed": False,
    "controller_decision_write_allowed": False,
    "runtime_truth_write_allowed": False,
    "current_package_promotion_allowed": False,
    "submission_package_regenerated": False,
    "legacy_archive_import_allowed": False,
    "user_entry_surface_materialization_allowed": True,
    "stage_native_directory_materialization_allowed": True,
    "stage_success_receipt_fabrication_allowed": False,
    "stage_migration_typed_blocker_materialization_allowed": True,
    "stage_receipt_or_blocker_fabrication_allowed": False,
}


def workspace_taxonomy(profile: WorkspaceProfile) -> dict[str, Any]:
    workspace_root = profile.workspace_root.expanduser().resolve()
    return {
        "workspace_root": {
            "path": str(workspace_root),
            "role": "disease_workspace_root",
            "owns": ["shared_data", "literature", "memory", "workspace_index", "runtime_projection"],
        },
        "studies_root": {
            "path": str(profile.studies_root.expanduser().resolve()),
            "role": "canonical_studies_root",
            "study_root_pattern": "studies/<study_id>",
        },
        "runtime_root": {
            "path": str(profile.runtime_root.expanduser().resolve()),
            "role": "runtime_execution_state_logs_receipts_provenance",
            "user_entry": False,
            "current_paper_truth": False,
        },
        "archive_roots": [
            {
                "path": str((workspace_root / "archive").resolve()),
                "role": "workspace_archive_provenance",
                "current_truth": False,
            },
            {
                "path": str((workspace_root / "runtime" / "archives").resolve()),
                "role": "legacy_runtime_archive_provenance",
                "current_truth": False,
            },
            {
                "path": str(profile.med_deepscientist_runtime_root.expanduser().resolve()),
                "role": "historical_fixture_or_archive_import",
                "current_truth": False,
            },
        ],
    }
