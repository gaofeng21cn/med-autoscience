from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.authority_handlers._generation_manifest import (
    build_generation_manifest_v2,
)
from med_autoscience.authority_handlers._stage_attempt_review_snapshot import (
    finalize_manuscript_authoring_producer_snapshot_closeout,
)
from med_autoscience.authority_handlers._record_validation import RequestShapeError


ATTEMPT_ID = "manuscript-producer-001"
MANUSCRIPT_ROLES = (
    "source_input_digest",
    "data_release",
    "denominator_definitions",
    "analysis_script",
    "analysis_output",
    "candidate_admission_receipt",
    "canonical_manuscript",
    "claim_evidence_map",
    "citation_ledger",
    "numeric_trace",
    "reference_library",
    "table_catalog",
    "table_file",
    "figure_catalog",
    "figure_file",
    "render_environment_and_font_manifest",
)


def _digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _case(workspace_root: Path, *, lane: str = "medical") -> tuple[
    list[dict[str, Any]], dict[str, str], dict[str, str], dict[str, Any]
]:
    artifact_root = workspace_root / "manuscript" / "frozen"
    artifact_root.mkdir(parents=True)
    artifacts: list[dict[str, Any]] = []
    paths: dict[str, Path] = {}
    for role in MANUSCRIPT_ROLES:
        payload = f"frozen bytes for {role}\n".encode()
        path = artifact_root / f"{role}.txt"
        path.write_bytes(payload)
        member_id = f"mas-member:{role}:primary"
        artifacts.append(
            {
                "role": role,
                "member_id": member_id,
                "ref": f"workspace://study/manuscript/{role}",
                "size_bytes": len(payload),
                "sha256": _digest(payload),
            }
        )
        paths[member_id] = path

    manifest = build_generation_manifest_v2(
        artifacts=artifacts,
        generation_id=f"manuscript-generation:{ATTEMPT_ID}",
        manifest_scope="manuscript_generation",
    )
    scope = next(item for item in manifest["review_scopes"] if item["review_lane"] == lane)
    source_refs = {
        item["member_id"]: paths[item["member_id"]].relative_to(workspace_root).as_posix()
        for item in scope["reviewed_members"]
    }
    environ = {
        "OPL_STAGE_ID": "manuscript_authoring",
        "OPL_STAGE_ATTEMPT_ID": ATTEMPT_ID,
        "OPL_STAGE_ATTEMPT_REF": f"opl://stage_attempts/{ATTEMPT_ID}",
        "OPL_EXECUTION_CONTENT_BINDING_SHA256": _digest(b"execution binding"),
        "OPL_PACKAGE_USE_BOUNDARY_ID": "package-use:manuscript-producer-001",
        "OPL_ROOT_PACKAGE_ID": "mas",
        "OPL_ROOT_PACKAGE_CONTENT_DIGEST": _digest(b"mas package content"),
        "OPL_WORKSPACE_ROOT": str(workspace_root),
    }
    return artifacts, source_refs, environ, paths


def _closeout() -> dict[str, Any]:
    return {
        "surface_kind": "stage_attempt_closeout_packet",
        "stage_attempt_id": ATTEMPT_ID,
        "closeout_ref_metadata": [],
        "route_impact": {"stage_quality_cycle": {}},
    }


def _finalize(tmp_path: Path, *, lane: str = "medical", closeout: dict[str, Any] | None = None):
    artifacts, source_refs, environ, _ = _case(tmp_path, lane=lane)
    return finalize_manuscript_authoring_producer_snapshot_closeout(
        closeout_packet=_closeout() if closeout is None else closeout,
        artifacts=artifacts,
        generation_id=f"manuscript-generation:{ATTEMPT_ID}",
        generation_ref="workspace://study/manuscript/generation-manifest.json",
        review_lane=lane,
        source_refs_by_member_id=source_refs,
        environ=environ,
    )


