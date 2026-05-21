from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def build_refs_only_patch_loop_closeout_bundle(
    *,
    root: Path,
    study_id: str,
    suite_id: str,
    task_id: str,
    promotion_gate_ref: str,
    developer_work_order: Mapping[str, Any],
    target_editable_surface_refs: list[str],
    controller_read_model_feedback_refs: list[str],
    forbidden_writes: list[str],
) -> dict[str, Any]:
    owner_closeout = _owner_receipt_or_typed_blocker(root=root)
    suite_status = "blocked" if owner_closeout["status"] == "typed_blocker" else "blocked_until_owner_receipt"
    return {
        "surface_kind": "mas_agent_lab_refs_only_patch_loop_closeout_bundle",
        "suite_status": suite_status,
        "domain_verdict_claimed": False,
        "blocked_suite": {
            "suite_id": suite_id,
            "blocked_task_ids": [task_id],
            "blocked_reason_refs": controller_read_model_feedback_refs
            or [f"typed-blocker-missing:mas/{study_id}/patch-loop-closeout"],
        },
        "developer_work_order": dict(developer_work_order),
        "patch_traceability": {
            "source_suite_id": suite_id,
            "source_task_id": task_id,
            "source_gate_id": promotion_gate_ref,
            "required_patch_refs": list(developer_work_order.get("required_patch_scopes", [])),
            "editable_surface_refs": target_editable_surface_refs,
            "verification_command_refs": _verification_command_refs(),
            "owner_route": owner_closeout["owner_route"],
            "forbidden_write_proof_ref": f"no-forbidden-write:mas/{study_id}/agent-lab-patch-loop-closeout",
            "expected_receipt_ref": f"owner-receipt-or-typed-blocker:mas/{study_id}/agent-lab-patch-loop-closeout",
            "monitor_freshness_ref": f"read-model-freshness-ref:mas/{study_id}/agent-lab-patch-loop-closeout",
            "contract_refs": [
                "contracts/agent_lab_handoff.json#/meta_agent_work_order_contract",
                "contracts/agent_lab_handoff.json#/receipt_closeout_policy",
            ],
            "required_traceability_axes": [
                "source_gate_id",
                "source_task_id",
                "required_patch_refs",
                "editable_surface_refs",
                "verification_command_refs",
                "owner_route",
                "forbidden_write_proof_ref",
                "expected_receipt_ref",
                "monitor_freshness_ref",
            ],
        },
        "target_verification": {
            "status": "blocked_until_verification_runs",
            "verification_command_refs": _verification_command_refs(),
            "focused_test_refs": [
                "tests/test_agent_lab_medical_manuscript_quality.py",
                (
                    "tests/test_agent_lab_medical_manuscript_quality.py::"
                    "test_medical_manuscript_quality_agent_lab_suite_projects_refs_only_patch_loop_closeout_bundle"
                ),
            ],
            "target_verification_ref": f"target-verification:mas/{study_id}/agent-lab-patch-loop-closeout",
        },
        "runtime_read_model_consumption": {
            "status": "refs_only_projected",
            "consumer": "one-person-lab.agent_lab",
            "consumable_ref_roles": [
                "blocked_suite",
                "developer_work_order",
                "patch_traceability",
                "owner_route",
                "typed_blocker",
                "no_forbidden_write_proof",
            ],
            "read_model_refs": controller_read_model_feedback_refs,
            "can_write_runtime_queue": False,
            "can_write_domain_truth": False,
        },
        "workspace_proof": {
            "workspace_ref": f"workspace-locator:mas/{study_id}",
            "workspace_body_included": False,
            "study_root_ref": str(root),
            "proof_ref": f"workspace-proof:mas/{study_id}/agent-lab-patch-loop-closeout",
        },
        "no_forbidden_write": {
            "result": "configured",
            "proof_ref": f"no-forbidden-write:mas/{study_id}/agent-lab-patch-loop-closeout",
            "forbidden_writes": _stable_forbidden_writes(forbidden_writes),
            "body_write_authorized": False,
            "authority_write_authorized": False,
        },
        "owner_receipt_or_typed_blocker": owner_closeout,
        "patch_absorption": {
            "status": "pending_verified_commit",
            "branch": "codex/ai-first-mas-patch-smoke",
            "absorption_mode": "commit_in_target_worktree",
            "can_absorb_without_owner_receipt_or_typed_blocker": False,
        },
        "worktree_cleanup": {
            "status": "pending_after_commit",
            "worktree_ref": str(Path.cwd()),
            "cleanup_requires_clean_status": True,
        },
        "agent_lab_re_evaluation_refs": [
            f"opl-agent-lab-run-ref:mas/{study_id}/patch-smoke",
            f"opl-agent-lab-evolve-ref:mas/{study_id}/patch-smoke",
        ],
    }


def _owner_receipt_or_typed_blocker(*, root: Path) -> dict[str, Any]:
    path = root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    payload = _read_json_object(path)
    typed_blocker = payload.get("typed_blocker")
    typed_blocker_owner = _text(payload.get("typed_blocker_owner") or payload.get("owner"))
    if isinstance(typed_blocker, Mapping) and typed_blocker_owner:
        return {
            "status": "typed_blocker",
            "owner_route": typed_blocker_owner,
            "typed_blocker": dict(typed_blocker),
            "owner_surface_ref": str(path),
            "owner_receipt_ref": None,
        }
    return {
        "status": "blocked_until_owner_receipt_or_typed_blocker",
        "owner_route": "MedAutoScience",
        "typed_blocker": {
            "blocker_id": "mas_agent_lab_patch_loop_owner_receipt_or_typed_blocker_missing"
        },
        "owner_surface_ref": str(path),
        "owner_receipt_ref": None,
    }


def _verification_command_refs() -> list[str]:
    return [
        "rtk scripts/run-pytest-clean.sh -q tests/test_agent_lab_medical_manuscript_quality.py",
        "rtk make test-meta",
        "rtk scripts/verify.sh",
    ]


def _stable_forbidden_writes(forbidden_writes: list[str]) -> list[str]:
    return _unique_refs(
        [
            *forbidden_writes,
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "paper/submission_minimal",
            "manuscript/current_package",
            "study_truth_body",
            "memory_body",
            "artifact_body",
            "quality/publication/submission verdict",
        ]
    )


def _unique_refs(refs: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if not ref or ref in seen:
            continue
        seen.add(ref)
        unique.append(ref)
    return unique


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["build_refs_only_patch_loop_closeout_bundle"]
