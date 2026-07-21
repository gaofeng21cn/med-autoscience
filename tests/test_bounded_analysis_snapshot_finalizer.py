from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.authority_handlers._stage_attempt_review_snapshot import (
    finalize_bounded_analysis_producer_snapshot_closeout,
)


ATTEMPT_ID = "bounded-producer-001"


def _digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _case(
    workspace_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, str]]:
    artifact_root = workspace_root / "analysis" / "frozen"
    artifact_root.mkdir(parents=True)
    artifacts = []
    source_refs = {}
    for role in (
        "source_input_digest",
        "data_release",
        "denominator_definitions",
        "analysis_script",
        "analysis_output",
    ):
        member_id = f"mas-member:{role}:primary"
        payload = f"frozen bytes for {role}\n".encode()
        path = artifact_root / f"{role}.txt"
        path.write_bytes(payload)
        artifacts.append(
            {
                "role": role,
                "member_id": member_id,
                "ref": f"workspace://study/analysis/{role}",
                "size_bytes": len(payload),
                "sha256": _digest(payload),
            }
        )
        if role != "source_input_digest":
            source_refs[member_id] = path.relative_to(workspace_root).as_posix()
    environ = {
        "OPL_STAGE_ID": "bounded_analysis_campaign",
        "OPL_STAGE_ATTEMPT_ID": ATTEMPT_ID,
        "OPL_STAGE_ATTEMPT_REF": f"opl://stage_attempts/{ATTEMPT_ID}",
        "OPL_EXECUTION_CONTENT_BINDING_SHA256": _digest(b"execution binding"),
        "OPL_PACKAGE_USE_BOUNDARY_ID": "package-use:bounded-producer-001",
        "OPL_ROOT_PACKAGE_ID": "mas",
        "OPL_ROOT_PACKAGE_CONTENT_DIGEST": _digest(b"mas package content"),
        "OPL_WORKSPACE_ROOT": str(workspace_root),
    }
    return artifacts, source_refs, environ


def _closeout() -> dict[str, Any]:
    return {
        "surface_kind": "stage_attempt_closeout_packet",
        "stage_attempt_id": ATTEMPT_ID,
        "closeout_ref_metadata": [
            {
                "kind": "analysis_output",
                "ref": "workspace://study/analysis/result",
                "size_bytes": 10,
                "sha256": _digest(b"result"),
            }
        ],
        "route_impact": {
            "stage_quality_cycle": {
                "artifact_refs": ["workspace://study/analysis/result"],
                "artifact_hashes": [_digest(b"result")],
            }
        },
    }


def test_finalizer_builds_statistical_snapshot_and_injects_closeout(
    tmp_path: Path,
) -> None:
    artifacts, source_refs, environ = _case(tmp_path)
    closeout = _closeout()
    original = deepcopy(closeout)

    result = finalize_bounded_analysis_producer_snapshot_closeout(
        closeout_packet=closeout,
        artifacts=artifacts,
        generation_id="analysis-generation:bounded-producer-001",
        generation_ref="workspace://study/analysis/generation-manifest.json",
        source_refs_by_member_id=source_refs,
        environ=environ,
    )

    assert closeout == original
    assert result["stage_id"] == "bounded_analysis_campaign"
    assert result["review_lane"] == "statistical"
    bundle = result["snapshot_bundle"]
    assert bundle["manifest_scope"] == "analysis_generation"
    assert bundle["review_lane"] == "statistical"
    request = bundle["review_input_snapshot_materialization_request"]
    assert request["producer_attempt_ref"] == environ["OPL_STAGE_ATTEMPT_REF"]
    assert request["execution_content_binding_sha256"] == environ[
        "OPL_EXECUTION_CONTENT_BINDING_SHA256"
    ]
    assert {item["member_id"] for item in request["members"]} == set(source_refs)
    assert {
        item["member_id"]: item["source_ref"] for item in request["members"]
    } == source_refs

    finalized = result["closeout_packet"]
    assert finalized["route_impact"]["stage_quality_cycle"][
        "review_input_snapshot_materialization_request"
    ] == request
    assert finalized["closeout_ref_metadata"][-1] == request[
        "owner_authority_ref"
    ]

    repeated = finalize_bounded_analysis_producer_snapshot_closeout(
        closeout_packet=finalized,
        artifacts=artifacts,
        generation_id="analysis-generation:bounded-producer-001",
        generation_ref="workspace://study/analysis/generation-manifest.json",
        source_refs_by_member_id=source_refs,
        environ=environ,
    )
    assert repeated["closeout_packet"] == finalized


def test_finalizer_fails_before_injection_when_source_bytes_do_not_match(
    tmp_path: Path,
) -> None:
    artifacts, source_refs, environ = _case(tmp_path)
    closeout = _closeout()
    original = deepcopy(closeout)
    member_id = next(iter(source_refs))
    (tmp_path / source_refs[member_id]).write_text("changed bytes\n", encoding="utf-8")

    with pytest.raises(ValueError, match="frozen MAS artifact identity"):
        finalize_bounded_analysis_producer_snapshot_closeout(
            closeout_packet=closeout,
            artifacts=artifacts,
            generation_id="analysis-generation:bounded-producer-001",
            generation_ref="workspace://study/analysis/generation-manifest.json",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )

    assert closeout == original
    assert "review_input_snapshot_materialization_request" not in closeout[
        "route_impact"
    ]["stage_quality_cycle"]


def test_finalizer_rejects_locator_escape_and_zero_artifact_fabrication(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    artifacts, source_refs, environ = _case(workspace_root)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    source_refs[next(iter(source_refs))] = outside.as_uri()

    with pytest.raises(ValueError, match="escapes OPL_WORKSPACE_ROOT"):
        finalize_bounded_analysis_producer_snapshot_closeout(
            closeout_packet=_closeout(),
            artifacts=artifacts,
            generation_id="analysis-generation:bounded-producer-001",
            generation_ref="workspace://study/analysis/generation-manifest.json",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )

    hard_boundary_closeout = _closeout()
    hard_boundary_closeout["route_impact"]["hard_stop_class"] = (
        "zero_consumable_artifact"
    )
    with pytest.raises(ValueError, match="missing required roles"):
        finalize_bounded_analysis_producer_snapshot_closeout(
            closeout_packet=hard_boundary_closeout,
            artifacts=[],
            generation_id="analysis-generation:bounded-producer-001",
            generation_ref="workspace://study/analysis/generation-manifest.json",
            source_refs_by_member_id={},
            environ=environ,
        )
    assert "review_input_snapshot_materialization_request" not in (
        hard_boundary_closeout["route_impact"]["stage_quality_cycle"]
    )


@pytest.mark.parametrize(
    "env_name",
    [
        "OPL_STAGE_ATTEMPT_REF",
        "OPL_EXECUTION_CONTENT_BINDING_SHA256",
        "OPL_PACKAGE_USE_BOUNDARY_ID",
        "OPL_ROOT_PACKAGE_ID",
        "OPL_ROOT_PACKAGE_CONTENT_DIGEST",
    ],
)
def test_finalizer_requires_every_attempt_package_binding(
    tmp_path: Path,
    env_name: str,
) -> None:
    artifacts, source_refs, environ = _case(tmp_path)
    del environ[env_name]

    with pytest.raises(ValueError, match=env_name):
        finalize_bounded_analysis_producer_snapshot_closeout(
            closeout_packet=_closeout(),
            artifacts=artifacts,
            generation_id="analysis-generation:bounded-producer-001",
            generation_ref="workspace://study/analysis/generation-manifest.json",
            source_refs_by_member_id=source_refs,
            environ=environ,
        )