def test_manuscript_authoring_finalizer_injects_request_and_owner_authority(tmp_path: Path) -> None:
    result = _finalize(tmp_path, lane="reference")
    bundle = result["snapshot_bundle"]
    request = bundle["review_input_snapshot_materialization_request"]

    assert result["surface_kind"] == "mas_manuscript_authoring_producer_snapshot_finalization"
    assert result["stage_id"] == "manuscript_authoring"
    assert result["review_lane"] == "reference"
    assert bundle["manifest_scope"] == "manuscript_generation"
    assert request["schema_version"] == 2
    assert request["producer_attempt_ref"] == "opl://stage_attempts/" + ATTEMPT_ID
    assert request["execution_content_binding_sha256"] == _digest(b"execution binding")
    assert request["owner_authority_ref"]["kind"] == "mas_review_input_snapshot_authority"
    assert request["owner_authority_ref"]["sha256"].startswith("sha256:")

    closeout = result["closeout_packet"]
    assert closeout["stage_attempt_id"] == ATTEMPT_ID
    assert closeout["route_impact"]["stage_quality_cycle"][
        "review_input_snapshot_materialization_request"
    ] == request
    assert closeout["closeout_ref_metadata"] == [request["owner_authority_ref"]]


def test_manuscript_authoring_finalizer_is_idempotent_and_does_not_mutate_input(tmp_path: Path) -> None:
    artifacts, source_refs, environ, _ = _case(tmp_path)
    closeout = _closeout()
    original = deepcopy(closeout)
    result = finalize_manuscript_authoring_producer_snapshot_closeout(
        closeout_packet=closeout,
        artifacts=artifacts,
        generation_id=f"manuscript-generation:{ATTEMPT_ID}",
        generation_ref="workspace://study/manuscript/generation-manifest.json",
        review_lane="medical",
        source_refs_by_member_id=source_refs,
        environ=environ,
    )
    repeated = finalize_manuscript_authoring_producer_snapshot_closeout(
        closeout_packet=result["closeout_packet"],
        artifacts=artifacts,
        generation_id=f"manuscript-generation:{ATTEMPT_ID}",
        generation_ref="workspace://study/manuscript/generation-manifest.json",
        review_lane="medical",
        source_refs_by_member_id=source_refs,
        environ=environ,
    )
    assert closeout == original
    assert repeated["closeout_packet"] == result["closeout_packet"]


@pytest.mark.parametrize(
    ("env_name", "value"),
    [
        ("OPL_STAGE_ID", "bounded_analysis_campaign"),
        ("OPL_STAGE_ATTEMPT_ID", "other-attempt"),
        ("OPL_STAGE_ATTEMPT_REF", "opl://stage_attempts/other-attempt"),
    ],
)
def test_manuscript_authoring_finalizer_rejects_wrong_stage_or_attempt(
    tmp_path: Path, env_name: str, value: str
) -> None:
    artifacts, source_refs, environ, _ = _case(tmp_path)
    environ[env_name] = value
    with pytest.raises(RequestShapeError):
        finalize_manuscript_authoring_producer_snapshot_closeout(
            closeout_packet=_closeout(),
            artifacts=artifacts,
            generation_id=f"manuscript-generation:{ATTEMPT_ID}",
            generation_ref="workspace://study/manuscript/generation-manifest.json",
            review_lane="medical",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )


def test_manuscript_authoring_finalizer_rejects_lane_fallback_or_unknown_lane(tmp_path: Path) -> None:
    artifacts, source_refs, environ, _ = _case(tmp_path)
    with pytest.raises((RequestShapeError, TypeError)):
        finalize_manuscript_authoring_producer_snapshot_closeout(
            closeout_packet=_closeout(),
            artifacts=artifacts,
            generation_id=f"manuscript-generation:{ATTEMPT_ID}",
            generation_ref="workspace://study/manuscript/generation-manifest.json",
            review_lane="",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )
    with pytest.raises(RequestShapeError):
        finalize_manuscript_authoring_producer_snapshot_closeout(
            closeout_packet=_closeout(),
            artifacts=artifacts,
            generation_id=f"manuscript-generation:{ATTEMPT_ID}",
            generation_ref="workspace://study/manuscript/generation-manifest.json",
            review_lane="publication",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )


