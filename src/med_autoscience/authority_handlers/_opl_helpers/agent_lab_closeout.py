"""Generic evaluator for target-owner closeout of Agent Lab self-evolution patches."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


TARGET_DOMAIN_OWNER_CLOSEOUT_SURFACE = "target_domain_owner_work_order_closeout"
_FORBIDDEN_WRITE_FLAGS = (
    "can_write_target_domain_truth",
    "can_write_target_domain_memory_body",
    "can_mutate_target_domain_artifact_body",
    "can_authorize_target_domain_quality_or_export",
)
_REF_NAME_BY_SHAPE = {
    "domain_receipt": "owner_receipt_ref",
    "no_regression_evidence": "no_regression_evidence_ref",
    "typed_blocker": "blocker_ref",
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


def _closeout_response(
    *,
    owner: str,
    version: str,
    ref_prefix: str,
    work_order_id: str,
    policy_ref: str,
    return_shape: str,
    status: str,
    reasons: list[str],
    evidence_refs: list[str],
) -> dict[str, Any]:
    core = {
        "surface_kind": TARGET_DOMAIN_OWNER_CLOSEOUT_SURFACE,
        "version": version,
        "owner": owner,
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
    ref_name = _REF_NAME_BY_SHAPE[return_shape]
    return {
        **core,
        ref_name: f"{ref_prefix}:{work_order_id}/{fingerprint}",
    }


def evaluate_agent_lab_self_evolution_closeout(
    receipt_draft: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    owner: str,
    version: str,
    ref_prefix: str,
    fallback_policy_ref: str = "policy:agent-lab-self-evolution/unknown",
) -> dict[str, Any]:
    """Return a fail-closed refs-only closeout answer without changing domain truth."""

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
    if any(proof.get(flag) is not False for flag in _FORBIDDEN_WRITE_FLAGS):
        reasons.append("no_forbidden_write_proof_invalid")
    evidence_refs.extend(_strings(proof.get("proof_refs")))

    patch = _object(receipt_draft.get("patch"))
    changed_files = _strings(patch.get("changed_files"))
    acceptance = _object(policy.get("target_owner_acceptance"))
    allowed_prefixes = _strings(acceptance.get("allowed_changed_file_prefixes"))
    if any(
        not any(file_path.startswith(prefix) for prefix in allowed_prefixes)
        for file_path in changed_files
    ):
        reasons.append("changed_file_outside_mechanism_scope")

    re_evaluation = _object(receipt_draft.get("agent_lab_re_evaluation"))
    suite_result = _object(re_evaluation.get("suite_result"))
    result_id = _text(suite_result.get("result_id"))
    if result_id:
        evidence_refs.append(result_id)
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
    policy_ref = _text(policy.get("policy_ref")) or fallback_policy_ref
    evidence_refs.append(policy_ref)

    if reasons:
        return _closeout_response(
            owner=owner,
            version=version,
            ref_prefix=ref_prefix,
            work_order_id=work_order_id,
            policy_ref=policy_ref,
            return_shape="typed_blocker",
            status="mechanism_change_blocked",
            reasons=_dedupe(reasons),
            evidence_refs=_dedupe(evidence_refs),
        )
    if not changed_files:
        return _closeout_response(
            owner=owner,
            version=version,
            ref_prefix=ref_prefix,
            work_order_id=work_order_id,
            policy_ref=policy_ref,
            return_shape="no_regression_evidence",
            status="mechanism_change_waived",
            reasons=["no_source_change_required_after_fresh_re_evaluation"],
            evidence_refs=_dedupe(evidence_refs),
        )
    return _closeout_response(
        owner=owner,
        version=version,
        ref_prefix=ref_prefix,
        work_order_id=work_order_id,
        policy_ref=policy_ref,
        return_shape="domain_receipt",
        status="mechanism_change_accepted",
        reasons=["absorbed_verified_mechanism_patch_accepted_by_target_owner"],
        evidence_refs=_dedupe(evidence_refs),
    )


def run_agent_lab_closeout_cli(
    *,
    default_policy_path: Path,
    policy_env_var: str,
    owner: str,
    version: str,
    ref_prefix: str,
    fallback_policy_ref: str = "policy:agent-lab-self-evolution/unknown",
) -> None:
    """Read closeout input JSON from stdin and print evaluated closeout JSON."""

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        payload = {}
    configured = os.environ.get(policy_env_var)
    policy_path = Path(configured) if configured else default_policy_path
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        policy = {}
    result = evaluate_agent_lab_self_evolution_closeout(
        _object(payload),
        _object(policy),
        owner=owner,
        version=version,
        ref_prefix=ref_prefix,
        fallback_policy_ref=fallback_policy_ref,
    )
    sys.stdout.write(f"{json.dumps(result, ensure_ascii=True, sort_keys=True)}\n")


__all__ = [
    "TARGET_DOMAIN_OWNER_CLOSEOUT_SURFACE",
    "evaluate_agent_lab_self_evolution_closeout",
    "run_agent_lab_closeout_cli",
]
