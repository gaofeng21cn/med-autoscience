from __future__ import annotations

import ast
import hashlib
import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _dir_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(child.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _cleanup_apply_fixture(
    root: Path,
    *,
    action: str = "delete-safe-cache",
    runtime_status: str = "stopped",
    artifact_role: str = "safe_cache",
    include_restore_contract: bool = True,
    allowlist: list[str] | None = None,
) -> tuple[Path, Path]:
    workspace_root = root / "workspace"
    cache_root = workspace_root / "scratch" / "cache"
    cache_root.mkdir(parents=True)
    (cache_root / "cache.tmp").write_text("delete-safe fixture\n", encoding="utf-8")
    restore_index = workspace_root / "restore_index.json"
    _write_json(restore_index, {"entries": [{"path": "scratch/cache"}]})

    cleanup_action: dict[str, object] = {
        "action": action,
        "target_path": "scratch/cache",
        "artifact_role": artifact_role,
        "target_allowlist": {"source": "test_fixture", "target_path": "scratch/cache"},
    }
    if include_restore_contract:
        cleanup_action["restore_contract"] = {
            "restore_index_path": "restore_index.json",
            "sha256": _dir_sha256(cache_root),
            "rehydrate_verification": {"status": "verified"},
        }

    _write_json(
        workspace_root / "control_plane_cleanup_apply.json",
        {
            "surface": "control_plane_cleanup_apply_contract",
            "runtime": {"status": runtime_status, "active_run_id": "run-live" if runtime_status == "running" else None},
            "controller_decision": {"decision": "approve_cleanup_apply", "apply_intent": True},
            "action_allowlist": allowlist if allowlist is not None else ["delete-safe-cache"],
            "actions": [cleanup_action],
        },
    )
    return workspace_root, cache_root


def _clear_contract_actions(workspace_root: Path) -> None:
    contract_path = workspace_root / "control_plane_cleanup_apply.json"
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["actions"] = []
    contract_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _retention_report_fixture(workspace_root: Path, cache_root: Path) -> dict[str, object]:
    return {
        "surface": "control_plane_lifecycle_report",
        "workspaces": [
            {
                "workspace_root": str(workspace_root),
                "retention_plan": {
                    "surface_kind": "artifact_retention_operations_plan",
                    "operation_listing": "bounded",
                    "operation_sample": [
                        {
                            "path": str(cache_root),
                            "workspace_relative_path": "scratch/cache",
                            "role": "cache",
                            "lifecycle": "cache_transient",
                            "cleanup_candidate_action": "delete-safe-cache",
                            "retention_action": "delete_safe_cache",
                            "physical_delete_allowed": True,
                        }
                    ],
                },
            }
        ],
    }


def _snapshot(*, cleanup_apply_allowed: bool = True, gate_state: str = "open") -> dict[str, object]:
    return {
        "surface": "control_plane_snapshot",
        "control_state": "ready",
        "canonical_next_action": "cleanup_apply",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "runtime_health": {"epoch": "health-1"},
        },
        "dispatch_gate": {
            "state": gate_state,
            "blocking_reasons": ["supervisor_only"] if gate_state != "open" else [],
        },
        "route_authorization": {
            "paper_write_allowed": True,
            "bundle_build_allowed": True,
            "runtime_recovery_allowed": True,
            "cleanup_apply_allowed": cleanup_apply_allowed,
            "authorized": cleanup_apply_allowed,
        },
    }


def _literal_set_assignment(module: ast.Module, name: str) -> set[str]:
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        value = node.value
        if not (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "frozenset"
            and value.args
            and isinstance(value.args[0], ast.Set)
        ):
            raise AssertionError(f"{name} must stay a literal frozenset")
        return {
            element.value
            for element in value.args[0].elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        }
    raise AssertionError(f"{name} assignment not found")


def _implemented_apply_actions(module: ast.Module) -> set[str]:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_apply_action":
            continue
        actions: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Compare) and isinstance(child.left, ast.Name) and child.left.id == "action_id":
                for comparator in child.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                        actions.add(comparator.value)
        return actions
    raise AssertionError("_apply_action not found")