def test_manuscript_authoring_finalizer_rejects_hash_drift_symlink_and_missing_member(tmp_path: Path) -> None:
    artifacts, source_refs, environ, paths = _case(tmp_path)
    drifted = next(iter(source_refs))
    paths[drifted].write_bytes(b"drifted bytes\n")
    with pytest.raises(RequestShapeError, match="frozen MAS artifact identity"):
        finalize_manuscript_authoring_producer_snapshot_closeout(
            closeout_packet=_closeout(),
            artifacts=artifacts,
            generation_id=f"manuscript-generation:{ATTEMPT_ID}",
            generation_ref="workspace://study/manuscript/generation-manifest.json",
            review_lane="medical",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )

    artifacts, source_refs, environ, paths = _case(tmp_path / "symlink")
    member = next(iter(source_refs))
    link = paths[member].with_name("link.txt")
    link.symlink_to(paths[member])
    source_refs[member] = link.relative_to(tmp_path / "symlink").as_posix()
    with pytest.raises(RequestShapeError, match="symlink"):
        finalize_manuscript_authoring_producer_snapshot_closeout(
            closeout_packet=_closeout(),
            artifacts=artifacts,
            generation_id=f"manuscript-generation:{ATTEMPT_ID}",
            generation_ref="workspace://study/manuscript/generation-manifest.json",
            review_lane="medical",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )

    artifacts, source_refs, environ, _ = _case(tmp_path / "missing")
    source_refs.pop(next(iter(source_refs)))
    with pytest.raises(RequestShapeError, match="exactly match"):
        finalize_manuscript_authoring_producer_snapshot_closeout(
            closeout_packet=_closeout(),
            artifacts=artifacts,
            generation_id=f"manuscript-generation:{ATTEMPT_ID}",
            generation_ref="workspace://study/manuscript/generation-manifest.json",
            review_lane="medical",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )


def test_manuscript_authoring_finalizer_rejects_conflicting_request_or_metadata(tmp_path: Path) -> None:
    result = _finalize(tmp_path)
    request = result["snapshot_bundle"]["review_input_snapshot_materialization_request"]
    conflicting_request = deepcopy(request)
    conflicting_request["producer_attempt_ref"] = "opl://stage_attempts/other"
    closeout = _closeout()
    closeout["route_impact"]["stage_quality_cycle"][
        "review_input_snapshot_materialization_request"
    ] = conflicting_request
    with pytest.raises(RequestShapeError, match="conflicting snapshot"):
        _finalize(tmp_path / "request-conflict", closeout=closeout)

    artifacts, source_refs, environ, _ = _case(tmp_path / "metadata")
    result = finalize_manuscript_authoring_producer_snapshot_closeout(
        closeout_packet=_closeout(),
        artifacts=artifacts,
        generation_id=f"manuscript-generation:{ATTEMPT_ID}",
        generation_ref="workspace://study/manuscript/generation-manifest.json",
        review_lane="medical",
        source_refs_by_member_id=source_refs,
        environ=environ,
    )
    closeout = result["closeout_packet"]
    closeout["closeout_ref_metadata"][0]["sha256"] = _digest(b"wrong")
    with pytest.raises(RequestShapeError, match="conflicting owner authority"):
        finalize_manuscript_authoring_producer_snapshot_closeout(
            closeout_packet=closeout,
            artifacts=artifacts,
            generation_id=f"manuscript-generation:{ATTEMPT_ID}",
            generation_ref="workspace://study/manuscript/generation-manifest.json",
            review_lane="medical",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )
