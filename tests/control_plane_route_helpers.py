from __future__ import annotations

from typing import Any


def writable_route_context(
    *,
    paper_write_allowed: bool = True,
    bundle_build_allowed: bool = True,
    runtime_recovery_allowed: bool = True,
) -> dict[str, Any]:
    return {
        "authority_snapshot": {
            "surface": "authority_snapshot",
            "control_state": "ready",
            "canonical_next_action": "continue_bundle_stage",
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "dispatch_gate": {
                "state": "open",
                "blocking_reasons": [],
            },
            "route_authorization": {
                "authorized": paper_write_allowed and bundle_build_allowed and runtime_recovery_allowed,
                "paper_write_allowed": paper_write_allowed,
                "bundle_build_allowed": bundle_build_allowed,
                "runtime_recovery_allowed": runtime_recovery_allowed,
            },
        }
    }


__all__ = ["writable_route_context"]
