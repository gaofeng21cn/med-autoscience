"""Evaluate target-owner closeout for an Agent Lab mechanism patch."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


POLICY_PATH = Path("contracts/agent_lab_self_evolution_policy.json")
SURFACE_KIND = "target_domain_owner_work_order_closeout"
VERSION = "mas-agent-lab-self-evolution-closeout.v1"


def evaluate_agent_lab_self_evolution_closeout(
    receipt_draft: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a refs-only MAS owner answer without changing publication truth."""

    work_order_id = _text(receipt_draft.get("work_order_id")) or "unknown-work-order"
    reasons: list[str] = []
    evidence_refs: list[str] = []

    target = _object(receipt_draft.get("target_agent"))
    target_domain = _text(target.get("domain_id"))
    allowed_domains = _strings(policy.get("target_domain_ids"))
    if target_domain not in allowed_domains:
        reasons.append("target_domain_mismatch")

    if receipt_draft.get("status") != "executed_absorbed_and_cleaned":
        reasons.append("execution_not_absorbed_and_cleaned")

    absorption = _object(receipt_draft.get("absorption"))
    absorbed_head = _text(absorption.get("absorbed_head"))
    if absorption.get("absorbed") is not True or not absorbed_head:
        reasons.append("patch_absorption_missing")
    elif absorbed_head:
        evidence_refs.append(f"git-commit:{absorbed_head}")

    verification = _object(receipt_draft.get("verification"))
    command_results = _objects(verification.get("command_results"))
    if verification.get("all_passed") is not True or any(
        result.get("exit_code") != 0 for result in command_results
    ):
        reasons.append("target_verification_not_passed")
    evidence_refs.extend(_strings(verification.get("required_verification_refs")))

    cleanup = _object(receipt_draft.get("cleanup"))
    if (
        cleanup.get("worktree_removed") is not True
        or cleanup.get("branch_removed") is not True
    ):
        reasons.append("worktree_cleanup_incomplete")

    proof = _object(receipt_draft.get("no_forbidden_write_proof"))
    forbidden_flags = (
        "can_write_target_domain_truth",
        "can_write_target_domain_memory_body",
        "can_mutate_target_domain_artifact_body",
        "can_authorize_target_domain_quality_or_export",
    )
    if any(proof.get(flag) is not False for flag in forbidden_flags):
        reasons.append("no_forbidden_write_proof_invalid")
    evidence_refs.extend(_strings(proof.get("proof_refs")))

    patch = _object(receipt_draft.get("patch"))
    changed_files = _strings(patch.get("changed_files"))
    allowed_prefixes = _strings(
        _object(policy.get("target_owner_acceptance")).get(
            "allowed_changed_file_prefixes"
        )
    )
    if any(
        not any(path.startswith(prefix) for prefix in allowed_prefixes)
        for path in changed_files
    ):
        reasons.append("changed_file_outside_mechanism_scope")

    re_evaluation = _object(receipt_draft.get("agent_lab_re_evaluation"))
    suite_result = _object(re_evaluation.get("suite_result"))
    result_id = _text(suite_result.get("result_id"))
    if result_id:
        evidence_refs.append(result_id)
    acceptance = _object(policy.get("target_owner_acceptance"))
    if suite_result.get("status") != acceptance.get("accepted_result_status"):
        reasons.append("fresh_re_evaluation_status_invalid")

    observations = _object(suite_result.get("observations"))
    for observation in _strings(acceptance.get("required_fresh_observations")):
        if observations.get(observation) is not True:
            reasons.append(f"fresh_observation_missing:{observation}")

    runs = _objects(suite_result.get("runs"))
    if not runs:
        reasons.append("fresh_re_evaluation_runs_missing")
    for run in runs:
        scorecard = _object(run.get("scorecard"))
        if scorecard.get("passed") is not acceptance.get("accepted_scorecard_passed"):
            reasons.append("domain_scorecard_boundary_not_preserved")
        taxonomy = _strings(run.get("failure_taxonomy"))
        if acceptance.get("required_failure_taxonomy") not in taxonomy:
            reasons.append("domain_scorecard_blocker_not_preserved")
        stage_assessment = _object(run.get("stage_completion_policy_assessment"))
        if stage_assessment.get("status") != "passed" or _strings(
            stage_assessment.get("blockers")
        ):
            reasons.append("stage_completion_policy_not_accepted")
        promotion = _object(run.get("promotion_safety_assessment"))
        if promotion.get("safety_status") != acceptance.get(
            "required_promotion_safety_status"
        ):
            reasons.append("mechanism_promotion_owner_gate_not_observed")
        if promotion.get("automatic_mechanism_promotion_ready") is not False:
            reasons.append("automatic_mechanism_promotion_forbidden")
        if _strings(promotion.get("missing_required_refs")):
            reasons.append("mechanism_promotion_evidence_incomplete")

    source_receipt_ref = _text(receipt_draft.get("source_execution_receipt_ref"))
    if source_receipt_ref:
        evidence_refs.append(source_receipt_ref)
    policy_ref = _text(policy.get("policy_ref")) or (
        "policy:mas/agent-lab-self-evolution/unknown"
    )
    evidence_refs.append(policy_ref)

    if reasons:
        return _response(
            work_order_id=work_order_id,
            policy_ref=policy_ref,
            return_shape="typed_blocker",
            status="mechanism_change_blocked",
            reasons=_dedupe(reasons),
            evidence_refs=_dedupe(evidence_refs),
        )
    if not changed_files:
        return _response(
            work_order_id=work_order_id,
            policy_ref=policy_ref,
            return_shape="no_regression_evidence",
            status="mechanism_change_waived",
            reasons=["no_source_change_required_after_fresh_re_evaluation"],
            evidence_refs=_dedupe(evidence_refs),
        )
    return _response(
        work_order_id=work_order_id,
        policy_ref=policy_ref,
        return_shape="domain_receipt",
        status="mechanism_change_accepted",
        reasons=["absorbed_verified_mechanism_patch_accepted_by_target_owner"],
        evidence_refs=_dedupe(evidence_refs),
    )


