from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def local_time_projection(value: str, *, timezone_name: str | None) -> dict[str, str]:
    tz_name = _non_empty_text(timezone_name) or system_timezone_name()
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz_name = "UTC"
        tz = timezone.utc
    parsed = _parse_datetime(value)
    local_dt = parsed.astimezone(tz)
    return {
        "timezone": tz_name,
        "iso": local_dt.isoformat(),
        "label": f"{local_dt.strftime('%Y-%m-%d %H:%M:%S %z')[:-2]}:{local_dt.strftime('%z')[-2:]} {tz_name}",
    }


def system_timezone_name() -> str:
    env_timezone = valid_timezone_name(timezone_name_from_localtime_target(os.environ.get("TZ", "")))
    if env_timezone is not None:
        return env_timezone
    symlink_timezone = valid_timezone_name(timezone_name_from_localtime_target(localtime_symlink_target()))
    if symlink_timezone is not None:
        return symlink_timezone
    local_tz = datetime.now().astimezone().tzinfo
    key = getattr(local_tz, "key", None)
    if valid_timezone_name(key) is not None:
        return str(key)
    return "UTC"


def localtime_symlink_target() -> str:
    localtime = Path("/etc/localtime")
    try:
        if not localtime.is_symlink():
            return ""
        return str(localtime.readlink())
    except OSError:
        return ""


def timezone_name_from_localtime_target(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    text = text.removeprefix(":")
    markers = (
        "/zoneinfo/",
        "/usr/share/zoneinfo/",
        "/usr/lib/zoneinfo/",
        "/usr/share/lib/zoneinfo/",
        "/etc/zoneinfo/",
    )
    for marker in markers:
        if marker in text:
            text = text.rsplit(marker, 1)[1]
            break
    for prefix in ("posix/", "right/"):
        text = text.removeprefix(prefix)
    return text.strip("/") or None


def valid_timezone_name(value: object) -> str | None:
    name = _non_empty_text(value)
    if name is None:
        return None
    try:
        ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return None
    return name


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc).replace(microsecond=0)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
