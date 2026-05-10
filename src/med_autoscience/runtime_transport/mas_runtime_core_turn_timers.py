from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any


_DELAYED_TIMERS_ENABLED = True
_DELAYED_TIMERS: list[threading.Timer] = []


def set_delayed_timers_enabled_for_tests(enabled: bool) -> None:
    global _DELAYED_TIMERS_ENABLED
    _DELAYED_TIMERS_ENABLED = enabled
    if not enabled:
        cancel_delayed_timers()


def arm_delayed_turn_timer(
    *,
    quest_root: Path,
    delay_seconds: float,
    source: str,
    drain_due_delayed_turn: Callable[..., dict[str, Any] | None],
) -> None:
    if not _DELAYED_TIMERS_ENABLED:
        return

    def _drain() -> None:
        try:
            drain_due_delayed_turn(quest_root=quest_root, source=f"{source}:timer")
        finally:
            prune_completed_timers()

    timer = threading.Timer(delay_seconds, _drain)
    timer.daemon = True
    _DELAYED_TIMERS.append(timer)
    timer.start()


def cancel_delayed_timers() -> None:
    for timer in list(_DELAYED_TIMERS):
        timer.cancel()
    _DELAYED_TIMERS.clear()


def prune_completed_timers() -> None:
    _DELAYED_TIMERS[:] = [timer for timer in _DELAYED_TIMERS if timer.is_alive()]


__all__ = [
    "arm_delayed_turn_timer",
    "cancel_delayed_timers",
    "prune_completed_timers",
    "set_delayed_timers_enabled_for_tests",
]
