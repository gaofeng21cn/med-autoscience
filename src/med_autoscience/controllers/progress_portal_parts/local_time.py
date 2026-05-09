from __future__ import annotations

import os

from med_autoscience.runtime_protocol import local_time_projection as _runtime_local_time


def local_time_projection(value: str, *, timezone_name: str | None) -> dict[str, str]:
    resolved_timezone = _non_empty_text(timezone_name) or system_timezone_name()
    return _runtime_local_time.local_time_projection(value, timezone_name=resolved_timezone)


def system_timezone_name() -> str:
    env_timezone = valid_timezone_name(timezone_name_from_localtime_target(os.environ.get("TZ", "")))
    if env_timezone is not None:
        return env_timezone
    symlink_timezone = valid_timezone_name(timezone_name_from_localtime_target(localtime_symlink_target()))
    if symlink_timezone is not None:
        return symlink_timezone
    return _runtime_local_time.system_timezone_name()


def localtime_symlink_target() -> str:
    return _runtime_local_time.localtime_symlink_target()


def timezone_name_from_localtime_target(value: object) -> str | None:
    return _runtime_local_time.timezone_name_from_localtime_target(value)


def valid_timezone_name(value: object) -> str | None:
    return _runtime_local_time.valid_timezone_name(value)


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
