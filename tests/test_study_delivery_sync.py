from __future__ import annotations

import importlib

from .test_study_delivery_sync_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_study_delivery_sync_facade_exposes_publication_profile_helpers() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")

    assert module.normalize_publication_profile(" general_medical_journal ") == "general_medical_journal"
    assert module.is_supported_publication_profile("general_medical_journal") is True


from .test_study_delivery_sync_cases.delivery_sync_cases import (
    test_sync_study_delivery_materializes_submission_root_and_keeps_manifest_under_manuscript,
    test_sync_study_delivery_writes_v2_layout_and_freshness_proof_for_submission_root,
    test_sync_study_delivery_refreshes_existing_legacy_package_aliases,
    test_describe_submission_delivery_uses_submission_root_and_detects_staleness,
    test_stale_notice_materializes_preview_into_submission_root,
)
from .test_study_delivery_sync_cases.stale_submission_delivery_cases import (
    test_materialize_submission_delivery_stale_notice_blocks_without_snapshot,
    test_materialize_submission_delivery_stale_notice_allows_open_snapshot,
    test_materialize_submission_delivery_stale_notice_blocks_projection_only_write,
)
from .test_study_delivery_sync_cases.clean_migration_guard_cases import (
    test_sync_study_delivery_blocks_pending_clean_paper_authority_cutover,
)
from .test_study_delivery_sync_cases.v2_layout_and_legacy_cases import (
    test_sync_study_delivery_mirrors_v2_source_manifest_into_v2_current_package,
    test_sync_study_delivery_prefers_newer_submission_minimal_source_over_stale_mirror,
    test_sync_study_delivery_reads_legacy_source_manifest_but_writes_v2_mirror_layout,
    test_current_package_zip_has_shallow_v2_layout_without_embedded_package_root,
    test_describe_submission_delivery_treats_role_specific_reproducibility_docs_as_current,
)