def test_cleanup_apply_physical_allowlist_matches_implemented_and_tested_actions() -> None:
    path = Path("src/med_autoscience/controllers/control_plane_cleanup_apply.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    allowed_actions = _literal_set_assignment(tree, "ALLOWED_PHYSICAL_ACTIONS")

    assert allowed_actions == {"delete-safe-cache"}
    assert _implemented_apply_actions(tree) == allowed_actions


def test_cleanup_apply_default_generates_plan_without_mutating(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)

    report = module.run_cleanup_apply(workspace_roots=[workspace_root])

    assert report["surface"] == "control_plane_cleanup_apply"
    assert report["apply"] is False
    assert report["status"] == "planned"
    assert cache_root.exists()
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 0, "mutating": 0}
    assert report["apply_plan"][0]["action"] == "delete-safe-cache"
    assert report["apply_plan"][0]["eligible_for_apply"] is True


def test_cleanup_apply_plans_safe_cache_candidate_from_retention_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)
    _clear_contract_actions(workspace_root)

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        retention_report=_retention_report_fixture(workspace_root, cache_root),
    )

    retention_action = report["apply_plan"][0]
    assert cache_root.exists()
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 0, "mutating": 0}
    assert retention_action["action"] == "delete-safe-cache"
    assert retention_action["artifact_role"] == "safe_cache"
    assert retention_action["eligible_for_apply"] is True
    assert retention_action["audit_payload"]["candidate_source"] == "retention_report"
    assert retention_action["safe_cache_candidate"]["source_ref"] == (
        "workspaces[0].retention_plan.operation_sample[0]"
    )
    assert retention_action["safe_cache_candidate"]["workspace_relative_path"] == "scratch/cache"


def test_cleanup_apply_deletes_safe_cache_candidate_from_retention_report_after_gates(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)
    _clear_contract_actions(workspace_root)

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
        retention_report=_retention_report_fixture(workspace_root, cache_root),
    )

    assert report["status"] == "applied"
    assert not cache_root.exists()
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 1, "mutating": 1}
    assert report["workspaces"][0]["contract_present"] is True
    assert report["workspaces"][0]["retention_report_candidate_count"] == 1
    assert report["applied_actions"][0]["audit_payload"]["candidate_source"] == "retention_report"


def test_cleanup_apply_ignores_non_safe_cache_retention_report_candidates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)
    (workspace_root / "control_plane_cleanup_apply.json").unlink()
    report_payload = _retention_report_fixture(workspace_root, cache_root)
    operation = report_payload["workspaces"][0]["retention_plan"]["operation_sample"][0]
    operation["retention_action"] = "archive_compress_candidate_blocked"
    operation["cleanup_candidate_action"] = "archive-compress"
    operation["physical_delete_allowed"] = False

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
        retention_report=report_payload,
    )

    assert report["status"] == "no_contract"
    assert cache_root.exists()
    assert report["action_counts"] == {"planned": 0, "blocked": 0, "applied": 0, "mutating": 0}
    assert report["apply_plan"] == []


def test_cleanup_apply_true_deletes_safe_cache_after_all_gates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "applied"
    assert not cache_root.exists()
    assert report["action_counts"] == {"planned": 1, "blocked": 0, "applied": 1, "mutating": 1}
    assert report["applied_actions"][0]["action"] == "delete-safe-cache"
    assert report["control_plane_route_gate"]["authorized"] is True


