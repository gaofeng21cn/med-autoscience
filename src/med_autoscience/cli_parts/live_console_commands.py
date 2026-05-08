from __future__ import annotations

import argparse
import http.server
import json
from pathlib import Path
from typing import Any, Callable


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
    if args.serve and not args.snapshot:
        return _serve_loopback_live_console(
            runtime_live_console=runtime_live_console,
            kwargs=kwargs,
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
    if url := result.get("url"):
        lines.append(f"url: {url}")
    if payload_path := result.get("payload_path"):
        lines.append(f"payload: {payload_path}")
    if history_path := result.get("history_path"):
        lines.append(f"history: {history_path}")
    lines.append(f"read_only={str(bool(result.get('read_only'))).lower()}")
    return "\n".join(lines) + "\n"


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
    host: str,
    port: int,
    interval_seconds: int,
    output_format: str,
) -> int:
    bind_host = "127.0.0.1"

    class LiveConsoleHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path not in {"/", "/events"}:
                self.send_error(404)
                return
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
        if output_format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(render_live_console_command_text(result), end="")
        server.serve_forever()
    return 0


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
