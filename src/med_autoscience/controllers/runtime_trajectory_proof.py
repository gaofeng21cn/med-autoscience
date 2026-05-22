from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "action_observation_trajectory"
_TRAJECTORY_ROLE = {
    "read_model_only": True,
    "can_be_study_truth_owner": False,
    "can_be_publication_quality_owner": False,
    "truth_authority_surface": "StudyTruthKernel",
    "publication_quality_authority_surface": "publication_eval/latest.json",
}
_MUTATING_SIDE_EFFECT_CLASSES = frozenset(
    {
        "artifact_write",
        "workspace_write",
        "runtime_write",
        "external_write",
    }
)
_AUTHORITY_GUARDED_REFS: tuple[str, ...] = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "progress_projection",
    "study_truth",
    "submission readiness",
)
_AUTHORITY_GUARDED_REF_MATCHES: tuple[str, ...] = (
    "artifacts/publication_eval/latest.json",
    "publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "controller_decisions/latest.json",
    "progress_projection",
    "study_truth",
    "submission readiness",
    "submission_minimal/readiness",
)
_AUTHORITY_GUARD = {
    "role": "observability_only",
    "authority_surface_replay_policy": "non_replayable",
    "guarded_refs": list(_AUTHORITY_GUARDED_REFS),
}


def build_runtime_trajectory_proof(
    *,
    active_run_id: str,
    steps: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    run_id = _required_text(active_run_id, "active_run_id")
    normalized_steps = [_normalized_step(run_id, step, index) for index, step in enumerate(steps)]
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "active_run_id": run_id,
        "trajectory_role": dict(_TRAJECTORY_ROLE),
        "authority_guard": dict(_AUTHORITY_GUARD),
        "steps": normalized_steps,
        "replay_summary": _replay_summary(normalized_steps),
    }


def validate_runtime_trajectory_proof(proof: Mapping[str, Any]) -> dict[str, Any]:
    role = proof.get("trajectory_role")
    role_mapping = role if isinstance(role, Mapping) else {}
    issues: list[dict[str, str]] = []
    if role_mapping.get("can_be_study_truth_owner") is not False:
        issues.append({"code": "trajectory_claims_study_truth_authority"})
    if role_mapping.get("can_be_publication_quality_owner") is not False:
        issues.append({"code": "trajectory_claims_publication_quality_authority"})
    return {"ok": not issues, "issues": issues}


def _normalized_step(active_run_id: str, raw_step: Mapping[str, Any], index: int) -> dict[str, Any]:
    step = raw_step if isinstance(raw_step, Mapping) else {}
    side_effect_class = _text(step.get("side_effect_class")) or "none"
    idempotency_key = _text(step.get("idempotency_key"))
    artifact_delta_refs = _text_list(step.get("artifact_delta_refs"))
    replay_policy = _replay_policy(
        requested_policy=_text(step.get("replay_policy")),
        side_effect_class=side_effect_class,
        idempotency_key=idempotency_key,
        artifact_delta_refs=artifact_delta_refs,
    )
    return {
        "step_id": _required_text(step.get("step_id"), f"steps[{index}].step_id"),
        "active_run_id": active_run_id,
        "action_type": _required_text(step.get("action_type"), f"steps[{index}].action_type"),
        "action_ref": _required_text(step.get("action_ref"), f"steps[{index}].action_ref"),
        "observation_ref": _required_text(step.get("observation_ref"), f"steps[{index}].observation_ref"),
        "artifact_delta_refs": artifact_delta_refs,
        "side_effect_class": side_effect_class,
        "idempotency_key": idempotency_key,
        "replay_policy": replay_policy,
        "status": _text(step.get("status")) or "observed",
    }


def _replay_policy(
    *,
    requested_policy: str | None,
    side_effect_class: str,
    idempotency_key: str | None,
    artifact_delta_refs: Sequence[str],
) -> str:
    if _touches_guarded_authority_surface(artifact_delta_refs):
        return "non_replayable"
    if side_effect_class == "none":
        return "observation_only"
    if side_effect_class in _MUTATING_SIDE_EFFECT_CLASSES and idempotency_key is None:
        return "non_replayable"
    return requested_policy or "idempotent_replay_allowed"


def _replay_summary(steps: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocked_reasons: list[dict[str, str]] = []
    auto_replayable = 0
    non_replayable = 0
    for step in steps:
        replay_policy = step.get("replay_policy")
        if replay_policy == "non_replayable":
            non_replayable += 1
            code = (
                "authority_surface_replay_blocked"
                if _touches_guarded_authority_surface(_text_list(step.get("artifact_delta_refs")))
                else "side_effect_missing_idempotency_key"
            )
            blocked_reasons.append(
                {
                    "step_id": str(step.get("step_id")),
                    "code": code,
                }
            )
        elif replay_policy in {"auto_replay_allowed", "idempotent_replay_allowed"}:
            auto_replayable += 1
    return {
        "auto_replayable_step_count": auto_replayable,
        "non_replayable_step_count": non_replayable,
        "blocked_replay_reasons": blocked_reasons,
    }


def _required_text(value: object, label: str) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"{label} must be non-empty")
    return text


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _touches_guarded_authority_surface(refs: Sequence[str]) -> bool:
    normalized_refs = [ref.replace("\\", "/").strip().lower() for ref in refs]
    for ref in normalized_refs:
        if any(match in ref for match in _AUTHORITY_GUARDED_REF_MATCHES):
            return True
    return False


__all__ = [
    "build_runtime_trajectory_proof",
    "validate_runtime_trajectory_proof",
]
