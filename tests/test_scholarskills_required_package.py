from __future__ import annotations

import json
import subprocess
from pathlib import Path

from med_autoscience.scholarskills_required_package import (
    MAS_PACKAGE_REPAIR_COMMAND,
    SCHOLARSKILLS_CAPABILITY_ABI,
    SCHOLARSKILLS_REQUIRED_EXPORT_IDS,
    SCHOLARSKILLS_REQUIRED_MODULE_IDS,
    SCHOLARSKILLS_REQUIRED_SKILL_IDS,
    build_scholarskills_required_package_readback,
    build_scholarskills_required_package_template,
    query_scholarskills_required_package_readback,
)


ROOT = Path(__file__).resolve().parents[1]


def _current_dependency(**overrides: object) -> dict[str, object]:
    dependency: dict[str, object] = {
        "package_id": "mas-scholar-skills",
        "status": "current",
        "installed_version": "0.1.0",
        "capability_abi": SCHOLARSKILLS_CAPABILITY_ABI,
        "content_digest": f"sha256:{'a' * 64}",
        "required_export_ids": list(SCHOLARSKILLS_REQUIRED_EXPORT_IDS),
        "required_module_ids": list(SCHOLARSKILLS_REQUIRED_MODULE_IDS),
    }
    dependency.update(overrides)
    return dependency


def _current_materialization(**overrides: object) -> dict[str, object]:
    materialization: dict[str, object] = {
        "scope": "workspace",
        "target_root": "/tmp/mas-workspace",
        "status": "current",
        "required_skill_ids": list(SCHOLARSKILLS_REQUIRED_SKILL_IDS),
        "materialized_skill_ids": list(SCHOLARSKILLS_REQUIRED_SKILL_IDS),
        "expected_digest": f"sha256:{'b' * 64}",
        "actual_digest": f"sha256:{'b' * 64}",
        "lifecycle_receipt_ref": "opl://packages/mas/materialization/workspace/receipt",
    }
    materialization.update(overrides)
    return materialization


def _status_payload(
    dependencies: list[dict[str, object]],
    *,
    materialization: dict[str, object] | None = None,
) -> dict[str, object]:
    dependency_status = (
        "missing"
        if not dependencies
        else "incompatible"
        if any(item.get("status") != "current" for item in dependencies)
        else "current"
    )
    return {
        "opl_agent_package_status": {
            "package_id": "mas",
            "package_dependency_readiness": {
                "status": dependency_status,
                "operational_ready": dependency_status == "current",
                "dependencies": dependencies,
            },
            "materialization_readiness": materialization
            or _current_materialization(),
        }
    }


def test_consumer_requirement_matches_mas_agent_package_manifest() -> None:
    manifest = json.loads(
        (ROOT / "contracts" / "opl_agent_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    dependency = manifest["capability_dependencies"][0]
    requirement = build_scholarskills_required_package_template()

    assert manifest["agent_id"] == "mas"
    assert manifest["package_id"] == "mas"
    assert dependency["package_id"] == requirement["package_id"]
    assert dependency["required"] is True
    assert dependency["dependency_kind"] == requirement["dependency_kind"]
    assert dependency["version_requirement"] == requirement["version_requirement"]
    assert dependency["capability_abi"] == requirement["capability_abi"]
    assert dependency["required_export_ids"] == list(SCHOLARSKILLS_REQUIRED_SKILL_IDS)
    assert dependency["required_module_ids"] == list(SCHOLARSKILLS_REQUIRED_MODULE_IDS)
    assert dependency["repair_command_templates"] == {
        scope: " ".join(command)
        for scope, command in requirement["repair_command_templates"].items()
    }
    assert dependency["activation_materialization"] == requirement["activation_materialization"]


def test_current_dependency_is_operationally_ready() -> None:
    readback = build_scholarskills_required_package_readback(
        _status_payload([_current_dependency()])
    )

    assert readback["status"] == "current"
    assert readback["operational_ready"] is True
    assert readback["repair_required"] is False
    assert readback["missing_export_ids"] == []


def test_missing_dependency_fails_closed_to_repair() -> None:
    readback = build_scholarskills_required_package_readback(
        _status_payload([])
    )

    assert readback["status"] == "missing"
    assert readback["operational_ready"] is False
    assert readback["repair_required"] is True
    assert readback["repair_command"] == [
        *MAS_PACKAGE_REPAIR_COMMAND,
        "--scope",
        "workspace",
        "--target-workspace",
        "<workspace-root>",
        "--json",
    ]


def test_incompatible_abi_or_missing_core_export_fails_closed() -> None:
    incompatible_abi = build_scholarskills_required_package_readback(
        _status_payload(
            [_current_dependency(capability_abi="mas-scholar-skills.v2")]
        )
    )
    missing_export = build_scholarskills_required_package_readback(
        _status_payload(
            [
                _current_dependency(
                    required_export_ids=list(SCHOLARSKILLS_REQUIRED_EXPORT_IDS[:-1])
                )
            ]
        )
    )
    missing_module = build_scholarskills_required_package_readback(
        _status_payload(
            [
                _current_dependency(
                    required_module_ids=list(SCHOLARSKILLS_REQUIRED_MODULE_IDS[:-1])
                )
            ]
        )
    )

    assert incompatible_abi["status"] == "incompatible"
    assert incompatible_abi["operational_ready"] is False
    assert missing_export["status"] == "incompatible"
    assert missing_export["operational_ready"] is False
    assert missing_export["missing_export_ids"] == [
        SCHOLARSKILLS_REQUIRED_EXPORT_IDS[-1]
    ]
    assert missing_module["status"] == "incompatible"
    assert missing_module["operational_ready"] is False
    assert missing_module["missing_module_ids"] == [
        SCHOLARSKILLS_REQUIRED_MODULE_IDS[-1]
    ]


def test_missing_workspace_materialization_receipt_fails_closed() -> None:
    workspace_root = str(Path("/tmp/mas-workspace").resolve())
    readback = build_scholarskills_required_package_readback(
        _status_payload(
            [_current_dependency()],
            materialization=_current_materialization(
                target_root=workspace_root,
                lifecycle_receipt_ref=None,
            ),
        ),
        target_root=workspace_root,
    )

    assert readback["status"] == "scope_materialization_missing_or_stale"
    assert readback["package_dependency_status"] == "current"
    assert readback["scope_materialization_status"] == "current"
    assert readback["operational_ready"] is False
    assert readback["materialization_receipt_ref"] is None


def test_unavailable_opl_status_never_claims_readiness() -> None:
    readback = build_scholarskills_required_package_readback(
        None,
        query_error="opl_packages_status_unavailable:FileNotFoundError",
    )

    assert readback["status"] == "status_unavailable"
    assert readback["operational_ready"] is False
    assert readback["repair_required"] is True


def test_doctor_query_uses_public_scoped_opl_packages_status(tmp_path: Path) -> None:
    workspace_root = tmp_path / "paper-workspace"
    materialization = _current_materialization(
        target_root=str(workspace_root.resolve())
    )
    payload = _status_payload(
        [_current_dependency()],
        materialization=materialization,
    )
    observed_command: list[str] = []

    def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        observed_command.extend(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(payload),
            stderr="",
        )

    readback = query_scholarskills_required_package_readback(
        workspace_root=workspace_root,
        runner=runner,
    )

    assert observed_command == [
        "opl",
        "packages",
        "status",
        "--package-id",
        "mas",
        "--scope",
        "workspace",
        "--target-workspace",
        str(workspace_root.resolve()),
        "--json",
    ]
    assert readback["operational_ready"] is True
