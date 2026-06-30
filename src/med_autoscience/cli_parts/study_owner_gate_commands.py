from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from typing import Any, Callable


def handle_study_owner_gate_command(
    args: argparse.Namespace,
    *,
    load_profile: Callable[[str], Any],
    study_interventions: Any,
) -> int | None:
    if args.command != "study-owner-gate-decision":
        return None
    profile = load_profile(args.profile)
    if getattr(args, "sync_truth_from_existing", False):
        result = study_interventions.materialize_truth_from_intervention_events(
            study_root=profile.studies_root / args.study_id,
            study_id=args.study_id,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if getattr(args, "apply_submission_authority_closeout", False):
        for field in ("decision", "reason"):
            if not str(getattr(args, field, "") or "").strip():
                raise SystemExit(
                    "study-owner-gate-decision requires "
                    f"--{field.replace('_', '-')} for --apply-submission-authority-closeout"
                )
        result = study_interventions.submission_authority_closeout_record(
            study_root=profile.studies_root / args.study_id,
            study_id=args.study_id,
            owner_gate_decision_ref=args.owner_gate_decision_ref,
            human_gate_ref=args.human_gate_ref,
            decision=args.decision,
            reason=args.reason,
            recorded_at=args.recorded_at or _utc_now(),
            apply=True,
            actor=args.actor,
            source=args.source,
            receipt_owner_consumption_ref=args.receipt_owner_consumption_ref,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    for field in (
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "blocker_type",
        "decision",
        "reason",
    ):
        if not str(getattr(args, field, "") or "").strip():
            raise SystemExit(f"study-owner-gate-decision requires --{field.replace('_', '-')} unless --sync-truth-from-existing is used")
    result = study_interventions.owner_gate_decision_record(
        study_root=profile.studies_root / args.study_id,
        study_id=args.study_id,
        action_type=args.action_type,
        work_unit_id=args.work_unit_id,
        work_unit_fingerprint=args.work_unit_fingerprint,
        blocker_type=args.blocker_type,
        decision=args.decision,
        reason=args.reason,
        recorded_at=args.recorded_at or _utc_now(),
        apply=bool(args.apply),
        actor=args.actor,
        source=args.source,
        stage_packet_refs=tuple(args.stage_packet_refs or ()),
        route_identity_key=args.route_identity_key,
        attempt_idempotency_key=args.attempt_idempotency_key,
        stable_typed_blocker_type=args.stable_typed_blocker_type,
        route_back_evidence_ref=args.route_back_evidence_ref,
        supersedes_owner_gate_decision_ref=args.supersedes_owner_gate_decision_ref,
        replacement_typed_blocker_ref=args.replacement_typed_blocker_ref,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = ["handle_study_owner_gate_command"]
