from __future__ import annotations


SELECTED_DISPATCH_STAGE_PACKET_BLOCKERS = frozenset(
    {
        "stage_packet_not_current_selected_dispatch",
        "no_selected_dispatch_for_authorized_stage_packet",
    }
)


def is_selected_dispatch_stage_packet_blocker(blocker_type: str | None) -> bool:
    return blocker_type in SELECTED_DISPATCH_STAGE_PACKET_BLOCKERS


__all__ = [
    "SELECTED_DISPATCH_STAGE_PACKET_BLOCKERS",
    "is_selected_dispatch_stage_packet_blocker",
]
