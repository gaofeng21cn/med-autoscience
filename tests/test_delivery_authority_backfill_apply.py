from __future__ import annotations

import importlib
import json
from pathlib import Path

from . import control_plane_fixtures as fixtures


def _snapshot(*, delivery_sync_allowed: bool = True, gate_state: str = "open") -> dict[str, object]:
    return {
        "surface": "authority_snapshot",
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
        },
    }


def _write_contract(
    workspace_root: Path,
    *,
    action_allowlist: list[str] | None = None,
    controller_decision: dict[str, object] | None = None,
    targets: list[dict[str, object]] | None = None,
) -> None:
    (workspace_root / "delivery_authority_backfill_apply.json").write_text(
        json.dumps(
            {
                "surface": "delivery_authority_backfill_apply_contract",
                "controller_decision": controller_decision
                or {
                    "decision": "approve_backfill_apply",
                    "apply_intent": True,
                },
                "action_allowlist": action_allowlist
                or [
                    "backfill_delivery_manifest_lifecycle_hook",
                    "backfill_delivery_manifest_source_signature",
                    "backfill_delivery_manifest_publication_refs",
                ],
                **({"targets": targets} if targets is not None else {}),
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
    module = importlib.import_module("med_autoscience.controllers.delivery_authority_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    _write_contract(workspace_root)
    manifest_path = _delivery_manifest(workspace_root)
    before = json.loads(manifest_path.read_text(encoding="utf-8"))

    report = module.run_backfill_apply(workspace_roots=[workspace_root])

    assert report["surface"] == "delivery_authority_backfill_apply"
    assert report["apply"] is False
    assert report["status"] == "planned"
    assert report["authority_route_action"] == "delivery_sync"
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
    module = importlib.import_module("med_autoscience.controllers.delivery_authority_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)

    report = module.run_backfill_apply(workspace_roots=[workspace_root], apply=True)

    assert report["status"] == "blocked"
    blockers = report["apply_plan"][0]["blockers"]
    assert "backfill_apply_contract_missing" in blockers
    assert "authority_route_gate:authority_snapshot_missing" in blockers
    assert report["action_counts"]["applied"] == 0


def test_backfill_apply_true_fails_closed_when_delivery_sync_route_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_authority_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    _write_contract(workspace_root)

    report = module.run_backfill_apply(
        workspace_roots=[workspace_root],
        apply=True,
        authority_snapshot=_snapshot(delivery_sync_allowed=False),
    )

    assert report["status"] == "blocked"
    assert "authority_route_gate:bundle_build_allowed_false" in report["apply_plan"][0]["blockers"]
    assert report["action_counts"]["applied"] == 0


def test_backfill_apply_true_fails_closed_when_controller_intent_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_authority_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    _write_contract(
        workspace_root,
        controller_decision={"decision": "audit_backfill_apply", "apply_intent": False},
    )
    manifest_path = _delivery_manifest(workspace_root)
    before = json.loads(manifest_path.read_text(encoding="utf-8"))

    report = module.run_backfill_apply(
        workspace_roots=[workspace_root],
        apply=True,
        authority_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert "controller_backfill_apply_intent_missing" in report["apply_plan"][0]["blockers"]
    assert report["action_counts"]["applied"] == 0
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == before


def test_backfill_apply_true_blocks_targets_outside_workspace_after_resolve(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_authority_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    outside_root = tmp_path / "outside-study"
    outside_manifest = outside_root / "manuscript" / "delivery_manifest.json"
    outside_manifest.parent.mkdir(parents=True)
    outside_manifest.write_text(
        json.dumps(
            {
                "study_id": "outside-study",
                "surface": "delivery_manifest",
                "authority_owner": "controller",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_contract(
        workspace_root,
        targets=[{"delivery_manifest_path": "../outside-study/manuscript/delivery_manifest.json"}],
    )
    before = json.loads(outside_manifest.read_text(encoding="utf-8"))

    report = module.run_backfill_apply(
        workspace_roots=[workspace_root],
        apply=True,
        authority_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert report["action_counts"]["applied"] == 0
    assert "target_outside_workspace" in report["apply_plan"][0]["blockers"]
    assert json.loads(outside_manifest.read_text(encoding="utf-8")) == before


def test_backfill_apply_true_updates_only_delivery_manifest_when_authorized(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_authority_backfill_apply")
    workspace_root = fixtures.build_migration_audit_fixture_legacy_delivery_manifest_backfill(tmp_path)
    _write_contract(workspace_root)
    manifest_path = _delivery_manifest(workspace_root)
    current_package = next(workspace_root.rglob("current_package/README.md"))
    submission_minimal = next(workspace_root.rglob("submission_minimal/paper.md"))
    current_package_before = current_package.read_text(encoding="utf-8")
    submission_minimal_before = submission_minimal.read_text(encoding="utf-8")
    manifest_before = json.loads(manifest_path.read_text(encoding="utf-8"))

    report = module.run_backfill_apply(
        workspace_roots=[workspace_root],
        apply=True,
        authority_snapshot=_snapshot(),
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert report["status"] == "applied"
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 1, "mutating": 1}
    assert payload["artifact_lifecycle"]["authority_sync"]["source"] == "delivery_authority_backfill_apply"
    assert payload["source_signature"].startswith("delivery-source::")
    assert payload["authority_source_signature"] == payload["source_signature"]
    assert "publication_gate" in payload["publication_refs"]
    assert current_package.read_text(encoding="utf-8") == current_package_before
    assert submission_minimal.read_text(encoding="utf-8") == submission_minimal_before
    assert set(payload) == set(manifest_before) | {
        "artifact_lifecycle",
        "source_signature",
        "authority_source_signature",
        "publication_refs",
    }
    assert report["applied_actions"][0]["apply_result"]["field_paths"] == [
        "artifact_lifecycle",
        "source_signature",
        "authority_source_signature",
        "publication_refs",
    ]
