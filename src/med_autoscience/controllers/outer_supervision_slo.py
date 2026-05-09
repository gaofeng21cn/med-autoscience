from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import runtime_dispatch_cost
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SURFACE_KIND = "outer_supervision_slo"
DEFAULT_INTERVAL_SECONDS = 5 * 60
FRESH_MULTIPLIER = 2
STALE_MULTIPLIER = 4
RECONCILE_LATEST_RELATIVE_PATH = Path("artifacts/supervision/reconcile/latest.json")


def build_outer_supervision_slo_projection(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    supervision_status: Mapping[str, Any] | None = None,
    reconcile_payload: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
    interval_seconds: int | None = None,
) -> dict[str, Any]:
    generated = generated_at or _utc_now()
    interval = int(interval_seconds or _interval_from_status(supervision_status) or DEFAULT_INTERVAL_SECONDS)
    fresh_after_seconds = interval * FRESH_MULTIPLIER
    stale_after_seconds = interval * STALE_MULTIPLIER
    reconcile = dict(reconcile_payload or _read_json_object(profile.workspace_root / RECONCILE_LATEST_RELATIVE_PATH) or {})
    supervision = dict(supervision_status or {})
    latest_run_at = _text(supervision.get("latest_run_recorded_at"))
    latest_reconcile_at = _text(reconcile.get("generated_at"))
    latest_event_at = _latest_timestamp(latest_run_at, latest_reconcile_at)
    blocked_reasons = _blocked_reasons(supervision)
    missing_reasons = _missing_reasons(supervision=supervision, latest_event_at=latest_event_at)
    age_seconds = _age_seconds(generated, latest_event_at)
    state, missing_reasons = _slo_state(
        age_seconds=age_seconds,
        fresh_after_seconds=fresh_after_seconds,
        stale_after_seconds=stale_after_seconds,
        blocked_reasons=blocked_reasons,
        missing_reasons=missing_reasons,
    )
    recommended_command = _recommended_reconcile_command(
        state=state,
        blocked_reasons=blocked_reasons,
        profile_ref=profile_ref,
        study_id=study_id,
    )
    action_cost = runtime_dispatch_cost.reconcile_dry_run_contract(
        reason="outer_supervision_slo_recommended_one_shot_reconcile"
        if recommended_command
        else "outer_supervision_slo_observe_only",
        action_fingerprint=_dedupe_fingerprint(
            state=state,
            study_id=study_id,
            latest_event_at=latest_event_at,
            blocked_reasons=blocked_reasons,
            missing_reasons=missing_reasons,
        ),
        recommended_command=recommended_command,
    ) if recommended_command else runtime_dispatch_cost.observe_only_contract(
        reason="outer_supervision_slo_observe_only",
        action_fingerprint=_dedupe_fingerprint(
            state=state,
            study_id=study_id,
            latest_event_at=latest_event_at,
            blocked_reasons=blocked_reasons,
            missing_reasons=missing_reasons,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "generated_at": generated,
        "state": state,
        "summary": _summary(state=state, age_seconds=age_seconds, blocked_reasons=blocked_reasons, missing_reasons=missing_reasons),
        "owner": "med_autoscience_outer_supervision_read_model",
        "supervision_owner": _text(supervision.get("owner")) or "hermes_gateway_cron",
        "latest_outer_supervision_at": latest_event_at,
        "latest_hermes_run_at": latest_run_at,
        "latest_supervisor_reconcile_at": latest_reconcile_at,
        "age_seconds": age_seconds,
        "fresh_after_seconds": fresh_after_seconds,
        "stale_after_seconds": stale_after_seconds,
        "recommended_command": recommended_command,
        "canonical_one_shot_supervisor_reconcile_command": recommended_command,
        "action_class": action_cost["action_class"],
        "will_start_llm": action_cost["will_start_llm"],
        "action_fingerprint": action_cost["action_fingerprint"],
        "action_cost": action_cost,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "missing_reasons": list(dict.fromkeys(missing_reasons)),
        "refs": {
            "supervision_status": "runtime-supervision-status",
            "reconcile_latest": str(profile.workspace_root / RECONCILE_LATEST_RELATIVE_PATH),
        },
        "authority": {
            "kind": "read_model_projection",
            "writes_runtime": False,
            "writes_study_workspace": False,
            "writes_publication_truth": False,
            "writes_controller_decisions": False,
            "executes_reconcile": False,
            "resident_daemon": False,
            "workspace_local_service_restore": False,
        },
    }


def _slo_state(
    *,
    age_seconds: int | None,
    fresh_after_seconds: int,
    stale_after_seconds: int,
    blocked_reasons: list[str],
    missing_reasons: list[str],
) -> tuple[str, list[str]]:
    if blocked_reasons:
        return "blocked", missing_reasons
    if missing_reasons:
        return "missing", missing_reasons
    if age_seconds is None:
        return "missing", [*missing_reasons, "outer_supervision_event_missing"]
    if age_seconds <= fresh_after_seconds:
        return "fresh", missing_reasons
    if age_seconds <= stale_after_seconds:
        return "due", missing_reasons
    return "stale", missing_reasons


def _recommended_reconcile_command(
    *,
    state: str,
    blocked_reasons: list[str],
    profile_ref: str | Path | None,
    study_id: str | None,
) -> str | None:
    if blocked_reasons or state not in {"due", "stale", "missing"}:
        return None
    return supervisor_reconcile_command(profile_ref=profile_ref, study_id=study_id)


def supervisor_reconcile_command(*, profile_ref: str | Path | None, study_id: str | None = None) -> str:
    command = (
        "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
        f"--profile {_quote(str(profile_ref) if profile_ref is not None else '<profile>')}"
    )
    resolved_study_id = _text(study_id)
    if resolved_study_id is not None:
        command = f"{command} --studies {_quote(resolved_study_id)}"
    return f"{command} --mode developer_apply_safe --dry-run"


def _blocked_reasons(supervision: Mapping[str, Any]) -> list[str]:
    status = _text(supervision.get("status"))
    reasons = [item for item in _string_items(supervision.get("runtime_contract_issues"))]
    if status == "retired_legacy_service_present":
        reasons.append("retired_legacy_service_present")
    if status == "execution_failed":
        reasons.append("latest_hermes_cron_execution_failed")
    if status in {"not_loaded", "not_installed"} and supervision:
        reasons.append(f"hermes_supervision_{status}")
    return list(dict.fromkeys(reasons))


def _missing_reasons(*, supervision: Mapping[str, Any], latest_event_at: str | None) -> list[str]:
    reasons: list[str] = []
    if not supervision:
        reasons.append("runtime_supervision_status_missing")
    elif not latest_event_at:
        reasons.append("outer_supervision_event_missing")
    return reasons


def _interval_from_status(supervision: Mapping[str, Any] | None) -> int | None:
    if not isinstance(supervision, Mapping):
        return None
    watch_command = supervision.get("watch_command")
    if isinstance(watch_command, list):
        for index, item in enumerate(watch_command):
            if item == "--interval-seconds" and index + 1 < len(watch_command):
                try:
                    return int(watch_command[index + 1])
                except (TypeError, ValueError):
                    return None
    return None


def _summary(*, state: str, age_seconds: int | None, blocked_reasons: list[str], missing_reasons: list[str]) -> str:
    if state == "blocked":
        return "outer Hermes supervision/reconcile SLA blocked: " + ", ".join(blocked_reasons)
    if state == "missing":
        return "outer Hermes supervision/reconcile SLA missing: " + ", ".join(missing_reasons)
    if state == "fresh":
        return f"outer Hermes supervision/reconcile is fresh ({age_seconds}s old)."
    if state == "due":
        return f"outer Hermes supervision/reconcile is due ({age_seconds}s old); request one-shot supervisor reconcile."
    return f"outer Hermes supervision/reconcile is stale ({age_seconds}s old); request one-shot supervisor reconcile."


def _dedupe_fingerprint(
    *,
    state: str,
    study_id: str | None,
    latest_event_at: str | None,
    blocked_reasons: list[str],
    missing_reasons: list[str],
) -> str:
    source = {
        "surface_kind": SURFACE_KIND,
        "state": state,
        "study_id": _text(study_id),
        "latest_event_at": latest_event_at,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "missing_reasons": list(dict.fromkeys(missing_reasons)),
    }
    encoded = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    import hashlib

    return f"{SURFACE_KIND}:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _latest_timestamp(*values: str | None) -> str | None:
    parsed = [(_parse_datetime(value), value) for value in values if value]
    parsed = [(dt, value) for dt, value in parsed if dt is not None]
    if not parsed:
        return None
    return max(parsed, key=lambda item: item[0])[1]


def _age_seconds(generated_at: str, latest_event_at: str | None) -> int | None:
    generated = _parse_datetime(generated_at)
    latest = _parse_datetime(latest_event_at)
    if generated is None or latest is None:
        return None
    return max(0, int((generated - latest).total_seconds()))


def _parse_datetime(value: str | None) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _quote(value: str) -> str:
    if value and all(char.isalnum() or char in "/._:-" for char in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return list(dict.fromkeys(item for raw in value if (item := _text(raw)) is not None))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "DEFAULT_INTERVAL_SECONDS",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_outer_supervision_slo_projection",
    "supervisor_reconcile_command",
]
