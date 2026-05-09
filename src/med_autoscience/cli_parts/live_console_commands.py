from __future__ import annotations

import argparse
import http.server
import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Callable

from med_autoscience.runtime_protocol import terminal_attach_gate
from med_autoscience.runtime_transport import mas_runtime_core


LoadProfile = Callable[[str], Any]


def register_live_console_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("runtime-live-console")
    parser.add_argument("--profile", required=True)
    study = parser.add_mutually_exclusive_group()
    study.add_argument("--study-id", type=str)
    study.add_argument("--study-root", type=str)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--bind", dest="host")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--enable-terminal-attach", action="store_true")


def handle_live_console_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    load_profile: LoadProfile,
    runtime_live_console: Any,
) -> int | None:
    if args.command != "runtime-live-console":
        return None
    profile = load_profile(args.profile)
    kwargs = {
        "profile": profile,
        "profile_ref": Path(args.profile),
        "study_id": args.study_id,
        "study_root": Path(args.study_root) if args.study_root else None,
    }
    if args.enable_terminal_attach and not args.serve:
        result = terminal_attach_gate.terminal_attach_status(
            owner_contract=_load_terminal_attach_owner_contract(profile=profile, study_id=args.study_id),
            profile_ref=Path(args.profile),
            study_id=args.study_id,
            study_root=Path(args.study_root) if args.study_root else None,
        )
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(render_live_console_command_text(dict(result)), end="")
        return 0 if result.get("status") == "available" else 2
    if args.serve and not args.snapshot:
        return _serve_loopback_live_console(
            runtime_live_console=runtime_live_console,
            kwargs=kwargs,
            profile=profile,
            enable_terminal_attach=bool(args.enable_terminal_attach),
            host=str(args.host),
            port=int(args.port),
            interval_seconds=int(args.interval_seconds),
            output_format=str(args.format),
        )
    if args.snapshot:
        result = runtime_live_console.serve_live_console_stream(
            **kwargs,
            host=str(args.host),
            port=int(args.port),
            interval_seconds=int(args.interval_seconds),
        )
        if args.snapshot:
            result["status"] = "snapshot"
    elif args.once:
        if hasattr(runtime_live_console, "read_live_console_snapshot"):
            snapshot = _read_legacy_snapshot(
                runtime_live_console=runtime_live_console,
                profile=profile,
                profile_ref=Path(args.profile),
            )
            if args.format == "json":
                print(json.dumps(snapshot, ensure_ascii=False, indent=2))
            else:
                print(render_sse_events(_validated_events(snapshot)), end="")
            return 0
        result = runtime_live_console.serve_live_console_stream(
            **kwargs,
            host=str(args.host),
            port=int(args.port),
            interval_seconds=int(args.interval_seconds),
        )
    else:
        result = runtime_live_console.materialize_live_console_session_read_model(**kwargs)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_live_console_command_text(dict(result)), end="")
    return 0


def render_live_console_command_text(result: dict[str, Any]) -> str:
    lines = ["MAS Live Console"]
    if status := result.get("status"):
        lines.append(f"status: {status}")
    if surface_kind := result.get("surface_kind"):
        lines.append(f"surface_kind: {surface_kind}")
    if forbidden_owner := result.get("forbidden_owner"):
        lines.append(f"forbidden_owner: {forbidden_owner}")
    if owner := result.get("owner"):
        lines.append(f"owner: {owner}")
    if capabilities := result.get("capabilities"):
        lines.append(f"capabilities: {', '.join(str(item) for item in capabilities)}")
    if url := result.get("url"):
        lines.append(f"url: {url}")
    if payload_path := result.get("payload_path"):
        lines.append(f"payload: {payload_path}")
    if history_path := result.get("history_path"):
        lines.append(f"history: {history_path}")
    lines.append(f"read_only={str(bool(result.get('read_only'))).lower()}")
    return "\n".join(lines) + "\n"


