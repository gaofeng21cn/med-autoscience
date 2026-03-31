from __future__ import annotations

import re
from dataclasses import dataclass


FIGURE_ROUTE_SCRIPT_FIX = "figure_script_fix"
FIGURE_ROUTE_ILLUSTRATION_PROGRAM = "figure_illustration_program"
SUPPORTED_FIGURE_ROUTE_PREFIXES = (
    FIGURE_ROUTE_SCRIPT_FIX,
    FIGURE_ROUTE_ILLUSTRATION_PROGRAM,
)


@dataclass(frozen=True)
class FigureRoute:
    route_prefix: str
    figure_id: str

    def render(self) -> str:
        return f"{self.route_prefix}:{self.figure_id}"


def normalize_figure_token(raw_id: str, panel: str | None) -> str | None:
    token = str(raw_id).strip().upper()
    if not token:
        return None
    if token.startswith("S"):
        base = f"FS{token[1:]}"
    else:
        base = f"F{token}"
    panel_part = str(panel or "").strip().upper()
    return f"{base}{panel_part}" if panel_part else base


def normalize_figure_id(raw_figure_id: str) -> str:
    match = re.fullmatch(r"(?i)F(S?\d+)([A-Z])?", str(raw_figure_id).strip())
    if not match:
        raise ValueError(f"Invalid figure route target `{raw_figure_id}`")
    figure_id = normalize_figure_token(match.group(1), match.group(2))
    if figure_id is None:
        raise ValueError(f"Invalid figure route target `{raw_figure_id}`")
    return figure_id


def _normalize_route_prefix(route_prefix: str) -> str:
    normalized = str(route_prefix).strip().lower()
    if normalized == "sidecar":
        raise ValueError(
            "Ambiguous figure sidecar route is not allowed; use "
            "`figure_script_fix:<figure-id>` or `figure_illustration_program:<figure-id>`"
        )
    if normalized == "figure_illustration_sidecar":
        raise ValueError(
            "Deprecated figure illustration route is not allowed; use "
            "`figure_illustration_program:<figure-id>`"
        )
    if normalized not in SUPPORTED_FIGURE_ROUTE_PREFIXES:
        raise ValueError(
            f"Unsupported figure route prefix `{route_prefix}`; expected one of: "
            + ", ".join(f"`{item}`" for item in SUPPORTED_FIGURE_ROUTE_PREFIXES)
        )
    return normalized


def build_figure_route(route_prefix: str, figure_id: str) -> str:
    return FigureRoute(
        route_prefix=_normalize_route_prefix(route_prefix),
        figure_id=normalize_figure_id(figure_id),
    ).render()


def parse_figure_route(raw_route: str) -> FigureRoute | None:
    item = str(raw_route).strip()
    if not item or ":" not in item:
        return None
    route_prefix, raw_target = item.split(":", 1)
    return FigureRoute(
        route_prefix=_normalize_route_prefix(route_prefix),
        figure_id=normalize_figure_id(raw_target.strip()),
    )


def normalize_required_route(raw_route: str) -> str:
    item = str(raw_route).strip()
    if not item:
        return ""
    if item.lower() in SUPPORTED_FIGURE_ROUTE_PREFIXES:
        raise ValueError(f"Figure route `{item}` must include <figure-id>")
    parsed = parse_figure_route(item)
    if parsed is None:
        return item
    return parsed.render()


def normalize_required_routes(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values:
        item = normalize_required_route(raw)
        if not item or item in seen:
            continue
        normalized.append(item)
        seen.add(item)
    return normalized


def partition_required_routes(required_routes: list[str]) -> tuple[list[str], list[str], list[str]]:
    mainline_routes: list[str] = []
    script_fix_routes: list[str] = []
    program_routes: list[str] = []
    for route in required_routes:
        parsed = parse_figure_route(route)
        if parsed is None:
            mainline_routes.append(str(route).strip())
            continue
        if parsed.route_prefix == FIGURE_ROUTE_SCRIPT_FIX:
            script_fix_routes.append(parsed.figure_id)
        elif parsed.route_prefix == FIGURE_ROUTE_ILLUSTRATION_PROGRAM:
            program_routes.append(parsed.figure_id)
        else:
            raise ValueError(f"Unsupported normalized required route `{route}`")
    return mainline_routes, script_fix_routes, program_routes


def supported_required_route_help() -> str:
    return (
        "Supported forms: plain mainline routes such as `literature_scout`, plus explicit figure routes "
        "`figure_script_fix:<figure-id>` and `figure_illustration_program:<figure-id>`. "
        "The ambiguous legacy form `sidecar:<figure-id>` is rejected."
    )
