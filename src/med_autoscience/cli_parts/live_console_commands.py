from __future__ import annotations

import argparse
import http.server
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable


LoadProfile = Callable[[str], Any]

REQUIRED_TOPICS = frozenset(("workspace.status", "runtime.health"))
TAIL_TOPICS = frozenset(("terminal.tail", "log.tail"))
REQUIRED_EVENT_FIELDS = ("source_ref", "observed_at", "sequence", "topic")


def register_live_console_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("runtime-live-console")
    parser.set_defaults(_command_parser=parser)
    parser.add_argument("--profile", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true")
    mode.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=4821)
    parser.add_argument("--format", choices=("sse", "json"), default="sse")


def handle_live_console_command(
    args: argparse.Namespace,
    *,
    parser: argparse.ArgumentParser,
    load_profile: LoadProfile,
    runtime_live_console: Any,
) -> int | None:
    if args.command != "runtime-live-console":
        return None

    profile_ref = Path(args.profile)
    profile = load_profile(args.profile)
    if bool(args.once):
        snapshot = _read_snapshot(
            runtime_live_console=runtime_live_console,
            profile=profile,
            profile_ref=profile_ref,
        )
        events = _validated_events(snapshot)
        if args.format == "json":
            _print_json(snapshot)
        else:
            print(render_sse_events(events), end="")
        return 0

    if bool(args.serve):
        command_parser = getattr(args, "_command_parser", None)
        if not isinstance(command_parser, argparse.ArgumentParser):
            command_parser = parser
        return _serve_sse(
            parser=command_parser,
            runtime_live_console=runtime_live_console,
            profile=profile,
            profile_ref=profile_ref,
            port=args.port,
        )

    return None


def render_sse_events(events: Sequence[Mapping[str, Any]]) -> str:
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


def _read_snapshot(
    *,
    runtime_live_console: Any,
    profile: Any,
    profile_ref: Path,
) -> dict[str, Any]:
    try:
        reader = getattr(runtime_live_console, "read_live_console_snapshot")
    except ModuleNotFoundError as exc:
        raise SystemExit("runtime live console read model is unavailable") from exc
    if not callable(reader):
        raise SystemExit("runtime live console read model must expose read_live_console_snapshot")
    snapshot = reader(profile=profile, profile_ref=profile_ref)
    if isinstance(snapshot, Mapping):
        return dict(snapshot)
    to_dict = getattr(snapshot, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    raise SystemExit("runtime live console snapshot must be a mapping")


def _validated_events(snapshot: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    events = snapshot.get("events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes, bytearray)):
        raise SystemExit("runtime live console snapshot must contain an events sequence")

    validated: list[Mapping[str, Any]] = []
    topics: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
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


def _serve_sse(
    *,
    parser: argparse.ArgumentParser,
    runtime_live_console: Any,
    profile: Any,
    profile_ref: Path,
    port: int,
) -> int:
    bind_port = _valid_port(port, parser=parser)

    class LiveConsoleHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path not in {"/", "/events", "/live-console/events"}:
                self.send_response(404)
                self.end_headers()
                return
            try:
                snapshot = _read_snapshot(
                    runtime_live_console=runtime_live_console,
                    profile=profile,
                    profile_ref=profile_ref,
                )
                payload = render_sse_events(_validated_events(snapshot)).encode("utf-8")
            except SystemExit as exc:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(str(exc).encode("utf-8"))
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:
            return None

    with http.server.ThreadingHTTPServer(("127.0.0.1", bind_port), LiveConsoleHandler) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}/events"
        _print_json({"status": "serving", "url": url, "bind_host": "127.0.0.1"})
        sys.stdout.flush()
        server.serve_forever()
    return 0


def _valid_port(port: object, *, parser: argparse.ArgumentParser) -> int:
    value = int(port)
    if value < 0 or value > 65535:
        parser.error("--port must be between 0 and 65535")
    return value


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


__all__ = [
    "handle_live_console_command",
    "register_live_console_parsers",
    "render_sse_events",
]