def _load_terminal_attach_owner_contract(*, profile: Any, study_id: str | None) -> dict[str, Any] | None:
    workspace_root = getattr(profile, "workspace_root", None)
    if workspace_root is None:
        return None
    root = Path(workspace_root).expanduser().resolve()
    candidate_paths = []
    if study_id:
        candidate_paths.append(root / "artifacts" / "runtime" / "terminal_attach" / "owners" / f"{study_id}.json")
    candidate_paths.append(root / "artifacts" / "runtime" / "terminal_attach" / "owner.json")
    for path in candidate_paths:
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    return None


REQUIRED_TOPICS = frozenset(("workspace.status", "runtime.health"))
TAIL_TOPICS = frozenset(("terminal.tail", "log.tail"))
REQUIRED_EVENT_FIELDS = ("source_ref", "observed_at", "sequence", "topic")


def render_sse_events(events: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> str:
    lines: list[str] = []
    for event in events:
        topic = str(event["topic"])
        sequence = int(event["sequence"])
        data = json.dumps(dict(event), ensure_ascii=False, separators=(",", ":"))
        lines.append(f"event: {topic}")
        lines.append(f"id: {sequence}")
        lines.append(f"data: {data}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _serve_loopback_live_console(
    *,
    runtime_live_console: Any,
    kwargs: dict[str, Any],
    profile: Any,
    enable_terminal_attach: bool,
    host: str,
    port: int,
    interval_seconds: int,
    output_format: str,
) -> int:
    bind_host = "127.0.0.1"

    class LiveConsoleHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/events"}:
                result = runtime_live_console.serve_live_console_stream(
                    **kwargs,
                    host=bind_host,
                    port=int(port),
                    interval_seconds=int(interval_seconds),
                )
                body = render_sse_events(_events_from_stream_result(dict(result))).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/terminal/status":
                payload = _terminal_status_payload(profile=profile, kwargs=kwargs, base_url="")
                self._write_json(payload, status_code=200 if payload.get("status") == "available" else 409)
                return
            self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            if not enable_terminal_attach:
                self._write_json(
                    terminal_attach_gate.blocked_by_missing_terminal_input_owner(
                        profile_ref=kwargs.get("profile_ref"),
                        study_id=kwargs.get("study_id"),
                        study_root=kwargs.get("study_root"),
                    ),
                    status_code=403,
                )
                return
            parsed = urlparse(self.path)
            operation = parsed.path.removeprefix("/terminal/").replace("-", "_")
            if operation not in {"attach", "input", "resize", "detach"}:
                self.send_error(404)
                return
            payload = self._read_json_body()
            result = _terminal_action(
                profile=profile,
                kwargs=kwargs,
                operation=operation,
                payload=payload,
            )
            self._write_json(result, status_code=200 if result.get("ok") is True else 409)

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return {}
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except json.JSONDecodeError:
                return {}
            return dict(payload) if isinstance(payload, dict) else {}

        def _write_json(self, payload: dict[str, Any], *, status_code: int) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    with http.server.ThreadingHTTPServer((bind_host, int(port)), LiveConsoleHandler) as server:
        resolved_host, resolved_port = server.server_address
        result = {
            "status": "serving",
            "surface_kind": "mas_live_console_stream",
            "url": f"http://{resolved_host}:{int(resolved_port)}/events",
            "host": resolved_host,
            "port": int(resolved_port),
            "interval_seconds": max(1, int(interval_seconds)),
            "read_only": True,
        }
        if enable_terminal_attach:
            base_url = f"http://{resolved_host}:{int(resolved_port)}"
            result["terminal_attach"] = _terminal_status_payload(profile=profile, kwargs=kwargs, base_url=base_url)
        if output_format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(render_live_console_command_text(result), end="")
        server.serve_forever()
    return 0


def _terminal_status_payload(*, profile: Any, kwargs: dict[str, Any], base_url: str) -> dict[str, Any]:
    context = _terminal_context(profile=profile, kwargs=kwargs)
    if context.get("ok") is not True:
        return {
            **terminal_attach_gate.blocked_by_missing_terminal_input_owner(
                profile_ref=kwargs.get("profile_ref"),
                study_id=kwargs.get("study_id"),
                study_root=kwargs.get("study_root"),
            ),
            "reason": context.get("reason"),
        }
    endpoints = {
        "attach": f"{base_url}/terminal/attach",
        "input": f"{base_url}/terminal/input",
        "resize": f"{base_url}/terminal/resize",
        "detach": f"{base_url}/terminal/detach",
    }
    return terminal_attach_gate.terminal_attach_status(
        owner_contract={
            "surface_kind": terminal_attach_gate.OWNER_SURFACE_KIND,
            "status": terminal_attach_gate.AVAILABLE_STATUS,
            "owner": "mas_terminal_attach_loopback",
            "capabilities": list(terminal_attach_gate.REQUIRED_CAPABILITIES),
            "owner_contract": list(terminal_attach_gate.REQUIRED_OWNER_CONTRACT_KEYS),
            "endpoints": endpoints,
        },
        profile_ref=kwargs.get("profile_ref"),
        study_id=context.get("study_id"),
        study_root=kwargs.get("study_root"),
    ) | {
        "quest_id": context["quest_id"],
        "run_id": context["run_id"],
        "runtime_root": str(context["runtime_root"]),
    }


def _terminal_action(*, profile: Any, kwargs: dict[str, Any], operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    context = _terminal_context(profile=profile, kwargs=kwargs)
    if context.get("ok") is not True:
        return {"ok": False, "status": "denied", "reason": context.get("reason"), "operation": operation}
    common = {
        "runtime_root": context["backend_runtime_root"],
        "quest_id": str(context["quest_id"]),
        "run_id": str(context["run_id"]),
        "study_id": str(context["study_id"]),
        "idempotency_key": _idempotency_key(payload, operation=operation),
        "source": "runtime_live_console.loopback_terminal_attach",
    }
    if operation == "attach":
        return mas_runtime_core.attach_terminal(**common)
    if operation == "input":
        return mas_runtime_core.terminal_input(
            **common,
            token=str(payload.get("token") or ""),
            lease_id=str(payload.get("lease_id") or ""),
            text=str(payload.get("text") or ""),
        )
    if operation == "resize":
        return mas_runtime_core.resize_terminal(
            **common,
            token=str(payload.get("token") or ""),
            lease_id=str(payload.get("lease_id") or ""),
            rows=int(payload.get("rows") or 0),
            cols=int(payload.get("cols") or 0),
        )
    if operation == "detach":
        return mas_runtime_core.detach_terminal(
            **common,
            token=str(payload.get("token") or ""),
            lease_id=str(payload.get("lease_id") or ""),
        )
    return {"ok": False, "status": "denied", "reason": "unknown_terminal_operation", "operation": operation}


def _terminal_context(*, profile: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    runtime_root = _managed_runtime_quests_root(profile)
    backend_runtime_root = _managed_runtime_home(profile=profile, quests_root=runtime_root)
    study_id = str(kwargs.get("study_id") or "").strip()
    candidates: list[tuple[str, dict[str, Any]]] = []
    quests_root = runtime_root
    if quests_root.is_dir():
        for quest_root in sorted(quests_root.iterdir(), key=lambda item: item.name):
            if not quest_root.is_dir():
                continue
            state = _read_json(quest_root / ".ds" / "runtime_state.json")
            active_run_id = str(state.get("active_run_id") or "").strip()
            if not active_run_id:
                continue
            if study_id and study_id not in {str(state.get("study_id") or "").strip(), quest_root.name}:
                continue
            lease = _read_json(quest_root / ".ds" / "runs" / active_run_id / "worker_lease.json")
            if lease.get("terminal_attach_capable") is True and state.get("worker_running") is True:
                candidates.append((quest_root.name, {"state": state, "lease": lease, "run_id": active_run_id}))
    if not candidates:
        return {
            "ok": False,
            "reason": "no_attach_capable_live_run",
            "runtime_root": runtime_root,
            "backend_runtime_root": backend_runtime_root,
            "study_id": study_id,
        }
    quest_id, item = candidates[0]
    state = item["state"]
    return {
        "ok": True,
        "runtime_root": runtime_root,
        "backend_runtime_root": backend_runtime_root,
        "quest_id": quest_id,
        "run_id": item["run_id"],
        "study_id": study_id or str(state.get("study_id") or quest_id),
    }


def _managed_runtime_quests_root(profile: Any) -> Path:
    value = getattr(profile, "managed_runtime_quests_root", None) or getattr(profile, "runtime_root", "")
    root = Path(value).expanduser().resolve()
    if root.name == "quests":
        return root
    quests_root = root / "quests"
    if quests_root.is_dir():
        return quests_root
    return root


def _managed_runtime_home(*, profile: Any, quests_root: Path) -> Path:
    value = getattr(profile, "managed_runtime_home", None)
    if value:
        return Path(value).expanduser().resolve()
    if quests_root.name == "quests":
        return quests_root.parent
    return quests_root


def _idempotency_key(payload: dict[str, Any], *, operation: str) -> str:
    value = str(payload.get("idempotency_key") or "").strip()
    if value:
        return value
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    import hashlib

    return f"live-console-{operation}-{hashlib.sha256(body.encode('utf-8')).hexdigest()[:24]}"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _events_from_stream_result(result: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    events = result.get("events")
    if isinstance(events, list | tuple):
        return tuple(dict(event) for event in events if isinstance(event, dict))
    model = result.get("session_read_model")
    if isinstance(model, dict) and isinstance(model.get("events"), list | tuple):
        return tuple(dict(event) for event in model["events"] if isinstance(event, dict))
    return (
        {
            "sequence": 1,
            "topic": "workspace.status",
            "observed_at": result.get("generated_at") or "",
            "source_ref": result.get("payload_path") or "live_console.session_read_model",
            "payload": result,
        },
    )


def _read_legacy_snapshot(
    *,
    runtime_live_console: Any,
    profile: Any,
    profile_ref: Path,
) -> dict[str, Any]:
    snapshot = runtime_live_console.read_live_console_snapshot(profile=profile, profile_ref=profile_ref)
    if isinstance(snapshot, dict):
        return snapshot
    to_dict = getattr(snapshot, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, dict):
            return payload
    raise SystemExit("runtime live console snapshot must be a mapping")


def _validated_events(snapshot: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    events = snapshot.get("events")
    if not isinstance(events, list | tuple):
        raise SystemExit("runtime live console snapshot must contain an events sequence")

    validated: list[dict[str, Any]] = []
    topics: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise SystemExit(f"runtime live console event[{index}] must be a mapping")
        missing = [field for field in REQUIRED_EVENT_FIELDS if field not in event]
        if missing:
            raise SystemExit(f"runtime live console event[{index}] missing required field: {missing[0]}")
        topic = event["topic"]
        if not isinstance(topic, str) or not topic.strip():
            raise SystemExit(f"runtime live console event[{index}] topic must be a non-empty string")
        observed_at = event["observed_at"]
        if not isinstance(observed_at, str) or not observed_at.strip():
            raise SystemExit(f"runtime live console event[{index}] observed_at must be a non-empty string")
        sequence = event["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int):
            raise SystemExit(f"runtime live console event[{index}] sequence must be an integer")
        topics.add(topic)
        validated.append(event)

    missing_topics = sorted(REQUIRED_TOPICS - topics)
    if missing_topics:
        raise SystemExit(f"runtime live console snapshot missing required topic: {missing_topics[0]}")
    if topics.isdisjoint(TAIL_TOPICS):
        raise SystemExit("runtime live console snapshot missing required topic: terminal.tail or log.tail")
    return tuple(validated)


__all__ = [
    "handle_live_console_command",
    "register_live_console_parsers",
    "render_live_console_command_text",
    "render_sse_events",
]
