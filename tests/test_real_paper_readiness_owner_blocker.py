from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    build_real_paper_autonomy_guarded_apply_proof,
)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_profile(workspace: Path, profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        "\n".join(
            [
                'name = "fixture"',
                f'workspace_root = "{workspace}"',
                f'runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace / "studies"}"',
                f'portfolio_root = "{workspace / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _readiness_payload(*, with_capability_surfaces: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "surface": "medical_paper_readiness",
        "overall_status": "missing",
        "authority_contract": {
            "authority": "observability_projection_only",
            "read_model_only": True,
            "can_authorize_quality": False,
            "can_authorize_submission": False,
            "can_authorize_finalize": False,
        },
        "next_action": {
            "action_id": "complete_medical_paper_readiness_surface",
            "surface_key": "literature_provider_runtime",
        },
    }
    if with_capability_surfaces:
        payload["capability_surfaces"] = [
            {
                "surface_key": "literature_provider_runtime",
                "status": "missing",
                "missing_reason": "missing_canonical_artifact",
                "required_for_ready": True,
            }
        ]
    return payload


def _dm002_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    dm002 = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(dm002 / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": dm002.name})
    return yang_root, profile_path, dm002


def test_real_paper_autonomy_guarded_apply_proof_keeps_readiness_projection_read_only(
    tmp_path: Path,
) -> None:
    yang_root, profile_path, dm002 = _dm002_fixture(tmp_path)
    _write_json(
        dm002 / "artifacts" / "medical_paper" / "readiness.json",
        _readiness_payload(with_capability_surfaces=False),
    )

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )

    assert payload["guarded_apply_status"] == "blocked_no_mas_owner_apply_receipt"
    receipt = payload["guarded_apply_receipts"][0]
    assert receipt["apply_result"] == "typed_blocker"
    assert receipt["mas_owner_apply_receipt_refs"] == []
    assert not (dm002 / "artifacts" / "controller_decisions" / "latest.json").exists()


def test_readiness_owner_blocker_projection_unblocks_guarded_apply_as_stable_blocker(
    tmp_path: Path,
) -> None:
    projector = importlib.import_module("med_autoscience.controllers.medical_paper_readiness_owner_blocker")
    yang_root, profile_path, dm002 = _dm002_fixture(tmp_path)
    _write_json(
        dm002 / "artifacts" / "medical_paper" / "readiness.json",
        _readiness_payload(with_capability_surfaces=True),
    )

    projection = projector.materialize_readiness_owner_blocker(
        study_root=dm002,
        source="test",
        apply=True,
    )

    decision_path = dm002 / "artifacts" / "controller_decisions" / "latest.json"
    assert projection["status"] == "materialized"
    assert projection["controller_decision_ref"] == str(decision_path)
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["surface"] == "controller_decision"
    assert decision["route_decision"] == "stable_blocker"
    assert decision["runtime_decision"] == "blocked"
    assert decision["blocked_reason"] == "medical_paper_readiness_missing"
    assert decision["quality_claim_authorized"] is False
    assert decision["submission_authorized"] is False

    payload = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=yang_root,
        profile_paths=[profile_path],
        target_studies=("DM002",),
    )

    assert payload["guarded_apply_status"] == "mas_owner_apply_receipt_observed"
    receipt = payload["guarded_apply_receipts"][0]
    assert receipt["apply_result"] == "stable_blocker"
    assert receipt["mas_owner_apply_receipt_refs"] == [str(decision_path)]
    assert payload["summary"]["writes_performed"] is False
    assert payload["summary"]["real_workspace_mutation_allowed"] is False
    assert receipt["workspace_mutation"]["provider_attempt_wrote_workspace"] is False
    assert receipt["workspace_mutation"]["writes_performed"] is False