def _response(
    *,
    work_order_id: str,
    policy_ref: str,
    return_shape: str,
    status: str,
    reasons: list[str],
    evidence_refs: list[str],
) -> dict[str, Any]:
    core = {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "owner": "med-autoscience",
        "status": status,
        "return_shape": return_shape,
        "work_order_id": work_order_id,
        "policy_ref": policy_ref,
        "receipt_scope": "target_agent_mechanism_change_only",
        "reason_codes": reasons,
        "evidence_refs": evidence_refs,
        "refs_only": True,
        "writes_visual_truth": False,
        "writes_artifact_body": False,
        "writes_memory_body": False,
        "authorizes_quality_or_export": False,
        "authorizes_publication_or_submission": False,
        "authorizes_domain_ready": False,
        "automatic_mechanism_promotion_ready": False,
    }
    fingerprint = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    ref_name = {
        "domain_receipt": "owner_receipt_ref",
        "no_regression_evidence": "no_regression_evidence_ref",
        "typed_blocker": "blocker_ref",
    }[return_shape]
    return {
        **core,
        ref_name: f"mas-self-evolution-closeout:{work_order_id}/{fingerprint}",
    }


def _object(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [_object(item) for item in value if isinstance(item, Mapping)]


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _strings(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        payload = {}
    configured = os.environ.get("MAS_SELF_EVOLUTION_POLICY_PATH")
    policy_path = Path(configured) if configured else POLICY_PATH
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        policy = {}
    result = evaluate_agent_lab_self_evolution_closeout(_object(payload), _object(policy))
    sys.stdout.write(f"{json.dumps(result, ensure_ascii=True, sort_keys=True)}\n")


if __name__ == "__main__":
    main()


__all__ = ["evaluate_agent_lab_self_evolution_closeout"]
