from __future__ import annotations

import importlib
import json
from pathlib import Path

from . import control_plane_fixtures as fixtures


def _snapshot(*, delivery_sync_allowed: bool = True, gate_state: str = "open") -> dict[str, object]:
    return {
        "surface": "control_plane_snapshot",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "runtime_health": {"epoch": "runtime-1"},
        },
        "dispatch_gate": {
            "state": gate_state,
            "blocking_reasons": ["supervisor_only"] if gate_state != "open" else [],
        },
        "route_authorization": {
            "paper_write_allowed": True,
            "bundle_build_allowed": delivery_sync_allowed,
            "runtime_recovery_allowed": True,
            "cleanup_apply_allowed": True,
        },
    }


def _write_contract(workspace_root: Path, *, action_allowlist: list[str] | None = None) -> None:
    (workspace_root / "control_plane_backfill_apply.json").write_text(
        json.dumps(
            {
                "surface": "control_plane_backfill_apply_contract",
                "controller_decision": {
                    "decision": "approve_backfill_apply",
                    "apply_intent": True,
                },
                "action_allowlist": action_allowlist
                or [
                    "backfill_delivery_manifest_lifecycle_hook",
                    "backfill_delivery_manifest_source_signature",
                    "backfill_delivery_manifest_publication_refs",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _delivery_manifest(workspace_root: Path) -> Path:
    manifests = sorted(workspace_root.rglob("delivery_manifest.json"))
    assert len(manifests) == 1
    return manifests[0]


def test_backfill_apply_default_plans_without_mutating(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    _write_contract(workspace_root)
    manifest_path = _delivery_manifest(workspace_root)
    before = json.loads(manifest_path.read_text(encoding="utf-8"))

    report = module.run_backfill_apply(workspace_roots=[workspace_root])

    assert report["surface"] == "control_plane_backfill_apply"
    assert report["apply"] is False
    assert report["status"] == "planned"
    assert report["control_plane_route_action"] == "delivery_sync"
    assert report["mutation_policy"]["manual_patch_current_package_allowed"] is False
    assert report["mutation_policy"]["manual_patch_submission_minimal_allowed"] is False
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 0, "mutating": 0}
    action = report["apply_plan"][0]
    assert action["eligible_for_apply"] is True
    assert action["actions"] == [
        "backfill_delivery_manifest_lifecycle_hook",
        "backfill_delivery_manifest_source_signature",
        "backfill_delivery_manifest_publication_refs",
    ]
    assert action["patch_preview"]["will_touch_current_package"] is False
    assert action["patch_preview"]["will_touch_submission_minimal"] is False
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == before


def test_backfill_apply_true_fails_closed_without_contract_or_snapshot(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)

    report = module.run_backfill_apply(workspace_roots=[workspace_root], apply=True)

    assert report["status"] == "blocked"
    blockers = report["apply_plan"][0]["blockers"]
    assert "backfill_apply_contract_missing" in blockers
    assert "control_plane_route_gate:control_plane_snapshot_missing" in blockers
    assert report["action_counts"]["applied"] == 0


def test_backfill_apply_true_fails_closed_when_delivery_sync_route_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    _write_contract(workspace_root)

    report = module.run_backfill_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(delivery_sync_allowed=False),
    )

    assert report["status"] == "blocked"
    assert "control_plane_route_gate:bundle_build_allowed_false" in report["apply_plan"][0]["blockers"]
    assert report["action_counts"]["applied"] == 0


def test_backfill_apply_true_updates_only_delivery_manifest_when_authorized(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    _write_contract(workspace_root)
    manifest_path = _delivery_manifest(workspace_root)
    current_package = next(workspace_root.rglob("current_package/README.md"))
    submission_minimal = next(workspace_root.rglob("submission_minimal/paper.md"))
    current_package_before = current_package.read_text(encoding="utf-8")
    submission_minimal_before = submission_minimal.read_text(encoding="utf-8")

    report = module.run_backfill_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert report["status"] == "applied"
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 1, "mutating": 1}
    assert payload["artifact_lifecycle"]["authority_sync"]["source"] == "control_plane_backfill_apply"
    assert payload["source_signature"].startswith("delivery-source::")
    assert payload["authority_source_signature"] == payload["source_signature"]
    assert "publication_gate" in payload["publication_refs"]
    assert current_package.read_text(encoding="utf-8") == current_package_before
    assert submission_minimal.read_text(encoding="utf-8") == submission_minimal_before

