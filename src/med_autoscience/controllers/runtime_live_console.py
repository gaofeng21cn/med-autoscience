from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import runtime_live_console_ui
from med_autoscience.runtime_protocol import runtime_live_console_read_model


def build_live_console_read_model(**kwargs: Any) -> dict[str, Any]:
    return runtime_live_console_read_model.build_live_console_read_model(**kwargs)


def read_live_console_snapshot(**kwargs: Any) -> dict[str, Any]:
    snapshot = build_live_console_read_model(**kwargs)
    snapshot["events"] = build_live_console_stream_events(snapshot)
    return snapshot


def materialize_live_console_read_model(
    *,
    workspace_root: str | Path,
    profile_name: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return runtime_live_console_read_model.materialize_live_console_read_model(
        workspace_root=workspace_root,
        profile_name=profile_name,
        **kwargs,
    )


def build_live_console_session_read_model(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return runtime_live_console_read_model.build_live_console_session_read_model(*args, **kwargs)


def materialize_live_console_session_read_model(*args: Any, **kwargs: Any) -> dict[str, Any]:
    result = runtime_live_console_read_model.materialize_live_console_session_read_model(*args, **kwargs)
    _materialize_live_console_ui(result, profile=_profile_from_call(args=args, kwargs=kwargs), stream_href=None)
    return result


def serve_live_console_stream(*args: Any, **kwargs: Any) -> dict[str, Any]:
    call_kwargs = dict(kwargs)
    if args and "profile" not in call_kwargs:
        call_kwargs["profile"] = args[0]
    if len(args) > 1:
        raise TypeError("serve_live_console_stream accepts only profile as a positional argument")
    result = runtime_live_console_read_model.live_console_stream_snapshot(**call_kwargs)
    _materialize_live_console_ui(
        result,
        profile=_profile_from_call(args=args, kwargs=call_kwargs),
        stream_href=str(result.get("url") or "") or None,
    )
    return result


def build_live_console_stream_events(read_model: Mapping[str, Any]) -> list[dict[str, Any]]:
    return runtime_live_console_read_model.build_live_console_stream_events(read_model)


def _profile_from_call(*, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> Any:
    return kwargs.get("profile") or (args[0] if args else None)


def _materialize_live_console_ui(
    result: dict[str, Any],
    *,
    profile: Any,
    stream_href: str | None,
) -> None:
    workspace_root = getattr(profile, "workspace_root", None)
    if workspace_root is None:
        return
    session_read_model = result.get("session_read_model")
    if not isinstance(session_read_model, Mapping):
        return
    root = Path(workspace_root).expanduser().resolve()
    ui_payload = runtime_live_console_ui.build_live_console_ui_payload(
        live_console_snapshot=session_read_model,
        generated_at=str(session_read_model.get("generated_at") or result.get("generated_at") or ""),
        progress_portal_href="../progress/index.html",
        stream_href=stream_href,
    )
    ui_payload_path = root / runtime_live_console_ui.LIVE_CONSOLE_PAYLOAD_REF
    html_path = root / runtime_live_console_ui.LIVE_CONSOLE_HTML_REF
    ui_payload_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    ui_payload_path.write_text(json.dumps(ui_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(runtime_live_console_ui.render_live_console_html(ui_payload), encoding="utf-8")
    result["ui_payload_path"] = str(ui_payload_path)
    result["html_path"] = str(html_path)
    result["ui_payload"] = ui_payload


__all__ = [
    "build_live_console_read_model",
    "build_live_console_session_read_model",
    "build_live_console_stream_events",
    "read_live_console_snapshot",
    "materialize_live_console_read_model",
    "materialize_live_console_session_read_model",
    "serve_live_console_stream",
]