def test_cleanup_apply_true_fails_closed_without_control_plane_snapshot(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)

    report = module.run_cleanup_apply(workspace_roots=[workspace_root], apply=True)

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    assert report["control_plane_route_gate"]["authorized"] is False
    assert "control_plane_snapshot_missing" in report["control_plane_route_gate"]["blocking_reasons"]
    assert "control_plane_route_gate:control_plane_snapshot_missing" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_true_fails_closed_when_route_flag_false(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(cleanup_apply_allowed=False),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    assert "cleanup_apply_allowed_false" in report["control_plane_route_gate"]["blocking_reasons"]
    assert "control_plane_route_gate:cleanup_apply_allowed_false" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_live_runtime_is_audit_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path, runtime_status="running")

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    assert report["apply_plan"][0]["candidate_action"] == "audit-only"
    assert "live_runtime_active" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_blocks_data_release_without_restore_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(
        tmp_path,
        artifact_role="data_release",
        include_restore_contract=False,
    )

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    blockers = report["apply_plan"][0]["blockers"]
    assert "missing_restore_contract" in blockers
    assert "missing_restore_index" in blockers
    assert "missing_checksum" in blockers
    assert "missing_rehydrate_verification" in blockers


def test_cleanup_apply_blocks_non_allowlisted_actions(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(
        tmp_path,
        action="delete",
        allowlist=["delete"],
    )

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert "action_not_allowlisted" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_missing_contract_has_no_planned_actions(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "no_contract"
    assert report["action_counts"] == {"planned": 0, "blocked": 0, "applied": 0, "mutating": 0}
    assert report["workspaces"][0]["contract_present"] is False
    assert report["apply_plan"] == []


def test_cleanup_apply_blocks_targets_outside_workspace_after_resolve(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)
    outside_cache = tmp_path / "outside-cache"
    outside_cache.mkdir()
    (outside_cache / "cache.tmp").write_text("outside\n", encoding="utf-8")
    contract_path = workspace_root / "control_plane_cleanup_apply.json"
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["actions"][0]["target_path"] = "../outside-cache"
    payload["actions"][0]["restore_contract"]["sha256"] = _dir_sha256(outside_cache)
    contract_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert outside_cache.exists()
    assert report["action_counts"]["applied"] == 0
    assert "target_outside_workspace" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_allowed_physical_actions_only_include_implemented_delete_safe_cache() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")

    report = module.run_cleanup_apply(workspace_roots=[])

    assert report["mutation_policy"]["allowed_physical_actions"] == ["delete-safe-cache"]


def test_cleanup_apply_blocks_archive_even_when_contract_allowlists_it(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(
        tmp_path,
        action="archive",
        allowlist=["archive"],
    )

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert "action_not_allowlisted" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_blocks_runtime_payload_without_restore_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(
        tmp_path,
        artifact_role="runtime_payload",
        include_restore_contract=False,
    )

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert "missing_restore_contract" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_blocks_non_terminal_runtime_even_with_apply_intent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path, runtime_status="starting")

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    assert "runtime_not_terminal" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_blocks_when_controller_intent_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path)
    contract_path = workspace_root / "control_plane_cleanup_apply.json"
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["controller_decision"] = {"decision": "audit_cleanup_apply", "apply_intent": False}
    contract_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    assert "controller_apply_intent_missing" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_blocks_data_payload_without_checksum_restore_index_or_rehydrate_verification(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path, artifact_role="data_release")
    contract_path = workspace_root / "control_plane_cleanup_apply.json"
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["actions"][0]["restore_contract"] = {}
    contract_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.run_cleanup_apply(
        workspace_roots=[workspace_root],
        apply=True,
        control_plane_snapshot=_snapshot(),
    )

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    assert "missing_restore_contract" in report["apply_plan"][0]["blockers"]


def test_cleanup_apply_blocks_runtime_payload_with_incomplete_restore_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_cleanup_apply")
    workspace_root, cache_root = _cleanup_apply_fixture(tmp_path, artifact_role="runtime_payload")
    contract_path = workspace_root / "control_plane_cleanup_apply.json"
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["actions"][0]["restore_contract"] = {"restore_index_path": "missing.json"}
    contract_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.run_cleanup_apply(workspace_roots=[workspace_root], apply=True)

    assert report["status"] == "blocked"
    assert cache_root.exists()
    assert report["action_counts"]["applied"] == 0
    blockers = report["apply_plan"][0]["blockers"]
    assert "missing_restore_index" in blockers
    assert "missing_checksum" in blockers
    assert "missing_rehydrate_verification" in blockers
