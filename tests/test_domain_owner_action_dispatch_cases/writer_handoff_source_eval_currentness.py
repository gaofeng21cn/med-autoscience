from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import owner_route as _owner_route
from tests.study_runtime_test_helpers import make_profile


def test_writer_handoff_does_not_reuse_owner_route_bound_to_stale_source_eval(
    tmp_path: Path,
) -> None:
    writer_handoff = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.writer_handoff"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = f"quest-{study_id}"
    current_eval_id = "publication-eval::dm003::current"
    old_eval_id = "publication-eval::dm003::old"
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "domain-transition::route-back::medical-prose-current"
    stale_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    stale_route.update(
        {
            "truth_epoch": old_eval_id,
            "route_epoch": old_eval_id,
            "runtime_health_epoch": "runtime-health::old",
            "work_unit_fingerprint": "domain-transition::route-back::medical-prose-old",
            "source_fingerprint": "truth-source::dm003::old",
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "idempotency_key": "owner-route::dm003::old-story-surface",
            "source_refs": {
                "source_eval_id": old_eval_id,
                "work_unit_id": "old_medical_prose_write_repair",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
        }
    )

    handoff = writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=quest_id,
        schema_version=1,
        source_eval_id=current_eval_id,
        source_eval_artifact_path="artifacts/publication_eval/latest.json",
        source_summary_artifact_path="artifacts/eval_hygiene/evaluation_summary/latest.json",
        repair_execution_evidence_path=(
            profile.studies_root
            / study_id
            / "artifacts/controller/repair_execution_evidence/latest.json"
        ),
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "current_owner_route": stale_route,
            "controller_route_context": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_eval_id": current_eval_id,
            },
        },
    )

    owner_route = handoff["owner_route"]
    assert owner_route["truth_epoch"] == current_eval_id
    assert owner_route["route_epoch"] == f"quality-repair-writer-handoff::{study_id}::{current_eval_id}"
    assert owner_route["source_refs"]["source_eval_id"] == current_eval_id
    assert owner_route["source_refs"]["work_unit_id"] == work_unit_id
    assert owner_route["work_unit_fingerprint"] == work_unit_fingerprint
    assert owner_route["idempotency_key"] == (
        f"quality-repair-writer-handoff::{study_id}::{work_unit_fingerprint}"
    )
